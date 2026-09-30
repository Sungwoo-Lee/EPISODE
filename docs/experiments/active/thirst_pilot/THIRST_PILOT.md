---
title: "Level 06 (pond + thirst) training pilot: is the new world learnable and sane?"
topic: thirst_pilot
status: active
created: 2026-10-01
last_updated: 2026-10-01
wandb_tag: "rppo_l06pilot_*"
develop_link: docs/develop/active/thirst/THIRST_WATER_PLAN.md
---

# Level 06 (pond + thirst) training pilot

> **Status**: DESIGNED, Revision 1 (answers the plan review, §1.1). Nothing launched. No new
> config files are needed (§3.1). Nodes assigned by the user (§3).
> **Branch**: `v5.0`, worktree `.claude/worktrees/thirst`. Water exists only there. Every launch
> runs the worktree's code, from the worktree. **Every output is written to the shared project
> folder**, outside any worktree (§2.5).
> **Related**: [[THIRST_WATER_PLAN]] (how water and thirst were built and verified) ·
> [[thirst_water]] (design page with the simulated difficulty) · [[LEVEL05_BODY_INTERACTIONS]]
> (source of the level-05 reference runs) · [[BASIC_LEVELS_Q2_DEFAULT]] (the ladder)

---

## 1. Question

The grid world now has a fourth body need, **thirst**, and **one pond per episode** to drink from.
The new ladder level 06 adds them to the campfire world of level 05. Hydration drains slowly.
Resting away from water kills in 160 steps. Drinking too much also kills: standing on the pond for
20 steps from the comfortable level is fatal. The pond is out in the open, so drinking means
exposure to predators.

The research reason for water is that the right action now depends on **combinations** of body
states (thirsty *and* hungry *and* cold *and* hurt). That is where an agent with a neuromodulator
(a small side network that rescales the main network according to what the body feels) should
beat an ordinary agent. **This pilot does not test that comparison.** It checks that the world is
fit for it. It trains the ordinary and the modulated agent for a short budget and asks five
things:

1. **Do both agents learn to drink?** Deaths from thirst should fall over training, and pond
   visits should rise.
2. **How do agents die by the end?** Is any single cause of death, such as thirst or
   over-drinking, absurdly dominant?
3. **How long do they survive** compared with the same agents in the level-05 world at the same
   budget? Existing level-05 runs serve as the reference, so they are not re-run.
4. **What does water cost in real training speed?** The bare environment is 9.8 % slower on a
   GPU. The question is how much of that reaches a whole training run.
5. **Did the runs really execute the new code?** The shared project folder is on the older
   branch, which has no water. A run that silently imported it would be invalid.

Each question has a pass line and a flag line fixed in advance (§2.7). A flag means "stop and show
the user". It does not mean "the world is broken". No outcome of this pilot is a claim about the
modulator.

### 1.1 Revision 1 — response to review (2026-10-01)

The plan review ([[plan_thirst_pilot]], verdict NOT READY, appended at the end) found one
critical problem: checkpoints and logs would have lived inside the worktree, which a routine
`git worktree remove` deletes silently. The user decided on the fixes on 2026-10-01. They also
declined the optional training-log counters and assigned the nodes.

| Finding | Change |
|---|---|
| C1: outputs in the worktree | Code still runs from the worktree, but **every output goes to the shared folder**: checkpoints via `--results-dir <shared>/results/JAX_RecurrentPPO/<ts>_<TAG>`, logs via `run_command.py --log <shared>/logs/…`, and WandB's local files via `WANDB_DIR=<shared>` (checked: `wandb.init` gets no `dir=`, and wandb 0.24 honours `WANDB_DIR`; offline test wrote under `$WANDB_DIR/wandb/`). The §4.2 stores go to `<shared>/results/analysis/thirst_pilot/`. A diary note goes in at launch (§3.2). No copy step is needed. |
| M1: speed read-out was a running mean | P4 is now Δ`timesteps` / Δ`_runtime` between the step row nearest 50 % of the run and the last row. The reference speeds in §2.7 were re-read the same way. |
| M2: WandB-metadata check could kill a valid run | Runs are gated on P5 (a), (b), (c), (e). (d) is informational until the first `wandb-metadata.json` has been read. An `"unknown"` sha in provenance falls back to the manifest's HEAD plus (a). |
| M3: drinking pass line ignored the unavoidable floor | Pass = last-tenth dehydration ≤ 0.10 **and** ≤ max(0.5 × first tenth, floor + 0.03). The floor is measured from the 0.4 M store. |
| L1 | P5(a): the log *contains* the gate line (JAX warnings may come first). |
| L2 | §4.2 names checkpoints as "nearest 0.4 M / 1.2 M" plus `final`, and checks that `final` ≥ 2,000,000. |
| L3 | The "≥ 80 % of past-deadline episodes drank" line is now a data-integrity check, not a pass line. |
| L4 | §4.2: a reader under `scripts/` updates `SCRIPTS_DEPENDENCY_MAP.md` in the same commit. Seeds are read from the top-level `seed:` or provenance `argv`, never `training.seed`. |
| L5 | §2.5 "The problem" corrected: the worktree's `run_command.py` derives its default log folder from its own location. |
| A2 (git on nodes) | `which git` is added to the pre-flight (§3.2). |
| A4 (reset cost) | Added to P4: if the 15 % flag trips, reset-rate cost is separated from water-op cost before concluding. |

---

## 2. Design

### 2.1 Runs

