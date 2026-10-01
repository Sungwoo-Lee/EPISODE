---
title: "Basic Behaviour Analysis: a reusable, figure-by-figure pipeline and page for any trained population"
topic: behavior
status: active
created: 2026-10-01
last_updated: 2026-10-01
---

# Basic Behaviour Analysis pipeline

> **Status**: PLANNED, **Revision 1 (2026-10-01)** — the cross-run analysis (F5) rewritten as exploratory screening after `plan-reviewer` returned NOT READY for it, plus the reviewer's other findings; awaiting a re-check by `plan-reviewer`, then user approval. See [Revision log](#revision-log).
> **Opened**: 2026-10-01
> **Author**: senior-developer
> **Related**: [[HYPERVIGILANCE_ANALYSIS_TOOLING]] (population manifests, per-cell store resolution, the golden-gate pattern and the reference files this plan reuses) · [[a01_hiding_drivers]] ("What makes this agent hide?" — the analyses this page generalises) · [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] (the first population: 18 runs in three smell worlds) · [[TRAJECTORY_STORE_SCHEMA]] (what a store records, and what it does not) · [[TRAJECTORY_COLLECTION_PIPELINE]] · `docs/develop/active/meta/artifact_generation_guide.md` (§0a, §2.7, §11) · `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (updated by this change) · Known Bugs rows "hiding-drivers cross-tabs bin injury from the same step" and "lab-node env drift" (see A6)

---

## Context

**What this is for.** After training, every agent in a study is replayed for about a million
episodes and each step is recorded in a *trajectory store*. The project already has one good
analysis of such a store — the "What makes this agent hide?" page for one agent — which asks how much
of its time the agent spends hiding in bushes, and which features of the world (how many predators,
how keen-sighted they are, how predator-like a rabbit smells, how hurt the agent starts) push that
up or down. The user wants that analysis as a **standard first look** at any trained population.

**Why new tooling is needed.** The existing script is welded to one world and one agent. It only
measures hiding; its list of world features is typed by hand, so a feature added since (campfires and
body temperature in the newest worlds) is mis-filed — campfires are currently counted as rocks — or
missed; and it has no figures of its own (that page draws them in the browser, which the project has
since ruled out).

**What this plan delivers.** A pipeline that (1) measures five behaviours — hiding in a bush,
eating, time within two squares of a rabbit, time within two squares of a predator, and (in worlds
with temperature) time on a warm square — each as a share of the agent's steps per episode; (2)
discovers the world's randomised features from each run's own saved settings and lists any it cannot
handle rather than dropping them; (3) drops, with a stated reason, features that never vary, duplicate
another, or are defined on too few episodes; (4) fits the hiding page's regression models per run; (5)
compares runs to **screen and rank which settings — smell world, agent type, even training seed —
move each behaviour more or less**, to help choose a training direction. This is exploratory, not a
verdict: each training run counts as one replicate, so every uncertainty comes from how much the
three seeds of a setting disagree (seed-to-seed variation), never from the million episodes inside a
run; and (6) must reproduce the hiding page's published regression tables byte for byte, and match
the old script on a new-world store wherever the two should agree, before any new number is trusted.
The smell study's own pre-registered test of whether a rabbit's smell causes more hiding the more
injured the agent is (*hypervigilance*) stays with that study; this page shows the same quantities
per run, labelled as screening. The page is built **one figure at a time** — six steps, each with
its own script, output, detailed plain-language method note, and a stop for the user's questions. The
first population is the 18 runs of the single-channel smell study.

---

## Analysis

### A1. What `hiding_drivers.py` does, and what of it is world-specific

`scripts/analysis/hiding_drivers.py` (414 lines) is the foundation. Its shape is right and is kept:

| Piece | Lines | Keep as-is? | World-specific part |
|---|---|---|---|
| `find_stores`, `shard_files`, `listcol` | 84–124 | **import** (do not copy) | none |
| `aggregate()` one sweep → per-episode arrays; asserts shard alignment, contiguous seeds, one reset row per episode | 127–243 | pattern kept; arithmetic primitives copied **exactly** (A5) | typed column list; outcome hard-wired to `agent_in_bush`; `slot_layout` splits obstacles only into bush / not-bush, so **campfires and trees are counted as rocks** (verified on the hv1ch saved config: obstacles `campfire, rock, tree, bush`) |
| `quasi_binomial_fit()` | 247–269 | **import** (do not copy) | none |
| `fit_glms()` — univariate per factor on the subset where it is defined; M1–M5 | 272–332 | generalised to a recipe table (B4) | the factor dicts `EXO`, `EXO_P`, `EXO_R`, `END` are typed; the intensity drop for single / sum smell layouts is a hand-written `if` (lines 287–291) |
| `cross_tabs()` | 335–354 | replaced (B6) | marginal injury / nutrition bins only; same-row binning (open Known Bug, A6) |

The outcome definition — successes / trials per episode, trials = the agent's **chosen** steps
`t ≥ 1` (row `t = 0` is the random spawn), success = the behaviour at row `t` — is generic and is
the definition every target in this plan uses. The model — quasi-binomial GLM on that share, effects
as percentage points per +1 SD at the pooled rate, univariate and multivariate, exogenous versus
consequence blocks — is kept unchanged (user decision 2).

### A2. What the store can and cannot support (schema version 1)

Checked against [[TRAJECTORY_STORE_SCHEMA]] §3 and a real hv store manifest
(`results/trajectories_hvsmell/20261001-002402_rppo_hv1ch_t1none_s42/10000038/cfde8dd044/_manifest.json`):

| Need | Store source | Available? |
|---|---|---|
| bush hiding, eating | step `agent_in_bush`, `ate_food` | yes |
| near rabbit / near predator | step `animal_row/col` + episode `animal_active` + slot classes | yes |
| temperature of the agent's own square | **no column.** Recoverable from `obs_true` when the world has thermal on, the thermoception sensor is present and body temperature is observable (hv worlds: `thermal.relative: true`, `body_temp_observable: true`): square temperature = thermoception reading at the agent's own cell + body temperature (with `relative: false` the reading is the square temperature itself) | yes, indirectly (B1, A2b) |
| body temperature | inside `obs_true` at the `Body Temperature` index; `sensor.py:480` documents `Thermoception[centre] + BodyTemperature == thermal_field[own cell]` under `relative: true`, and the centre is the first of the five cells (`sensor.py:68-70`) | yes, when observable |
| per-episode baseline world temperature (`thermal.default_temp`, hv: drawn from −31…−29) | not recorded as a column. Recoverable at `t = 0`: the field equals the baseline exactly on any square farther than the blur's kernel radius from every active campfire (`core.py` `_build_thermal_field`: fill, stamp, one blur), so any in-grid square of the agent's five thermoception cells that lies that far away gives it (square temperature = reading + body temperature) | yes, on episodes where such a square exists at spawn (exogenous: depends only on the spawn layout) → factor `ambient_temp` (B2 handler 6b) |
| hydration / water | no column; no water mechanic exists in `src/environment/` (only the `thirst_water` simulation study) | **no** → any water draw is flagged *unhandled* |
| thermal hot-spot positions (`thermal.use_random_spots`) | not recorded | **no** → *unhandled* when enabled (hv worlds: disabled) |
| visual-property draws (`visual_properties_std > 0`) | episode `animal_visual_property_sampled` | recorded, no handler in this plan → *unhandled* (no maintained world jitters them) |
| resource property draws | `res_property_sampled_init` is re-drawn on regeneration (schema §6 caveat) | *unhandled* if `properties_std > 0` on a resource |
| termination incl. thermal death (code 5) | episode `termination_reason` | yes |

**A2b. The observation-index trap.** The manifest stores `observation_breakdown` as a JSON object
written with `sort_keys=True` (`src/utils/trajectory_store.py:506`), so its key order is
**alphabetical, not the observation order** — reading an index off it would silently pick the wrong
slot. The order must come from `src.environment.sensor.get_observation_breakdown(params)` on params
rebuilt from the saved config, as `scripts/eval/traj_collect/traj_scan.py:353` does, then be
cross-checked against the manifest's widths (same names, same widths, same total `D`). Which of the
five thermoception cells is the agent's own cell comes from the sensor code in
`src/environment/sensor.py` (`get_observation`'s thermoception block), and is verified empirically
(Checkpoint S0.4) against the environment's own field. `obs_true` is noise-free; a store whose
`obs_precision` is not `float32` makes the warm-cell target unavailable (reason stated).

### A3. What varies in the two reference worlds (read from the saved configs)

| Draw | a01 (the hiding page's agent) | hv worlds (first population) |
|---|---|---|
| start injury / nutrition | random | random |
| start satiation | fixed | fixed |
| start position | random | random |
| start body temperature | — (no thermal) | random, −10…5, observable |
| baseline world temperature | — | random −31…−29, recovered at spawn where possible (A2) |
| predator count, rabbit count | 0–2 each | 0–2 each |
| predator traits | detection 1–7, attack delay 1–3, attack range 2–3, stamina 30–150 | same |
| smell | two-channel *difference* layout | *single*, *sum* (matched strength) or *difference*, per world |
| obstacle counts | bush 4–10, rock 6–12 | **campfire 1–3**, rock 6–12, tree 0 (fixed), bush 4–10 |
| resource counts | food 1–4, hiding predator 2–12 | same |
| ranges that are **not** episode draws | `damage` on predators / rocks / hiding predators (drawn per hit) | same, plus `temperature_ratio` (fixed 11) |

On a01 the rule "include a trait iff its range varies" yields **exactly** the legacy predator trait
set (detection, delay, range, stamina) and the legacy rabbit set (smell only). That is what makes the
byte-identity gate (A5) reachable without special-casing a01.

### A4. Population and blinding

- **Manifests** are written by the existing `scripts/analysis/studies/hypervigilance/make_population.py`
  (with `--out` under this pipeline's root) and read with `readings.load_population()` (completed
  cells only; duplicate-seed, tag and store checks). No new manifest format. Each cell carries
  `world`, `agent`, `seed` — exactly the run-level factors the cross-run screening needs.
- **First population: 18 runs** = the 16 hv runs (H01–H16) + the two level-05 body-interaction
  controls (C01, C02, mapped to world `hv2ch` seed 42 by `make_population.py`'s `CELL_WORLD`) of
  [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] §3: 3 smell worlds × 2 agents × 3 seeds. On 2026-10-01
  stores exist for the 8 ordinary-agent hv runs and C01 (`results/trajectories_hvsmell/`); the
  modulated-agent runs and C02 are not collected yet. **Precondition (owned by the parent session,
  which will update the study's Launch Manifest):** `make_population.py --from-study-doc`
  (`make_population.py:153-187`) hard-fails today on two kinds of row — C02 (status `completed`, no
  store yet) and any H-row still marked `running` that already has a final checkpoint and a store
  (stale-status guard). Until the manifest is updated, the hv population cannot be built; S0's
  infrastructure, tests and the a01 gate do not need it, the hv sweeps of S0 wait for it. This
  pipeline never edits or promotes a status. **The cross-run screening (S5) needs all 18 runs.**
- **Blinding.** The study pre-registered that no hv run is read before its reference measurement of
  seed-to-seed variation (on five control seeds) is frozen (study §5.3). This pipeline reads hv runs,
  so it calls `readings.require_yardstick_for(cells)` (the function's name in code) before sweeping.
  That measurement exists today (`results/analysis/hypervigilance/cmp10m/yardstick.json`), so this is
  a guard, not a blocker.

### A5. The golden gate — what "reproduces hiding_drivers" means concretely

| Object | Reference | Criterion |
|---|---|---|
| bush-hiding `univariate.csv` and `multivariate.csv` written by the **new** pipeline on the a01 store (`results/JAX_RecurrentPPO/20260810-185749_rppo_restprem_a01_n106`, store root `results/trajectories`) into a scratch dir | `results/analysis/hypervigilance/_golden_scratch/g3_reference/{univariate,multivariate}.csv` — produced by the base-commit `hiding_drivers.py` on the same store by the hypervigilance gate | **byte-identical** (`cmp -s`). Before comparing, the reference files' sha256 must equal the values recorded in `results/analysis/hypervigilance/_golden_sweep_pass.json` → `g3_reference` (`univariate.csv` `c3d7259c…`, `multivariate.csv` `0ad912ee…`); a mismatch is a hard failure, never a reason to regenerate silently |

What byte identity forces on the design:

1. `quasi_binomial_fit` is **imported** from `hiding_drivers.py`, not copied.
2. The per-run CSV columns and their order are the legacy ones
   (`model,term,n,coef,se,z,p,dpp_per_unit,dpp_per_sd,pseudo_r2,overdispersion[,block]`); anything
   new (target name, exclusions) goes to a separate `prefit.json`, never into these CSVs.
3. Factor **names and order** on a01 equal the legacy ones (`EXO` → `EXO_P` → `EXO_R` → `END`;
   intensity appended last in the predator block, as at line 286). The registry carries a name map
   for known declarations (B2) and emits factors in a fixed role order.
4. Model labels on a01 equal the legacy strings exactly (B4).
5. Per-episode arithmetic uses the same primitives in the same order as `aggregate()`
   (`np.add.reduceat` over episode starts per shard, `np.bincount` with `minlength`, float64 casts of
   the same columns, `mean_over` for slot means). `core/golden.py`'s docstring records why
   float32-origin sums are order-insensitive on this data; the gate is what proves it.
6. **Pre-fit checks exclude nothing on a01.** If a check excludes an a01 factor the gate fails by
   construction — the intended signal that a threshold is too aggressive (Checkpoint S0.7).

**The reference files are copied into this pipeline's own tree at S0**
(`results/analysis/basic_behaviour/_golden_reference/a01/`, with their sha256s), because the hv
tooling's `golden_check.py --tier sweep` may regenerate `g3_reference/` at a different base commit.

**Second gate — the new-world paths (reviewer M4).** The a01 gate exercises only the unchanged path
(bush hiding, two-channel smell, no exclusions). A second, differential gate runs on **one hv1ch store**
(single-channel smell, campfires, thermal), where the frozen `hiding_drivers.py` still runs (it
accepts the single layout):

| Check | Criterion |
|---|---|
| per-episode arrays shared by both (all legacy `aggregate.npz` keys except `n_rock`, which the legacy code fills with rocks **and** campfires) | `np.array_equal` after the name map of B2 |
| univariate rows of factors not involving the rock / campfire split | each legacy `univariate.csv` line appears **verbatim** among the new file's lines (the new file has extra rows — `n_campfire`, `start_body_temp`, `ambient_temp`, thermal consequences — so the files are compared as line sets, not with `cmp`) |
| `eating` successes | `== n_ate` (legacy) per episode |
| `near_predator` successes | `== n_pred_near` per episode |
| `near_rabbit` successes − steps with a rabbit **and** a predator near | `== n_rab_near` per episode (the sweep stores the both-near count for this) |
| intensity exclusion | `pred_olf_intensity`, `rab_olf_intensity` excluded as duplicates; the legacy file has no such rows either |

Not in either gate: cross-tables (`summary.json`), whose binning convention this plan changes on
purpose (A6), and the cross-run screening, which has no legacy counterpart (its checks are in S5).
Runtime reference: the legacy a01 sweep took 346.7 s on this container
(`_golden_sweep_pass.json` → `timings_seconds.g3_candidate`).

### A6. Two known hazards this plan must not inherit

- **Same-row binning** (Known Bugs, OPEN, "The hiding-drivers cross-tabs bin injury from the same step
  as the bush outcome"): `hiding_drivers.py:223` pairs the behaviour at row `t` with the injury at row
  `t`, although the action was chosen while the agent was in row `t−1`. `hiding_drivers.py` stays
  **frozen** (it is the golden reference and published pages cite it). This settles the row's
  freeze-versus-fix decision, which was handed to senior-developer: **freeze** the old script, and
  do it right in the new one. `bug-curator` records that decision and this pipeline as a new consumer
  in the same change as the implementation (File Changes). The new cross-tables condition on
  **row `t−1`** — injury, nutrition, animal distances — and the page says so. Episode-level GLM
  inputs are episode summaries and are unaffected, which is why the gate can be byte-identical.
- **Lab-node env drift** (Known Bugs, OPEN): `statsmodels` is missing on the lab nodes. Every fit
  stage runs **locally** (`nice -n 19`), never via `run_command.py`; statsmodels / numpy versions
  move the last bits of a fit, so the gate and all population fits run in the same local env.

### A7. Comparing runs: what the cross-run analysis is for, and where its uncertainty comes from

**Purpose (user, 2026-10-01).** The cross-run figure screens and ranks which settings — smell world,
agent type, training seed — move each behaviour more or less, to choose a training direction. It is
**exploratory**, not confirmatory: no verdict, and no pass/fail that could compete with the smell
study's pre-registered decision rule (study §5.3).

**The replicate is the training run.** The pooled data are ~18 million episodes but only **18
training runs** (3 smell worlds × 2 agents × 3 seeds), and world and agent are properties of a run.
Standard errors computed from episodes treat every episode as independent and would call a world
difference overwhelmingly certain even if the three seeds of each setting disagreed
(*pseudo-replication*). So every interpreted effect's uncertainty is computed **at the run level,
from seed-to-seed variation**, by a two-stage analysis — the standard summary-statistics route to a
mixed-effects model with world and agent as fixed effects and run as the random replicate:

1. **Stage 1, per run.** In each run, the same within-run model is fitted (B5): its logit-scale
   coefficients on a common scale (smell per nat, injury and nutrition in raw points), and the run's
   behaviour level (the logit of its share). Within-run standard errors are negligible beside the
   spread between seeds at ~1 M episodes per run (checked, S5.3).
2. **Stage 2, across runs.** Each per-run quantity is regressed on the six world × agent cells by
   ordinary least squares (n = 18, residual df 12, exact *t*). This estimates every cell directly
   (no additivity imposed) and gives cell means, contrasts between settings, and the pooled
   within-cell SD of the 18 values — the **seed-to-seed SD**.
3. **Exact permutation, within agent.** For each agent, all 9!/(3!·3!·3!) = 1,680 relabelings of the
   world labels across its 9 runs give an assumption-free p-value for "the three worlds differ".
4. **Effect sizes and variance components.** Each setting contrast is also reported divided by the
   seed-to-seed SD (a standardised effect size), and the run-to-run variation of each quantity is
   split into the shares due to world, agent, world × agent, shared starting weights (seed within
   agent — runs of one seed and one agent start from identical weights, study §2.4) and the remainder.
   These two are what rank the settings.

No sandwich (cluster-robust) estimator is used: with 3 runs per cell the two-stage regression has
exact small-sample degrees of freedom, and a sandwich would add a second, more optimistic answer.
The episode-level standard error appears only as a **secondary column labelled "conditional on these
runs"** — the uncertainty if these exact 18 trained agents were the whole question.

**Relation to the smell study.** Its pre-registered hypervigilance test (S1: early-window bush share,
no-predator one-rabbit episodes, quarter contrast, decision rule §5.3) lives in that study and its
tooling. This page shows the smell × start-injury slope per run and per cell, **per agent**, using the
study's registered control-world reading (B5), with no test attached, under the label "exploratory
screening — not the smell study's pre-registered verdict".

**Two open assumptions, stated on the page.** (i) All runs are evaluated on the same episode seeds
(`seed_base` 1,000,000), so episode *k* is correlated across runs; stage 2 sees only per-run
summaries, so this does not inflate its df, but it makes run-to-run differences slightly more
precise than independent draws would. (ii) The seed-42 control runs (C01, C02) were trained a week
earlier than the others (study §2.4); they are the only cell members with different provenance.

---

## Implementation Plan

### Design

```
make_population.py (existing) ──► population.json
                                        │
