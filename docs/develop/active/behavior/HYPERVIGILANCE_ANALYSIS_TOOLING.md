---
title: "Hypervigilance analysis tooling: smell readings for any odour layout, the scent × injury reading, and the pre-registered verdict rule"
topic: behavior
status: active
created: 2026-10-01
last_updated: 2026-10-01
---

# Hypervigilance analysis tooling

> **Status**: IMPLEMENTING, **Revision 2 (2026-10-01)** — Revision 1 after `plan-reviewer` NOT READY, re-check SOUND WITH CONCERNS (`8646c0ce`); Revision 2 folds the re-check's N1–N4 in ([Revision 2 amendments](#revision-2-amendments-n1n4)). See [Revision log](#revision-log).
> **Opened**: 2026-10-01
> **Study text this plan is checked against:** study Revision 4 (commit `39420f2c`), which contains Revisions 2 (`7ec62720`) and 3 (`86ce3119`).
> **Author**: senior-developer
> **Related**: [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] (the study this serves; its §5.6 lists the tooling it needs, and both plan-reviewer passes at its end carry the findings N3/N4 and M3 this plan implements) · [[a01_hiding_drivers]] ("What makes this agent hide?", whose scent readings are re-done here) · the modulator-clues page `docs/experiments/active/modulator_clues/modulator_clues.html` ("Injury, Behaviour and the Modulator", whose Figure A3 hypervigilance reading is re-done here) · [[TRAJECTORY_COLLECTION_PIPELINE]] (where the stores come from) · `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (updated by this change)
> **Back-link:** study §5.6 and header link here (added in study Revision 3). Review: [[plan_hypervigilance_analysis_tooling]].

---

## Context

**What this is for.** The project is testing whether an agent that finds it harder to tell a
harmless rabbit from a hunting predator by smell ends up treating the rabbit as a threat, and
whether that gets worse the more injured it is (the project's definition of *hypervigilance*). Sixteen
training runs are under way in three smell worlds: today's world, where the two animals give off
opposite mixes of two odours; a *single-channel* world, where only one odour is left and the animals
differ only in how strongly they smell; and a *matched-strength* world, where both animals give off
the same 50/50 odour mix and again differ only in strength. After training, each run is replayed for
a million episodes and every step is recorded.

**Why new tooling is needed.** Every existing analysis script decides "how predator-like does this
animal smell?" by looking for one odour on which predators are stronger and a second on which rabbits
are stronger, and takes the difference. Neither new world has that second odour, so the scripts stop
with an error on both. The study also pre-registered several readings no script computes yet: whether
the rabbit-scent false alarm grows with the wound the agent was given at the start (the *scent × injury*
reading), a reusable version of the "is the extra hiding aimed at the rabbit?" split, two sensitivity
checks on the main measure, and a two-stage decision rule over three and then five training seeds.

**What this plan delivers.** (1) One shared definition of "predator-likeness" that works for all three
worlds and refuses any other; (2) those new readings; (3) one results file per run with every count
used, working on any run including future ones; (4) a verdict script that applies the study's rule and
refuses to run if its thresholds disagree with the study document; and (5) a gate that re-computes
already-published numbers on today's world and must match them *before* any new result is looked at.
The same readings also run on the older stores (curriculum levels 03–06, including level 06, where smell
becomes noisier the more injured the agent is), so one combined hypervigilance page can be built from
them. Building that page is **not** part of this plan.

---

## Analysis

### A1. Where the smell statistic lives today (three copies)

| Copy | Lines | Callers | Behaviour on the new worlds |
|---|---|---|---|
| `scripts/analysis/core/env.py::smell_channels` | 73–82 | `studies/sensor_ladder/collect_arm_data.py:61`, `studies/sensor_ladder/collect_hiding_drivers.py:154` | `SystemExit` on both (argmin lands on a zero column in single-channel; both differences positive in matched) |
| `scripts/analysis/hiding_drivers.py::smell_channels` | 81–97 | its own `main()` at 368 | same |
| `scripts/analysis/figures/_common.py::smell_channels` | 57–67 | **none** (grep of `scripts/analysis/figures/`: definition only) | same |

`core/env.py:1-20` records that the three copies were proven behaviourally equal when they were
consolidated; the merge left the two outer copies in place. How the statistic is used:

- `hiding_drivers.aggregate()` lines 176–185: `pred_/rab_predatorness = ch_a − ch_b`, `*_olf_ch1/ch2`,
  `*_olf_intensity = ch_a + ch_b`. `fit_glms()` (258–328) puts predatorness **and** intensity side by
  side in models M2/M3 (lines 269–273, 312–315).
- `collect_arm_data.build()` lines 74–75: only the **intensity** (`ch1 + ch2`), for the odour-quartile
  grids. P1/P2/S4/S5 (the proximity grids, lines 118–133) do not use smell at all.
- `rabbit_avoidance.py` (P2d, S5): no smell use; runs unchanged on all worlds (confirmed by the
  study's §5.6 item 1 and by reading lines 43–98).

**Consequence for the treated worlds.** Once the ratio of the two odours says nothing about identity,
predator-likeness *is* strength: in the single-channel world statistic = `x1` = intensity; in the
matched world statistic = `x1 + x2` = intensity. Models M2/M3 would then carry two identical columns
and the GLM is singular. The intensity terms must be dropped in those two layouts (study §2.5 item 2
names this: "strength carries class in both treated worlds").

### A2. One statistic per layout, and the evidence scale (from study §2.2)

For animals with Gaussian recipes of equal spread, the log-likelihood ratio "predator vs rabbit" of one
animal's recipe is linear in a per-layout statistic `s = w·x`:

$$
\mathrm{LLR}(s) = \frac{\mu_p - \mu_r}{\sigma_s^2}\left(s - \frac{\mu_p + \mu_r}{2}\right),\qquad \mu = w\cdot m,\quad \sigma_s^2 = \sum_c w_c^2\,\sigma_c^2
$$

| Layout (world) | Statistic `s` | midpoint | nats per unit `k` | Study §2.2 |
|---|---|---|---|---|
| `difference` (control, today's level 05, all existing stores) | `x_a − x_b` | 0 | 0.4 / 0.18 = 2.222 | `2.22 × (x1 − x2)` ✓ |
| `single` (single-channel) | `x_a` | 0.6 | 0.2 / 0.09 = 2.222 | `2.22 × (x1 − 0.6)` ✓ |
| `sum` (matched-strength) | `x_1 + x_2` | 1.2 | 0.28 / 0.18 = 1.556 | `1.56 × (x1 + x2 − 1.2)` ✓ |

All three derive mechanically from the run's saved config (class means `m`, spreads `σ`), so the
helper hard-codes no world. `plan-reviewer` independently verified these three scale factors
(study, "re-check of Revision 1", Assumptions). Clipping at 0/1 is ignored by the formula, as in the study.

Per-nat slopes need **no new stored column**: LLR is linear in `s`, so "pp per nat" = "pp per unit of
`s`" ÷ `k`. This keeps every existing aggregate file's key set unchanged, which is what lets the golden
gate (A4) stay byte-for-byte.

### A3. What each pre-registered reading needs, and from where

| Study ID | Reading | Source today | Work |
|---|---|---|---|
| P1, P2, S4, S5 (hiding) | proximity effect and its injury shift | `collect_arm_data` `rd/rdc/pd` grids + `_ladder.proximity_effect`; `a4_hypervigilance.hiding_shift` | none beyond the smell fix; `hiding_shift` is re-stated (a4 is a figure script with plotting side effects on import, so it cannot be imported) |
| P2d, S5 (distance) | rabbit-within-2 share, injury shift | `rabbit_avoidance.py` | none |
| Survival, terminations | mean episode length; termination shares | `collect_arm_data` JSON `mean_survival`, `term_pct` | none |
| S1 | scent × injury, no-predator exactly-one-rabbit episodes, first 25 steps | per-episode early bush share exists in `collect_arm_data`'s `<arm>_episodes.npz` (`bush_early`, `steps_early`, `inj0`, `n_pred`, `n_rab`); rabbit scent and M1 covariates exist in `hiding_drivers`'s `aggregate.npz` | **new post-processing**: join the two per-episode files by episode seed (both sorted by seed, same population — asserted equal), then quarter contrast + GLM. No new sweep. **Plus (Rev 1, R5) a matched control reading** in the difference layout: channel 1 as the statistic, channel 2 as a covariate — see A6. |
| S2 | scent ladder, M3, extreme rows, control matched reading | `hiding_drivers` CSVs; extreme rows were computed by the archived `supplementary/curves.py` from a tmp file | **new post-processing** from `aggregate.npz` |
| S3 | aimed split (nothing / predator / rabbit near) × rabbit-like vs predator-like | archived `supplementary/falsealarm.py`, hard-codes the a01 store, slots `[0,1]/[2,3]`, seed base, a tmp npz | **new run-agnostic sweep** `aimed_response.py` |
| S6 (a) | rabbit on the agent's own square: count, share, P1/P2 without it | `collect_arm_data.py:124` clips distance 0 into the near bin | **new accumulators** in the same sweep, written to a **separate** file |
| S6 (b) | predator-free P1/P2 (`dpred > 2`) | `rd`/`rdc` grids gate on `has_r` only (`:129`) | same as above |
| §5.3 | two-stage rule, contrasts A/B/C, verdict map, absolute sign of P2, top-up list, seed yardstick | nothing | **new** `verdict.py` |

**Two quirks in the a01 source that a reproduction must copy, not fix:**
`falsealarm.py` reads distances on the **same** row as the bush state (row `t`), whereas the study's §5
preamble says distances are read on the row the action was chosen from (row `t−1`); and a01's
"extreme sixths" are **fixed bins of the scent range** (`< −0.2`, `≥ 0.6`, from `curves.py`), not
population sextiles. The new tools compute both variants; which one is primary for the study is a
designer call (Open questions Q2, Q4).

### A4. The golden gate — what "reproduces published numbers" means concretely

| Gate | Object compared | Reference | Criterion |
|---|---|---|---|
| G1 ladder (existing refactor gate) | `collect_arm_data` output for three sensor-ladder arms | `results/_golden_prerefactor_20260904/` | `core/golden.py` REPRODUCED (tier 1 bit-exact, tier 2 rtol 1e-12), as when `--manifest` was added (dependency map row for `collect_arm_data.py`) |
| G2 clue page Figure A3 | `collect_arm_data --manifest` on two Wave cells: `w2_lvl05_control` and `w1_lvl06_modulated` (level 06 = injury-gated smell noise) | `results/analysis/basicq2_integrated/ladderstyle/<cell>.json` + `_episodes.npz` | golden.py REPRODUCED; `hiding_shift(rd)`, `(rdc)`, `(pd)` equal on candidate vs reference; min/max of the fourteen published `hide_s` values (the twelve Wave cells plus the two blind cells a4 reads) round to the caption's **−1.9** and **+0.3**; `rabbit_avoidance.py` rerun on `w2_lvl05_control` equals `results/analysis/basicq2_integrated/rabbit_avoidance/w2_lvl05_control.json` |
| G3 a01 page — code identity (Rev 1, R1) | `hiding_drivers` aggregate + CSVs from the **new** code on the a01 store (the resting-bonus arm `20260810-185749_rppo_restprem_a01_n106`), written to scratch | a **freshly regenerated reference**: the **base commit's** `hiding_drivers.py` (`git show <BASE>:scripts/analysis/hiding_drivers.py`, `<BASE>` = the commit the developer starts from, recorded in the stamp) run on the same store into `_golden_scratch/g3_reference/` | golden.py REPRODUCED on `aggregate.npz` (tier 1 bit-exact, tier 2 rtol 1e-12, key sets equal); `univariate.csv`, `multivariate.csv`, `summary.json` **byte-identical** (`cmp`) |
| G3 published values (printed precision) | computed from the G3 **candidate** aggregate + a new `aimed_response.py` sweep on the a01 store (same-row distances); the univariate scent effects additionally read from the **Aug-25 published** `results/analysis/hiding_drivers/<a01>/univariate.csv` | a01 doc Finding 2 and ranking table | univariate scent effect +1.6 pp/SD (rabbit; CSV `dpp_per_sd` 1.6117), +1.7 (predator; 1.7154) — both in the candidate and in the Aug-25 CSV; extreme rows rabbit hides 14.9 % / 22.6 %, survived 193.3 / 175.6 steps; predator hides 29.7 % / 35.0 %, survived 88.9 / 115.4; aimed split +8.0 / +6.4 / **+23.1** pp, rabbit-near hiding 26.7 % → 49.8 %, time near rabbit 13.0 % vs 14.3 % |

**Why G3's reference is regenerated (Rev 1, R1).** The existing a01 `aggregate.npz` (written
2026-08-25 14:39) predates commit `01fe5701` (20:41 the same day), which added six columns
(`pred_/rab_olf_ch1/ch2`, `pred_/rab_olf_intensity`, `pred_detect_max/min`) and made `fit_glms` read
two of them. `core/golden.py` counts a candidate-only key as MISSING and fails on it, so no current
code — changed or not — can reproduce that file, and the old `fit_glms` raises `KeyError` on it. The
reference is therefore produced by the unchanged code at the base commit on the same store. The Aug-25
files are used only for the published-value check at printed precision. **`core/golden.py` is not
changed**; no key is ignored, no tolerance widened.

The extreme-row columns *Food per step*, *Starved*, *Killed* are printed on the a01 page but their
producing code is not in the repo (`curves.py` computes only hiding and survival). The gate checks them
with the obvious definitions (below); a mismatch is **reported, not tuned** — see Checkpoint C6.

Existing results a01 cites were produced by `hiding_drivers.py` and archived scripts; the clue page's A3
by `collect_arm_data.py --manifest` → `a4_hypervigilance.py`, `rabbit_avoidance.py`. `d3_rabbit_scenes.py`
(clue page, controlled scenes) reads evaluation-probe histories, not trajectory stores; it has no smell
dependence and nothing here changes it (Q5).

### A5. Rule constants that must match the study text (Rev 1: rewritten against study Revisions 2–3)

Source: study §5.2 and §5.3 **as of Revision 3** (`86ce3119`). Every row is anchored by `verdict.py`
to the study's own sentence, copied verbatim from the study (not from this table), inside the
§5.2–§5.3 slice only (R8).

| Constant | Value | Where in the study |
|---|---|---|
| P1 predicted sign / minimum | + / 3 pp | §5.3 outcomes table |
| P2 predicted sign / minimum | + / 2 pp | same |
| P2d predicted sign / minimum | − / 1 pp; decides nothing alone; H₁b needs P2 established and P2d's Δ of the predicted sign | same |
| S1 predicted sign / minimum | + / 2 pp per nat (quarter contrast) | same |
| Survival | − ; Δ with its 95 % interval, no threshold, no decision | same |
| Scope of the two-stage rule | contrasts **A and B only** | §5.3 "The two-stage rule below applies to contrasts A and B only." |
| Stage 1 | 3 v 3; established iff complete separation in the predicted direction (one-sided exact p = 0.05) and \|Δ\| ≥ minimum; anything else → stage 2 | §5.3 Stage 1 |
| Stage 2 | 5 v 5; established iff one-sided U ≤ 4 in the predicted direction and \|Δ\| ≥ min; refuted iff the one-sided 95 % Welch bound **on the predicted side** (upper for +, lower for −) falls short of the minimum (below +min / above −min), or U ≤ 4 in the opposite direction; else not established; no further top-up | §5.3 Stage 2 (Revision 2, N5) |
| Contrast C (single-channel − matched) | **two-sided, descriptive** (Revision 2, N1): Δ, per-seed values, 95 % interval always; never "established"; at 5 v 5 (both worlds topped up) two-sided U ≤ 2 → "C clearly non-zero"; triggers no top-up of its own | §5.3 paragraph before Stage 1 |
| **C-sign classification on P1** (Rev 1, R2) | per agent: (i) B established and \|C\| < 3 pp → "identifiability; strength-halving does not change it"; (ii) B established, A not, C ≤ −3 pp → "strength loss masks confusion in 1ch"; (iii) A established, B not established, C ≥ +3 pp → "1ch effect not explained by identifiability"; (iv) A and B established, any C → "both raise confusion; C = size of the strength component"; any other combination → "no registered cross-contrast reading". C is its point estimate | §5.3 "Across the three contrasts" (Revision 2) |
| **S4 "did not fall"** (Rev 1, R2) | one-sided 95 % Welch **lower** bound of the predator proximity effect's Δ **> −3 pp**, evaluated at the stage at which the primary outcome (the P1 of that agent × contrast) was decided (3 v 3 or 5 v 5); otherwise "S4 may have fallen". Read with sign: a rising S4 never triggers the detection row | §5.2 S4 (Revision 2, N2) |
| Verdict map | six rows, labels copied verbatim; rows 4–6 use "S4 did not fall" / "S4 may have fallen" | §5.3 verdict map |
| Absolute sign of P2 | treated-world mean P2 and its one-sided 95 % lower bound (t, n−1 df); if P2's Δ is established and that bound is not > 0 → the "weakens the wounded agent's boldness" reading | §5.3 "Absolute sign of P2" |
| S1 reference arm | the tested Δ uses the **matched control reading** (channel 1, channel 2 as covariate, 2.22 nats per unit); plain `x1 − x2` reading descriptive; matched decides if they disagree | §5.2 S1 (Revision 4) |
| S1 primary estimator | weighted least-squares slope (pp per nat, weights = early step count) within the top and bottom start-injury quarters; contrast = top − bottom; the quasi-binomial product term is descriptive | §5.2 S1 (Revision 3, Q3) |
| S1 window | first 25 chosen steps | §5.2 S1 |
| S2 extreme rows | within-world population sextiles of the rabbit's statistic over that world's exactly-one-rabbit episodes; each row reports its mean evidence in nats; cut points identical for every run of a world (**asserted**); a01 fixed bins (`< −0.2`, `≥ 0.6`) in the control only | §5.2 S2 (Revision 3, Q2) |
| S3 groups | rabbit-like LLR < 0, predator-like LLR ≥ +0.67 (implemented as 2/3 nat: control `x1−x2 ≥ 0.3`, single `x1 ≥ 0.9`, matched `x1+x2 ≥ 1.6286`) | §5.2 S3 |
| S3 distance row | primary = deciding row (`t−1`); same row = sensitivity and a01 reproduction | §5.2 S3 (Revision 3, Q4) |

Precondition P0 of the first draft (the study text lacking N1/N2/N5) is **satisfied**: Revision 2
carries all three and Revision 3 registers the three primary-variant choices.

### A6. S1's control reference is not like-for-like (Rev 1, R5)

In the control world the statistic `x1 − x2` is independent of total strength `x1 + x2` (equal-spread
independent jitter), so the control's scent × injury slope measures an identity-only effect. In both
treated worlds the statistic *is* strength, so their slope is identity × injury **plus** any
strength × injury response. The per-nat rescaling equalises ideal-observer evidence, not this. The
tooling therefore also computes an **S1 matched control reading** in the difference layout — statistic
= the rabbit's channel 1 (`rab_olf_ch1`), with channel 2 (`rab_olf_ch2`) as a covariate, on the
single-channel evidence scale (channel 1 alone has means 0.7 / 0.5 and SD 0.3, so `k` = 2.222 per unit,
midpoint 0.6, identical to the single-channel world) — through the same quarter-contrast and GLM code.
Every S1 reading records `statistic_equals_intensity` (true in both treated worlds and in the matched
control reading, false in the plain control reading). **Registered by study Revision 4 (`39420f2c`,
pre-data):** S1's tested Δ uses the **matched** control reading; the plain control reading is reported
beside it as descriptive ("identity-only reference"), with its own Δ; if the two disagree on whether Δ
clears 2 pp per nat, both appear in the result's first sentence and the matched one decides; on
contrast B the residual strength-per-nat difference (0.64 vs 0.45 units of strength per nat) is stated
with every S1 result. `verdict.py` anchors this.

---

## Implementation Plan

### Design

```
run dir (saved models/config.yaml) ──► core/env.scent_spec(cfg) ──► ScentSpec {layout, channels, midpoint, k}
                                                  │ (refuses anything but difference / single / sum)
