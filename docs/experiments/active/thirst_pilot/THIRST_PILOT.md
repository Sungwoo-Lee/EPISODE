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

> **Status**: ANALYSED 2026-10-01 (experiment-analyzer). All seven runs finished; results in §7–§9.
> One pre-registered flag tripped (P1, §7.3) and goes to the user. The verdict has not yet been
> through `plan-reviewer`. Design: Revision 1 (answers the plan review, §1.1).
> **Branch**: `v5.0`, worktree `.claude/worktrees/thirst`. Water exists only there. Every launch
> runs the worktree's code, from the worktree. **Every output is written to the shared project
> folder**, outside any worktree (§2.5).
> **Related**: [[THIRST_WATER_PLAN]] (how water and thirst were built and verified) ·
> [[thirst_water]] (design page with the simulated difficulty) · [[LEVEL05_BODY_INTERACTIONS]]
> (source of the level-05 reference runs) · [[BASIC_LEVELS_Q2_DEFAULT]] (the ladder)

---

## Verdict (plain language, 2026-10-01)

All seven training runs finished their 2 million episodes without errors. Every one ran the new
pond-and-thirst code and not the older shared copy; this was checked five ways (§7.1).

**The new world can be learned, and it behaves sensibly.** Both the ordinary agent and the agent
with the modulator learned to drink. On the frozen, best-action policy, drinking bouts per episode
rose from about 0.2 at 0.4 M episodes to about 5.5 at 2 M. In training, deaths from thirst
peaked at about 1 episode in 5, a third of the way through training, and fell to about 1 in 16. No single cause of death
dominates. The mix of causes looks like level 05 with a small thirst share added, and deaths from
drinking too much are about 1 in 800.

The ordinary agent in the pond world survives **197 steps** on average at the end of training (the
modulated agent 203). The same ordinary agent in
the campfire world survives 228 steps, so the drop is **13.5 %**, inside the predicted 5–25 %. Part
of the gap is a budget effect. The budget is counted in episodes, and pond-world episodes are
shorter, so these agents got **about 30 % fewer steps of experience**. Compared at equal
experience, the gap is about **10 %**. Survival was still rising, by about 4 % per tenth of
training, when the runs stopped. The level-05 control reproduced its older reference run **bit for
bit**. Water costs about **5 %** in training speed (same machine, same card, same time).

**One pre-registered check tripped, and the user must decide on it.** The "learned to drink" pass
line asked that the end-of-training thirst-death share be at most half its first-tenth value. Five
of six runs missed by 0.15–0.7 percentage points. The likely cause is the baseline. In the first
tenth, most agents die of other causes before thirst can kill them, so the starting share (0.12)
is low. The share then rose to 0.20 before falling to 0.06. Under the design's rules this is a
"show the user" flag. It is not evidence that the world is broken. Nothing here is a claim about
the modulator.

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

**Re-check of Revision 1 (SOUND WITH CONCERNS), folded in at analysis time only.** The launch
commands (§2.5) and the run table (§3) are unchanged.