registry.py   saved config + store manifest ──► targets available, factors, audit of unhandled draws
                                        │
sweep.py      one pass over each cell's store ──► per-cell cache: episodes.npz, xtab.npz, inventory.json
                                        │
fit.py        --kind univariate|multivariate --target T ──► <cell>/<T>/{univariate,multivariate}.csv, prefit.json
screen.py     --target T ──► screen/<T>/{per_run,cells,contrasts,variance,permutation}.csv, prefit.json
                                        │
golden_gate.py a01: cmp vs reference CSVs; hv1ch: frozen script vs new ──► _golden_pass.json
                                        │
f1 … f6 figure scripts (read caches only; seconds) ──► figures/<stem>.{svg,pdf,png} + <stem>.samples.json
                                        │
build_page.py house template + present figures; absent ones shown as "not yet produced"
```

The store sweep (~6 min per million-episode store) happens once per cell; every figure step reads
cached files, so a question about Figure 3 never forces a re-sweep unless a target or factor
definition changes. Lesson recorded in the LLM Wiki (`20260909_1505_one_python_figure_pipeline_not_split`):
one Python script per figure, figures as files, and an incomplete set must be **visibly** incomplete,
never reported as a clean pass.

#### B1. Target menu (`registry.py`) — user decision 1

Each target is successes / trials per episode over chosen steps `t ≥ 1`. A target is computed for a
cell only when every requirement holds; otherwise F1 lists it as unavailable with the reason.

| Target id | Plain name on the page | Success at row `t` | Requires |
|---|---|---|---|
| `bush_dwell` | hiding in a bush | `agent_in_bush` | step column present; ≥ 1 obstacle declaration with `hides_agent: true` and allocation > 0 |
| `eating` | eating | `ate_food` | column present; `environment.eat_action_enabled` true; a resource declaration of type `food` |
| `near_rabbit` | within two squares of a rabbit | any active neutral-class animal within Chebyshev distance 2 (`NEAR_D`, imported) | ≥ 1 neutral-class slot |
| `near_predator` | within two squares of a predator | any active predator-class animal within Chebyshev distance 2 | ≥ 1 predator-class slot |
| `warm_cell` | on a warm square | a body resting on the agent's own square (A2) would settle **at or above the comfort setpoint and at or below the survivable maximum**: with `T* = config_loader._thermal_equilibrium(T_square, k_exchange, k_loss, k_metabolic, temperature_setpoint)` (the environment's own function, imported, not re-implemented), success iff `temperature_setpoint ≤ T* ≤ max_temperature`. Squares whose equilibrium is lethally hot are not "warm". In the hv worlds (`k_metabolic = 0`, setpoint 0, maximum 15) this is 0 ° ≤ ⅔·T_square ≤ 15 °, against a baseline of about −30 ° | `thermal.enabled`; thermoception and body temperature in the observation (or `relative: false`); `obs_precision == float32` |

Note on `near_rabbit`: the target counts every step with a rabbit within two squares. The legacy
*consequence* factor `frac_time_rabbit_near` (kept for the gate) counts only steps with a rabbit near
**and no predator near**; the two are deliberately named apart on the page.

Survival (episode length — the project's evaluation metric) and termination shares (codes 1–5,
including thermal death) are reported on F1 for every cell; they are not fitted as binomial targets.

#### B2. Factor registry and config audit (`registry.py`)

Every factor carries `name`, `block` (`exogenous` / `consequence`), `role` (`episode` /
`class_trait:<class>` / `consequence`), the **subset** where it is defined (`all`, `exactly one of
class C`, `exactly one C1 and one C2`, `exactly two of C`), and `source` (the config feature that
produced it). Roles are emitted in this fixed order, which on a01 is the legacy order:

| Order | Handler (config feature → factor) | Factor names (legacy names on a01 kept) |
|---|---|---|
| 1 | `body.random_start_<x>: true` and store step column for `<x>` exists (`injury`→`injury_level`, `nutrition`, `satiation`) | `start_injury`, `start_nutrition`, `start_satiation` |
| 2 | each entity declaration with `count_low < count_high` | `n_predators` (tag `pred`), `n_rabbits` (tag `rabbit`); unknown tag → `n_<tag>` |
| 3 | each obstacle declaration with varying count, **by declaration name** (fixes campfire-as-rock) | `n_bushes`, `n_rocks`; unknown → `n_<name>` (so `n_campfire`) |
| 4 | each resource declaration with varying count, by name | `n_food`, `n_ambush_predators` (`hiding_predator`); unknown → `n_<name>` |
| 5 | `environment.random_start_pos: true` and ≥ 1 hiding obstacle | `spawn_dist_to_bush` |
| 6 | `thermal.enabled` and `random_start_body_temp` and `body_temp_observable` | `start_body_temp` (from `obs_true` at `t = 0`, index per A2b) |
| 6b | `thermal.enabled` and `thermal.default_temp` is a range with low ≠ high, thermoception and body temperature observable | `ambient_temp` (A2: read at `t = 0` from a thermoception square beyond the kernel radius of every active campfire; undefined — NaN — on episodes with no such square, and its subset is "episodes where recoverable") |
| 7 | per predator-class declaration: each varying trait range in `TRAIT_COLUMNS` (`detection_range`→`animal_detect_sampled`, `attack_delay`, `attack_range`, `max_stamina`, `stamina_recovery_rate`→`animal_recovery_sampled`, `hunt_stamina_threshold`, `lose_interest_multiplier`, `move_interval`), mean over active slots; then smell statistic; then `spawn_dist_to_predator`; then smell intensity | `pred_detection_range`, `pred_attack_delay`, `pred_attack_range`, `pred_max_stamina`, `pred_smell_predatorness`, `spawn_dist_to_predator`, `pred_olf_intensity`; subset = exactly one predator |
| 8 | per neutral-class declaration: varying traits, then smell statistic, then intensity | `rab_smell_predatorness`, `rab_olf_intensity`; subset = exactly one rabbit |
| 9 | consequences (legacy `END`, same formulas) | `frac_time_injured`, `frac_time_inj_severe`, `mean_injury`, `peak_injury`, `frac_time_low_nutrition`, `mean_nutrition`, `total_damage_taken`, `eat_rate`, `rest_rate`, `episode_length`, `frac_time_predator_near`, `frac_time_rabbit_near` |
| 10 | consequences, thermal worlds only | `mean_body_temp` (when observable), `frac_time_warm_cell` |
| — | M5 helpers (not univariate) | `detect_keenest`, `detect_least_keen`, `detect_spread` (two-predator episodes) |

Smell statistic and intensity come from `core/env.scent_spec(cfg)` (`statistic`, `intensity`,
`llr`), so the three accepted smell layouts are handled and any other odour config is refused by that
function. In the single and sum layouts intensity is the same array as the statistic; the duplicate
check (B3) drops it with that reason — the generic replacement for the hand-written `if` at lines 287–291.
`sweep.py` also stores the rabbit smell on the **common evidence scale** — the log-likelihood ratio in
nats, `spec.llr(statistic)` — as `rab_smell_llr` (used by the cross-run screening, B5; not a per-run
univariate factor, since it is a linear rescaling of `rab_smell_predatorness` within a run).

**Config audit.** `audit(cfg, manifest)` walks the saved config and lists every *randomised draw
marker*: any key `random_*` set to `true`; any `<x>_low` / `<x>_high` pair with different values; in
`environment.entities / obstacles / resources`: `count_low < count_high`, any two-number list `[a, b]`
with `a ≠ b`, any `properties_std` / `visual_properties_std` entry `> 0`; and any two-number list with
`a ≠ b` in the `thermal` block. Each marker must be **claimed** by a handler above or by an explicit
`NOT_A_DRAW` entry with a reason (`damage` — drawn per hit; `spawn_area` / `patrol_area` / `area` —
placement regions; `start_<x>_low/high` — handler 1; `start_body_temp_low/high` — handler 6; smell
`properties_std` on emitting channels — the smell handler). Everything unclaimed becomes an
**unhandled** row (`marker`, `config path`, `why no handler`) in `inventory.json` and on F2. The run is
not stopped — a new feature is either picked up or **visibly** not. Expected on the hv worlds: none
(`thermal.default_temp` is claimed by handler 6b). Must also catch, in tests: a body `random_start_hydration:
true` (no store column) and `thermal.use_random_spots: true` (positions not recorded).

**Slot cross-check.** The registry's slot indices (`core/env.slot_layout` plus a per-name split of
obstacles and resources) must agree with the manifest's per-slot `animal_classes` / `animal_tags`,
`obstacle_names`, `res_type`; any disagreement is a hard stop.

#### B3. Pre-fit checks (`fit.py`, `screen.py`; per run, per target)

Applied in this order to each factor on its own subset, and again inside each multivariate design:

| Check | Rule | Reason string on F2 |
|---|---|---|
| too few episodes | finite on fewer than `MIN_EPISODES = 1000` episodes of its subset | "defined on N episodes (< 1000)" |
| never varies | one unique value on its subset | "constant (= v) in this run" |
| exact duplicate | `np.array_equal` with an earlier factor on the shared defined rows | "identical to <name>" |
| is the outcome | consequence whose formula is the target's indicator: `eat_rate` for `eating`; `frac_time_predator_near` for `near_predator`; `frac_time_rabbit_near` for `near_rabbit` (a sub-count of the outcome); `frac_time_warm_cell` for `warm_cell` | "is (part of) the outcome being modelled" |
| collinear (multivariate and within-run screening models only) | design rank < columns, or `|r| ≥ 0.999` with an earlier column | "collinear with <name> (r = …)" |

A model whose subset has fewer than `MIN_EPISODES` episodes is skipped with a reason. Every exclusion
goes to `prefit.json`; nothing is excluded silently. Thresholds are pre-registered module constants
(Open question Q2).

#### B4. Per-run models (`fit.py`) — unchanged from a01

Univariate: one quasi-binomial GLM per included factor on its subset; ranked by `|dpp_per_sd|` (legacy
line 312). Multivariate: a recipe table, written as data, evaluated in this order:

| Id | Recipe (generic) | Subset | a01 label (must match byte-for-byte) |
|---|---|---|---|
| M1 | all `episode`-role exogenous factors | all episodes | `M1 exogenous, all episodes` |
| M2 | M1 set minus the count of the first predator class C1, plus C1's class-trait factors | exactly one C1 | `M2 exogenous + predator traits, 1-predator episodes` |
| M3 | M2 set minus the count of the first neutral class C2, plus C2's class-trait factors | exactly one C1 and one C2 | `M3 + rabbit smell, 1 predator + 1 rabbit` |
| M5 | M1 set minus the C1 count, plus `detect_keenest`, `detect_least_keen`, `detect_spread`, and the C1 means of `attack_delay` and `max_stamina` — a **fixed recipe carried over from a01**, skipped with a reason where two-C1 episodes < `MIN_EPISODES` or C1 lacks those traits | exactly two C1 | `M5 two-predator episodes, keenest vs least-keen` |
| M4 | all exogenous `episode`-role factors plus all consequences | all episodes | `M4 exogenous + consequences` |

Labels are templates over the class display names (`predator`, `rabbit`) and the word `smell` when
every C2 trait is a smell trait, else `traits`. Output order M1, M2, M3, M5, M4 is the legacy order.

#### B5. Which settings move each behaviour — exploratory screening across runs (`screen.py`)

Method and rationale in A7. For each target:

**Stage 1 — per run** (from `episodes.npz`; quasi-binomial GLM, logit link, as in a01):

- *Level*: the run's behaviour share over all episodes, and its logit.
- *Within-run model*, on episodes with **exactly one rabbit** (rabbit smell is defined only there;
  Open question Q3): logit of the episode's share on `start_injury` (per 10 points), `start_nutrition`
  (per 10 points), the rabbit's smell **in nats**, smell × start injury, and the M1 exogenous
  covariates included (B3) in every run of the population. The smell regressor follows the smell
  study's registered reading (study §5.2 S1, Revision 4) so the control world is read on the same
  identity-plus-strength composition as the treated worlds:
  - single-channel and matched-strength worlds: `rab_smell_llr` (the scent statistic on its evidence
    scale, `scent_spec.llr`);
  - two-channel control world: the rabbit's **channel 1 in nats** (`scent_spec.channel_scale` for
    channel 1: 2.22 nats per unit) **with channel 2 as a covariate** — the same reading as
    `readings.s2_matched`. The plain control reading (`x1 − x2` in nats) is fitted too and reported
    beside it as descriptive.
- Outputs per run: every coefficient on the **logit scale** with its episode-level SE, and its
  **average marginal effect** in percentage points (the mean over that run's episodes of
  β·p̂(1 − p̂)·100, at each episode's own fitted rate) — the pp reading that stays meaningful when
  base rates differ between worlds. For the interaction the pp reading is the change in the smell
  effect per 10 points of start injury, computed by finite difference of fitted probabilities, not by
  converting the coefficient (a logit interaction coefficient is not a marginal effect).

**Stage 2 — across runs**, for every stage-1 quantity `q` (level, each slope), separately:

- OLS of the 18 values on the six world × agent cells (cell-means coding; n = 18, residual df 12):
  each cell's mean with its run-level SE (`s / √3`, `s` = pooled within-cell seed-to-seed SD) and
  95 % interval from *t*₁₂; the seed-to-seed SD `s` itself; and these contrasts with run-level SE and
  exact *t*₁₂: each treated world − control world **within each agent**, modulated − ordinary agent
  **within each world**, and the world and agent averages under sum-to-zero (effect) coding — stated
  as such, so an "average" effect means the unweighted average over cells, never a reference cell.
- Standardised effect size of each contrast: contrast ÷ `s`.
- Variance components (balanced design, sums of squares): shares of the run-to-run variation of `q`
  due to world (2 df), agent (1), world × agent (2), shared starting weights = seed within agent (4),
  and the remainder (8). These shares and the standardised effects are what F5 ranks.
- Exact permutation p-value per agent for "the three worlds differ" (all 1,680 relabelings of world
  labels across that agent's 9 runs; statistic = the between-world F).
- Secondary column, labelled **"conditional on these runs"**: the cell mean's SE from the per-run
  episode-level SEs alone (`√Σ se_r² / 3`).

**Smell terms on the hv-study population.** For the rabbit-smell slope and the smell × start-injury
slope, F5 shows per-run values and per-cell means ± seed-to-seed SD **per agent**, with no p-value
and no pass/fail, under "exploratory screening — not the smell study's pre-registered verdict". The
study's own S1 reading differs on purpose (first 25 steps, no-predator episodes, quarter contrast)
and is the one that decides. Tests (t, permutation) are reported for the non-smell quantities only.

**Outputs** (`results/analysis/basic_behaviour/<population>/screen/<target>/`): `per_run.csv`
(stage 1, one row per run × quantity), `cells.csv` (cell means, SEs, intervals, seed-to-seed SD,
conditional SE), `contrasts.csv` (estimate, run-level SE, t, df, p, standardised effect),
`variance.csv` (shares), `permutation.csv`, `prefit.json` (exclusions; per-run subset sizes).

#### B6. Cross-tables (`sweep.py` accumulates; `f6` reads)

All conditioned on **row `t−1`** (A6), for each available target:
- injury band × nutrition band (legacy edges `INJ_EDGES`, `NUT_EDGES`, imported): 4 × 4 successes
  and trials;
- rabbit near / far × predator near / far (Chebyshev 2): 2 × 2;
- rabbit-smell ladder: from `episodes.npz` — episodes with exactly one rabbit and no predator, in
  sextiles of `rab_smell_llr` (nats), so the three smell worlds share one axis.

The `t−1` row is the previous row in the shard; assert `seed[i−1] == seed[i]` **and**
`t[i] == t[i−1] + 1` for every `t ≥ 1` row.

### File Changes

All new code lives in a new folder `scripts/analysis/basic_behaviour/` — **two levels** under
`scripts/`, so any repo-root walk is three `..` (dependency map §0 depth hazard). Scripts run with
`/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`; outputs go to
`results/analysis/basic_behaviour/<population>/` (gitignored); page artifacts to a **mandatory**
`--page-dir` (no default; first population: `docs/experiments/active/hypervigilance/basic_behaviour_hvsmell/`).

#### `scripts/analysis/basic_behaviour/registry.py` (new)

`targets(cfg, manifest, step_schema)` (B1), `factors(cfg, manifest)` (B2), `audit(cfg, manifest)`
(unhandled rows), `slots(cfg, manifest)` (with the cross-check), `obs_indices(cfg, manifest)` →
`{body_temp, thermo_own_cell}` or `None` (A2b: rebuilds params as `traj_scan.py` does, calls
`get_observation_breakdown`, cross-checks names, widths and `D` against the manifest). Imports
`core/env` (`slot_layout`, `scent_spec`, `listcol`), `hiding_drivers` (`NEAR_D`, `INJ_EDGES`,
`NUT_EDGES`, `find_stores`, `shard_files`) and `src.environment.config_loader._thermal_equilibrium` —
no copies.

#### `scripts/analysis/basic_behaviour/sweep.py` (new)

`--population <population.json> --out-root <abs path under results/analysis/basic_behaviour/>
[--cells L …] [--reuse-cache]`. Loads with `readings.load_population`; calls
`readings.require_yardstick_for` (blinding guard, A4). Per cell, serially: one pass over the step shards reading only the
columns the cell's targets and factors need (`obs_true` only on thermal worlds), writing
`<cell>/episodes.npz` (per episode: every factor, `rab_smell_llr`, every target's successes and the
trials), `<cell>/xtab.npz` (B6), `<cell>/inventory.json` (targets available / unavailable with
reasons; factors with role, subset, source; unhandled audit rows; slot map; scent spec; world / agent
/ seed), and `<cell>/_provenance.json` (run, stores, checkpoint, sha256 of the pipeline sources, git
HEAD, seconds). Keeps the legacy assertions (contiguous seeds, shard alignment, one reset row per
episode, successes ≤ trials). **Stale-cache guard:** refuses a cell whose outputs exist unless
`--reuse-cache`, and then only if run, stores and source hashes equal the recorded ones (the trap in the
dependency-map row for `nmn_site_grid/run_hiding_drivers.py`).

#### `scripts/analysis/basic_behaviour/fit.py` (new)

`--population … --out-root … --kind univariate|multivariate --target <id> [--cells …]`. Reads
`episodes.npz`, runs B3 then B4 with `hiding_drivers.quasi_binomial_fit`, writes
`<cell>/<target>/{univariate,multivariate}.csv` in the legacy format and `<cell>/<target>/prefit.json`.
Refuses to run unless `_golden_pass.json` exists and its recorded source hashes equal the current
`registry.py`, `sweep.py`, `fit.py`, `core/env.py`, `hiding_drivers.py`.

#### `scripts/analysis/basic_behaviour/screen.py` (new)

`--population … --out-root … --target <id>`. B5. Same golden-stamp requirement as `fit.py`. Refuses
to run unless every cell of the population is completed and swept (a partial set would change what
the cell means are). Stage 1 uses `hiding_drivers.quasi_binomial_fit` per run (no pooled episode-level
fit, so no large in-memory design); stage 2 is plain numpy OLS on 18 rows, the exact permutation and
the sums-of-squares decomposition. Design columns are built explicitly (no formula strings), so term
names are testable.

#### `scripts/analysis/basic_behaviour/golden_gate.py` (new)

**Gate 1 (a01).** Builds a one-cell a01 population —
`make_population.py --population bb_golden_a01 --runs results/JAX_RecurrentPPO/20260810-185749_rppo_restprem_a01_n106 --world a01 --agent unmodulated --store-root results/trajectories --out <scratch>/population.json`
(`--population` is required by the script; `--agent` is required because the a01 tag carries no
agent name) — runs `sweep.py` and both `fit.py` kinds for `bush_dwell` into
`results/analysis/basic_behaviour/_golden_scratch/<sources-hash12>/`, verifies the copied reference
sha256s (A5), then `cmp -s` on both CSVs; asserts `prefit.json` lists **zero** exclusions and
`inventory.json` **zero** unhandled markers for a01.
**Gate 2 (hv1ch).** Runs the frozen `hiding_drivers.py` (unchanged file, invoked by subprocess) and
the new sweep + univariate fit on one hv1ch store into scratch, then the checks of A5's second table.
Pass of both → writes `results/analysis/basic_behaviour/_golden_pass.json` (source sha256s, reference
sha256s, HEAD, sweep seconds). Fail → no stamp, non-zero exit, the differing arrays / lines printed
(first 40). `fit.py` and `screen.py` require this stamp.

#### `scripts/analysis/basic_behaviour/_fig.py` (new, shared by the figure scripts)

`load_outputs(out_root)`, `record_samples(fig_dir, stem, rows)` (rows `{what, used, total, note}`;
percentage derived; `used > total` refused — same contract as `scripts/analysis/ladder/_ladder.py:352`),
and the cell → world / agent / seed labelling and marker encoding shared by every figure (colour =
world, shape = agent, so all six figures read the same way). Each figure script calls `house.apply()`
first, sets no style of its own, and saves via `house.save(fig, <fig_dir>/<stem>)`.

#### Figure scripts (new) — one per step, each reads caches only (user's sequence)

| Script | Stem(s) | What it draws |
|---|---|---|
| `f1_behaviours_survival.py` | `f1_behaviours_survival` | One panel per available target: share of chosen steps (%) per run, grouped by world × agent, one dot per seed. Then mean survival steps per run, and termination shares (starved / killed / overate / thermal / reached max) per run. Unavailable targets in the samples rows with reasons |
| `f2_factor_inventory.py` | `f2_factor_inventory` | Rows = factors (registry order) + unhandled markers; columns = runs; cell = included / excluded (reason code) / not applicable / unhandled. The builder renders the full reason table from `inventory.json` + `prefit.json` |
| `f3_univariate.py --target T` | `f3_univariate__<T>` | Rows = factors ranked by median `|Δpp per SD|` across runs; x = Δpp per +1 SD; one marker per run |
| `f4_multivariate.py --target T` | `f4_multivariate__<T>` | One panel per M-model; same encoding; models skipped in a run listed in the samples rows |
| `f5_settings.py --target T` | `f5_settings__<T>` | "Which settings move each behaviour" (exploratory screening). (a) Ranking: for the behaviour level and each slope, the variance-component shares (world, agent, world × agent, shared starting weights, remainder) as one stacked bar per quantity; (b) the standardised effect of each contrast (treated world − control within agent; modulated − ordinary within world), sorted, with run-level 95 % intervals; (c) per world × agent cell: the 3 per-run values as dots and the cell mean ± seed-to-seed SD, for the level, start injury, start nutrition, smell (per nat) and smell × injury — the two smell panels **per agent, no tests**, titled "exploratory screening — not the smell study's pre-registered verdict" |
| `f6_crosstabs.py --target T` | `f6_crosstabs__<T>` | (a) injury band × nutrition band share per world × agent (trial-weighted over seeds; seed range in the cell label); (b) rabbit-smell ladder in nats, one line per run; (c) near / far rabbit × near / far predator share per run |

#### `scripts/analysis/basic_behaviour/page_template.html` (new) and `build_page.py` (new)

The template holds six figure blocks F1–F6 in order. Audience is the user, reading figure by figure
(user decision 4), so each block carries: the §11a `<b>Axes.</b>` sentence; a §11c "How it is
computed" note of 150–250 words in plain language, glossing every statistical term where it first
appears (quasi-binomial, overdispersion, "per SD", logit scale, average marginal effect,
pseudo-replication, seed-to-seed variation, two-stage analysis, variance components, permutation test); and a short "What this figure cannot tell you". Numbers come from tokens the builder fills
from cached data (`{{N_RUNS}}`, `{{TARGET_LABEL}}`, …). The template carries **no interpretive
claims** — interpretation for a population is written by `experiment-analyzer` in its own doc. The
entry section (`PURPOSE`) is plain-language per CLAUDE.md "Documentation framing".

`build_page.py --population … --out-root … --page-dir …`:
- takes the House Style Sheet's `<style>`, viewer and fonts from
  `docs/develop/active/meta/house_style_sheet.template.html` at build time, as
  `scripts/analysis/studies/modulator_clues/build_algorithmic_null_page.py` does;
- for figure blocks whose files exist: embeds the PNG, renders the samples table from
  `<stem>.samples.json`, prints the regenerating command; F3–F6 show one figure per target present;
- for blocks with nothing on disk: renders a visible "Figure Fn — not yet produced" box, and the build
  prints `partial: present [F1, F2], pending [F3 … F6]` and exits 0;
- **fails** on: a present figure missing any of PNG / SVG / PDF / samples / generating script; a
  `<figure>` holding `<svg>` or `<canvas>`; a figure on disk not in the F1–F6 sequence; a caption
  without `<b>Axes.</b>`; a block without "How it is computed"; any unsubstituted token;
- writes `<page-dir>/basic_behaviour.html` and a generated markdown mirror
  `<page-dir>/basic_behaviour.md` (each caption's Axes sentence + samples table; generated from the
  same source, so it cannot drift — §11a mirror).

#### `tests/analysis/test_basic_behaviour.py` (new, fast — no store reads)

- `test_registry_a01_legacy_names_and_order`: the a01 saved config yields exactly the legacy factor
  names in the legacy order.
- `test_registry_hv_campfire_is_own_factor`: the hv1ch saved config yields `n_campfire`, and `n_rocks`
  counts only rock slots.
- `test_audit_flags_unknown_draw`: the a01 config plus `body.random_start_hydration: true` → one
  unhandled row naming that path; plus `thermal.use_random_spots: true` → another; the hv1ch config →
  `thermal.default_temp` flagged.
- `test_prefit_duplicate_constant_outcome`: synthetic arrays where intensity == statistic, one column
  constant, and `eat_rate` with target `eating` → three exclusions with the stated reasons, nothing
  else.
- `test_screen_stage2_on_known_values`: 18 synthetic per-run values with known cell means and
  within-cell SD → cell means, `s`, the contrasts' t (df 12), the variance shares (summing to 1, and
  a pure world effect giving the world share ≈ 1), and exactly 1,680 permutations per agent.
- `test_screen_uses_seed_variation`: synthetic runs whose slopes are +1 for two seeds and −1 for the
  third in every cell → the run-level SE of each cell mean is far larger than the "conditional on
  these runs" SE, and no contrast is reported as different from zero.
- `test_control_smell_reading`: on the hv2ch saved config, the control-world smell regressor is
  channel 1 × 2.22 nats per unit with channel 2 as a covariate; on hv1ch and hv1chm it is
  `scent_spec.llr`.
- `test_build_partial_and_broken`: in a tmp page dir, F1 present → build exits 0 and reports F2–F6
  pending; F1 present without its samples file → build fails naming F1.

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`

