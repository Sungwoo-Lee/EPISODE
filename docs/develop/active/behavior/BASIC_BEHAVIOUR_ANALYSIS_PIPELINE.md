---
title: "Basic Behaviour Analysis: a reusable, figure-by-figure pipeline and page for any trained population"
topic: behavior
status: active
created: 2026-10-01
last_updated: 2026-10-01
---

# Basic Behaviour Analysis pipeline

> **Status**: PLANNED (awaiting `plan-reviewer`, then user approval). Includes the user's decisions of 2026-10-01 (targets, method, pooled model, audience) — see [Revision log](#revision-log).
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
fits one **pooled** model over all runs that asks whether the smell world and the agent type change
those effects — including whether a rabbit's smell triggers more hiding the more injured the agent
starts (the project's *hypervigilance* question) — with uncertainty computed at the level of whole
training runs, so a million episodes from one run cannot masquerade as a million independent
observations; and (6) must reproduce the hiding page's published regression tables byte for byte
before any new number is trusted. The page is built **one figure at a time** — six steps, each with
its own script, output, detailed plain-language method note, and a stop for the user's questions. The
first population is the 18 runs of the single-channel smell study.

---

## Analysis

### A1. What `hiding_drivers.py` does, and what of it is world-specific

`scripts/analysis/hiding_drivers.py` (414 lines) is the foundation. Its shape is right and is kept:

| Piece | Lines | Keep as-is? | World-specific part |
|---|---|---|---|
| `find_stores`, `shard_files`, `listcol` | 81–117 | **import** (do not copy) | none |
| `aggregate()` one sweep → per-episode arrays; asserts shard alignment, contiguous seeds, one reset row per episode | 121–250 | pattern kept; arithmetic primitives copied **exactly** (A5) | typed column list; outcome hard-wired to `agent_in_bush`; `slot_layout` splits obstacles only into bush / not-bush, so **campfires and trees are counted as rocks** (verified on the hv1ch saved config: obstacles `campfire, rock, tree, bush`) |
| `quasi_binomial_fit()` | 253–276 | **import** (do not copy) | none |
| `fit_glms()` — univariate per factor on the subset where it is defined; M1–M5 | 279–348 | generalised to a recipe table (B4) | the factor dicts `EXO`, `EXO_P`, `EXO_R`, `END` are typed; the intensity drop for single / sum smell layouts is a hand-written `if` (line 298) |
| `cross_tabs()` | 351–370 | replaced (B6) | marginal injury / nutrition bins only; same-row binning (open Known Bug, A6) |

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
| body temperature | inside `obs_true` at the `Body Temperature` index | yes, when observable |
| per-episode baseline world temperature (`thermal.default_temp`, hv: drawn from −31…−29) | not recorded | **no** → expected *unhandled* marker on every thermal world |
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
| baseline world temperature | — | random −31…−29, **not recorded** |
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
  `world`, `agent`, `seed` — exactly the run-level factors the pooled model needs.
- **First population: 18 runs** = the 16 hv runs (H01–H16) + the two level-05 body-interaction
  controls (C01, C02, mapped to world `hv2ch` seed 42 by `make_population.py`'s `CELL_WORLD`) of
  [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] §3: 3 smell worlds × 2 agents × 3 seeds. On 2026-10-01
  stores exist for the 8 ordinary-agent hv runs and C01 (`results/trajectories_hvsmell/`); the
  modulated-agent runs and C02 are not collected yet. **Precondition:** the study's Launch Manifest
  `Status` column must be updated by the session running that study — `make_population.py` refuses a
  `running` row whose run already has a final checkpoint and a store (stale-status guard). This
  pipeline never promotes a status. **The pooled model (S5) needs all 18 runs**; S0–S4 can run on the
  completed subset and be topped up.
- **Blinding.** The study pre-registered that no hv run is read before its seed-noise yardstick is
  frozen (study §5.3). This pipeline reads hv runs, so it calls `readings.require_yardstick_for(cells)`
  before sweeping. The yardstick exists today (`results/analysis/hypervigilance/cmp10m/yardstick.json`),
  so this is a guard, not a blocker.

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
   intensity appended last in the predator block, as at line 296). The registry carries a name map
   for known declarations (B2) and emits factors in a fixed role order.
4. Model labels on a01 equal the legacy strings exactly (B4).
5. Per-episode arithmetic uses the same primitives in the same order as `aggregate()`
   (`np.add.reduceat` over episode starts per shard, `np.bincount` with `minlength`, float64 casts of
   the same columns, `mean_over` for slot means). `core/golden.py`'s docstring records why
   float32-origin sums are order-insensitive on this data; the gate is what proves it.
6. **Pre-fit checks exclude nothing on a01.** If a check excludes an a01 factor the gate fails by
   construction — the intended signal that a threshold is too aggressive (Checkpoint S0.7).

Not in the gate: cross-tables (`summary.json`), whose binning convention this plan changes on purpose
(A6), and the pooled model, which has no legacy counterpart (its own checks are in S5). Runtime
reference: the legacy a01 sweep took 346.7 s on this container
(`_golden_sweep_pass.json` → `timings_seconds.g3_candidate`).

### A6. Two known hazards this plan must not inherit

- **Same-row binning** (Known Bugs, OPEN, "The hiding-drivers cross-tabs bin injury from the same step
  as the bush outcome"): `hiding_drivers.py:214` pairs the behaviour at row `t` with the injury at row
  `t`, although the action was chosen while the agent was in row `t−1`. `hiding_drivers.py` stays
  **frozen** (it is the golden reference and published pages cite it). The new cross-tables condition
  on **row `t−1`** — injury, nutrition, animal distances — and the page says so. Episode-level GLM
  inputs are episode summaries and are unaffected, which is why the gate can be byte-identical.
- **Lab-node env drift** (Known Bugs, OPEN): `statsmodels` is missing on the lab nodes. Every fit
  stage runs **locally** (`nice -n 19`), never via `run_command.py`; statsmodels / numpy versions
  move the last bits of a fit, so the gate and all population fits run in the same local env.

### A7. Why the pooled model needs run-level uncertainty (user decision 3)

The pooled data are ~18 million episodes but only **18 training runs**, and world and agent are
properties of a run, not of an episode. A standard GLM standard error treats every episode as an
independent observation, so it would report a world or agent difference as overwhelmingly certain
even if the three seeds of each cell disagreed — *pseudo-replication*. Two complementary run-level
guards, both reported:

1. **Cluster-robust standard errors by run** (sandwich estimator, `groups = run`, small-sample
   correction, *t* reference with `G − 1 = 17` degrees of freedom). With 18 clusters this is the
   minimum honest correction, and it is known to be somewhat optimistic with few clusters — which is
   why guard 2 exists.
2. **Seed-level (two-stage) check.** Fit the *within-run part* of the pooled model separately in each
   run, collect the 18 per-run coefficients of each slope, and regress them on world, agent and
   world × agent by ordinary least squares (n = 18; residual df 12). This is the classic
   summary-statistics test: it can only see run-to-run variation, so it cannot be inflated by episode
   counts. The page shows the 18 per-run slopes as dots next to every pooled estimate, so a pooled
   slope cannot hide runs that disagree.

Terms whose variation is **within** runs (e.g. the slope of start injury, averaged over runs) also
get the ordinary episode-level quasi-binomial SE (Pearson-scaled, as in a01), as the user allowed.
Every term's table row carries both SEs and names which one is primary: run-level (cluster) for any
term involving world or agent; episode-level for pure within-run slopes.

**Memory budget.** The pooled subset (episodes with exactly one rabbit, B5) is roughly a third of 18M
≈ 6M rows × ~40 columns; this container has 125 GB. Fit on all eligible episodes (no subsampling);
Checkpoint S5.1 records peak memory and time and stops if peak RSS exceeds 60 GB.

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
pooled.py     --target T ──► pooled/<T>/{coef.csv, per_run_within.csv, two_stage.csv, prefit.json}
                                        │
golden_a01.py sweep + fit on a01 into scratch; cmp vs g3_reference ──► _golden_a01_pass.json
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
| `warm_cell` | on a warm square | the temperature of the agent's own square (A2) is warm enough that a body resting there would settle **at or above the comfort setpoint**: `config_loader._thermal_equilibrium(T_square, k_exchange, k_loss, k_metabolic, temperature_setpoint) ≥ temperature_setpoint` — the environment's own equilibrium function, imported, not re-implemented. In the hv worlds (`k_metabolic = 0`) this is simply "square temperature ≥ 0 °", against a baseline of about −30 ° | `thermal.enabled`; thermoception and body temperature in the observation (or `relative: false`); `obs_precision == float32` |

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
| 7 | per predator-class declaration: each varying trait range in `TRAIT_COLUMNS` (`detection_range`→`animal_detect_sampled`, `attack_delay`, `attack_range`, `max_stamina`, `stamina_recovery_rate`→`animal_recovery_sampled`, `hunt_stamina_threshold`, `lose_interest_multiplier`, `move_interval`), mean over active slots; then smell statistic; then `spawn_dist_to_predator`; then smell intensity | `pred_detection_range`, `pred_attack_delay`, `pred_attack_range`, `pred_max_stamina`, `pred_smell_predatorness`, `spawn_dist_to_predator`, `pred_olf_intensity`; subset = exactly one predator |
| 8 | per neutral-class declaration: varying traits, then smell statistic, then intensity | `rab_smell_predatorness`, `rab_olf_intensity`; subset = exactly one rabbit |
| 9 | consequences (legacy `END`, same formulas) | `frac_time_injured`, `frac_time_inj_severe`, `mean_injury`, `peak_injury`, `frac_time_low_nutrition`, `mean_nutrition`, `total_damage_taken`, `eat_rate`, `rest_rate`, `episode_length`, `frac_time_predator_near`, `frac_time_rabbit_near` |
| 10 | consequences, thermal worlds only | `mean_body_temp` (when observable), `frac_time_warm_cell` |
| — | M5 helpers (not univariate) | `detect_keenest`, `detect_least_keen`, `detect_spread` (two-predator episodes) |

Smell statistic and intensity come from `core/env.scent_spec(cfg)` (`statistic`, `intensity`,
`llr`), so the three accepted smell layouts are handled and any other odour config is refused by that
function. In the single and sum layouts intensity is the same array as the statistic; the duplicate
check (B3) drops it with that reason — the generic replacement for the hand-written `if` at line 298.
`sweep.py` also stores the rabbit smell on the **common evidence scale** — the log-likelihood ratio in
nats, `spec.llr(statistic)` — as `rab_smell_llr` (used by the pooled model, B5; not a per-run
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
not stopped — a new feature is either picked up or **visibly** not. Expected on the hv worlds:
`thermal.default_temp` (not recorded). Must also catch, in tests: a body `random_start_hydration:
true` (no store column) and `thermal.use_random_spots: true` (positions not recorded).

**Slot cross-check.** The registry's slot indices (`core/env.slot_layout` plus a per-name split of
obstacles and resources) must agree with the manifest's per-slot `animal_classes` / `animal_tags`,
`obstacle_names`, `res_type`; any disagreement is a hard stop.

#### B3. Pre-fit checks (`fit.py`, `pooled.py`; per cell or pool, per target)

Applied in this order to each factor on its own subset, and again inside each multivariate design:

| Check | Rule | Reason string on F2 |
|---|---|---|
| too few episodes | finite on fewer than `MIN_EPISODES = 1000` episodes of its subset | "defined on N episodes (< 1000)" |
| never varies | one unique value on its subset | "constant (= v) in this run" |
| exact duplicate | `np.array_equal` with an earlier factor on the shared defined rows | "identical to <name>" |
| is the outcome | consequence whose formula is the target's indicator: `eat_rate` for `eating`; `frac_time_predator_near` for `near_predator`; `frac_time_rabbit_near` for `near_rabbit` (a sub-count of the outcome); `frac_time_warm_cell` for `warm_cell` | "is (part of) the outcome being modelled" |
| collinear (multivariate / pooled only) | design rank < columns, or `|r| ≥ 0.999` with an earlier column | "collinear with <name> (r = …)" |

A model whose subset has fewer than `MIN_EPISODES` episodes is skipped with a reason. Every exclusion
goes to `prefit.json`; nothing is excluded silently. Thresholds are pre-registered module constants
(Open question Q2).

#### B4. Per-run models (`fit.py`) — unchanged from a01

Univariate: one quasi-binomial GLM per included factor on its subset; ranked by `|dpp_per_sd|` (legacy
line 290). Multivariate: a recipe table, written as data, evaluated in this order:

| Id | Recipe (generic) | Subset | a01 label (must match byte-for-byte) |
|---|---|---|---|
| M1 | all `episode`-role exogenous factors | all episodes | `M1 exogenous, all episodes` |
| M2 | M1 set minus the count of the first predator class C1, plus C1's class-trait factors | exactly one C1 | `M2 exogenous + predator traits, 1-predator episodes` |
| M3 | M2 set minus the count of the first neutral class C2, plus C2's class-trait factors | exactly one C1 and one C2 | `M3 + rabbit smell, 1 predator + 1 rabbit` |
| M5 | M1 set minus the C1 count, plus `detect_keenest`, `detect_least_keen`, `detect_spread`, and the C1 means of `attack_delay` and `max_stamina` — a **fixed recipe carried over from a01**, skipped with a reason where two-C1 episodes < `MIN_EPISODES` or C1 lacks those traits | exactly two C1 | `M5 two-predator episodes, keenest vs least-keen` |
| M4 | all exogenous `episode`-role factors plus all consequences | all episodes | `M4 exogenous + consequences` |

Labels are templates over the class display names (`predator`, `rabbit`) and the word `smell` when
every C2 trait is a smell trait, else `traits`. Output order M1, M2, M3, M5, M4 is the legacy order.

#### B5. Pooled model over all runs (`pooled.py`) — user decision 3

**Subset.** Episodes with exactly one rabbit (rabbit smell is defined only there), from every
completed run in the population; refuses to run unless every cell of the population manifest is
completed (a partial pool would change the meaning of world and agent effects silently).

**Coding.** World and agent are categorical with reference levels the control world (`hv2ch`, today's
two-odour world) and the ordinary agent (`t1none`); seed is categorical (reference 42). Each
continuous factor is centred at its pooled mean and scaled by its pooled SD, so a main effect is the
effect at the average of the other factors and coefficients convert to pp per +1 SD as in a01.

**Terms** (logit of the target share):

- run level: `world + agent + world:agent + seed`;
- key exogenous factors, each with its world and agent interactions:
  `x + x:world + x:agent` for `x ∈ {start_injury, start_nutrition, rab_smell_llr}`;
- the hypervigilance terms: `rab_smell_llr:start_injury` and `rab_smell_llr:start_injury:world`
  (all lower-order terms are already present);
- covariates: every other `episode`-role exogenous factor that is included (B3) in **every** run,
  main effects only (e.g. `n_predators`, `n_bushes`, `n_food`, `spawn_dist_to_bush`).

**Fits and outputs** (`results/analysis/basic_behaviour/<population>/pooled/<target>/`):

- `coef.csv`: one row per term — coefficient, pp per SD, **cluster-robust SE by run**
  (statsmodels `GLM(...).fit(cov_type="cluster", cov_kwds={"groups": run_id, "use_correction": True,
  "df_correction": True}, use_t=True)`), its t and p with 17 df, **episode-level quasi-binomial SE**
  (Pearson-scaled, same point estimates), and a `primary_se` column (`cluster` for any term
  involving world or agent; `episode` otherwise);
- `per_run_within.csv`: in each run, the within-run part of the model
  (`start_injury + start_nutrition + rab_smell_llr + rab_smell_llr:start_injury + covariates`) — the
  18 per-run slopes shown beside the pooled estimates;
- `two_stage.csv`: for each per-run slope, OLS of the 18 values on `world + agent + world:agent`
  (n = 18, residual df 12) — the seed-level check (A7);
- `prefit.json`: exclusions, subset sizes per run, peak memory, seconds.

#### B6. Cross-tables (`sweep.py` accumulates; `f6` reads)

All conditioned on **row `t−1`** (A6), for each available target:
- injury band × nutrition band (legacy edges `INJ_EDGES`, `NUT_EDGES`, imported): 4 × 4 successes
  and trials;
- rabbit near / far × predator near / far (Chebyshev 2): 2 × 2;
- rabbit-smell ladder: from `episodes.npz` — episodes with exactly one rabbit and no predator, in
  sextiles of `rab_smell_llr` (nats), so the three smell worlds share one axis.

The `t−1` row is the previous row in the shard; assert `seed[i−1] == seed[i]` for every `t ≥ 1` row.

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
`readings.require_yardstick_for`. Per cell, serially: one pass over the step shards reading only the
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
Refuses to run unless `_golden_a01_pass.json` exists and its recorded source hashes equal the current
`registry.py`, `sweep.py`, `fit.py`, `core/env.py`, `hiding_drivers.py`.

#### `scripts/analysis/basic_behaviour/pooled.py` (new)

`--population … --out-root … --target <id>`. B5. Same golden-stamp requirement as `fit.py`. Builds
the design with plain numpy / pandas column construction (no formula strings, so term names are
explicit and testable), runs B3 on the pooled design, fits once, computes both SE types from the same
point estimates, then the per-run within models and the two-stage OLS.

#### `scripts/analysis/basic_behaviour/golden_a01.py` (new)

Builds a one-cell a01 population (`make_population.py --runs <a01 run> --world a01 --store-root
results/trajectories --out <scratch>/population.json`), runs `sweep.py` and both `fit.py` kinds for
`bush_dwell` into `results/analysis/basic_behaviour/_golden_scratch/<sources-hash12>/`, verifies the
reference sha256s (A5), then `cmp -s` on both CSVs; also asserts `prefit.json` lists **zero**
exclusions and `inventory.json` **zero** unhandled markers for a01. Pass → writes
`results/analysis/basic_behaviour/_golden_a01_pass.json` (source sha256s, reference sha256s, HEAD,
sweep seconds). Fail → no stamp, non-zero exit, first 40 lines of each `diff` printed.

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
| `f5_pooled.py --target T` | `f5_pooled__<T>` | (a) run-level terms (world, agent, world × agent) with cluster-robust 95 % intervals; (b) each key slope (start injury, start nutrition, rabbit smell in pp per nat, smell × injury) per world × agent: pooled estimate with its primary interval, and the 18 per-run slopes as dots beside it; (c) the two-stage table's p-values printed in the panel titles |
| `f6_crosstabs.py --target T` | `f6_crosstabs__<T>` | (a) injury band × nutrition band share per world × agent (trial-weighted over seeds; seed range in the cell label); (b) rabbit-smell ladder in nats, one line per run; (c) near / far rabbit × near / far predator share per run |

#### `scripts/analysis/basic_behaviour/page_template.html` (new) and `build_page.py` (new)

The template holds six figure blocks F1–F6 in order. Audience is the user, reading figure by figure
(user decision 4), so each block carries: the §11a `<b>Axes.</b>` sentence; a §11c "How it is
computed" note of 150–250 words in plain language, glossing every statistical term where it first
appears (quasi-binomial, overdispersion, "per SD", cluster-robust, pseudo-replication, two-stage
check); and a short "What this figure cannot tell you". Numbers come from tokens the builder fills
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
- `test_pooled_cluster_se_detects_disagreeing_runs`: synthetic 6 runs × 2,000 episodes in which a
  slope is +1 in three runs and −1 in three (same world): the cluster-robust SE of that slope is at
  least 5× the episode-level SE; with identical slopes in all runs the two are within 2× of each other.
- `test_build_partial_and_broken`: in a tmp page dir, F1 present → build exits 0 and reports F2–F6
  pending; F1 present without its samples file → build fails naming F1.

#### `docs/environment/SCRIPTS_DEPENDENCY_MAP.md`

Rows for every new file above (caller, HAND/TEST, purpose), the folder's depth note, and the new
importer edges onto `hiding_drivers.py`, `core/env.py`, `studies/hypervigilance/readings.py`,
`make_population.py` and `src/environment/config_loader.py`. Required by the map's Maintenance
Contract, same commit as the scripts.

#### Not changed

`scripts/analysis/hiding_drivers.py`, `core/env.py`, `core/golden.py`, the hypervigilance tooling,
the trajectory store schema, every config, everything under `src/`. No config keys are added (all
thresholds are pre-registered module constants; all world facts come from the saved config).

### Step sequence — one figure per step, stop after each

| Step | Work | What the user reviews | Then |
|---|---|---|---|
| **S0** | registry, sweep, fit, pooled, golden gate, `_fig.py`, template, builder, tests, dependency map; gate passes; sweep every **completed** cell of the hvsmell population | golden stamp + a one-cell-per-world summary of `inventory.json` in the Implementation Report | stop |
| **S1** | `f1_behaviours_survival.py`; build page (partial) | F1 — behaviours + survival per run | stop for questions |
| **S2** | `f2_factor_inventory.py`; rebuild | F2 — factor inventory | stop |
| **S3** | `fit.py --kind univariate` for the target(s) the user names (default `bush_dwell`); `f3_univariate.py`; rebuild | F3 — per-run univariate | stop |
| **S4** | `fit.py --kind multivariate`; `f4_multivariate.py`; rebuild | F4 — per-run multivariate | stop |
| **S5** | (all 18 runs swept) `pooled.py`; `f5_pooled.py`; rebuild | F5 — pooled model with run factors + interactions, per-run slopes alongside | stop |
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
  Implementation Report. Expected: none on a01; `thermal.default_temp` on hv worlds; anything else →
  stop and report (a feature the plan missed).
- [ ] S0.6 Golden gate: both CSVs byte-identical; reference sha256s verified first.
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
- [ ] F1: survival for one cell equals the mean of `length` read directly from that store's episode
  shards (independent of `episodes.npz`).
- [ ] F6: for one cell, the trial total of the injury × nutrition table equals that cell's total chosen
  steps; one cell value recomputed by a direct pandas read of one shard matches.

**S5 — pooled model**
- [ ] S5.1 Peak RSS and wall-clock recorded; stop if peak RSS > 60 GB.
- [ ] S5.2 Number of clusters reported by the fit = number of runs (18); df used for t = 17.
- [ ] S5.3 For each run-level term, the cluster SE is ≥ the episode-level SE (if not, report — it
  means the run-level variation is smaller than the binomial noise, which needs a sentence on the page).
- [ ] S5.4 Each pooled key slope lies within the range of its 18 per-run slopes; the two-stage
  estimate of each world / agent difference in slopes has the same sign as the pooled interaction, or
  the disagreement is shown on F5 and reported.
- [ ] S5.5 `rab_smell_llr` for one run equals `spec.llr(rab_smell_predatorness)` for that run's own
  `scent_spec` (common-scale check, all three layouts).

---

## Open questions (defaults chosen so implementation is not blocked)

- **Q1 Warm-square threshold.** Default: a square is warm when a body resting there would settle at or
  above the comfort setpoint (A2, B1). Alternative: a fixed temperature, or "warmer than the
  episode's baseline". Default as stated.
- **Q2 Thresholds.** `MIN_EPISODES = 1000`, collinearity `|r| ≥ 0.999`.
- **Q3 Pooled subset.** Default: episodes with exactly one rabbit, any number of predators
  (`n_predators` as a covariate). Alternative: exactly one rabbit and no predator — the cleanest
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