store(s) ─┬─► hiding_drivers.py        → glm/aggregate.npz, univariate.csv, multivariate.csv, scent.json
          ├─► collect_arm_data.py      → ladderstyle/<label>.json, <label>_episodes.npz  (unchanged keys)
          │                              + ladderstyle/<label>_sensitivity.json        (NEW: S6)
          ├─► rabbit_avoidance.py      → rabbit_avoidance.json                          (unchanged)
          └─► aimed_response.py (NEW)  → aimed_response.json                            (S3)
                          │
     studies/hypervigilance/make_population.py (NEW) — population.json with a status column
     studies/hypervigilance/readings.py (NEW) — reads population.json (completed cells only), runs the
     four sweeps (subprocess, guarded cache, asserted output root), assembles readings.json per run
     (P1…S6 + data accounting)
                          │
     studies/hypervigilance/verdict.py (NEW) — §5.3 over readings.json of a population;
     anchors its constants to the study text; needs the seed yardstick first
     studies/hypervigilance/golden_check.py (NEW) — G1–G3 (G3 against a reference regenerated
     by the base commit's hiding_drivers.py); on pass writes a stamp that
     readings.py requires (hashes of the analysis sources) before it will read any population
```

Why this shape: every existing sweep stays the single producer of its numbers (no second
implementation), new readings are either post-processing of existing per-episode files (S1, S2) or one
small guarded sweep (S3), and every new output lives in a **new file**, so no existing JSON/npz changes
key set and the golden gate stays a strict equality test. Sweeps are chained by subprocess, as
`nmn_site_grid/run_hiding_drivers.py` already does, because `collect_arm_data` binds its output root
from the environment at import time.

**Non-goals.** No change under `src/` or `configs/` (study §5.6: "Metrics requested from `src/`: none").
No change to `collect_hiding_drivers.py` (ladder-only port; it keeps calling `smell_channels`, whose
behaviour on two-channel configs is unchanged). No page build, no figures. No WandB training-curve
reading (§5.4.1 is `experiment-analyzer`'s, via `wandb-analysis`). No re-analysis of the archived
supplementary scripts beyond the S3 port.

### Precondition P0 — satisfied (Rev 1)

The first draft blocked Checkpoint C9 on the study absorbing plan-review N1/N2/N5. Study Revision 2
(`7ec62720`) did, and Revision 3 (`86ce3119`) registered the S1 estimator, the S2 sextiles and the S3
deciding row (A5). The last open registration — which control reference S1's Δ uses — was made by study Revision 4
(`39420f2c`): the matched control reading (A6).

### Revision 2 amendments (N1–N4)

*2026-10-01, folded in by `developer` at the user's request from the `plan-reviewer` re-check of
Revision 1 (`8646c0ce`), before any code was written. Where this section and a File Changes bullet
below disagree, this section wins; the bullets it supersedes are marked "(see Revision 2)".*

- **N1 — who keeps the Launch Manifest status true, and a stale-status refusal.** The study's §3
  Launch Manifest `Status` column is flipped `running` → `completed` by **the parent session that
  runs training and then the trajectory collection** (collection is what makes a cell readable), in
  the same edit that records the store path. The tooling never promotes a row itself.
  `make_population.py --from-study-doc` adds a disk-consistency check per row: a row whose status is
  `running` **and** whose run dir holds a final checkpoint (a `models/<N>` directory with
  `N ≥` the saved config's top-level `episodes`) **and** that has a store under `--store-root` →
  refuse the whole manifest with "stale status: <run> is marked running but has a final checkpoint
  and a store — update the study's Launch Manifest"; a `completed` row with no store → refuse (as
  already planned). Tests: both refusals, and a `running` row with a final checkpoint but no store
  is accepted as `running` (training done, collection not yet).
- **N2 — two-tier golden stamp.** The single stamp of §6/§8 is split in two, with the same
  guarantee:
  - **Sweep tier** (`golden_check.py --tier sweep`, hours): runs G1–G3's store sweeps and every
    `golden.py` / `cmp` comparison. Its stamp `_golden_sweep_pass.json` records the sha256 of the
    **sweep sources only** — `core/env.py`, `core/scan.py`, `core/store.py`, `hiding_drivers.py`,
    `studies/sensor_ladder/collect_arm_data.py`, `ladder/_ladder.py`, `rabbit_avoidance.py`,
    `aimed_response.py` — and the candidate outputs stay cached under
    `_golden_scratch/sweep_<first 12 hex of the combined sweep hash>/`.
  - **Assembly tier** (`golden_check.py --tier assembly`, seconds): requires a sweep stamp whose
    hashes equal the current sweep sources and whose cache directory exists, then re-derives every
    published value of A4 (a01 extreme rows, univariate +1.6/+1.7, aimed split; clue-page
    `hiding_shift` values and the −1.9/+0.3 span) **through `readings.py`'s own functions** from the
    cached candidate outputs. Its stamp `_golden_assembly_pass.json` records the sha256 of
    `readings.py` and `make_population.py` plus the sweep stamp's hash.
  - `readings.py` refuses any non-`a01` population unless **both** stamps exist and all recorded
    hashes equal the current files. An edit to an assembly file re-requires only the seconds-long
    tier; an edit to a sweep file re-requires the hours-long one.
- **N3 — per-cell checkpoint and store root.** Each `population.json` cell carries `checkpoint` (the
  actual checkpoint directory name of its store, e.g. `8000033`) and `store_root` next to `stores`.
  `make_population.py --checkpoint-nearest N` picks, per run, the store checkpoint under
  `--store-root` whose number is closest to N (ties → refuse) and records the actual number;
  without it, a run with more than one store checkpoint is refused (as `find_stores` does).
  `readings.py` **drops its `--checkpoint` flag** and reads the checkpoint from the manifest; a
  population whose cells carry different checkpoints is fine (that is the point). Output of a
  time-course population goes to its own population directory, never over the final-store one.
  Test: two fake runs with store checkpoints `8000033` / `8000043` both resolve to their own
  directories for N = 8,000,000.
- **N4 — backtick-aware table parser.** `make_population.py` splits Launch Manifest rows on `|` only
  outside backtick spans, and refuses (naming the row) any row whose cell count differs from the
  header's. Test: a row with a `|` inside a backticked path parses; a row with one cell too many is
  refused.
- **A5 (budget) — recorded, not a code change.** C8 records the wall-clock per sweep; if one cell
  exceeds about an hour, the Implementation Report states the serial-budget estimate. The user's
  hand-off for this implementation allows the heavy sweeps to run on free lab nodes (not 114; not the
  training nodes 102/106–112), so independent cells may run concurrently on different nodes, each
  `readings.py` invocation still serial within itself.

### File Changes

No new config keys. No registry setting touched (`CONFIG_CRITICAL_SETTINGS.md` unaffected).

#### 1. `scripts/analysis/core/env.py` (lines 73–82; add ~70 lines)

Add `ScentSpec` and `scent_spec(cfg)`; turn `smell_channels` into a wrapper.

```python
@dataclass(frozen=True)
class ScentSpec:
    layout: str                   # "difference" | "single" | "sum"
    channels: tuple[int, ...]     # difference: (a, b) predator-leaning, rabbit-leaning; single: (a,); sum: emitting channels, ascending
    midpoint: float               # (mu_p + mu_r) / 2 of the statistic, from config means (unclipped)
    llr_scale: float              # nats per unit of statistic: (mu_p - mu_r) / var_s; NaN if var_s == 0
    pred_mean: tuple; rab_mean: tuple; sd: tuple   # provenance, written to outputs

    def statistic(self, prop):    # prop[..., n_channels]
        # difference: prop[..., a] - prop[..., b]   <- the SAME expression as today (byte-identity)
        # single:     prop[..., a]
        # sum:        prop[..., c0] + prop[..., c1] (+ ... left to right)
    def intensity(self, prop):    # total animal odour on the emitting channels
        # difference: prop[..., a] + prop[..., b]   <- same expression as collect_arm_data:74 / hiding_drivers:184
        # single: prop[..., a];  sum: same as statistic
    def llr(self, s): return self.llr_scale * (s - self.midpoint)
```

Inference in `scent_spec(cfg)` (animal `entities` only; class means and spreads averaged over
declarations exactly as today, `np.mean` unweighted). `E` = channels where either class mean is non-zero;
`d = m_pred − m_rab`:

1. `difference`: `|E| == 2`, one `d > 0` and one `d < 0` on `E` → `a = argmax(d)`, `b = argmin(d)`.
2. `single`: `|E| == 1` and `d > 0` on it.
3. `sum`: `|E| ≥ 2`, `d > 0` on every channel of `E`, and each class's mean is equal across `E`
   (`np.allclose`, atol 1e-9) — i.e. the ratio carries no identity.
4. Anything else → `SystemExit` naming both class means and the three accepted layouts.
   Also `SystemExit` if the predator and rabbit spreads differ on any channel of `E` (the LLR formula
   of A2 assumes equal spreads). Means are checked **before** `properties_std` is read, so the existing
   test `test_smell_channels_refuses_a_config_that_does_not_separate` (no `properties_std` key) still
   fails on the means, as today. A missing `properties_std` on an otherwise valid config →
   `SystemExit` naming the entity (no fallback value).

```python
def smell_channels(cfg):          # kept: collect_hiding_drivers.py and old callers
    spec = scent_spec(cfg)
    if spec.layout != "difference":
        raise SystemExit(f"this run's odour layout is '{spec.layout}'; smell_channels() is defined "
                         f"only for the two-channel difference layout -- use scent_spec()")
    return spec.channels
```

Update the module docstring's consolidation table with one line: "`smell_channels` → wrapper over
`scent_spec` (2026-10-01, hypervigilance tooling)".

#### 2. `scripts/analysis/hiding_drivers.py`

- **Lines 81–97:** delete the local `smell_channels`; after the imports add
  `sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "core"))` and
  `from env import scent_spec, smell_channels  # noqa: E402` (so `hiding_drivers.smell_channels` still resolves).