| Factor | Values | Why |
|---|---|---|
| World | level 06 (pond + thirst); level 05 (campfire, no water) as a **same-code control**, one run | The control is the only clean throughput reference (same code, same card, same time; §2.7 P4). It also checks that level-05 training still reproduces on `v5.0` (P5b). |
| Agent | ordinary (`t1none`: no modulator); modulated (`t16quad`: FiLM modulator writing to encoder, recurrent core, actor and critic, reading every sensor) | The matched pair used in every recent level-05 run (§2.2) |
| Seed | 42, 43, 44 on level 06; 42 on the control | 3 seeds is the project minimum. It also gives the seed spread on level 06 that the later modulator comparison needs to size itself. |

In total there are **7 runs**: 2 agents × 3 seeds on level 06, plus 1 control.

### 2.2 Agent configs: a change from the pair named in the request

The request named `recurrent_ppo_nmn_het_unmod.yaml` / `recurrent_ppo_nmn_het_film_g1.yaml`. Both
build and train at width 59 (checked 2026-10-01, CPU smoke on level 06, exit 0). **They are not the
current matched pair, though.** They come from the May noise-heterogeneity sweep: Monte-Carlo
returns, and a FiLM modulator on encoder and recurrent core only, with the legacy gate-bias
operator and temperature on.

Every level-05 run since the input × site grid uses
`nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` (ordinary) and `nmngaenorm_t16quad_ALL.yaml`
(modulated). That covers Wave 2 of [[BASIC_LEVELS_Q2_DEFAULT]], the three level-05 pilots and the
32-run factorial of [[LEVEL05_BODY_INTERACTIONS]]. The two files are identical except for
`modulation` (GAE_NORM returns, γ = 0.95). **Question 3 needs a like-for-like level-05 reference,
and only this pair has one.** Using the older pair would mean training new level-05 references
too.

Both were checked on level 06 (CPU smoke, 300 episodes, exit 0):
- `t1none` prints `Observation Dim: 59 (… Body Temperature=1, Hydration=1 …)` and
  `Neuromodulation: DISABLED (baseline)`;
- `t16quad` prints the same width and
  `Neuromodulation: ENABLED (type=FiLM, … sites=[encoder,rnn,actor,critic], rnn_mechanism=activation, temperature=off)`.

The modulator's `input_sensors: "all"` is width-agnostic. The header comment's "27 of the 27
observation numbers" is stale text, not a value that is read.

**If the user prefers the older pair**, the pilot still runs. Question 3 then has no reference and
two more level-05 runs are needed.

### 2.3 Budget

**2,000,000 training episodes per run**, the same as the three unchanged level-05 pilots (P0a–c in
[[LEVEL05_BODY_INTERACTIONS]] §3.0). The same budget makes question 3 a direct comparison, over the
same episode window, with the same agent and the same launch flags. At level 05 the ordinary agent
reaches about 90 % of its 2 M value by 1.4 M episodes (tenths below). So 2 M is long enough to see
whether drinking is learned, and short enough to be a pilot.

Nothing in the trainer is keyed to the episode budget: no learning-rate or entropy schedule
(checked in the plan review appended to [[LEVEL05_BODY_INTERACTIONS]]). A 2 M run is therefore the first 2 M episodes of
any longer run with the same seed.

### 2.4 Controls (pinned)

- **World:** level 06 = `basic/06-pond_thirst_10x10.yaml` as committed on `v5.0`. It is level 05
  plus water. The pond is 2×2, at one of the four quadrant spots drawn per episode. Drain is 0.625
  per step, net drink +5 per step, maximum 200, setpoint 100. Start hydration is random over
  [0, 200) (user decision 2026-09-29). The observation has 59 numbers.
- **Level-05 ladder unchanged since the references:** `git diff 8187c570 HEAD` touches only
  `default.yaml` (the `water:` block, switched off; byte-parity is proven by the plan's 43/43
  parity tests) and `configs/train/` (balance metrics logging, which is documented as training-
  bit-identical on or off). `basic/03`, `04` and `05` are untouched.
- **Launch flags** as the level-05 pilots: `--episodes 2000000 --log-interval 10`. Seed 42 is
  config-owned. Seeds 43/44 pass `--seed` (flagged deviation, as P0b/P0c did). `num_envs` (128) and
  `checkpoint_frequency` (200,000 episodes → 10 checkpoints, all kept) are config-owned.
- **Hardware (user-assigned, Revision 1):** all seven runs are on **RTX 2080 Ti** cards, on nodes
  101, 103, 104 and 105 (§3). The throughput pair (runs 1 and 7) share node 101, GPUs 0 and 1, and
  are launched within a minute of each other. The references ran on RTX 3090 (P0a–c, `w0000 m`)
  and RTX 2080 Ti (`w0000 o`). The card affects speed, not what is learned per episode, so Q3 is
  unaffected. Q4 reads only the same-card pair.

### 2.5 Launch path: running `v5.0` code from the worktree

**The problem.** Two things point the *code* at the shared folder, which is on `v4.0` and has no
water. The header of `train_command-agent.sh` does
`cd /media/nas01/projects/Interoceptive-AI/grid_world_pain`, and the conda env has an editable
install whose `.pth` puts `<shared>/src` on `sys.path`. (`run_command.py` is harmless here. Each
copy derives its default log folder from its own constant (`run_command.py:40-43`), and this pilot
passes `--log` explicitly anyway.)

Code and outputs go in **different** places on purpose (user decision C1, 2026-10-01). The code
runs from the worktree, because only `v5.0` has water. The outputs go to the shared folder, because
a worktree exists to be deleted, and `git worktree remove` deletes gitignored files without asking.