Rows for every new file above (caller, HAND/TEST, purpose), the folder's depth note, and the new
importer edges onto `hiding_drivers.py`, `core/env.py`, `studies/hypervigilance/readings.py`,
`make_population.py` and `src/environment/config_loader.py`. Required by the map's Maintenance
Contract, same commit as the scripts.

#### `docs/develop/active/issues/KNOWN_BUGS.md` — via `bug-curator`, not edited directly

In the implementation commit, `bug-curator` records on the row "The hiding-drivers cross-tabs bin
injury from the same step as the bush outcome": decision **freeze** (`hiding_drivers.py` stays as
published; reference for two gates), and the new consumer `scripts/analysis/basic_behaviour/`, which
bins on row `t−1`.

#### Not changed

`scripts/analysis/hiding_drivers.py`, `core/env.py`, `core/golden.py`, the hypervigilance tooling,
the trajectory store schema, every config, everything under `src/`. No config keys are added (all
thresholds are pre-registered module constants; all world facts come from the saved config).
**Hard constraint:** no edit — not even exporting a constant — to any file the hypervigilance golden
stamps hash: `core/env.py`, `core/scan.py`, `core/store.py`, `hiding_drivers.py`,
`studies/sensor_ladder/collect_arm_data.py`, `ladder/_ladder.py`, `rabbit_avoidance.py`,
`aimed_response.py`, `studies/hypervigilance/readings.py`, `studies/hypervigilance/make_population.py`
(`readings.py:66-72`). An edit there blocks every hv reading until `golden_check.py` is re-run, and
this pipeline's own stamp too. Anything needed from them is imported as it stands.