- **`aggregate(stores, lay, spec, verbose=True)`** (143): parameter `chans` → `spec: ScentSpec`.
  Lines 178–185 become `spec.statistic(prop[:, P])` / `spec.intensity(...)`. `*_olf_ch1` = channel
  `spec.channels[0]`; `*_olf_ch2` = `spec.channels[1]` if it exists, else an all-NaN array (key set stays
  identical for every layout). No new keys.
- **Lift the nested `fit` (284–299) to module level** as
  `quasi_binomial_fit(X, keep, label, Y, L)` — body unchanged, `Y`/`L` passed in. `fit_glms` calls it.
  Needed because S1 and the S2 matched reading fit the same model on other outcomes.
- **`fit_glms(D, out_dir, *, layout)`** (258): required keyword. When `layout != "difference"`, delete
  `pred_olf_intensity` from `EXO_P` and `rab_olf_intensity` from `EXO_R` (they equal the predatorness
  column there — A1), and print one line saying so. Two-channel output is unchanged.
- **`main()`** (366–390): `spec = scent_spec(cfg)`; line 377 prints the layout, channels, midpoint and
  `k`; `aggregate(stores, lay, spec)`; `fit_glms(D, out, layout=spec.layout)`; write
  `{out}/scent.json` (the spec fields). `summary.json` is **not** changed (it is a golden product).