**What was checked (2026-10-01).**
- `src` has no `__init__.py`: it is a namespace package. With the working directory at the
  worktree root, `src.__path__` is exactly `[<worktree>/src]`, and `src.__file__` is `None`. So
  "log `src.__file__`" **cannot** serve as the check. The gate below checks `src.__path__`.
- The editable `.pth` adds `<shared>/src` itself. That makes `environment`, `models`, `utils` and
  the rest importable as **bare** top-level names from the shared folder. A scan of `train.py`,
  `src/` and `scripts/eval/` found no bare import of those names. Everything goes through `src.`.
  So `python train.py` from the worktree imports only worktree code. The mixing the developer saw
  was in `tests/algorithms/`, which the trainer does not run.
- The trainer's subprocesses (checkpoint video render) and `provenance.py` find the repo root from
  their own `__file__`. They follow the worktree.
- The gate was tested both ways. From the worktree it prints `OK` (1,939 modules checked, none from
  the shared `src/`). With `PYTHONPATH=<shared root>` forced, it exits 1:
  `src resolves to [<worktree>/src, <shared>/src]`.

**No launcher change is needed.** The runner already launches through a unique `/tmp` script on
the node (its CIFS-bypass rule). For this pilot, that script (a) `cd`s into the **worktree**, not
the shared folder, (b) runs the gate, then (c) runs `train.py` with every output directed into
the shared folder. `run_command.py` is used unchanged, with `--log` pointing at the shared
`logs/`. Neither `run_command.py` nor any shared-folder script is edited. No shared-folder file is
modified: the pilot only **adds** new run directories under `results/`, `wandb/` and `logs/`, which
is what every training run does.

**The `/tmp` launch script, per row** (fill in `<GPU>`, `<ENV_CFG>`, `<AGENT_CFG>`, `<SEED_FLAG>`,
`<TAG>` from §3 and §3.1; `<TS>` is the launch timestamp `YYYYmmdd_HHMMSS`, the same one used in the
log name):

```bash
#!/bin/bash
set -euo pipefail
WT=/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst
SHARED=/media/nas01/projects/Interoceptive-AI/grid_world_pain
PY=/home/vncuser/miniconda3/envs/grid_world_pain/bin/python
# WandB's local run files go to $SHARED/wandb/run-*, next to every other run (train.py passes no dir=).
export WANDB_DIR="$SHARED"
cd "$WT"
# --- v5.0 code-origin gate (THIRST_PILOT §2.5). CPU-only; never touches the GPU. ---
JAX_PLATFORMS=cpu "$PY" - <<'PYEOF'
import os, sys, subprocess
WT = os.path.realpath(os.getcwd())
SHARED_SRC = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/src/"
def fail(msg): sys.exit(f"[v5-gate] FAIL: {msg}")
sys.argv = ["train.py"]
import src
paths = [os.path.realpath(p) for p in src.__path__]
if paths != [os.path.join(WT, "src")]: fail(f"src resolves to {paths}")
import train  # train.py's whole import graph; main() is guarded by __name__ == "__main__"
bad = sorted({os.path.realpath(m.__file__) for m in list(sys.modules.values())
              if getattr(m, "__file__", None) and os.path.realpath(m.__file__).startswith(SHARED_SRC)})
if bad: fail(f"modules loaded from the shared folder: {bad[:5]}")
from src.environment.state import EnvParams
if "water_enabled" not in EnvParams.__dataclass_fields__: fail("imported code has no water")
br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True,
                    text=True, cwd=WT, timeout=120).stdout.strip()
if br != "v5.0": fail(f"worktree branch is {br!r}")
print(f"[v5-gate] OK src={paths[0]} branch={br} train={os.path.realpath(train.__file__)} "
      f"modules={len(sys.modules)}", flush=True)
PYEOF
exec "$PY" train.py \
  --config <ENV_CFG> \
  --agent_config <AGENT_CFG> \
  --episodes 2000000 --device cuda:<GPU> --log-interval 10 <SEED_FLAG> \
  --results-dir "$SHARED/results/JAX_RecurrentPPO/<TS>_<TAG>" \
  --tag <TAG> --wandb-name <TAG> \
  --wandb-group thirst_pilot --wandb-job-type pilot
```

`--results-dir` is used exactly as given (`train.py:939-942`), so the runner supplies the full
per-run path. That keeps the project's usual `<ts>_<tag>` naming.

The gate runs in stdin mode (`python -`). That puts the working directory first on `sys.path`, the
same as `python train.py` does for the script's own directory. **Do not** save the gate as a file
elsewhere and run it by path: `sys.path[0]` would then be that file's directory and `import src`
would fail.

**Launch call** (from the worktree, once per row; the runner's usual `--no-tail`, no local
`timeout`):

```bash
./run_command.py --no-tail \
  --log /media/nas01/projects/Interoceptive-AI/grid_world_pain/logs/<TS>_<TAG>.log \
  <NODE> "bash $TMP_SCRIPT"
```

**Audit record.** The runner appends the commented command block for each row to the
**worktree's** `train_command-agent.sh`, which is tracked on `v5.0`. It never edits the shared
folder's copy. It must **not** copy that file's header `cd` into the `/tmp` script. The `/tmp`
script above is complete as written.

**Where outputs land (user decision C1, 2026-10-01).**

| Output | Location | How |
|---|---|---|
| Checkpoints, saved config, provenance, checkpoint videos | `<shared>/results/JAX_RecurrentPPO/<TS>_<TAG>/` | `--results-dir` |
| Local WandB run files | `<shared>/wandb/run-<date>-<id>/` | `WANDB_DIR=<shared>`. wandb 0.24 reads it when `init` gets no `dir=`, which is the case in `train.py:1023-1030`. Checked with an offline `wandb.init` (2026-10-01): the run folder appeared under `$WANDB_DIR/wandb/`. No copy step is needed. |
| nohup log | `<shared>/logs/<TS>_<TAG>.log` | `run_command.py --log` |
| Stored episodes (§4.2) | `<shared>/results/analysis/thirst_pilot/` | `--out-root` |