### Step sequence — one figure per step, stop after each

| Step | Work | What the user reviews | Then |
|---|---|---|---|
| **S0** | registry, sweep, fit, screen, both golden gates, `_fig.py`, template, builder, tests, dependency map; gate passes; sweep every **completed** cell of the hvsmell population | golden stamp + a one-cell-per-world summary of `inventory.json` in the Implementation Report | stop |
| **S1** | `f1_behaviours_survival.py`; build page (partial) | F1 — behaviours + survival per run | stop for questions |
| **S2** | `f2_factor_inventory.py`; rebuild | F2 — factor inventory | stop |
| **S3** | `fit.py --kind univariate` for the target(s) the user names (default `bush_dwell`); `f3_univariate.py`; rebuild | F3 — per-run univariate | stop |
| **S4** | `fit.py --kind multivariate`; `f4_multivariate.py`; rebuild | F4 — per-run multivariate | stop |
| **S5** | (all 18 runs swept) `screen.py`; `f5_settings.py`; rebuild | F5 — which settings move each behaviour (exploratory screening) | stop |
| **S6** | `f6_crosstabs.py`; rebuild; `publish-page` skill (it sequences `artifact-format-reviewer`) | F6 — cross-tables + the full page | done |

Cells collected later are added with `sweep.py --cells <labels>`; figures re-run in seconds. The
developer never calls `Artifact` directly — every publish goes through `publish-page`.