- Grep `scripts/` and `tests/` for other importers of `aggregate`, `fit_glms` or `smell_channels`
  from this module before changing signatures; today there are none (A1), confirm.

#### 3. `scripts/analysis/figures/_common.py` (lines 57–67)

Replace the copy with delegation: insert `scripts/analysis/core` on `sys.path` (relative to `__file__`)
and `from env import smell_channels, scent_spec  # noqa: E402`. It has no caller today; this removes the
third copy rather than generalising it separately.

#### 4. `scripts/analysis/studies/sensor_ladder/collect_arm_data.py`

- **Line 61:** `spec = ENV.scent_spec(cfg)` replaces `ch1, ch2 = ENV.smell_channels(cfg)`.
- **Lines 74–75:** `pred_olf = mean_over(spec.intensity(prop[:, P]), pa)`, same for `rab_olf`.
  For the two-channel layout this is the identical expression (A2 table; floating-point addition is
  commutative, so channel order cannot matter).
- **S6 accumulators, new, in `collect()` after line 133.** Put the arithmetic in a module-level pure
  function so it can be unit-tested without a store:

```python
def accumulate_sensitivity(S, y, drab_prev, dpred_prev, ib, cb, hr):
    """Study S6 (plan-review M3). Rows are chosen steps of episodes with >=1 rabbit (mask hr).
    (a) a rabbit ON the agent's square (drab_prev == 0): counted per start-injury quarter, and the
        rd grid rebuilt WITHOUT those rows (today they are clipped into the 1-2 bin, :124);
    (b) predator-free rows (dpred_prev > 2; inf = no live predator counts as free): rd and rdc grids.
    Uses np.bincount on flattened (dist_bin * 4 + inj_bin) indices, not np.add.at, to keep the sweep fast."""
```

  Grids: `rd_no0_bush/tot` (start injury), `rab_on_cell` (4), `rab_steps` (4, the `hr` step count, as
  denominator), `rdpf_bush/tot` (start injury), `rdcpf_bush/tot` (current injury). Distance binning for
  the new grids reuses the existing `drb` expression. The existing `G` grids are not touched.
- **After line 184:** `L.save_json(f"{arm}_sensitivity", {...})` with `arm, run, stores, n_episodes,
  seed_range`, the spec fields, and the new grids. `<arm>.json` and `<arm>_episodes.npz` keep exactly
  their current keys (golden products).

#### 5. `scripts/analysis/aimed_response.py` — NEW (one level deep, like `rabbit_avoidance.py`)

Run-agnostic port of `supplementary/falsealarm.py` (study S3; §5.6 item 2).

- **Imports (Rev 1, R9):** at the top, `sys.path.insert(0, HERE)` and
  `sys.path.insert(0, os.path.join(HERE, "core"))` with `HERE = os.path.dirname(os.path.abspath(__file__))`
  (i.e. `scripts/analysis/`), then `from hiding_drivers import find_stores` and
  `import env as ENV, store as STORE, scan as SCAN`. `hiding_drivers.py` has a `__main__` guard and no
  import-time side effects, so the import is safe. Recorded in the dependency-map row.
- CLI: `--run`, `--store-root` (nargs+, required), `--checkpoint`, `--out` (required). **No
  `--max-blocks`** (Rev 1, R4: `core/scan.sweep` asserts full step counts; smoke mode is dropped).
- Layout from `ENV.slot_layout` + `ENV.scent_spec` on the run's saved config; stores via `find_stores`;
  the sweep via `STORE.open_run` + `SCAN.sweep` (the guarded scan: seed contiguity, shard alignment,
  reset-row handling, `fr.prev`).
- Episodes: exactly one predator and one rabbit (`animal_active`). Rabbit statistic from
  `animal_property_sampled` → LLR. Groups: `RABBIT_LIKE_BELOW_NATS = 0.0`,
  `PREDATOR_LIKE_AT_NATS = 2/3` (study "≥ +0.67"; 2/3 is the value that maps exactly to a01's `0.3` in the
  control: `0.3 × 0.4/0.18 = 2/3`). The statistic-space thresholds actually used are written to the output.