Nothing the pilot produces is inside the worktree, so removing the worktree loses no data. **One
consequence:** the shared `results/` will hold 59-wide water runs, but the shared folder's `v4.0`
code does not know water. Any tool that reads these runs must run from the worktree (or from
`v5.0` once it is merged). §4.4 lists the tools that must not be used.

### 2.6 Confounds and limits

| Confound | Affects | Severity | Handling |
|---|---|---|---|
| Level-05 references ran on older code (`4209024d`, `f00f6c61`), without balance metrics | Q3 survival, Q4 speed | Low for survival (the level-05 world and training path are unchanged, §2.4). High for speed | Q4 uses only the same-code control pair. The historical speed is secondary. |
| Card model differs across rows | Q4 | High if uncontrolled | Q4 reads only the pair on one node |
| Random start hydration kills some episodes early whatever the agent does (simulated 1.8–2.4 %; upper bound ~5 % by step 16) | Q1, Q2, Q3 | Medium | Early (≤ 20 steps) and late deaths are reported apart (`Bal_EarlyDeathShare` / `Bal_LateDeath_*`). Survival is also reported by start-hydration band (§4.3). |
| WandB survival comes from the exploring **training** policy; stored episodes come from the greedy policy | Q2, Q3 | Medium | Never pooled. The references are training-policy windows, so Q3's primary number is too. |
| `w0000 m` is a single seed | Q3 (modulated) | Medium | The modulated comparison is descriptive; the ordinary agent carries Q3 |
| Two runs per node share CPU and NAS | Q4 | Low | Both members of the pair share the same load |

### 2.7 Predictions and pre-registered criteria

**Level-05 reference values** (read 2026-10-01). Survival and death shares come from WandB sampled
history, `_window_n`-weighted, episodes 1.8–2.0 M; the analyzer re-reads them exactly. Speed is
defined as in P4: Δ`timesteps` / Δ`_runtime` from the step row nearest 50 % of the run to the last
row. It was read from the full step history for P0a–c. For the two 10 M `w0000` runs, the full scan
did not finish within the session's time limit, so their speed is the whole-run value (last row's
`timesteps` / `_runtime`). On P0a–c that differs from the windowed value by 1.1–1.5 %.

| Run (level 05, 2 M episodes) | Survival S | Starvation | Injury | Thermal | Step limit | Speed (env steps/s) |
|---|---|---|---|---|---|---|
| P0a ordinary s42 (3090) | 228.3 | 0.264 | 0.431 | 0.033 | 0.273 | 44.6 k |
| P0b ordinary s43 (3090) | 225.8 | 0.261 | 0.439 | 0.030 | 0.270 | 43.2 k |
| P0c ordinary s44 (3090) | 228.6 | 0.268 | 0.433 | 0.029 | 0.270 | 44.6 k |
| `w0000` ordinary s42, first 2 M of 10 M (2080 Ti) | 227.8 | 0.283 | 0.415 | 0.032 | 0.270 | 32.9 k (whole run) |
| `w0000` modulated s42, first 2 M of 10 M (3090) | 228.4 | 0.265 | 0.435 | 0.029 | 0.272 | 34.9 k (whole run) |

Ordinary agent: S_05 = **227.6**, seed s.d. **1.5** (P0a–c). Survival by tenth of training (0–2 M),
P0a: 51, 88, 140, 174, 200, 206, 214, 220, 225, 228.

**P1: both agents learn to drink.** Read per run.
- *Floor* (measured before judging, from the 0.4 M store, §4.2): the share of episodes that
  **cannot** reach water before dying of thirst whatever the policy does. That is, their no-drink
  deadline (1.6 × start hydration, in steps) is no longer than the grid distance from the start
  cell to the nearest cell of that episode's pond. The floor depends only on the episode's start
  and not on the policy, so any store measures it. It is a lower bound: it ignores detours forced
  by obstacles and predators.
- *Pass (Revision 1):* the dehydration share (`Episode/Term_Dehydration`) in the last tenth
  (1.8–2.0 M) is **≤ 0.10 and ≤ max(0.5 × first-tenth share, floor + 0.03)**, **and** the
  per-episode drinking-bout count rises from the 0.4 M store to the 2.0 M store.
- *Data-integrity check (not a pass line):* in every store, 100 % of episodes that outlive their
  own no-drink deadline drank at least once. That is true by construction, so anything below 100 %
  means the reader or the store is wrong, and the P1 numbers are not used until it is fixed.
- *Prediction:* last-tenth dehydration share 0.03–0.08 (the early-death floor plus a few late
  misses). Late dehydration (`Bal_LateDeath_Dehydration`) falls monotonically after the first two
  tenths. The design page's scripted agent made about 1.7 pond visits per episode; a trained agent
  should be within a factor of 2 of that.
- *Flag:* any run fails the pass line, **or** the dehydration share is still flat over the last
  three tenths while above 0.10.

**P2: no absurdly dominant cause of death.** Mean over seeds, per agent, last tenth; all seven
`Term_*` shares.
- *Flag (any one):* a single cause > **0.60** of all episodes (the largest at level 05 is injury,
  0.43); dehydration > **0.25**; over-drinking > **0.10**; or the seven shares do not sum to 1 ± 0.01
  (a dropped code).