---

## Checkpoints

**S0 — infrastructure and gate**
- [ ] S0.1 `pytest tests/analysis/test_basic_behaviour.py` passes locally (pytest is absent on lab nodes).
- [ ] S0.2 Slot cross-check passes on a01 and one store of each hv world; a deliberately wrong slot map fails it.
- [ ] S0.3 `obs_indices` on an hv1ch store: the body-temperature index differs from its alphabetical
  position in the manifest (the trap is real), and **every** `t = 0` value read there lies in
  [−10, 5] with non-zero variance. A wrong index (satiation = 100, nociception = 0) fails this.
- [ ] S0.4 Warm-square reconstruction, by an **independent path**: for 20 episodes of one hv1ch store,
  rebuild the episode's `thermal_field` with the environment's own reset (episode seed → key, params
  from the saved config, as `traj_scan.py` does) and assert that the field at the agent's square equals
  the `obs_true` reconstruction at every step to 1e-4. This is what proves which thermoception cell is
  the agent's own.
- [ ] S0.5 Audit on the 18-run population configs and on a01: list every unhandled marker in the
  Implementation Report. Expected: none on either; anything else → stop and report (a feature the
  plan missed).
- [ ] S0.5b `ambient_temp`: on the 20 episodes of S0.4, equal to the replayed episode's baseline draw
  to 1e-4 wherever defined; report the share of episodes where it is defined.