- Per chosen step: state = predator within 2 (Chebyshev, live) → "predator near"; else rabbit within 2 →
  "rabbit near"; else "nothing near" (a01 precedence). Computed **twice in the one sweep**:
  `prev_row` (distances on the deciding row `t−1`; **primary**, study Revision 3 Q4) and `same_row`
  (row `t`, a01's convention; sensitivity reading and the G3 reproduction).
- Output JSON: spec, thresholds (nats and statistic space), group episode counts, per group × state:
  steps, bush steps, bush share; per-state differences (pp); time share per state; `NEAR = 2`;
  run/stores/seed range; data accounting (episodes used / available with the filter named).

#### 6. `scripts/analysis/studies/hypervigilance/readings.py` — NEW (three levels deep: `ROOT` walks four `..`)

Per-run assembly over a **population manifest**; run-agnostic (any run whose store and saved config
exist, including the next study's).

- **CLI:** `--manifest <population.json>` (required), `--labels` (subset), ~~`--checkpoint`~~ (see Revision 2, N3),
  `--stage {check, sweep, assemble, all}`, `--reuse-cache`, `--out-root` (required; must resolve under
  `<ROOT>/results/analysis/hypervigilance/`). **No `--max-blocks` / smoke mode** (Rev 1, R4 — dropped
  rather than adding a shard limit to the golden-gated `core/scan`, `hiding_drivers.py` and
  `collect_arm_data.py`; see C8/C10 for the re-budget). Stage `check` reads only the saved config and the
  first episodes shard — no step sweep — and is the cheap first look at a new store.
- **Population manifest (Rev 1, R3)** — JSON, one entry per cell:
  `{label, run, stores, world, agent, seed, level, wave, status}`; `status` ∈ {`completed`, `running`,
  `failed`, `planned`}. Written by the companion `make_population.py` (§6b). `readings.py` reads **only
  `completed`** cells; it refuses the manifest if any `(world, agent, seed, level, wave)` key has more
  than one `completed` entry, or if a `completed` entry's run dir has no `models/config.yaml` or no
  store. A tag-regex cross-check (full tag, anchored, optional `_r\d+` relaunch suffix:
  `^\d{8}-\d{6}_(?P<tag>rppo_(hv1ch|hv1chm|hv2ch)_(t1none|t16quad)_s(\d+))(_r\d+)?$`, never `*hv1ch*` —
  study Revision 2 N4) must agree with the entry's `world/agent/seed`; disagreement = refuse.
- **Ground-truth checks per cell** (stage `check`, and repeated at the start of `sweep`; fail = refuse
  that cell): the saved config's top-level `seed` equals the manifest's seed; the inferred layout matches
  the world (`hv2ch`, `basicq2`, `cmp10m`, `a01` → `difference`; `hv1ch` → `single`; `hv1chm` → `sum`);
  **from the store itself**, on the first episodes shard: every `animal_property_sampled` channel outside
  the spec's emitting set is exactly 0 for active animals, and the per-class empirical means of the
  emitting channels are recorded (verifies the store came from the world the config says).
- **Golden stamp gate (see Revision 2, N2 — now two stamps):** refuses every manifest whose population is not `a01` unless
  `results/analysis/hypervigilance/_golden_pass.json` exists and its recorded sha256 of each analysis
  source (`core/env.py`, `core/scan.py`, `core/store.py`, `hiding_drivers.py`, `collect_arm_data.py`,
  `ladder/_ladder.py`, `rabbit_avoidance.py`, `aimed_response.py`, `make_population.py`, `readings.py`)
  equals the current file.
  Any edit to those files re-requires the golden check.
- **Output-root guard (Rev 1, R7), before any subprocess is spawned:** `OUT = realpath(--out-root)`
  must start with `realpath(<ROOT>/results/analysis/hypervigilance) + os.sep`; the child environment is
  a copy of `os.environ` with `LADDER_OUT_ROOT` **set explicitly** to the absolute
  `<OUT>/<label>/ladderstyle`, and the driver asserts that value is absolute, under `OUT`, and not
  `realpath(<ROOT>/results/analysis/ladder)`. `_ladder.OUT_ROOT` otherwise defaults to the live
  sensor-ladder root (`_ladder.py:35`). `hiding_drivers.py` gets absolute `--out` and `--cache`;
  `rabbit_avoidance.py` / `aimed_response.py` absolute `--out`. Same guard in `golden_check.py` with
  `_golden_scratch/` as the required parent.
- **Sweeps** (stage `sweep`; `subprocess.run([sys.executable, …], cwd=ROOT, env=child_env, check=True)`,
  one cell at a time — the NAS is the bottleneck): `hiding_drivers.py`; `collect_arm_data.py --manifest
  <cell manifest>` (the one-cell `{label: {run, stores}}` JSON it already accepts); `rabbit_avoidance.py`;
  `aimed_response.py`. Outputs under `<OUT>/<label>/` (`/ckpt_<N>/` when `--checkpoint` is given, for the
  §5.4 time course). **Stale-cache guard** (the trap `run_hiding_drivers.py` documents): refuse if any
  output exists unless `--reuse-cache`; with it, require each JSON's recorded `run`/`stores` to equal the
  requested ones and `aggregate.npz["seed"]` to equal `<label>_episodes.npz["seed"]`.
- **Assembly** (stage `assemble`) → `<label>/readings.json`:
  - `scent`: the `ScentSpec` fields and **`statistic_equals_intensity`** at run level (Rev 1, R5;
    false for `difference`, true for `single`/`sum`); each S1 sub-reading carries its own copy of the flag
    (study Revision 4: true in the treated worlds and in the matched control reading, false in the plain
    control reading).
  - `survival`: mean steps, termination shares (from the ladder JSON).
  - `P1` = `proximity_effect(rd_bush, rd_tot)`; `P2` = `hiding_shift(rd)` =
    `proximity_effect(..., (3,)) − proximity_effect(..., (0,))` (re-stated one-liner, identical to
    `a4_hypervigilance.py:34-36`, which cannot be imported: it draws a figure at import); `P2d` =
    `rabbit_avoidance` `start.near_share_shift`.
  - `S1` (no predator, exactly one rabbit): episodes joined by seed (assert equal seed arrays);
    early bush share = `bush_early / steps_early`; LLR = `spec.llr(rab_predatorness)`.
    (i) **primary** (study Revision 3 Q3): within start-injury quarters 0 and 3 (edges 25/50/75),
    weighted least-squares slope of the share (pp) on LLR (nats), weights `steps_early`; contrast =
    q3 − q0 in pp per nat; per-quarter slopes and episode counts reported. (ii) descriptive GLM:
    `quasi_binomial_fit` with `Y = bush_early`, `L = steps_early`, regressors LLR, start injury,
    LLR × start injury, start nutrition, bushes, rocks, food, ambush predators, spawn distance to bush;
    product term reported as `coef × p̄(1−p̄) × 100 × 100` (pp per nat per 100 injury) with its SE.
    Both repeated on one-predator-one-rabbit episodes (sensitivity).
    (iii) **matched control reading** (Rev 1, R5; `difference` layout only; A6): the same (i) and (ii)
    with the statistic replaced by the rabbit's channel 1 on the single-channel evidence scale
    (`k` = 0.2/0.09, midpoint 0.6, derived from the config's channel-1 means and SD, not typed) and
    `rab_olf_ch2` added as a covariate — in (i) as a second regressor of the same weighted least squares
    in each quarter, in (ii) as a GLM term. Written as `S1.matched_control` (the registered reference for
    the tested Δ, study Revision 4); the plain reading is `S1.plain`.
  - `S2`: univariate rabbit (and predator) scent from `glm/univariate.csv`: pp per unit, **÷ k → pp per
    nat**, pp per SD, n; M3 row(s) from `multivariate.csv`; extreme rows on exactly-one-rabbit episodes
    (and exactly-one-predator for the predator table) — *hides* = pooled `bush_steps / n_steps`, *food
    per step* = `n_ate / n_steps`, *starved* / *killed* = termination shares, *survived* = mean
    `n_steps` — (a) **primary** (Revision 3 Q2): within-world population sextiles of the statistic, each
    row with its mean evidence in nats, the cut points written to the output; (b) `difference` only:
    a01's fixed bins `< −0.2`, `≥ 0.6`; control matched reading (`difference` only):
    `quasi_binomial_fit` on exactly-one-rabbit episodes with `rab_olf_ch1` and `rab_olf_ch2`, reporting
    the channel-1 coefficient per unit, per nat and per SD. **Cross-run assertion** (study S2: "the tool
    asserts this"): after assembling a population, the sextile cut points must be identical across all
    `completed` runs of the same world; a mismatch refuses the population.
  - `S3`: the `aimed_response.json` summary (both distance rows, `prev_row` labelled primary; group
    sizes).
  - `S4`: `proximity_effect(pd_bush, pd_tot)`, killed-by-predator share, confusion index = P1 ÷ S4.
  - `S5`: `hiding_shift(rdc)`; `rabbit_avoidance` `current.near_share_shift`.
  - `S6`: rabbit-on-square steps and share of rabbit-episode steps; P1/P2 without distance 0; P1/P2
    predator-free (start injury) and P2 predator-free on current injury.
  - Every NaN carries a `reason` ("bin below 1000 steps", "no rabbit slots", "deterministic smell: k
    undefined"); study §5.7 says such a reading is reported as not computable, never substituted.
  - `accounting`: a list of `{what, used, total, pct, reason}` rows per reading (episodes and steps),
    emitted by code — the artifact guide's data-accounting requirement is met at the source.
  - `code`: git HEAD, dirty flag, and the source sha256s.

#### 6b. `scripts/analysis/studies/hypervigilance/make_population.py` — NEW (Rev 1, R3)

Writes the population manifest JSON `readings.py` reads. Sources, one flag each:

- `--from-study-doc <md> --store-root <root>`: parses the study's **Launch Manifest** table (the ground
  truth for status; columns *Run, Status, Cell, Tag, Seed, … Log path*). Status = the cell's first word,
  lower-cased (`completed (not relaunched; …)` → `completed`). Run dir = the `run dir` path in the *Log
  path* cell; a row with no run dir is `planned`. For the hv study this yields the 16 H-rows and C01/C02
  (world `hv2ch`), and any future `_r2` relaunch row the runner adds.
- `--from-ladder-manifest <json> --world basicq2`: wraps an existing `{label: {run, stores}}` file
  (e.g. `results/analysis/basicq2_integrated/_manifest.json`) plus Wave 1/2 level-03 cells found under
  `results/trajectories_basicq2_w{1,2}/`, all `completed`.
- `--runs <dir> ... --world <w> --store-root <root>`: explicit list, all `completed` (cmp10m, a01,
  l05body_w0000).

In every mode, stores are resolved with `hiding_drivers.find_stores` (refuses several checkpoints
without `--checkpoint`). Output: `results/analysis/hypervigilance/<population>/population.json`, with the
source and its sha256 recorded. `make_population.py` never decides between two candidates for one seed;
it writes both and `readings.py` refuses.

#### 7. `scripts/analysis/studies/hypervigilance/verdict.py` — NEW

- Modes: `--yardstick --manifest <cmp10m population.json>`: between-seed SD of P1, P2, P2d, S1,
  S2-univariate per nat → `results/analysis/hypervigilance/cmp10m/yardstick.json`, plus the power table
  re-stated with those SDs. Default `--manifest <hvsmell population.json>` →
  `results/analysis/hypervigilance/hvsmell/verdict.{json,md}`. The default mode **refuses** unless
  `yardstick.json` exists (study §5.3: the yardstick is frozen before any hv run is read).
- **Post-hoc seed-noise line (Rev 1, reviewer A1):** beside every frozen yardstick SD, the verdict prints
  the between-seed SD of the same outcome in the hv **control** world (`hv2ch`, three seeds per agent),
  labelled "post hoc — not used by the rule". It is never fed into the rule or the power table.
- `RULES` constant block (A5) and `DOC_ANCHORS` (Rev 1, R8): for each constant, the exact study text it
  comes from, **copied verbatim from the study file** (the study writes `|Δ|`; this plan's tables escape
  it as `\|Δ\|` — do not copy from the plan). On start the script reads the study doc, keeps only the
  slice from the line `### 5.2 Secondary outcomes` up to the line `### 5.4 Temporal evolution` (the doc's
  feedback and response sections quote superseded rules and must not satisfy an anchor), collapses every
  whitespace run to one space, and refuses with the list of missing anchors if any is absent. Anchored,
  at least: the four minimum-effect rows; "applies to contrasts A and B only"; the Stage 1 and Stage 2
  sentences incl. "on the predicted side"; C's "two-sided and descriptive" and "U ≤ 2"; the four
  "Across the three contrasts" bullets (C-sign 3 pp); the S4 "did not fall" sentence ("lies above −3 pp",
  "at which the primary outcome was decided"); the six verdict-map row labels; the absolute-sign
  sentence; S1's weighted-least-squares and 25-step text; S2's "population sextiles"; S3's "≥ +0.67" and
  "deciding row". It imports `aimed_response.PREDATOR_LIKE_AT_NATS` and `readings.EARLY` and checks them
  against their anchors.
- Per agent (ordinary, modulated — never pooled) × contrast × outcome (P1, P2, P2d, S1, S4, survival):
  per-seed values, world means, between-seed SDs, paired per-seed differences (secondary), Δ, and:
  - **Contrasts A and B:** 3 v 3 → stage 1; not established → listed in `top_up_required` with the two
    worlds and seeds 45/46. 5 v 5 → stage 2 (U with ties counted ½; one-sided Welch bound, Welch–
    Satterthwaite df, on the predicted side). Any other seed count, or a NaN seed value → `not evaluable
    under §5.3` (no invented rule).
  - **Contrast C:** descriptive only — Δ, per-seed values, two-sided 95 % Welch interval; at 5 v 5 in
    both worlds the two-sided U ≤ 2 flag "C clearly non-zero"; never "established"; never in
    `top_up_required`.
  - P2d decides nothing alone; `H1b` flag = P2 established and P2d Δ of the predicted sign.
  - Survival: Δ with a 95 % Welch interval, no decision.
  - **S4 condition (Rev 1, R2):** for each agent × contrast (A, B), the stage at which that P1 was
    decided (1 if established at 3 v 3, else 2 if the 5 v 5 data exist) fixes the seed set; on it,
    "S4 did not fall" iff the one-sided 95 % Welch **lower** bound of the predator proximity effect's Δ
    is **> −3 pp**; else "S4 may have fallen". If P1 is still pending the top-up, S4 is "pending".
  - Verdict-map row per agent × contrast (A, B) from P1/P2 finals and the S4 condition, using the
    study's six row labels verbatim.
  - **C-sign classification (Rev 1, R2):** per agent, the five cases of A5 on P1 (B/A final statuses and
    C's point estimate against ±3 pp), with C's interval printed beside it.
  - Absolute-sign reading of P2 per treated world (mean, one-sided 95 % lower bound, t with n−1 df) and
    the "weakens boldness" flag when P2's Δ is established and the bound is not > 0.
  - S6 re-runs of P1/P2 through the same rule, reported beside the primary (study S6).
  - S1's Δ against both control references (A6, study Revision 4): the **matched** reference decides
    (anchored: "the tested Δ uses the **matched-control reading**"); the plain one is printed beside it as
    "identity-only reference, descriptive"; if exactly one of the two clears 2 pp per nat, the output
    flags "references disagree" for the first sentence; on contrast B the 0.64-vs-0.45
    strength-per-nat note is attached.
- Descriptive context (study §5.5): within-wave level 06 minus level 05 P1 and P2 per agent, from the
  `basicq2` readings, printed beside the contrasts; never pooled, never decided.
- `power(effect, sd, n_draws, rng_seed)` Monte-Carlo of the two-stage rule (used by the test and by
  the yardstick re-statement).

#### 8. `scripts/analysis/studies/hypervigilance/golden_check.py` — NEW (Rev 1: G3 reference regenerated, R1)

Runs G1–G3 (A4) into `results/analysis/hypervigilance/_golden_scratch/` (never a live output root; the
golden README forbids pointing a port at the live root) with the R7 output-root guard (§6), shells out
to `core/golden.py` for every file comparison and requires `REPRODUCED`, then checks the published values
of A4 at their printed precision.

- `--base <commit>` (required): the commit the implementation starts from (the developer records it in
  the Implementation Report). G3 reference: `git show <base>:scripts/analysis/hiding_drivers.py` →
  `_golden_scratch/g3_reference/hiding_drivers_base.py`, run from `ROOT` (it is cwd-relative) with
  `--run <a01 run> --store-root results/trajectories --out <scratch>/g3_reference --cache
  <scratch>/g3_reference/aggregate.npz`. G3 candidate: the current `hiding_drivers.py` into
  `<scratch>/g3_candidate`. Compare `aggregate.npz` with `golden.py`; `cmp` the three CSV/JSON products.
  The base script is run once; if `<scratch>/g3_reference/aggregate.npz` exists, `--reuse-reference`
  must be passed and the stamp records that the reference was reused with its sha256.
- Published values: from the G3 candidate aggregate (extreme rows), `aimed_response.py` on the a01 store
  (`same_row`), and the Aug-25 `univariate.csv` (read-only) for the univariate scent rows.
- `core/golden.py` is invoked unchanged; `golden_check.py` never filters keys out of either side.
- Prints a table of every check; on all-pass writes `_golden_pass.json` (date, HEAD, `--base`, source
  sha256s, per-check result). Any failure: no stamp, non-zero exit.

#### 9. Tests (new or extended, `tests/analysis/`)

Run with `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest …` (R10).

| File | Tests (each must fail on the pre-change code or on a planted defect) |
|---|---|
| `test_core_env.py` (extend) | the three study layouts (literal dicts copied from study §2.1 / Appendix B) → `layout`, `channels`, `midpoint` (0 / 0.6 / 1.2), `llr_scale` (0.4/0.18, 0.2/0.09, 0.28/0.18 exact; 2.22 / 2.22 / 1.56 at 2 dp); `statistic` on a small array is bit-identical to `x[...,a] − x[...,b]` in the difference layout; refusals: equal classes (existing test kept), two channels both predator-leaning but unequal (ratio informative), rabbit stronger on the only channel, three emitting channels with mixed signs, unequal class spreads, missing `properties_std`; `smell_channels` returns `(1, 2)` on the control and raises on single and sum. **Fails today**: `scent_spec` does not exist. |
| `test_hiding_drivers_layout.py` (new, Rev 1 R8) | `fit_glms` on a small synthetic `D` (a few thousand episodes, all keys `aggregate` writes) with `layout="single"` and `rab_olf_intensity == rab_predatorness`: runs without a singular-matrix failure, and the univariate and M2/M3 outputs contain no `*_olf_intensity` term; with `layout="difference"` they do. `fit_glms` without `layout=` raises `TypeError`. |
| `test_hv_sensitivity.py` (new) | `accumulate_sensitivity` known answer on hand-built rows: distance-0 rows counted per quarter and absent from `rd_no0`; a row with a predator at distance 2 absent from `rdpf`, at distance 3 present, with no predator (inf) present; `aimed_response`'s state classifier gives predator-near precedence; statistic thresholds from 2/3 nat = 0.3 / 0.9 / 1.6286 for the three layouts. |
| `test_hv_readings.py` (new) | S1 quarter contrast recovers a planted slope difference (synthetic episodes, q3 slope 5 pp/nat, q0 1 pp/nat → 4 ± 0.3); the matched-control variant recovers a planted channel-1 slope while channel 2 carries a separate planted effect; GLM product term has the planted sign; the seed-join assertion fires on misaligned arrays; `statistic_equals_intensity` false / true / true for the three layouts; S2 sextile cross-run assertion fires when one run's cut points differ; world/layout mismatch refused; golden-stamp gate refuses on a changed source hash; **output-root guard** refuses `--out-root results/analysis/ladder`, a relative path, and a path outside `results/analysis/hypervigilance/` (R7). |
| `test_hv_population.py` (new, Rev 1 R3) | `make_population` on a `tmp_path` markdown manifest + fake run dirs (each with `models/config.yaml` and a store dir): rows `…_rppo_hv1ch_t1none_s42` status `failed` and `…_rppo_hv1ch_t1none_s42_r2` status `completed` → the cell resolves to the `_r2` run and its store; both `completed` → `readings` refuses as ambiguous; a `…_rppo_hv1chm_t1none_s42` dir is never classified as world `hv1ch`; `completed (not relaunched; stores re-collected)` parses as `completed`; a `planned` row with no run dir is skipped; regex/entry disagreement refused. |
| `test_hv_verdict.py` (new) | stage 1: complete separation with \|Δ\| ≥ min → established; separation with \|Δ\| < min → top-up; one overlapping seed → top-up; stage 2: U matches `scipy.stats.mannwhitneyu` on random data; U ≤ 4 + min → established; Welch bound short of min → refuted; U ≤ 4 in the opposite direction → refuted; predicted-negative outcome (P2d) uses the lower side; contrast C is never "established" and never in `top_up_required`; 4 v 4 → "not evaluable". **S4 bound (R2), hand-computed:** predator-effect seeds treated [−1, −2, −3] vs reference [0, 0, 0]: Δ = −2, SE = 1/√3 = 0.5774, df = 2, t₀.₉₅ = 2.920, lower bound −3.686 → "S4 may have fallen"; treated [0, −1, −2]: lower bound −2.686 → "did not fall"; the bound is taken on the stage-2 seed set when P1 was decided at stage 2. **Absolute-sign bound (R2):** P2 seeds [1, 2, 3] → mean 2, lower bound 0.314 → above 0; [−1, 0, 1] → −1.686 → not above 0, and with an established Δ flags "weakens boldness". **C-sign:** one case per bullet plus "no registered reading". **Anchors (R8):** refuses a `tmp_path` copy of the study doc with the §5.3 "**3 pp**" changed to "**2 pp**"; also refuses a copy where the §5.3 text is removed but the same sentence survives in a feedback section (slice restriction). `power()` reproduces the study's power table within ±3 points at 40,000 draws, fixed seed: P1 +3 pp / SD 1.4 → 59 % established overall, 5 % wrongly refuted; P1 0 → < 1 % false positive, 92 % correctly refuted; P2 +2 pp / SD 1.5 → 51 %; P2 0 / SD 2.67 → 7 % false positive, 27 % correctly refuted. (That table was computed by the designer and independently reproduced by plan-reviewer; matching it is evidence the implementation is the registered rule, not a re-derivation of this code.) |

Unit tests must not read the 1 M-episode stores; the store-scale checks are the golden check and the
checkpoints below.

#### 10. Docs updated in the same change

- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (Maintenance Contract — files added under `scripts/`):
  - **new rows**: `scripts/analysis/aimed_response.py` (one level deep, cwd-relative like
    `rabbit_avoidance.py`; `sys.path`-inserts its own directory and `core/`, imports `hiding_drivers`
    (`find_stores`) and `core/{env,store,scan}`; subprocess callee of `readings.py` and
    `golden_check.py`; unit-tested by `test_hv_sensitivity.py`); `scripts/analysis/studies/hypervigilance/`
    `make_population.py`, `readings.py`, `verdict.py`, `golden_check.py` (**three** levels deep, `ROOT`
    walks four `..` — the §0 depth hazard; `readings.py` subprocess-invokes `hiding_drivers.py`,
    `collect_arm_data.py`, `rabbit_avoidance.py`, `aimed_response.py` with `sys.executable` and an
    explicit absolute `LADDER_OUT_ROOT`; `make_population.py` reads the study doc's Launch Manifest and
    imports `hiding_drivers.find_stores`; `verdict.py` reads the study doc's §5.2–§5.3 and imports
    `readings`/`aimed_response` constants; `golden_check.py` shells out to `core/golden.py`, to
    `git show <base>:scripts/analysis/hiding_drivers.py`, and to the three sweeps); the five new test
    files as callers.
  - **amended rows**: `core/env.py` (adds `scent_spec`; `smell_channels` is now a two-channel-only wrapper;
    new importers `hiding_drivers.py`, `figures/_common.py`, `aimed_response.py`, `readings.py`);
    `hiding_drivers.py` (the row at line 285 says it "imports only numpy/pyarrow/yaml/statsmodels/scipy" —
    it now `sys.path`-inserts `scripts/analysis/core` and imports `env`; `aggregate` takes a `ScentSpec`;
    `fit_glms` requires `layout=`; new module-level `quasi_binomial_fit`; writes `scent.json`; new
    subprocess callers `readings.py`, `golden_check.py` (which also runs the base-commit copy); new
    importers `aimed_response.py`, `make_population.py`; new test caller
    `test_hiding_drivers_layout.py`); `collect_arm_data.py` (writes `<arm>_sensitivity.json`; uses
    `scent_spec`; new subprocess callers `readings.py`, `golden_check.py`; **its CLI is unchanged — no
    block limit was added**, R4); `rabbit_avoidance.py` (new subprocess callers `readings.py`,
    `golden_check.py`); and the "Last updated" line.
- `scripts/analysis/supplementary/README.md`: one line under the `falsealarm.py` row — "run-agnostic
  successor: `scripts/analysis/aimed_response.py`"; the archived script itself is not changed.
- This plan's Implementation Report.

---

## Checkpoints

- [ ] **C1 — Equivalence on every existing run (before any sweep).** Loop over every run dir in
  `results/JAX_RecurrentPPO/` that has a store under any `results/trajectories*/` root: the pre-change
  `core/env.smell_channels` (from `git show`) and the new `scent_spec` agree — every config the old
  function accepted is `difference` with the same `(a, b)`, every config it refused is refused. Report the
  count per layout. Any disagreement → stop.
- [ ] **C2 — Unit tests.** `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python -m pytest
  tests/analysis/test_core_env.py tests/analysis/test_hiding_drivers_layout.py tests/analysis/test_hv_*.py`
  green; the full `tests/analysis/` suite still green. Each new test was seen to fail once against the
  pre-change code or a planted defect (record which).
- [ ] **C3 — G3 reference regenerated (Rev 1, R1; one full a01 sweep, not cheap).** `golden_check.py
  --base <BASE>` runs the base commit's `hiding_drivers.py` on the a01 store into
  `_golden_scratch/g3_reference/`. Record its wall-clock and the reference `aggregate.npz` key count
  (expected 41 = the 35 of the Aug-25 file + the six `01fe5701` columns; state the actual number).
- [ ] **C4 — G1 ladder gate.** Three sensor-ladder arms, `REPRODUCED` on JSON and npz.
- [ ] **C5 — G2 clue page.** Both Wave cells `REPRODUCED`; `hiding_shift` values equal; the fourteen
  published `hide_s` values span −1.9 … +0.3; `rabbit_avoidance` rerun equal.
- [ ] **C6 — G3 a01.** New-code aggregate `REPRODUCED` against the C3 reference; `univariate.csv`,
  `multivariate.csv`, `summary.json` byte-identical to the reference's; published values match at printed
  precision (candidate and Aug-25 CSV both give +1.6 / +1.7). If *food per step*, *starved* or *killed* do
  not match with the definitions in File Changes §6, **stop and report** the definition tried and both
  values — do not search for a definition that fits. `core/golden.py` unchanged (`git diff` empty).
- [ ] **C7 — Golden stamp written** only after C3–C6 all pass (`golden_check.py` exit 0).
- [ ] **C8 — First full cell on existing stores (Rev 1, R4: no smoke mode).** `make_population.py` for
  `basicq2`; `readings.py --stage check` on all cells (seconds each); then `--stage all --labels
  w2_lvl05_control` — four full sweeps of one 1 M-episode store; record the wall-clock (it sets the budget
  for the rest). `readings.json` has every reading or a NaN with a reason; accounting rows present. Then
  the full `basicq2` and `cmp10m` populations (the combined page's existing-store inputs and the study's
  yardstick), run serially.
- [ ] **C9 — Anchors on the real study doc.** `verdict.py --yardstick` runs on `cmp10m`; the anchor check
  passes on the study doc as of Revision 4 (`39420f2c`) or later; the post-hoc hv-control SD line is
  present and labelled.
- [ ] **C10 — First treated store (after collection starts).**
  `make_population.py --from-study-doc` for `hvsmell`; `readings.py --stage check --labels <first hv1ch>
  <first hv1chm>` reports layouts `single` / `sum`, finds channel 2 exactly 0 for every active animal in
  `hv1ch`, and records empirical class means near study §2.2's clipped means (predator/rabbit total
  0.68/0.50 single-channel, 1.30/1.05 matched). Only then `--stage all` on those two cells. This is the
  first time the new layouts touch real data; it is a check on the tooling, not a reading of results.
- [ ] **C11 — Timing.** Wall-clock of `collect_arm_data.py` on `w2_lvl05_control` before (the pre-change
  code's G2 run) and after the S6 accumulators; and of one full `readings.py` cell (C8). Record both.

**Speed.** Analysis-only change, no training path touched. The only hot-loop addition is S6 in
`collect_arm_data`; with `np.bincount` it should cost well under 10 %. A slowdown above 15 % on C11 is a
blocker to be discussed before merge.

## Open questions

- **Q1–Q4 — answered** by study Revisions 2–3 (A5). Kept here for the record: contrast C two-sided and
  descriptive; S4 by the one-sided lower bound above −3 pp; S2 within-world sextiles; S1 weighted least
  squares; S3 deciding row primary.
- **Q6 — answered** by study Revision 4 (`39420f2c`): S1's tested Δ uses the matched control reading.
- **Q5 (for the user).** The clue page's controlled-scene figure (D3) reads evaluation-probe runs, not
  trajectory stores; nothing in the hv study produces them and the study did not pre-register them.
  Re-doing D3 on the hv runs needs scene evaluations on their checkpoints — a separate compute job and
  a design decision, not tooling.

## What the combined hypervigilance page can draw from these outputs (not built here)

| Page section re-done | Reading | Tool | Populations |
|---|---|---|---|
| a01 Finding 2 (scent false alarm and its price) | S2 | `hiding_drivers.py` + `readings.py` | hvsmell, basicq2, l05body_w0000 |
| a01 aimed split | S3 | `aimed_response.py` | same |
| clue page A3 (hiding and distance, causal and current) | P2, P2d, S5 | `collect_arm_data.py`, `rabbit_avoidance.py` | same |
| new: scent × injury | S1 | `readings.py` | same |
| new: study verdict, top-up list, level-06 context | §5.3 | `verdict.py` | hvsmell (+ cmp10m yardstick, basicq2 context) |
| clue page D3 (controlled scenes) | — | not store-based | Q5 |

## Hand-off

1. `plan-reviewer` re-checks Revision 1 before the user approves it.
2. `experiment-designer`: nothing outstanding (Q1–Q4 answered by study Revisions 2–3, Q6 by Revision 4).
3. `developer` implements; `code-reviewer` optional (no JAX; NumPy/statsmodels only).
4. `senior-developer` verifies against this plan.
5. `experiment-analyzer` reads results only after C7 (golden stamp) and C9 (yardstick) are ticked.

## Revision log

- **2026-10-01 — first draft** (senior-developer, commit `27d63da3`).
- **2026-10-01 — Revision 1** (senior-developer), after `plan-reviewer` NOT READY
  ([[plan_hypervigilance_analysis_tooling]], commits `62242241`, `92c7f2b8`). No code exists yet. Changes:
  G3 reference regenerated from the base commit's `hiding_drivers.py`, Aug-25 files kept for the
  printed-precision check only, C3 re-budgeted as one full sweep, `golden.py` untouched (R1); A5 rewritten
  against study Revisions 2–3, P0 marked satisfied, S4 "did not fall" = one-sided 95 % Welch lower bound
  above −3 pp at the deciding stage, C-sign classification added, tests for the S4 and absolute-sign bounds
  (R2); population resolution through a manifest JSON with a status column, new `make_population.py`,
  `_s42` + `_s42_r2` test (R3); smoke mode dropped instead of adding a block limit to golden-gated files,
  new `--stage check`, C8/C10 re-budgeted (R4); S1 matched control reading and
  `statistic_equals_intensity` (R5, A6; the designer registered the matched reference in study Revision 4,
  `39420f2c`, while this revision was being written, and the plan follows it); Revision 3 cited for the
  three primary-variant choices, deciding row primary in S3, S2 sextile cross-run assertion (R6); explicit
  absolute `LADDER_OUT_ROOT` and output-root guard with a test (R7); anchors copied verbatim from the study
  and restricted to its §5.2–§5.3 slice, `fit_glms(layout="single")` test (R8); `aimed_response.py`
  import path stated (R9); pytest via the project interpreter (R10); post-hoc hv-control seed SD printed
  beside the frozen yardstick (reviewer A1).
- **2026-10-01 — Revision 2** (developer, at the user's request, before any code), after the
  `plan-reviewer` re-check of Revision 1 (SOUND WITH CONCERNS, `8646c0ce`): status-column owner named
  and stale-status refusal (N1); two-tier golden stamp (N2); per-cell `checkpoint` / `store_root` and
  `--checkpoint-nearest` (N3); backtick-aware Launch Manifest parser (N4); serial-budget note (A5).
  See [Revision 2 amendments](#revision-2-amendments-n1n4).

## Implementation Report

> **Implemented by**: —
> **Date**: —

*(Filled by `developer`: what was done, deviations and why, checkpoint results with numbers, timing.)*

## Verification Report

> **Verified by**: —
> **Date**: —

| File | Change | Status | Notes |
|------|--------|:------:|-------|
| | | | |

**Conclusion**: —

## Feedback from plan-reviewer

*2026-10-01, on commit `27d63da3`, checked against the study doc as it stands after Revision 2
(`7ec62720`). Full report: [[plan_hypervigilance_analysis_tooling]]
(`docs/reviews/plan_hypervigilance_analysis_tooling.md`).*

**Verdict: NOT READY** — one Critical, five Moderate (R6 resolved by study Revision 3 `86ce3119` mid-review), three Low. The design (one `scent_spec` for
three layouts, refusing others; every new number in a new file; a reproduce-before-read gate) is
sound and the two-channel byte-identity argument holds. The block is in the gate's own reference.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Where | Issue (short) | Fix | Owner |
|---|---|---|---|---|---|
| R1 | 🔴 | A4 G3, §8, C3/C6/C7 | The a01 `aggregate.npz` reference (2026-08-25 14:39) predates commit `01fe5701` (20:41 the same day), which added `*_olf_ch1/ch2`, `*_olf_intensity`, `pred_detect_max/min`; `golden.py:130` counts a candidate-only key as MISSING, so G3 cannot pass for any current code, and C3's "cheap" old-vs-new fit `KeyError`s on the old code. The C7 stamp — which every population waits on — is therefore unreachable as written. | Regenerate the G3 reference with the base commit's `hiding_drivers.py` (one a01 sweep into the scratch dir), compare against that; keep the Aug-25 CSV only for the printed-precision check; never teach `golden.py` to ignore extra keys. | `senior-developer` |
| R2 | 🟡 | A5, P0, Q1, §7 | Revision 2 already carries N1/N2/N5; A5's S4 rule ("not established either way and \|Δ\| < 3 pp") differs from the registered one (one-sided 95 % Welch lower bound of Δ above −3 pp, at the deciding stage); the C-sign classification (\|C\| < 3 / ≤ −3 / ≥ +3 pp) is missing from `verdict.py`. | Rewrite A5 against Revision 2, mark P0 satisfied, add the C-sign reading and tests for the S4 bound and absolute-sign bound. | `senior-developer` |
| R3 | 🟡 | §6 population regex | A `_r2` relaunch (study §5.7) never matches and the failed run's dir does; also not run-agnostic. | Manifest JSON with a status column; refuse ambiguous seeds; test the `_s42` + `_s42_r2` case. | `senior-developer` |
| R4 | 🟡 | §6 `--max-blocks`, C8/C10 | `hiding_drivers.py` and `collect_arm_data.py` have no block limit and `scan.sweep` asserts full step counts; smoke mode has no implementation path. | List the shard-limit change (golden-gated files, default off) or drop smoke mode and re-budget C8/C10. | `senior-developer` |
| R5 | 🟡 | §6 S1; study S1 | In the control the statistic is orthogonal to strength; in the treated worlds it *is* strength, so S1's Δ (a tested outcome) compares identity × injury against identity × injury + strength × injury. Dropping the collinear intensity terms is right; the reference arm is not like-for-like. | Compute an S1 matched control reading (channel 1, channel 2 as covariate); write `statistic_equals_intensity` into `readings.json`; designer registers which reference S1 uses before C10. | `senior-developer` → `experiment-designer` |
| R6 | resolved | Q2–Q4 | Primary variants (S2 bins, S1 estimator, S3 row) had to be registered before the first treated store is read. **Study Revision 3 (`86ce3119`, pre-data) registers them**: population sextiles, weighted-LS slope, deciding row (same row = a01 reproduction). | Cite Revision 3 as the anchor source; anchor the three choices in `verdict.py`. | `senior-developer` |
| R7 | 🟡 | §6 sweeps, §8 | `_ladder.OUT_ROOT` defaults to the **live** `results/analysis/ladder` when `LADDER_OUT_ROOT` is unset; `<population>/ladderstyle` reads as a relative path. | Assert the root is set and under `results/analysis/hypervigilance/` before spawning; spell the absolute path. | `senior-developer` |
| R8–R10 | 🟢 | §7 anchors, §9 tests, §5, C2 | Anchor text `|Δ|` vs `\|Δ\|`; restrict anchors to §5.2–5.3 (the doc quotes superseded rules in its feedback sections); no test for `fit_glms(layout="single")`; `aimed_response.py`'s bare `hiding_drivers` import needs its dir on `sys.path`; C2 via the project interpreter. | wording / one test | `senior-developer` |

❓ Open: A1 the cmp10m yardstick's fairness for worlds with a different rabbit percept (print the hv
control arm's own seed SD beside it, labelled post hoc); A2 the extreme-row food/starved/killed
definitions; A3 the C01/C02 re-collection lands before `hvsmell` is swept; A4 S6 cost < 10 %.

**Cost of being wrong:** a lost day and a loosened golden gate (R1); a failed run read as a seed
(R3); a verdict map scored on a superseded S4 rule (R2). No raw-data loss; R7 is the only path to
losing re-derivable live aggregates.

**What flips it:** R1, R2, R3, R4, R7 in this plan; R5 registered by the designer before C10 (R6 already is).

*Reviewed by: plan-reviewer*

## Response to plan-reviewer

*senior-developer, 2026-10-01, Revision 1. Each finding and where it now lives.*

| # | Response | Where |
|---|---|---|
| R1 | Accepted. G3's reference is produced by the base commit's `hiding_drivers.py` on the a01 store (one full sweep into scratch); the new code's aggregate is compared with `golden.py` unchanged and the three CSV/JSON products with `cmp`. The Aug-25 files serve only the printed-precision check. C3 is now that sweep, not a "cheap" refit. | A4 G3 rows + paragraph; File Changes §8; C3, C6, C7 |
| R2 | Accepted. A5 rewritten against Revisions 2–3; P0 satisfied; S4 = one-sided 95 % Welch lower bound of Δ above −3 pp on the seed set of the stage that decided P1; C-sign classification (\|C\| < 3 / ≤ −3 / ≥ +3 pp) with the "no registered reading" fallback; hand-computed tests for the S4 bound and the absolute-sign bound. | A5; Precondition P0; §7; §9 `test_hv_verdict.py` |
| R3 | Accepted. `make_population.py` writes a manifest with a status column (from the study's Launch Manifest for hvsmell); `readings.py` reads `completed` cells only, refuses two completed candidates for one key, and keeps the anchored tag regex (with an optional `_r\d+` suffix) as a cross-check. Test covers `_s42` failed + `_s42_r2` completed, and both completed. | §6, §6b; §9 `test_hv_population.py` |
| R4 | Smoke mode dropped (and `--max-blocks` removed from `aimed_response.py`); no change to the golden-gated sweeps or `core/scan`. A cheap `--stage check` (config + first episodes shard) replaces the smoke look; C8/C10 are full-cell runs with recorded wall-clock. | §5, §6; C8, C10; §10 |
| R5 | Accepted. S1 matched control reading (channel 1 on the single-channel evidence scale, channel 2 as covariate, same estimator code); `statistic_equals_intensity` in every `readings.json`; study Revision 4 (`39420f2c`) registered the matched reference as deciding; `verdict.py` anchors that, reports the plain reference as descriptive, and flags disagreement. | A3, A6; §6 S1 (iii); §7; Q6 |
| R6 | Cited: Revision 3 is the anchor source for the S2 sextiles, the S1 weighted-least-squares slope and the S3 deciding row; all three anchored; S2 cut-point equality across runs of a world asserted. | A5; §5; §6 S2; §7 |
| R7 | Accepted. `--out-root` must resolve under `results/analysis/hypervigilance/`; the child env sets `LADDER_OUT_ROOT` explicitly to an absolute path under it and the driver refuses the live ladder root; same in `golden_check.py` under `_golden_scratch/`; tested. | §6 output-root guard; §8; §9 `test_hv_readings.py` |
| R8 | Anchors copied verbatim from the study, searched in the §5.2–§5.3 slice only; a test proves a quotation in a feedback section cannot satisfy an anchor; `fit_glms(layout="single")` test added. | §7; §9 `test_hiding_drivers_layout.py`, `test_hv_verdict.py` |
| R9 | `aimed_response.py` inserts its own directory and `core/` on `sys.path`; recorded in the map row. | §5; §10 |
| R10 | Fixed. | §9 header; C2 |
| A1 | The verdict prints the hv control world's own three-seed SD beside each frozen yardstick SD, labelled post hoc and never used by the rule. | §7 |
| A2 | Unchanged: mismatch on food/starved/killed is reported, not tuned. | C6 |
| A3 | `readings.py --stage check` refuses a cell whose store is missing, and C10 starts with the hvsmell population built from the study manifest, so a not-yet-collected C01/C02 store is refused rather than substituted. | §6; C10 |
| A4 | Measured at C11; > 15 % is a blocker. | C11 |

## Feedback from plan-reviewer — re-check of Revision 1

*2026-10-01, on commit `fac1964d`, against study Revision 4 (`39420f2c`). Full addendum:
[[plan_hypervigilance_analysis_tooling]] (`docs/reviews/plan_hypervigilance_analysis_tooling.md`, "Addendum").*

**Verdict: SOUND WITH CONCERNS.** R1, R2, R3, R4, R7, R8–R10 resolved and independently re-verified;
R5 registered (study §5.2 S1, inside the anchor slice); A1 addressed. The base commit is well-defined
(`hiding_drivers.py` unchanged since `5cadbfdb`, self-contained, runs standalone), the G3 comparison
exercises the changed `difference`-layout paths against a reference that contains none of them,
`summary.json` carries no path or timestamp, and the a01 run has exactly one store — the Aug-25
aggregate matches it 100 % on length and termination. No Critical remains.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

| # | Sev | Where | Issue (short) | Fix | Owner |
|---|---|---|---|---|---|
| N1 | 🟡 | §6b; study §3 | Nobody is named to flip the Launch Manifest's `running` → `completed`; `readings.py` reads `completed` only, so a stale table yields an empty/partial population. | Name the owner (the collecting session); `make_population.py` refuses a `running` row that has a final checkpoint and a store ("stale status") — never auto-promotes; test. | `senior-developer` · `experiment-designer` |
| N2 | 🟡 | §6 stamp hash list | `readings.py`/`make_population.py` are hashed, so every edit to the assembly script re-requires G1–G3 (≈ nine full 1 M-episode sweeps). | Two tiers: sweep-tier stamp over the sweep sources with cached candidate outputs; assembly-tier stamp over `readings.py`/`make_population.py` re-deriving the published values from the cache in seconds. | `senior-developer` |
| N3 | 🟡 | §6 `--checkpoint`; §6b; study §5.4 | Checkpoint numbers are per run (spec: `final` 10000046 / 10000021; late specs 8000033 vs 8000043), so a population-wide `--checkpoint N` cannot build the mandatory §5.4 time course. | `checkpoint` and `store_root` per cell in `population.json`; `make_population.py --checkpoint-nearest N`; `readings.py` reads it from the manifest. Test with 8000033 / 8000043. | `senior-developer` |
| N4 | 🟢 | §6b parser | Free-prose Log-path cells; a stray `|` mis-aligns rows silently. | Backtick-aware splitter; refuse a row with the wrong column count. | `senior-developer` |

❓ A5: the serial sweep budget (≈ 37 cells × four sweeps, one cell at a time) may be days; state the
estimate after C8 and ask the user about parallel cells if one cell exceeds about an hour.

**Cost of being wrong:** a finished wave sitting unread (N1); a nominal rather than real golden
guarantee (N2); a hand-edited time course reading the wrong store (N3). No training run, no raw data.

**What would make this SOUND:** N1–N3 in one text revision; N4 optional; N2 may be accepted knowingly.

*Reviewed by: plan-reviewer*