- *Prediction:* injury stays the largest cause (0.35–0.45). Starvation 0.2–0.3. Dehydration
  0.03–0.12. Over-drinking < 0.02: it needs 20 unbroken steps on the pond from the setpoint, and one
  move always exits. Step limit below level 05's 0.27.

**P3: survival against level 05.** S_06 = the `_window_n`-weighted mean of `Episode/Steps` over
1.8–2.0 M, mean over 3 seeds, compared with S_05 (ordinary 227.6; modulated 228.4).
- *Prediction:* S_06 is **5–25 % below** S_05 (about 171–216 steps). The scripted agent lost 3
  points of full-length episodes to water. A learning agent pays more, in exposure, detours, a
  fourth clock and early thirst deaths. Seed spread on level 06 stays below 3 % of S_06.
- *Flag, too hard:* S_06 < **0.5 × S_05** (< 114 steps).
- *Flag, water does not bite:* S_06 ≥ S_05 − 2 steps **and** P1's pond-visit count is below 1 per
  episode.
- *Not converged* (reported, not a flag): the last-tenth S exceeds the ninth-tenth S by more than
  2 %.
- The modulated-minus-ordinary difference on level 06 is reported, with its seed spread, as
  **descriptive only**.

**P4: training-speed cost.** Speed = Δ`timesteps` / Δ`_runtime` between the step row nearest 50 %
of the run's final `timesteps` and the last row. Compile and warm-up fall outside that window.
(`Time/sps_env` is **not** used: it is `global_step` / seconds since start, a running mean over the
whole run, `train.py:2003`.) Ratio = run 1 (level 06) / run 7 (level 05), same node (101) and
card.
- *Prediction:* level 06 is **0–10 % slower**. An rPPO iteration spends much of its time in the
  network update, not the environment, so less than the full 9.8 % bare-env cost should reach
  training.
- *Flag:* > **15 %** slower, the plan's own block line for the bare environment. If it trips,
  separate before concluding: level 06's shorter episodes mean more resets per step, which costs
  time independently of the water operations.
- *Secondary, reported:* hours per 2 M episodes. This also depends on episode length, which differs
  between worlds. Also the modulated/ordinary speed ratio on level 06.

**P5: the runs executed `v5.0` code.** Every run must pass (a), (b), (c) and (e). A run that fails
any of them is **invalid**: it is stopped and not analysed, whatever its numbers. (d) is
informational (Revision 1).
- (a) The log **contains** `[v5-gate] OK src=<worktree>/src branch=v5.0 …`. JAX warnings may come
  before it.
- (b) The banner prints `Observation Dim: 59 (… Hydration=1 …)` on level 06 and `58` (no
  Hydration) on the control.
- (c) `models/provenance.json` (now under the shared `results/`) shows `branch: v5.0` and
  `git_sha` equal to the launch commit the runner records in the manifest. Any of the three git
  fields may read `"unknown"`, because all share the helper's 10 s git timeout on this NAS. An
  `"unknown"` sha or branch falls back to the manifest's recorded HEAD plus (a), and does not
  invalidate the run. `git_dirty: "unknown"` is accepted.