- [ ] S0.6 Gate 1: both a01 CSVs byte-identical; reference sha256s verified first.
- [ ] S0.6b Gate 2 (hv1ch): every check of A5's second table passes.
- [ ] S0.7 Golden gate: a01 `prefit.json` lists zero exclusions (otherwise stop and report; do not tune).
- [ ] S0.8 On an hv1ch cell, `pred_olf_intensity` and `rab_olf_intensity` are excluded as
  "identical to …_smell_predatorness"; on an hv2ch cell they are included.
- [ ] S0.9 Speed: sweep wall-clock on a01 vs the legacy 346.7 s (same container), and on one hv store
  with and without the `obs_true` read. > 1.5× on a01 is a discussion point.
- [ ] S0.10 `bush_dwell` pooled share on a01 equals the reference `summary.json` `overall_dwell`.

**S1–S4, S6 — per figure**
- [ ] Each figure script runs from caches only (no parquet reads) in under a minute.
- [ ] Each writes SVG + PDF + PNG + `<stem>.samples.json`; `house.save` raised no floor / edge error.
- [ ] `build_page.py` reports the expected present / pending split and exits 0.
- [ ] F1: survival is defined as the episode-table `length` (not reconstructed from step counts); for
  one cell it equals the mean of `length` read directly from that store's episode shards.