| Finding | Change |
|---|---|
| R1 | §4.2: the per-step pond cross-check, with params built from the run's saved config through `apply_sensor_compat` |
| R2 | P1 floor: "cannot reach" = ceil(1.6 × start hydration) ≤ distance − 1 |
| R3 | P5(d): expect `root` = the worktree |
| R4 | §4.4: `v4.0` batch tools exclude `*l06pilot*` until merge |
| R5 | No change. The modulated agent on an 11 GB card is covered by the runner's post-launch check. |

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
  **cannot** reach water before dying of thirst whatever the policy does. Precisely: an episode
  cannot reach water when **ceil(1.6 × start hydration) ≤ d − 1**. Here d is the Manhattan
  distance (moves are 4-neighbour) from the start cell to the nearest cell of that episode's pond.
  The bound is d − 1, not d, because the drink on the arrival step is added before the death
  test (`core.py:599-604`). An episode whose deadline equals the distance therefore survives by
  arriving on that step (re-check R2). The floor depends only on the episode's start and not on
  the policy, so any store measures it. It is a lower bound: it ignores detours forced by
  obstacles and predators.
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
  values come from WandB's own detection and have never been observed for a worktree launch.
  **Expected: `root` = the worktree**, because WandB detects it from the working directory's git
  checkout, and `WANDB_DIR` only moves the files (re-check R3). After the first run, the runner reads its `wandb-metadata.json`, records the observed
  values here, and from then on only the commit (= (c)'s sha) is compared. A mismatch is reported,
  but it does not stop a run that passes (a)–(c) and (e).
  - *Observed (training-runner, 2026-10-01, runs 1 `883s9cak` and 7 `ffjgdq7f`, `wandb-metadata.json`):* `program` = `<worktree>/train.py`, `commit` = `d35a3c67…` (= (c)), **`root` = the shared folder** `/media/nas01/projects/Interoceptive-AI/grid_world_pain`, not the worktree as expected. Reported per (d); not a stop (all seven pass (a)–(c)).
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
| 1 | running | L06 ordinary (throughput pair A) | `rppo_l06pilot_t1none_s42` | thirst_pilot | pilot | 42 | 101 | cuda:1 | 2026-10-01T13:21:38 | `883s9cak` | `logs/20261001_132138_rppo_l06pilot_t1none_s42.log` (HEAD `d35a3c67`) |
| 2 | running | L06 ordinary | `rppo_l06pilot_t1none_s43` | thirst_pilot | pilot | 43 | 103 | cuda:0 | 2026-10-01T13:21:59 | `1olnaeg8` | `logs/20261001_132158_rppo_l06pilot_t1none_s43.log` (HEAD `d35a3c67`) |
| 3 | running | L06 ordinary | `rppo_l06pilot_t1none_s44` | thirst_pilot | pilot | 44 | 103 | cuda:1 | 2026-10-01T13:22:00 | `1dxqibr3` | `logs/20261001_132159_rppo_l06pilot_t1none_s44.log` (HEAD `d35a3c67`) |
| 4 | running | L06 modulated | `rppo_l06pilot_t16quad_s42` | thirst_pilot | pilot | 42 | 104 | cuda:0 | 2026-10-01T13:22:00 | `z3ogjds3` | `logs/20261001_132200_rppo_l06pilot_t16quad_s42.log` (HEAD `d35a3c67`) |
| 5 | running | L06 modulated | `rppo_l06pilot_t16quad_s43` | thirst_pilot | pilot | 43 | 104 | cuda:1 | 2026-10-01T13:22:01 | `rs8gq0w4` | `logs/20261001_132201_rppo_l06pilot_t16quad_s43.log` (HEAD `d35a3c67`) |
| 6 | running | L06 modulated | `rppo_l06pilot_t16quad_s44` | thirst_pilot | pilot | 44 | 105 | cuda:0 | 2026-10-01T13:22:02 | `tpg1snlp` | `logs/20261001_132201_rppo_l06pilot_t16quad_s44.log` (HEAD `d35a3c67`) |
| 7 | running | L05 control, `v5.0` code (throughput pair B) | `rppo_l06pilot_l05ctl_t1none_s42` | thirst_pilot | pilot | 42 | 101 | cuda:0 | 2026-10-01T13:21:37 | `ffjgdq7f` | `logs/20261001_132137_rppo_l06pilot_l05ctl_t1none_s42.log` (HEAD `d35a3c67`) |

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
  recomputes it by resetting the environment with the episode's `episode_seed`, using the
  collector's own key recipe. **The environment parameters are built exactly as the collector
  builds them**: the run's own saved `models/config.yaml`, passed through `apply_sensor_compat`
  (`collect_trajectories.py:963-1000`). They are never built from the worktree's level-06 YAML,
  which could have drifted from what the run trained on. Two checks, both over **every**
  episode (re-check R1):
  1. the recomputed start cell equals the store's `agent_row` / `agent_col` at t = 0. This proves
     the seed → key recipe and the grid, but not the pond: the start cell depends on the pond only
     in the ≈ 4 % of episodes whose raw draw lands on a pond cell;
  2. **the per-step pond check, which is what validates the pond.** For every step t → t+1 of
     every episode, "hydration rose from t to t+1" must hold **exactly when** the store's
     `agent_row` / `agent_col` at t+1 is a recomputed pond cell. Drinking means standing on a pond
     cell after the move (`core.py:1201`), and hydration rises only then (`core.py:599-604`). The
     check must hold in both directions, with zero exceptions.

  If either check fails on any step or any episode, the recomputed ponds are wrong. The floor is
  then **not reported**, and P1 is judged on its other clauses only, with that stated.

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

**Caution for everyone else, until `v5.0` is merged (re-check R4).** The seven pilot run folders
sit in the shared `results/JAX_RecurrentPPO/` beside every other run. Their saved configs carry a
`water:` block and a 59-wide observation that the shared folder's `v4.0` code does not know. A
`v4.0` loader that meets them will refuse them or misread them. Any batch tool that globs that
folder from the shared folder, such as dwell sweeps, trajectory collection specs or result
refreshes, should **exclude `*l06pilot*`** until `v5.0` is merged.

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

*Filled by experiment-analyzer, 2026-10-01. Training-policy numbers come from each run's local
WandB binary under `<shared>/wandb/`. Every `Episode/*` value is `Episode/_window_n`-weighted, with
rows selected by `lo < Episode/Number ≤ hi`, which is the `pilot_pick.py` rule. "Last tenth" means
episodes 1.8–2.0 M. Greedy numbers come from the §4.2 stores and are never pooled with training
numbers. Survival is in steps, and reward is never read. The tools banned in §4.4 were not used.
All code and raw outputs are in `<shared>/results/analysis/thirst_pilot/readout/` (code in
`readout/code/`).*

### 7.0 Completeness

| Run | Cell | Final checkpoint | Last PPO iteration (logged) | Env steps | Wall time | NaN / traceback |
|---|---|---|---|---|---|---|
| 1 | L06 ordinary s42 (101:1) | 2,000,008 | 15,150 | 248.2 M | 2.24 h | none |
| 2 | L06 ordinary s43 (103:0) | 2,000,049 | 14,350 | 235.1 M | 2.07 h | none |
| 3 | L06 ordinary s44 (103:1) | 2,000,057 | 13,600 | 222.8 M | 1.99 h | none |
| 4 | L06 modulated s42 (104:0) | 2,000,001 | 14,750 | 241.7 M | 2.87 h | none |
| 5 | L06 modulated s43 (104:1) | 2,000,071 | 15,350 | 251.5 M | 2.98 h | none |
| 6 | L06 modulated s44 (105:0) | 2,000,036 | 15,650 | 256.4 M | 2.98 h | none |
| 7 | L05 control s42 (101:0) | 2,000,025 | 21,450 | 351.4 M | 3.04 h | none |

All seven logs end with `Training complete`, and every WandB binary has exit code 0, with 500
episode rows reaching `Episode/Number` = 2,000,000. Each run has ten checkpoints and its final key
is at least 2,000,000 (L2). The §3 manifest still reads `running` in its Status column. That column
belongs to `training-runner` and was not edited here.

### 7.1 P5: the runs executed `v5.0` code. **PASS (all 7 valid)**

| Check | Result |
|---|---|
| (a) gate line in log | All 7 contain `[v5-gate] OK src=<worktree>/src branch=v5.0 … modules=1939` |
| (b) banner | Runs 1–6: `Observation Dim: 59 (… Hydration=1 …)`. Run 7: `58`, no Hydration |
| (c) provenance | All 7: `branch: v5.0`, `git_sha: d35a3c67…` (= manifest HEAD), `git_dirty: "unknown"` (accepted) |
| (d) WandB metadata, informational | All 7: `program` = `<worktree>/train.py`, `commit` = `d35a3c67…`, **`root` = the shared folder**, not the worktree that re-check R3 expected. Informational only, as the design says |
| (e) water flag | Saved `models/config.yaml` and WandB `config.yaml`: `water.enabled: true` on runs 1–6, `false` on run 7. `Episode/Term_Dehydration` is non-zero in every level-06 window |
| Seeds | Top-level `seed:` = 42/43/44 as planned, matching provenance `argv` (`--seed 43/44` where passed) |

**P5b: the control reproduces level 05. PASS, and stronger than the band.** S_ctl = **227.8**,
inside 228.3 ± 6. The control is also **bit-identical** to the first 2 M episodes of the older
reference run `w0000` ordinary (same seed, same card model, older code). All 500 episode rows
match exactly in `Episode/Steps`, all `Term_*` and `timesteps` (max abs difference 0). So `v5.0`
with water off trains level 05 exactly as before.

### 7.2 Temporal evolution (training policy, 200 k-episode tenths)

Survival `Episode/Steps`:

| Run | 0.0–0.2 | 0.2–0.4 | 0.4–0.6 | 0.6–0.8 | 0.8–1.0 | 1.0–1.2 | 1.2–1.4 | 1.4–1.6 | 1.6–1.8 | 1.8–2.0 M |
|---|---|---|---|---|---|---|---|---|---|---|
| L06 ordinary s42 | 38.0 | 49.3 | 69.5 | 83.8 | 112.7 | 147.2 | 169.9 | 179.9 | 192.2 | 199.8 |
| L06 ordinary s43 | 35.6 | 44.7 | 54.1 | 77.1 | 101.8 | 133.4 | 160.5 | 179.4 | 191.4 | 199.7 |
| L06 ordinary s44 | 34.8 | 52.3 | 60.6 | 74.5 | 98.0 | 116.5 | 141.2 | 164.0 | 183.5 | 190.8 |
| L06 modulated s42 | 37.8 | 50.5 | 61.7 | 77.2 | 105.4 | 132.6 | 168.5 | 186.0 | 191.1 | 200.4 |
| L06 modulated s43 | 36.5 | 43.9 | 57.5 | 82.0 | 119.6 | 153.9 | 176.9 | 189.7 | 197.3 | 203.5 |
| L06 modulated s44 | 41.9 | 59.1 | 64.6 | 80.4 | 120.0 | 150.6 | 174.9 | 189.7 | 197.2 | 204.7 |
| L05 control s42 | 50.6 | 88.1 | 157.3 | 179.4 | 189.2 | 203.2 | 214.6 | 220.4 | 226.4 | 227.8 |
| L05 P0a s42 (ref) | 51.1 | 87.9 | 139.5 | 174.2 | 199.6 | 205.6 | 214.2 | 220.1 | 224.7 | 228.3 |

Dehydration share `Term_Dehydration` (all episodes), and late-death dehydration
`Bal_LateDeath_Dehydration` (share **among deaths after step 20**), seed means:

| Tenth | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Dehydration, ordinary | 0.116 | 0.155 | 0.185 | **0.201** | 0.182 | 0.125 | 0.102 | 0.075 | 0.065 | 0.062 |
| Dehydration, modulated | 0.125 | 0.163 | 0.186 | **0.197** | 0.156 | 0.101 | 0.077 | 0.071 | 0.067 | 0.064 |
| Late dehydration, ordinary | 0.148 | 0.181 | 0.205 | **0.231** | 0.205 | 0.140 | 0.111 | 0.076 | 0.063 | 0.059 |
| Late dehydration, modulated | 0.161 | 0.193 | 0.224 | **0.233** | 0.178 | 0.109 | 0.078 | 0.071 | 0.066 | 0.063 |
| Over-drinking, ordinary | 0.0037 | 0.0042 | 0.0042 | 0.0036 | 0.0020 | 0.0022 | 0.0016 | 0.0015 | 0.0013 | 0.0012 |
| Early-death share (≤ 20 steps), ordinary | 0.508 | 0.388 | 0.314 | 0.302 | 0.270 | 0.270 | 0.240 | 0.230 | 0.213 | 0.202 |
| Early-death share, L05 control | 0.412 | 0.245 | 0.207 | 0.199 | 0.189 | 0.169 | 0.159 | 0.153 | 0.148 | 0.147 |

Per-seed dehydration curves have the same rise-and-fall shape in all six runs. The peak falls in
tenth 3 or 4 (tenth 5 for ordinary s44), at 0.18–0.22. The other causes, seed means, ordinary
agent:

| Tenth | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Starvation | 0.223 | 0.331 | 0.350 | 0.328 | 0.328 | 0.282 | 0.273 | 0.242 | 0.228 | 0.225 |
| Injury | 0.547 | 0.406 | 0.363 | 0.383 | 0.384 | 0.445 | 0.433 | 0.465 | 0.465 | 0.462 |
| Thermal | 0.110 | 0.104 | 0.098 | 0.079 | 0.072 | 0.055 | 0.050 | 0.035 | 0.029 | 0.024 |
| Step limit | 0.000 | 0.000 | 0.000 | 0.006 | 0.032 | 0.092 | 0.140 | 0.181 | 0.211 | 0.227 |
| `Bal_TimeBush` | 0.076 | 0.342 | 0.420 | 0.352 | 0.315 | 0.260 | 0.251 | 0.234 | 0.235 | 0.234 |
| `Bal_TimeEat` | 0.003 | 0.005 | 0.026 | 0.066 | 0.096 | 0.122 | 0.135 | 0.144 | 0.150 | 0.152 |
| `Bal_TimeWarm` | 0.047 | 0.087 | 0.096 | 0.109 | 0.123 | 0.147 | 0.158 | 0.174 | 0.180 | 0.184 |
| `Bal_HideRatio_True` | 0.53 | 0.38 | 0.71 | 0.92 | 1.15 | 1.76 | 2.11 | 2.52 | 2.72 | 2.86 |

Level 06 runs the same curriculum as level 05, a few tenths later. The step-limit share passes
0.1 by tenth 3 on the control, but only by tenth 6–7 on level 06 (0.092, then 0.140). Eating time reaches 0.125 by
tenth 3 on the control and by tenth 6 on level 06. The hiding ratio crosses 2 at tenth 4 on the
control and at tenth 7 on level 06. By the last tenth every balance key is close to the control's
(bush time 0.234 vs 0.263, eat time 0.152 vs 0.156, warm time 0.184 vs 0.207, hiding ratio 2.86
vs 2.94). Full per-seed tables for every key: `readout/tenths_out.txt`.

### 7.3 P1: both agents learn to drink. **FLAG (pass line missed by 5 of 6 runs, narrowly)**

**Floor, R1 and integrity checks (stores).** The pond recomputation (params built from each run's
saved config through `apply_saved_config_compat` → `load_env_params`, as the collector does) passed
both R1 checks on **all 18 stores**. There were 0 start-cell mismatches in 180,000 episodes. The
per-step "hydration rose ⇔ standing on a recomputed pond cell" test had 0 exceptions in
**25.0 M** steps. The design names the helper `apply_sensor_compat`. The collector's actual
params path for these runs, which pass no `--assume-pre-v3x` flag, is
`apply_saved_config_compat` (`collect_trajectories.py:1007-1014`), and that path was used. The
floor is valid: **0.0165** (165 of 10,000 episode starts cannot reach water under
ceil(1.6 × H0) ≤ d − 1). It is identical in every store because all stores share
`--seed-base 1000000`. The integrity check holds: **100 %** of episodes that outlived their own
no-drink deadline drank, in all 18 stores (94–4,656 such episodes per store). The bout reader
passed its known-input test (a synthetic trace with 2 bouts returns 2).

**Pass line, per run** (last-tenth `Term_Dehydration` ≤ 0.10 **and** ≤ max(0.5 × first tenth,
floor + 0.03 = 0.0465); bouts rise from 0.4 M to 2.0 M):

| Run | First tenth | 0.5 × first | Threshold | Last tenth | ≤ 0.10 | ≤ threshold | Bouts/ep 0.4 M → 1.2 M → 2.0 M | P1 |
|---|---|---|---|---|---|---|---|---|
| ordinary s42 | 0.1146 | 0.0573 | 0.0573 | 0.0602 | yes | **no (+0.0029)** | 0.27 → 2.80 → 5.75 | fail |
| ordinary s43 | 0.1188 | 0.0594 | 0.0594 | 0.0656 | yes | **no (+0.0062)** | 0.19 → 3.90 → 5.33 | fail |
| ordinary s44 | 0.1152 | 0.0576 | 0.0576 | 0.0591 | yes | **no (+0.0015)** | 0.06 → 2.67 → 5.31 | fail |
| modulated s42 | 0.1214 | 0.0607 | 0.0607 | 0.0677 | yes | **no (+0.0070)** | 0.35 → 2.79 → 5.58 | fail |
| modulated s43 | 0.1195 | 0.0598 | 0.0598 | 0.0630 | yes | **no (+0.0032)** | 0.10 → 4.24 → 5.78 | fail |
| modulated s44 | 0.1351 | 0.0676 | 0.0676 | 0.0603 | yes | yes | 0.17 → 4.02 → 5.76 | **pass** |

The second flag clause, "flat over the last three tenths while above 0.10", does **not** trip.
Every run is below 0.07 and still drifting down: the ordinary mean goes 0.075 → 0.065 → 0.062.

**Drinking in the greedy stores** (seed means):

| Checkpoint | Bouts / episode (ord / mod) | Bouts / 100 steps | Steps / bout | Share of episodes that drank | Greedy mean length |
|---|---|---|---|---|---|
| ≈ 0.4 M | 0.17 / 0.21 | 0.33 / 0.38 | 1.7–4.9 | 0.08 / 0.11 | 52 / 55 |
| ≈ 1.2 M | 3.12 / 3.68 | 2.09 / 2.33 | 3.3–3.9 | 0.44 / 0.45 | 148 / 157 |
| 2.0 M | 5.47 / 5.71 | 2.62 / 2.71 | 3.3–3.7 | 0.62 / 0.61 | 209 / 210 |

At 2 M, bouts have a median of 3 steps and a 99th percentile of 13–15 steps. The longest bout in
any 2 M store is 27 steps.

**Anatomy of the remaining thirst deaths** (greedy, 2.0 M stores, per run). There are 502–750
dehydration deaths per 10,000 episodes. Of these, 150–155 are the unreachable floor, 262–320
happen within 20 steps, and 461–674 belong to episodes that **never drank at all**. In training,
the last-tenth dehydration share of 0.059–0.068 splits into about **0.028 early** (≤ 20 steps; a thirst
death that early needs a start hydration below 12.5, which is 6.25 % of starts) and **0.031–0.039 late**.

**Prediction check.** The last-tenth share of 0.059–0.068 is **inside** the predicted 0.03–0.08.
"Late dehydration falls monotonically after the first two tenths" is **refuted**: it **rises**
through tenth 4 (peak 0.23 among late deaths) and falls monotonically only from tenth 4 or 5 on.
"Within a factor of 2 of the scripted agent's 1.7 pond visits" is **refuted on the high side**:
trained agents make 5.3–5.8 bouts per episode of about 3.5 steps each. That is frequent short
sips, not 1–2 long drinks. A bout counts each separate arrival on the pond, so this is not an
artefact of pausing on the pond.

### 7.4 P2: no absurdly dominant cause of death. **PASS (no flag)**

Last tenth, seed mean, all seven `Term_*` shares. Training policy, with the greedy 2.0 M store in a
separate column:

| Cause | Ordinary, training | Modulated, training | Ordinary, greedy | Modulated, greedy | L05 control, training | Flag line |
|---|---|---|---|---|---|---|
| Starvation | 0.225 | 0.231 | 0.209 | 0.224 | 0.283 | |
| Injury | **0.462** | 0.445 | 0.462 | 0.427 | 0.415 | > 0.60 any cause |
| Thermal | 0.024 | 0.024 | 0.022 | 0.026 | 0.032 | |
| Step limit | 0.227 | 0.236 | 0.249 | 0.250 | 0.270 | |
| Over-eating | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | |
| Dehydration | 0.062 | 0.064 | 0.056 | 0.071 | — | > 0.25 |
| Over-drinking | 0.0012 | 0.0011 | 0.0015 | 0.0010 | — | > 0.10 |
| **Sum** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1 ± 0.01 |

The sum check holds on **every individual logged row** of every run (min/max 1 ± 2e-16), not only
on window means. The stores have no reason code 0. Predictions: injury is the largest cause, as
predicted, but at 0.462 for the ordinary agent it is just above the predicted 0.35–0.45 (modulated
0.445 is inside). Starvation of 0.225–0.231 is inside 0.2–0.3. Dehydration is inside 0.03–0.12.
Over-drinking is below 0.02. The step-limit share of 0.227–0.236 is below level 05's 0.27. All
are as predicted.

### 7.5 P3: survival against level 05. **Inside the predicted band; no flag; not converged**

| | Seeds (last tenth) | Mean | Seed s.d. (% of mean) | 95 % CI (t, n = 3) | Ratio to S_05 | Ninth tenth → last tenth |
|---|---|---|---|---|---|---|
| L06 ordinary | 199.8, 199.7, 190.8 | **196.7** | 5.2 (2.6 %) | 183.9–209.5 | **0.865** (−13.5 %) | +3.9, +4.3, +4.0 % |
| L06 modulated | 200.4, 203.5, 204.7 | **202.9** | 2.2 (1.1 %) | 197.4–208.4 | 0.888 vs `w0000 m` 228.4 (one seed) | +4.9, +3.1, +3.8 % |
| L05 ordinary (P0a–c) | 228.3, 225.8, 228.6 | 227.5 | 1.5 | 223.8–231.3 | — | +1.6, +1.8, +1.9 % |

- **Prediction** "5–25 % below S_05" holds: 13.5 % below, with every seed between 12.2 % and 16.1 %
  below. "Seed spread below 3 % of S_06" holds (2.6 % and 1.1 %).
- **Flag "too hard"** (S_06 < 114): no. **Flag "water does not bite"**: no (S_06 is 31 steps below
  S_05, and pond bouts are 5.5 per episode).
- **Not converged** (reported, not a flag): the last tenth beats the ninth by more than 2 % in **all
  six** level-06 runs (3.1–4.9 %). The level-05 references are under 2 %. The 2 M gap is measured
  on a curve that is still rising.
- **Modulated minus ordinary, descriptive only:** +0.6, +3.9, +14.0 steps per seed pair, mean
  +6.2, s.d. 7.0. One seed pair drives most of it (ordinary s44 is the low run). This is not
  evidence about the modulator (§1).

**Budget confound: fewer environment steps for the same number of episodes (parent fact (b),
checked).** Every PPO iteration is 128 worlds × 128 steps = 16,384 environment steps. That is true
on both levels, so env steps and PPO updates are proportional. Level-06 episodes are shorter
(averaged over the whole run: 111–128 steps, against 176 on the control), so 2 M episodes buy fewer
iterations:

| Run | Iterations | Env steps | vs its level-05 reference |
|---|---|---|---|
| L06 ordinary s42 / s43 / s44 | 15,150 / 14,350 / 13,600 | 248.2 / 235.1 / 222.8 M | 0.711 / 0.719 / 0.636 of P0a / P0b / P0c; s42 is 0.706 of the same-seed control (21,450 iterations) |
| L06 modulated s42 / s43 / s44 | 14,750 / 15,350 / 15,650 | 241.7 / 251.5 / 256.4 M | 0.730 / 0.760 / 0.775 of `w0000 m`'s first 2 M (331 M) |

The ordinary level-06 agent therefore got **about 31 % fewer steps of experience and PPO updates**
than its level-05 reference: 29 % for seed 42 against the control, which matches the parent's
"≈ 28 %". For the modulated agent the figure is about 25 %. **Equal-experience comparison**
(post hoc, labelled): each ordinary level-05 reference was read over the env-step window that
the same-seed level-06 run covered in its last tenth. This also gives an equal number of PPO
updates.

| Pair | Env-step window | L05 survival there (L05 episodes) | L06 last tenth | Ratio |
|---|---|---|---|---|
| L06 s42 vs P0a | 209–248 M | 219.4 (1.38–1.56 M) | 199.8 | 0.910 |
| L06 s43 vs P0b | 196–235 M | 218.1 (1.41–1.59 M) | 199.7 | 0.916 |
| L06 s44 vs P0c | 186–223 M | 217.5 (1.27–1.43 M) | 190.8 | 0.877 |
| L06 s42 vs control | 209–248 M | 219.7 (1.37–1.54 M) | 199.8 | 0.909 |

At equal experience the gap is **about 10 %** (8.4–12.3 %), against 13.5 % at equal episodes. So
roughly a quarter of the episode-matched gap is less training, not the harder world. Both readings
are inside the predicted 5–25 %. The pre-registered number is the episode-matched one.

**Survival by start hydration** (greedy, 2.0 M stores, seed means; table 4 of §4.3):

| Start hydration band | Episodes | Ordinary: mean length / dehydration share | Modulated: mean length / dehydration share |
|---|---|---|---|
| 0–50 | 2,545 | 182.5 / 0.186 | 181.6 / 0.229 |
| 50–100 | 2,538 | 216.1 / 0.027 | 219.0 / 0.039 |
| 100–150 | 2,433 | 214.4 / 0.007 | 217.3 / 0.009 |
| 150–200 | 2,484 | 222.9 / 0.002 | 224.7 / 0.002 |

Almost all of the thirst cost sits in the quarter of episodes that start below 50 (deadline under 80
steps). Above 50, survival is within about 10 steps across bands.

### 7.6 P4: training-speed cost. **PASS (≈ 5 % slower; flag line 15 %)**

| Read-out | L06 run 1 (101:1) | L05 control run 7 (101:0) | L06 / L05 |
|---|---|---|---|
| **Design method**: Δ`timesteps`/Δ`_runtime`, the row nearest 50 % of each run's own final timesteps → last row | 31,404 /s (67–134 min) | 32,105 /s (91–182 min) | **0.978 (−2.2 %)** |
| **Same wall-clock window**, minutes 53–107 (both running) | 31,381 /s | 32,914 /s | **0.953 (−4.7 %)** |
| Same wall-clock window, minutes 53–134 (until run 1 ends) | 31,398 /s | 32,931 /s | 0.953 (−4.7 %) |

The parent's figure (a), 4.7 % slower in minutes 53–107, is **confirmed**. The design's own method
gives 2.2 %, and it is biased toward a smaller cost. Its two windows are not simultaneous: level-06
episodes are shorter, so run 1 finished at 134 min, while the control ran on to 182 min. The
control's window therefore includes 48 minutes after run 1 had finished, and in that stretch the
control **slowed** by 5.1 % (32.9 k → 31.3 k /s; 30.3 k in minutes 140–160). The cause is
unknown: other load on node 101 cannot be checked after the fact. The control's speed was flat at
32.9 k /s from minute 20 to minute 134, while both runs shared the node. The simultaneous window
is the clean comparison, and its answer is **4.7 %**. Both readings are inside the predicted
0–10 % and far from the 15 % flag, so the reset-cost split (A4) was not needed. Every level-06
episode is shorter, so level 06 completes **more** episodes per second: 176 against 163 in the
simultaneous window.

Secondary:
- **Hours per 2 M episodes:** level-06 ordinary 2.24 / 2.07 / 1.99 h, against 3.04 h for the
  control on the same card type. The shorter episodes make a 2 M-episode level-06 run about
  30 % faster in wall time, even though each step costs about 5 % more.
- **Modulated / ordinary speed on level 06:** 23.5–24.0 k against 31.4–32.3 k env steps/s, a
  ratio of about **0.74**. This is cross-node (104/105 against 101/103), but every card is an
  RTX 2080 Ti.
- The node-103 ordinary runs (seeds 43 and 44, design method) ran at 32.3 k and 31.8 k /s. That is
  2–3 % below the control's simultaneous 32.9 k, which matches the parent's "2–3 %". Being
  cross-node, it is indicative only.

### 7.7 Context: placement behaviour (parent fact (c); not re-measured here)

A separate placement audit ([[PLACEMENT_FIXES_PLAN]], `docs/develop/active/placement/`, 2,000
resets per level) reports two current behaviours. About 2 % of food regrowths land on a burning
campfire, where the food cannot be eaten (2.01 % level 05, 2.09 % level 06). The agent starts on a
burning fire in about 1.8 % of episodes (1.70 % level 05, 1.85 % level 06). Both are present at
almost the same rate in both worlds and in the references, so they do not bias the
level-06-versus-level-05 comparison. They do add to the early-death share on both levels:
0.20 (level 06) and 0.15 (control) in the last tenth. A fix is being planned. The pilot is not
blocked.

---

## 8. Analysis

**What the pre-registration asked and what came back.** P2–P5 came back clean, and P5b came back
stronger than designed (bit-identical reproduction). P1 tripped its pass line in 5 of 6 runs by
0.15–0.70 percentage points. Under §2.7, a flag means "stop and show the user", and it does not
mean "the world is broken".

**Why P1 trips, and the evidence for that.** The clause that fails is "≤ 0.5 × first-tenth share".
It assumed that thirst deaths start high and fall. The data show a competing-risks shape instead:

- In the first tenth, 51 % of all episodes end within 20 steps and injury takes 55 %. Most agents
  die before their thirst deadline (1.6 × start hydration, a median of 160 steps) can arrive. The
  first-tenth dehydration share of 0.115–0.135 is therefore a low baseline, not a measure of
  "not drinking".
- As agents learn to survive the other threats (seed-mean survival goes from 36 to 79 steps by tenth 4),
  more of them live long enough to die of thirst. Dehydration climbs to **0.20** at tenth 4. Over
  the same period the stores show almost no drinking: 0.17–0.21 bouts per episode at 0.4 M, and
  only 8–11 % of episodes drank at all.
- Drinking is then learned. Bouts go 0.17 → 3.1 → 5.5 per episode, and dehydration falls from
  0.20 to 0.06, a **70 % drop from the peak**. The pre-registered line measures the fall from the first
  tenth, not from the peak.
- About 0.028 of the remaining 0.06 are deaths within 20 steps (start hydration below 12.5,
  6.25 % of starts). In the stores, 1.65 % of starts cannot reach water at all. What remains above
  the floor + 0.03 line (0.0465) is 0.013–0.021. In the greedy stores most thirst deaths come from
  episodes that started below 50 (dehydration share in that band: 0.19 ordinary, 0.23 modulated).

This reading is post hoc. It explains the miss, but it does not convert the failures into passes.
The evidence that drinking is learned is the store bout counts (a pre-registered clause, passed
by every run) and the 70 % fall of dehydration from its peak. The 100 % integrity check only
validates the reader, and it is true by construction. The pass line remains failed as written.

**Prediction scorecard.** Hits: P1 last-tenth range, P2 cause ranges (injury marginally over for
the ordinary agent), P3 band and seed spread, P4 range. Misses: monotone fall of late dehydration
after tenth 2 (it peaks at tenth 4); pond visits within 2× of the scripted 1.7 (the observed
5.5 comes as short sips); and convergence. Level 06 is still rising at 2 M, while level 05 had
flattened.

**Seed dispersion.** Within each agent, the level-06 seeds agree closely in survival (s.d. 2.6 %
and 1.1 %), in death shares (dehydration 0.059–0.068) and in drinking (5.3–5.8 bouts). None of
the P1–P4 verdicts depends on a single seed. The one place a single seed matters is the descriptive
modulated-minus-ordinary gap (+14 steps from seed 44 alone).

**Failure-mode catalogue (§5) check.** No run is invalid (P5). There is no NaN or explosion. The
dehydration share is below 0.10, so the "not converged, still falling above 0.10" row does not
apply. Over-drinking is 0.001. Level-06 survival is not above level 05. The control is inside its
band. The speed cost is 5 %. Both agents learn to drink. The only row hit is the P1 flag itself,
which §2.7 sends to the user.

**What this pilot cannot say.** Anything about the modulator, since it is neither powered nor
designed for that. Where level-06 survival converges, since the runs are still rising. Whether
drinking *tracks thirst* (state-dependent drinking). The declined `Bal_DrinkShare_*` metrics
would answer that last question, and the start-hydration bands only hint at it: bouts per episode
are highest in the 50–100 band and lowest in the 150–200 band.

---

## 9. Conclusions

**Per question:**

| Q | Verdict | One-line evidence |
|---|---|---|
| P1 learn to drink | **FLAG** (pass line missed by 5/6 runs by 0.15–0.70 pp; the other clauses pass) | Dehydration 0.20 → 0.06 from its tenth-4 peak; bouts 0.17 → 5.5 per episode; integrity 100 %; floor 0.0165, pond recomputation validated on 25.0 M steps |
| P2 no dominant cause | **PASS** | Largest cause injury 0.46; dehydration 0.06; over-drinking 0.001; sums 1 ± 1e-15 |
| P3 survival vs level 05 | **PASS, as predicted (no flag), not converged** | 196.7 vs 227.5 (−13.5 %); about −10 % at equal experience; still +4 % per tenth |
| P4 speed | **PASS** | −4.7 % on the same node at the same time (design method −2.2 %, biased low) |
| P5 / P5b | **PASS (all 7 valid); control bit-identical to the reference** | Gate, banner, provenance, water flag; 500/500 rows equal |

**Is the world fit for the modulator comparison?** On this evidence, yes, with one open call for
the user (P1 below). The world can be learned by both agents. Thirst is a real but minor cause of
death that the agents learn to manage. No cause is absurd, and the code path is verified.

### 9.1 Decisions for the user

1. **P1 flag.** Accept "drinking is learned" on the passed clauses, recording the pass-line miss
   and the competing-risks reason, **or** hold until more evidence. The design does not allow
   re-scoring the line after the fact. If the line should change for later water experiments, a
   peak-referenced or floor-referenced line would avoid the low first-tenth baseline, and that is
   for `experiment-designer` to pre-register.
2. **Not converged.** Survival is still rising about 4 % per tenth at 2 M. If the modulator
   comparison needs plateau behaviour, it should run longer than 2 M on level 06. A resumed run
   from the kept checkpoints is possible (`--load-checkpoint`). Alternatively, the budget could be
   matched on env steps rather than episodes when comparing across levels.
3. **Budget currency.** Across levels, an episode budget gives level 06 about 30 % less
   experience. Future level-05 versus level-06 comparisons should state which currency they use,
   or report both, as §7.5 does.
4. **Speed method.** The P4 design method compares windows that are not simultaneous when the two
   runs end at different times. Future throughput pairs should use a common wall-clock window.
5. **Launch Manifest status** still reads `running` for all seven rows. `training-runner` owns
   that column.

### 9.2 Limitations

- P1, P3 and the tables: the training policy explores, while the stores are greedy (never pooled).
  The stores use 10,000 episodes per checkpoint at one fixed `--seed-base`.
- The equal-experience comparison and the competing-risks explanation are post hoc.
- The level-05 references ran on older code. P5b shows this does not matter, because the control is
  bit-identical to `w0000` ordinary.
- The P4 slow-down of the control after run 1 ended is unexplained (other load on node 101 is
  suspected but not verified).

### 9.3 Metrics requested

These are repeated from §6, which was declined for this pilot. The analysis shows where each one
would have helped.

| Metric | Why now | Where it would live | Cost |
|---|---|---|---|
| `Bal_TimePond` (share of window steps on a pond cell) | The drinking curve was readable only at 3 stored checkpoints. The rise of bouts between 0.4 M and 1.2 M, when dehydration peaks and turns, is not resolved in time | `src/behavior/balance_metrics.py` | cheap |
| `Bal_DrinkShare_Thirsty` / `_Sated` / `Bal_DrinkRatio` | Whether drinking tracks thirst (the state-dependence the modulator study needs) is open. The bands hint at it only indirectly | same file, thirst bins in `balance_calibration` | cheap |

If the user accepts these, they go through `feature-workflow`. They are not requested from here
directly.

### 9.4 Related issues

- [[PLACEMENT_FIXES_PLAN]]: food regrowth on burning fires and starts on fires (context, §7.7).
- §4.4 / re-check R4 still stand. The pilot run folders sit in the shared `results/` with 59-wide
  water configs. `v4.0` batch tools must exclude `*l06pilot*` until `v5.0` is merged. The stores
  under `results/analysis/thirst_pilot/` (4.7 GB) are in the same position.
- R3: the expected WandB `root` was wrong. WandB reports the shared folder for worktree launches,
  so later designs should expect that.

**Analysis artefacts.** WandB read-outs: `<shared>/results/analysis/thirst_pilot/readout/wandb_readout.json`,
`tenths_out.txt`, `speed_out.txt`, `early_late_out.txt`. Store read-outs: `readout/<agent>_<seed>_<ckpt>.json`,
`summary_all_stores.json`, `store_summary_out.txt`. Code: `readout/code/`. Stores:
`<shared>/results/analysis/thirst_pilot/<run>/<ckpt>/<env fingerprint>/` (one fingerprint per run; all 18
stores use `--episodes 10000 --seed-base 1000000 --obs-precision float32`, CPU, collected from the
worktree at `e98a0689`).

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

### Re-check of Revision 1 (plan-reviewer, 2026-10-01, commit `4deacc00`)

**Verdict: SOUND WITH CONCERNS.** The Critical is closed. Every output now leaves the worktree,
and I could find no path that still writes into it during a run: the run directory and everything
under it (checkpoints, saved config, provenance, recordings, checkpoint videos, stats,
experiment-eval) derive from `--results-dir` (`train.py:939-945`, `evaluation_core.py:279-280,315`,
`async_render.py` `videos_dir`); WandB files follow `WANDB_DIR` (no `dir=` in `train.py:1023-1030`);
the nohup log follows `--log`; stored episodes follow `--out-root`. No persistent JAX/XLA
compilation cache is configured anywhere (trainer, `src/`, train configs; `~/.cache/jax*` absent),
so there is nothing to relocate. The two other cwd-relative writers are off (`stats_during_training:
false`, `auto_analysis: false`; experiment-eval has no config block). What remains in the worktree
is the code and its `__pycache__`, which is why the "do not remove the worktree until all runs
finish" diary row in §3.2 is the right closing step — checkpoint-time renders start new processes
from it. The speed read-out (M1), the P5 gating (M2), the seed read and checkpoint naming (L2, L4)
and the 2080 Ti pair on node 101 are all as asked.

| # | Sev | Where | Issue → fix |
|---|---|---|---|
| R1 | 🟡 | §4.2 pond recomputation | The validation is weaker than it looks. The start cell depends on the pond only when the raw draw lands on a pond cell (≈ 4 % of episodes, `core.py:1904-1912`); in the other 96 % the start-cell check passes whatever pond the reader recomputed. It proves the seed → key recipe and grid size, not the pond. → Add the exact per-step cross-check from columns the store already has: for every step, "hydration rose from t to t+1" ⇔ "`agent_row`/`agent_col` at t+1 is a recomputed pond cell" (`core.py:599-604`, drinking = standing on a pond cell after the move, `core.py:1201`). It must hold on every step of every episode. And build the params exactly as the collector does — the run's `models/config.yaml` through `apply_sensor_compat` (`collect_trajectories.py:963-1000`) — not from the worktree's level-06 YAML. |
| R2 | 🟢 | §2.7 P1 floor definition | Boundary: the drink on the arrival step is added before the death test (`core.py:599-604`), so an episode whose deadline equals the distance survives by arriving on that step. "Cannot reach" is ceil(1.6 × start hydration) ≤ distance − 1, not ≤ distance. Effect far below the 0.03 margin, but the number is pre-registered. Manhattan distance is the right metric (4-neighbour moves, `core.py:1072`). |
| R3 | 🟢 | §2.7 P5(d) | `root` comes from WandB's git detection on the working directory (the worktree); `WANDB_DIR` only moves the files. Expect `root` = worktree, not the shared folder. Informational either way. |
| R4 | ❓ | §2.5 consequence | The shared `results/JAX_RecurrentPPO/` now holds 59-wide water runs beside `v4.0` tools that glob that folder; a `v4.0` loader meeting their `water:` block will refuse or misread it. §4.4 covers the tools this pilot uses; any batch tool run from the shared folder before merge should exclude `*l06pilot*`. |
| R5 | ❓ | §3 hardware | The modulated agent (`t16quad`) has not run on an 11 GB card in this series (`w0000 m` was a 3090). rPPO's footprint is small and preallocation is off, so it should fit; the runner's post-launch check covers it. |

**Cost of being wrong now:** R1 could report a floor computed against the wrong pond — a wrong
pre-registered number, caught only if someone notices; the per-step check makes that impossible.
Nothing else costs more than a note in the results.

— plan-reviewer