- (d) *Informational until observed.* WandB run metadata: `program`, `root` and the commit. These
  values come from WandB's own detection and have never been observed for a worktree launch. With
  `WANDB_DIR` pointing at the shared folder, `root` may well name the shared folder rather than the
  worktree. After the first run, the runner reads its `wandb-metadata.json`, records the observed
  values here, and from then on only the commit (= (c)'s sha) is compared. A mismatch is reported,
  but it does not stop a run that passes (a)–(c) and (e).
- (e) The saved `models/config.yaml` and the WandB config show `water.enabled: true` on level 06
  and `false` on the control. On level 06, `Episode/Term_Dehydration` is non-zero in at least one
  logged window.

**P5b: level 05 still trains the same on `v5.0`** (control run 7).
- *Pass:* S_ctl lies within **228.3 ± 6** steps, which is P0a (same seed, same world) ± about 4 seed
  s.d.
- *Flag:* outside that band. That would mean the training path changed under level 05, and every
  level-06 versus level-05 comparison would be suspect until explained.

---

## 3. Launch Manifest

| Run | Status | Cell | Tag (= wandb-name) | wandb-group | wandb-job-type | Seed | Node | GPU | Launched at | WandB run ID | Log path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | planned | L06 ordinary (throughput pair A) | `rppo_l06pilot_t1none_s42` | thirst_pilot | pilot | 42 | 101 | cuda:1 | — | — | — |
| 2 | planned | L06 ordinary | `rppo_l06pilot_t1none_s43` | thirst_pilot | pilot | 43 | 103 | cuda:0 | — | — | — |
| 3 | planned | L06 ordinary | `rppo_l06pilot_t1none_s44` | thirst_pilot | pilot | 44 | 103 | cuda:1 | — | — | — |
| 4 | planned | L06 modulated | `rppo_l06pilot_t16quad_s42` | thirst_pilot | pilot | 42 | 104 | cuda:0 | — | — | — |
| 5 | planned | L06 modulated | `rppo_l06pilot_t16quad_s43` | thirst_pilot | pilot | 43 | 104 | cuda:1 | — | — | — |
| 6 | planned | L06 modulated | `rppo_l06pilot_t16quad_s44` | thirst_pilot | pilot | 44 | 105 | cuda:0 | — | — | — |
| 7 | planned | L05 control, `v5.0` code (throughput pair B) | `rppo_l06pilot_l05ctl_t1none_s42` | thirst_pilot | pilot | 42 | 101 | cuda:0 | — | — | — |

**Node and GPU assignment:** made by the user on 2026-10-01 from a live check. All seven cards are
free RTX 2080 Ti (11 GB; level-05 rPPO trained on this card before, `w0000` ordinary). The
throughput pair is on node 101, run 7 on GPU 0 and run 1 on GPU 1, launched back to back. The rest
are packed node-first (103, then 104, then 105). The runner still does its own pre-launch
free-check on each card.

All seven tags are unique. No WandB run name contains `l06pilot` and the group `thirst_pilot` is
unused (WandB API query, 2026-10-01). The runner confirms before launch that no
`<shared>/results/JAX_RecurrentPPO/*l06pilot*` directory exists. The
branch is not written into names: it is recorded in `provenance.json` and in WandB metadata, and
the group `thirst_pilot` exists only on `v5.0`. In the Log-path cell the runner also records
`git rev-parse HEAD` of the worktree at launch, for P5c/d.

### 3.1 Configs (all existing; none produced)

| Run | Env config | Agent config | `<SEED_FLAG>` |
|---|---|---|---|
| 1 | `configs/environment/experiment/basic/06-pond_thirst_10x10.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` | *(none; config-owned 42)* |
| 2 | same as 1 | same as 1 | `--seed 43` |
| 3 | same as 1 | same as 1 | `--seed 44` |
| 4 | `configs/environment/experiment/basic/06-pond_thirst_10x10.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t16quad_ALL.yaml` | *(none)* |
| 5 | same as 4 | same as 4 | `--seed 43` |
| 6 | same as 4 | same as 4 | `--seed 44` |
| 7 | `configs/environment/experiment/basic/05-campfire_thermal_10x10.yaml` | `configs/models/recurrent_ppo/nmn_input_site_grid_gaenorm/nmngaenorm_t1none.yaml` | *(none)* |

The level-06 config was reviewed by `env-config-reviewer` during implementation
(`docs/reviews/env_config_review_thirst_water.md`: two 🟡, no 🔴). Since then it has changed only
in comments. No registry setting changes, so no `CONFIG_CRITICAL_SETTINGS.md` entry is needed.

### 3.2 For the training-runner

- **GPUs:** 7, as assigned in the table above (all RTX 2080 Ti). Runs 7 and 1 go on 101:0 and
  101:1, launched back to back.
- **Per-run budget:** `--episodes 2000000`, `--log-interval 10`, 10 checkpoints (every 200 k).
- **Expected wall time on a 2080 Ti:** the level-05 pilots took 2.1–2.2 h on a 3090, and a 2080 Ti
  runs this job about 30 % slower (32.9 k versus about 44 k env steps/s). So expect the ordinary
  agent at about 3–4 h and the modulated agent at about 3.5–4.5 h. Level 06 may finish a little
  sooner if its episodes are shorter. Total about 25 GPU-hours. The last run should finish about
  4.5 h after launch.
- **Pre-flight additions** to the runner's usual checks:
  - the NAS is mounted on the node, and
    `/media/nas01/projects/Interoceptive-AI/grid_world_pain/.claude/worktrees/thirst/train.py` is
    readable from it;
  - `which git` succeeds on the node (the gate and provenance need it);
  - `git rev-parse --abbrev-ref HEAD` in the worktree prints `v5.0`, and the worktree is clean, so
    the provenance sha describes the code;
  - no `<shared>/results/JAX_RecurrentPPO/*l06pilot*` directory exists yet.
- **Diary note at launch (user decision C1):** one `note` row saying that the seven
  `rppo_l06pilot_*` runs execute code from the worktree `.claude/worktrees/thirst` (branch `v5.0`),
  and that the worktree must not be removed, and `v5.0` must not be switched or reset, until all
  seven runs have finished. The outputs themselves are in the shared folder and are safe either
  way. A running job, however, reads its code from the worktree (checkpoint-time renders start new
  processes from it).
- **Post-launch (after the usual 3–8 min wait):** check P5 (a) and (b) in the log. Check (c) once
  `models/provenance.json` exists. Record the WandB run ID and the HEAD sha in the manifest. After
  the first run, read its `wandb-metadata.json` (under `<shared>/wandb/run-*-<id>/files/`) and
  record `program` / `root` for P5(d).

---

## 4. Analysis plan (pre-specified)

### 4.1 Training-log reads (WandB; primary for P1–P4)

- Every `Episode/*` value is a rolling-window mean. Windows are combined weighted by
  `Episode/_window_n` and selected by `Episode/Number`, as in [[LEVEL05_BODY_INTERACTIONS]] §2.3.
  Reward is never read.
- **Temporal evolution (mandatory):** tenth-by-tenth (200 k-episode bins) series for
  `Episode/Steps`, all seven `Term_*`, `Bal_EarlyDeathShare`, `Bal_LateDeath_Dehydration`,
  `Bal_LateDeath_Overdrinking`, and the existing balance keys (`Bal_TimeBush`, `Bal_TimeEat`,
  `Bal_TimeWarm`, and the hiding and eating ratios), both agents, per seed and seed-mean.
- **Throughput:** Δ`timesteps` / Δ`_runtime`, from the step row nearest 50 % of final `timesteps` to
  the last row (P4). Step rows are a different row set from the `Episode/*` rows.
- **Local binaries** for the pilot are in `<shared>/wandb/run-*-<id>/` (`WANDB_DIR`). The reference
  runs can be read through the WandB API. Use the same read (full or sampled) for pilot and
  reference values.
- **Seeds:** read each run's seed from the saved config's **top-level** `seed:` or from
  provenance `argv`, never from `training.seed`. That nested copy always reads 42 (Known Bugs
  registry, stale second copy of the seed).

### 4.2 Stored episodes (greedy policy; P1 pond visits, P3 by start hydration)

With the worktree's `scripts/eval/traj_collect/collect_trajectories.py`, run **from the worktree**
on CPU, per run: the checkpoint **nearest 0.4 M**, the one **nearest 1.2 M**, and `final`.
Checkpoint keys are the episode count at save time (for example `400123`), not round numbers, so
list `models/` and pass the nearest key. Before using `final`, check it is ≥ 2,000,000, so that it
is really the end of training. Use `--episodes 10000`, `--obs-precision float32` and a fixed
`--seed-base` shared by all runs. `--run` is the shared-folder run directory. Out-root:
`<shared>/results/analysis/thirst_pilot/`. Measure the first store's size before running the rest.

The store's noise-free observation (`obs_true`) carries **Hydration** (hydration / 200, the
column after Body Temperature in the 59-wide layout). That gives everything P1 and P3 need without
the pond's location:
- **start hydration** = 200 × `obs_true[Hydration]` at t = 0;
- a **drinking step** is a step where hydration rises. Only the pond raises it: the net is +5 per
  step on the pond and −0.625 everywhere else. A **bout** is a run of consecutive drinking steps;