- [ ] F6: for one cell, the trial total of the injury × nutrition table equals that cell's total chosen
  steps; one cell value recomputed by a direct pandas read of one shard matches.

**S5 — cross-run screening**
- [ ] S5.1 Stage 2 reproduces a hand computation for one quantity (cell means, `s`, one contrast's t)
  done with pandas `groupby` in the Implementation Report.
- [ ] S5.2 Residual df = 12 for every stage-2 regression; permutation count = 1,680 per agent.
- [ ] S5.3 For the level and each slope, the median per-run episode-level SE is reported next to the
  seed-to-seed SD; if the SE is not clearly smaller (< ½ of `s`), stage 1 noise is not negligible —
  report it and say so on the page.
- [ ] S5.4 Per cell: the cell mean lies within the range of that cell's 3 per-run values (true by
  construction for a mean — a failure means a bookkeeping error), and each contrast equals the
  difference of its two cell means.
- [ ] S5.5 The smell regressor per world matches B5 (control: channel 1 at 2.22 nats per unit, channel
  2 as covariate; treated: `spec.llr`), checked on one run of each world.
- [ ] S5.6 No p-value or pass/fail appears for any smell term on F5 or in `contrasts.csv` for an hv
  population.

---

## Open questions (defaults chosen so implementation is not blocked)

- **Q1 Warm-square band.** Default: a square is warm when a body resting there would settle between
  the comfort setpoint and the survivable maximum (B1). Alternative: a fixed temperature.
- **Q2 Thresholds.** `MIN_EPISODES = 1000`, collinearity `|r| ≥ 0.999`.
- **Q3 Within-run model subset (B5).** Default: episodes with exactly one rabbit, any number of
  predators (`n_predators` as a covariate). Alternative: exactly one rabbit and no predator — the cleanest
  "false alarm" reading, at a third of the data.
- **Q4 `obs_true` cost.** Body temperature and the warm-square target need the 58-wide `obs_true`
  column on thermal worlds. If S0.9 shows it more than doubles the hv sweep, the user decides.
- **Q5 Cross-tab convention.** F6 conditions on row `t−1`, so its injury / nutrition tables will not
  equal the a01 page's (row `t`). Default: `t−1`.

---

## Revision log

- **2026-10-01, initial draft + user decisions (before first commit).** Targets fixed to bush hiding,
  eating, near rabbit, near predator, warm square (resting dropped; the campfire-distance proxy of the
  first draft replaced by the warm-square definition recovered from `obs_true`). Method kept as in
  a01. Added the pooled model with run-level factors and interactions, cluster-robust-by-run SEs and
  the two-stage seed check (A7, B5, `pooled.py`, F5). Figure sequence changed to F1 behaviours +
  survival, F2 inventory, F3 per-run univariate, F4 per-run multivariate, F5 pooled, F6 cross-tables
  (the first draft's separate cross-world comparison figure is absorbed into F1 and F5). Method notes
  written for the user reading figure by figure.
- **2026-10-01, Revision 1 — after `plan-reviewer` NOT READY for S5 (commit `954b7bd6`) and the
  user's clarification that the cross-run analysis is for screening and ranking settings, not a
  verdict.** C1/C2/M1–M3: the pooled episode-level GLM, its cluster-robust SEs and the seed main
  effect are removed; F5 is now "Which settings move each behaviour", a two-stage analysis with world
  and agent as fixed effects and the run as replicate — per-run logit coefficients on a common scale,
  stage-2 cell-means OLS with exact df 12, exact within-agent permutation, standardised effects and
  variance components (seed within agent = shared starting weights); episode-level SEs only as a
  "conditional on these runs" column (A7, B5, `screen.py`, F5, S5). Smell terms per agent, on the
  study's registered control reading, no tests, labelled as screening. M4: second differential gate
  on an hv1ch store and target cross-identities (A5, `golden_gate.py`). M5: population precondition
  and fixed golden command (A4). M6: freeze decision recorded via `bug-curator`; `t` contiguity
  assertion. L1 line numbers refreshed; L2 references copied; L3 warm band capped at the survivable
  maximum and the ambient draw recovered (`ambient_temp`); L4 survival = `length`. Hard constraint on
  golden-stamped files added. Terminology: "yardstick" replaced by plain wording (project policy,
  commit `d94250b6`).

---

## Implementation Report

> **Implemented by**:
> **Date**:

<!-- Filled by the developer: per step S0–S6, what was done, deviations, checkpoint results
     (with numbers), the unhandled-marker list (S0.5), and the timings (S0.9, S5.1). -->

## Verification Report

> **Verified by**:
> **Date**:

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**:

---

## Feedback from plan-reviewer

> **Reviewed by**: plan-reviewer · 2026-10-01 · against commit `d9ea3bf0` · full report: [[plan_basic_behaviour_pipeline]] (`docs/reviews/plan_basic_behaviour_pipeline.md`)

**Verdict: NOT READY for S5 (the pooled model). S0–S4 are sound once M5 and M4 are addressed.**
The per-run machinery is a faithful generalisation of the hiding page, and the golden gate is real
ground truth: a frozen-commit script output whose sha256 is checked before comparison, so it is not
circular. The pooled model is where things go wrong. Its smell × injury × world term re-tests the
smell study's registered hypervigilance question. It uses a control-world smell reading the study
itself rejected. It pools the two agents. And it attaches p-values outside the study's decision
rule. Separately, the hypervigilance slope's "primary" uncertainty is episode-level.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|
| 🔴 C1 | B5 terms; F5(b); [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] §5.2 S1 (Revision 4), §5.3, §2.1 | `rab_smell_llr:start_injury:world` is a second, unregistered test of the study's Q2 / S1 on the same runs. It uses the plain `x1 − x2` log-likelihood ratio (LLR) in the control world, which carries identity only. The study's Revision 4 rejected that reference because in both treated worlds the scent statistic *is* odour strength. The term also has no `:agent` (the study analyses agents separately), and it is judged by a cluster t on 17 degrees of freedom (df) rather than the study's §5.3 rule. | On hv populations, either (a) fit the smell terms per agent, using the study's matched-control reading in the control world (channel 1, with channel 2 as a covariate), and label F5 "descriptive — verdict lives in study §5.3"; or (b) show per-run slopes and per-cell means only, with no world-contrast p-values for smell terms. State the relation to S1 / §5.3 in B5. | senior-developer (+ experiment-designer as study owner) |
| 🔴 C2 | A7 last paragraph; B5 `primary_se` rule | `primary_se = episode` for within-run slopes covers the hypervigilance term `rab_smell_llr:start_injury` and the injury / nutrition slopes. A Pearson-scaled SE on about 6 M episodes calls a small average significant even when the 18 seeds split in sign, which is the case your own unit test builds. Under treatment coding plus `x:world` and `x:agent`, that "main" slope is also the slope of the reference cell only (control world × ordinary agent). | Run-level SE becomes primary for every term the page interprets as a property of an agent type or world. Episode SE stays as a secondary column labelled "conditional on these runs". Re-confirm user decision 3 with this in view. | senior-developer |
| 🟡 M1 | A7 guard 1; B5 `coef.csv` | CR1 (the ordinary cluster-robust sandwich with a small-sample correction) on a t with G − 1 = 17 df is optimistic here. There are 8 run-level parameters (intercept, world ×2, agent, world:agent ×2, seed ×2) on 18 runs, 3 per cell. High-leverage clusters shrink the residuals CR1 is built from, and the effective df for a cell contrast is about 10 or fewer, not 17. A wild cluster bootstrap is **not** a good substitute with only 3 clusters per cell (few-treated-clusters failure, MacKinnon & Webb 2017). `seed` as a main effect is mis-specified. Starting weights are shared only within seed × agent (study §2.4), and the study's rule is unpaired. The two-stage OLS omits seed, so the two guards fit different models. | Make the **two-stage seed-level regression primary** for every world or agent term and every generalised slope. Its df (12) is exact, and per-run slope SEs are negligible beside between-seed spread. Fit it on **logit-scale** per-run coefficients, on a common scale (nats, raw injury units), not on per-run SDs. If a sandwich is still wanted, use CR2 with Bell–McCaffrey df (Imbens & Kolesár 2016; Pustejovsky & Tipton 2018). Cheapest assumption-free addition: an exact run-level permutation of world labels within agent (9 runs per agent → 1,680 relabelings). Drop `seed`, or model it as seed × agent consistently in both guards. | senior-developer |
| 🟡 M2 | B5 terms; F5(b); S5.4 | The model has `x:world + x:agent` but no `x:world:agent`, so the "per world × agent" slopes in F5(b) are imposed additive, not estimated. The two-stage OLS includes world:agent while the pooled model does not. S5.4 checks a reference-cell slope against all 18 per-run slopes, which does not test what it says. | Fit per agent, which also matches the study (C1), or include the full 3-way interactions. Derive F5(b) slopes as per-cell linear combinations with their own SE. Rewrite S5.4 per cell (pooled cell slope within that cell's 3 per-run slopes). | senior-developer |
| 🟡 M3 | B5 "Coding"; F5(b) "pp per nat" vs `coef.csv` "pp per SD" | Answering the focus question: as specified, "pp per SD" does **not** stay interpretable across worlds. (i) One pooled-rate p̄(1 − p̄) conversion is applied to worlds and agents whose base rates differ. (ii) An interaction coefficient converted to pp is not a marginal effect in a logit model (Ai & Norton 2003). (iii) The claim that a main effect is "the effect at the average of the other factors" is false under treatment coding with interactions: it is the reference-cell effect. (iv) Standardisation is *pooled*, not per-world. For start injury and nutrition this is harmless (identical draws in every world), but for the smell LLR one pooled SD is a different share of each world's spread (rabbit-LLR SD ≈ 0.94 nats in the control vs ≈ 0.66 in the treated worlds, from d′ in study §2.2). The logit slope **per nat** is the comparable quantity. | Report terms on the logit scale (or as odds ratios), smell per nat everywhere, and pp only as average marginal effects per world × agent cell at that cell's own rate. Use sum-to-zero coding if the "average" reading is wanted. | senior-developer |
| 🟡 M4 | A5; S0 checkpoints | The byte-identity gate exercises only the unchanged path: a01, `bush_dwell`, difference layout, zero exclusions. It never runs the per-name resource split (the legacy code splits by `damage > 0`, the plan by name), the single / sum layouts, the four new targets, or the exclusion path. S0.2 / S0.8 / S0.10 cover pieces only. | Add a **differential gate on one hv1ch store**. The frozen `hiding_drivers.py` accepts the single layout, so run it and require byte equality of every per-episode array and univariate row not involving the rock / campfire split. Also add cross-identities: `eating` successes == legacy `n_ate`; `near_predator` == `n_pred_near`; `near_rabbit` minus rabbit-and-predator-near steps == `n_rab_near`. | senior-developer → developer |
| 🟡 M5 | A4 precondition; `golden_a01.py` | Checked against `make_population.py:153-187` and the Launch Manifest today: `--from-study-doc` **hard-fails** on C02 (status `completed`, no store in `results/trajectories_hvsmell/`), and on any H-row still `running` that has a final checkpoint and a store. "S0–S4 can run on the completed subset" is therefore not reachable until the hv session edits the manifest. Separately, `golden_a01.py`'s command omits the required `--population`, and the a01 tag carries no `t1none` / `t16quad`, so `--agent` is required too. | State the C02 condition explicitly. Name the fallback: either `--runs` per world with `--world`, or wait. Fix the golden command. | senior-developer |
| 🟡 M6 | A6; B6 | The Known Bugs row "cross-tabs bin injury from the same step" is OPEN, with the **freeze-vs-fix decision handed to senior-developer**. This plan settles it as "freeze" without recording that. The `t−1` assertion checks `seed[i−1] == seed[i]` but not `t[i] == t[i−1] + 1`. | Ask `bug-curator` to record the freeze decision and the new consumer in the same change. Add the `t` contiguity assertion. | bug-curator; developer |
| 🟢 L1 | A1 table, A6 | Line citations into `hiding_drivers.py` are stale. Actual: `aggregate` 127–243, `quasi_binomial_fit` 247–269, `fit_glms` 272–332, intensity drop 287–291, ranking 312, same-row binning 223 (not 214, which the registry row also cites). | Refresh the citations. | senior-developer |
| 🟢 L2 | A5 | The reference CSVs live in the hv tooling's `_golden_scratch/g3_reference/`, which `golden_check.py --tier sweep` regenerates when `aggregate.npz` is absent. If it is regenerated at a different base commit, this gate hard-fails (loudly, not silently). | Copy the two CSVs, with their sha256s, into this pipeline's own tree at S0. | developer |
| 🟢 L3 | B1 `warm_cell`; A2 | (i) "Equilibrium ≥ setpoint" also counts lethally hot squares (equilibrium > `max_temperature` 15). (ii) The ambient draw (−31…−29) is recoverable, from S0.4's reset replay or from far-from-fire thermoception cells, rather than having to be "unhandled". Borderline squares near a campfire flip with it. | Q1: consider the band [setpoint, max_temperature]. Optionally recover ambient as a factor. | user / senior-developer |
| 🟢 L4 | F1 checkpoint | Survival must be the episode `length`. If F1 computes it from `n_steps`, the independent check can be off by one. | Define F1 survival as `length`. | developer |

**Points checked and found sound.** The warm-square reconstruction holds: `sensor.py:480` documents
`Thermoception[centre] + BodyTemperature == thermal_field[own cell]` under `relative: true`, and the
centre is the first of the 5 cells (`sensor.py:68-70`). The thermal field is set only at reset
(`core.py:2240`), so it is static per episode, and S0.4 is a genuinely independent path. The hv
saved config has `temperature_setpoint 0`, `k_metabolic 0`, `default_temp [-31, -29]`. The
alphabetical `observation_breakdown` trap is real (the hv1ch manifest lists `Body Temperature`
first; widths sum to 58). The a01 set of varying traits equals the legacy set (detection, delay,
range, stamina; `damage` is per hit). On local-only compute: correct given the node-env-drift row.
On `MIN_EPISODES = 1000`: harmless on 1 M stores, but it is a degeneracy floor, not a power
criterion. Do not describe it as one.

**Hypervigilance golden stamps.** The plan does not invalidate them, provided its "Not changed" list
holds. The hv stamps hash `SWEEP_SOURCES` (`core/env.py`, `core/scan.py`, `core/store.py`,
`hiding_drivers.py`, `collect_arm_data.py`, `_ladder.py`, `rabbit_avoidance.py`,
`aimed_response.py`) and `ASSEMBLY_SOURCES` (`readings.py`, `make_population.py`;
`readings.py:66-72`). Any convenience edit to one of those files during implementation, for example
exporting a constant from `hiding_drivers.py`, blocks every hv reading until `golden_check.py` is
re-run. It also blocks this pipeline's own `fit.py` stamp. Make that an explicit hard constraint in
"Not changed".

**Assumptions the conclusion rests on**

- ✅ Verified: a01 trait set = legacy; hv obstacle order `campfire, rock, tree, bush`; obs identity; static field; hv thermal constants; `obs_precision float32`; `seed_base 1,000,000` on the hv1ch store.
- ❓ Open: common evaluation draws across runs (same `seed_base`, study §5) mean episodes with the same seed are correlated *across* clusters. One-way clustering ignores this. It is probably conservative for contrasts and optimistic for levels, and is never checked.
- ❓ Open: C01 (and later C02) is equivalent to an hv2ch seed-42 run apart from launch week (study §2.4 validates the config, not the training trajectory). The seed-42 cell of the control world is the only one with different provenance, and the `seed` term partly absorbs it.
- ❓ Open: the local statsmodels honours `df_correction` for `GLM` with `cov_type="cluster"` and `use_t=True`. S5.2 checks this, which is good. Keep it as a hard failure.
- ❓ Open: the hv session will update the Launch Manifest statuses. Today all of H01–H16 read `running`.

**Cost of being wrong.** No training compute is at risk, and the infrastructure is a few local CPU
hours. The cost is an F5 figure that answers the project's central hypervigilance question with a
confounded reading and overconfident p-values, published beside, and possibly against, the study's
pre-registered verdict. That is how a wrong claim reaches a paper.

**What flips the verdict.** C1 and C2 resolved in B5 / A7 / F5 (doc edits only). M1–M3 belong in
the same edit, because they all live in B5. S0–S4 may proceed once M5 is resolved and M4's
differential gate is added.