- **no-drink deadline** = 1.6 × start hydration, in steps;
- **cause of death** = `termination_reason` 1–7, all seven reported;
- **pond cells** (needed only for P1's floor): the store does not record the pond. The reader
  recomputes it by resetting the level-06 environment with the episode's `episode_seed`, using the
  collector's own key recipe. The recomputation is checked on every episode: the recomputed start
  cell must equal the store's `agent_row` / `agent_col` at t = 0. If any episode fails, the floor is
  not reported.

This needs a small reader over existing columns (no new collection code). Its first check is a
known-input test: a synthetic hydration trace with 2 bouts must return 2. If the reader is placed
under `scripts/`, `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` is updated in the **same commit**
(its Maintenance Contract). Seeds are read as in §4.1.

### 4.3 Reported tables

1. Per run and per agent mean: S_06 (last tenth), the Q3 ratio to S_05, the not-converged flag, and
   seed s.d.
2. All seven death shares, last tenth, training policy. The same from the 2.0 M store, greedy
   policy, in a separate column and never pooled.
3. Drinking bouts per episode and steps per bout, by checkpoint. The P1 floor. The data-integrity
   share (past-deadline episodes that drank; must be 100 %).
4. Survival by start-hydration band (0–50, 50–100, 100–150, 150–200) from the 2.0 M store (user
   decision 2026-09-29: report survival conditional on start hydration).
5. P4 speed ratio. P5 checklist per run. P5b control band.

### 4.4 Tools that must not be used here

They silently drop codes 6 and 7:
- `scripts/analysis/ladder/lad03_how_it_ends.py` hard-codes three outcomes (step limit, starved,
  predator) and never checks that its shares sum to 1;
- `scripts/analysis/studies/context_exploration/part4_readout.py:440` reads only
  `Term_Starvation / Term_Injury / Term_Thermal`;
- `scripts/analysis/studies/level05_body_interactions/pilot_pick.py` reads survival and starvation
  only. Its S read-out is fine, but it cannot answer P2.

Also, no `v4.0` tool from the shared folder may read these runs. The sum-to-1 check in P2 is the
safeguard against any dropped code.

---

## 5. Failure-mode catalogue (decided in advance)

| Outcome | Reading |
|---|---|
| P5 (a), (b), (c) or (e) fails for a run | The run is **invalid**, not a result. Stop it and fix the launch path. It is never analysed. A (d) mismatch alone is reported and does not invalidate (Revision 1). |
| NaN or value explosion in one seed | That run is bad. Report it. If the same agent's other two seeds are healthy, the question is answered with 2 seeds and the fact is stated. If it happens in 2 or more seeds of one agent on level 06 but not on the control, flag a possible water-specific instability to the user. |
| Dehydration falls but is still > 0.10 and still falling at 2 M | "Not converged", not "not learnable". Report the slope. The user decides whether to extend (a resumed run with `--load-checkpoint` is possible because all checkpoints are kept). |
| Over-drinking > 0.10 | A world-design flag: the brake is too easy to hit (W6 set 20 steps as "reachable but avoidable"). Report it with the bout-length distribution. The user decides whether to retune. No retune happens inside this pilot. |
| Survival of the level-06 ordinary agent above level 05 | The "water does not bite" flag is checked with the pond-visit count. A small positive difference with normal drinking is noise. |
| Control run outside 228.3 ± 6 | Stop interpreting level 06 against level 05 until explained. Route to `senior-developer`. |
| Speed cost > 15 % | Report to the user. It is the user's call (they accepted 9.8 % bare-env). |
| One agent learns to drink and the other does not | Report as observed. It is not evidence about the modulator: the pilot is not powered or designed for that. |

---

## 6. Metrics requested — declined (user, 2026-10-01)

**Declined for this pilot:** it launches as designed, without new training-log counters. P1 is
answered from stored episodes (§4.2). The table is kept as a record for later water experiments.

Launching does **not** depend on these. §4.2 answers P1 from stored episodes. They would put
drinking in the training logs, over time, for this pilot and for every later water experiment.

| Metric | Why now | Where it would live | Cost |
|---|---|---|---|
| `Bal_TimePond`: share of the window's steps on a pond cell | P1's "pond visits rising" would be read continuously, not at 3 stored checkpoints | `src/behavior/balance_metrics.py` (time-split family, next to `Bal_TimeEat`) | cheap (scalar per window) |
| `Bal_DrinkShare_Thirsty`, `Bal_DrinkShare_Sated`, `Bal_DrinkRatio`, `Bal_N_Thirsty`, `Bal_N_Sated`: drinking share among thirsty steps (hydration below a low bin) and sated steps (at or above the setpoint), read before the step; this mirrors `Bal_EatShare_*` | This is the state-dependent drinking measure the later modulator comparison will need. Having it in the pilot tells whether drinking tracks thirst at all at 2 M. | same file; the thirst bins go into the `balance_calibration` block | cheap |

If accepted, these go through `feature-workflow` (`senior-developer` → `developer`) **before**
launch, and the launch uses the new commit. If they are added after launch, these runs will not
have them.

---

## 7. Results

*(to be filled after training)*

## 8. Conclusions

*(to be filled after training)*

---

## Links

- Implementation plan and reports: `docs/develop/active/thirst/THIRST_WATER_PLAN.md` ([[THIRST_WATER_PLAN]])
- Design page: `docs/develop/active/thirst/thirst_water.html`
- Level-05 references: `docs/experiments/active/level05_body_interactions/LEVEL05_BODY_INTERACTIONS.md`
  §3.0 (P0a `nz0o6b70`, P0b `p4tlq5fq`, P0c `qwrtf2x5`) and §3.0b (`w0000` ordinary `dg1ry2be`,
  modulated `nl1h2j21`)
- WandB metric definitions: `docs/develop/active/behavior/WANDB_METRICS_REFERENCE.md`
- Trajectory store columns: `docs/environment/TRAJECTORY_STORE_SCHEMA.md`

---

## Feedback from plan-reviewer

*2026-10-01, on commit `9d969d04`. Full report: [[plan_thirst_pilot]]
(`docs/reviews/plan_thirst_pilot.md`). Severity legend: 🔴 Critical = fix before going further ·
🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.*

**Verdict: NOT READY — one Critical, cheap to fix.** The launch path (§2.5) held up under attack:
the gate inspects the process's own import state, the static scan for bare imports is clean
(indented lazy imports included), every child process locates the repo from its own file, and no
persistent JAX cache exists. Death-cause consumers, the drinking-step rule and the level-05
like-for-like claim all check out (details in the report).

| # | Severity | Where | Issue → fix |
|---|---|---|---|
| C1 | 🔴 | §2.5 outputs table + warning box | All outputs land in the worktree's gitignored `results/`, `wandb/`, `logs/`. `git worktree remove` deletes ignored files **without** `--force`, and a worktree exists to be removed after merge. The plan warns but has no step, destination or owner. → User names a destination outside any worktree; then either launch with `--results-dir <dest>/JAX_RecurrentPPO/<ts>_<TAG>` (`train.py:446`, used as given) and `--log <dest>/…`, or add a numbered post-run copy step the runner executes when each run finishes. Diary row at launch: "worktree `thirst` holds live training outputs — do not remove". |
| M1 | 🟡 | §2.7 P4 | `Time/sps_env` is `global_step / seconds since start` (`train.py:2003`) — a running mean, not a rate; the median of it is biased by compile/warm-up and by run length, which differs between the two arms. → Use Δ`timesteps` / Δ`_runtime` between the 50 % row and the last row (or the last-row value); read the reference speeds the same way. |
| M2 | 🟡 | §2.7 P5(c)(d), §5 row 1 | (d) asserts WandB metadata values never observed for a worktree launch; a format quibble would stop a valid run. (c) tolerates `git_dirty: unknown` but not `git_sha: unknown`, though the same 10 s timeout applies. → Gate on (a)(b)(c)(e); (d) informational until the first `wandb-metadata.json` is read; an unknown sha falls back to the manifest HEAD + (a). |
| M3 | 🟡 | §2.7 P1 pass line | "≤ half of the first tenth" does not subtract the floor of unavoidable thirst deaths (~2–3 %); if the first-tenth share is modest the target sits within 2–3 points of the floor and a well-drinking agent can fail. → State the floor (measure it from the 0.4 M store) and use "≤ 0.10 and ≤ max(0.5 × first tenth, floor + 0.03)". |
| L1–L5 | 🟢 | P5(a) "first line" → "contains"; §4.2 checkpoint keys are actual episode counts (`train.py:2625`), say "nearest"; the ≥ 80 % drank clause is 100 % by construction, label it integrity; the §4.2 reader needs a `SCRIPTS_DEPENDENCY_MAP.md` row if under `scripts/`, and seeds 43/44 must be read from top-level `seed:` / provenance `argv`, never `training.seed` (Known Bugs, stale seed copy); the worktree's `run_command.py` default log dir is its own folder, not the shared one. |

**Open assumptions**: A1 WandB `program`/`root` for a worktree launch; A2 `git` present on every
node; A3 a finished run's `models/` has a key ≥ 2,000,000; A4 P4 folds in the reset-rate cost of
shorter episodes, separate it if the 15 % flag trips; A5 the ±6 control band is ~2 s.d. if the
true seed s.d. is 3, not 1.5 (accepted, a flag costs a pause); A6 the reference S values came from
WandB sampled history — read both arms the same way.

**Cost of being wrong**: the Critical is a data-loss risk, not a wrong-conclusion risk — a routine
worktree cleanup after merge would erase ~20 GPU-hours and the stored episodes. The Moderates cost
at most one falsely stopped run or a mis-sized speed/drinking read-out.

**To flip the verdict**: named destination + copy or `--results-dir` step (C1); (d) informational
(M2); windowed speed rate (M1); floor in the drinking pass line (M3).

— plan-reviewer
