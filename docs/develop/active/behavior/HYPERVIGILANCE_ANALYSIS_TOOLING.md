---
title: "Hypervigilance analysis tooling: smell readings for any odour layout, the scent × injury reading, and the pre-registered verdict rule"
topic: behavior
status: active
created: 2026-10-01
last_updated: 2026-10-01
---

# Hypervigilance analysis tooling

> **Status**: PLANNED (not implemented; awaiting `plan-reviewer`, then user approval)
> **Opened**: 2026-10-01
> **Author**: senior-developer
> **Related**: [[SINGLE_CHANNEL_SMELL_HYPERVIGILANCE]] (the study this serves; its §5.6 lists the tooling it needs, and both plan-reviewer passes at its end carry the findings N3/N4 and M3 this plan implements) · [[a01_hiding_drivers]] ("What makes this agent hide?", whose scent readings are re-done here) · the modulator-clues page `docs/experiments/active/modulator_clues/modulator_clues.html` ("Injury, Behaviour and the Modulator", whose Figure A3 hypervigilance reading is re-done here) · [[TRAJECTORY_COLLECTION_PIPELINE]] (where the stores come from) · `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (updated by this change)
> **Back-link owed:** the study doc's §5.6 should link here. That doc is owned by `experiment-designer`; this plan does not edit it (see Hand-off).

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
| S1 | scent × injury, no-predator exactly-one-rabbit episodes, first 25 steps | per-episode early bush share exists in `collect_arm_data`'s `<arm>_episodes.npz` (`bush_early`, `steps_early`, `inj0`, `n_pred`, `n_rab`); rabbit scent and M1 covariates exist in `hiding_drivers`'s `aggregate.npz` | **new post-processing**: join the two per-episode files by episode seed (both sorted by seed, same population — asserted equal), then quarter contrast + GLM. No new sweep. |
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
| G3 a01 page | `hiding_drivers` aggregate on the a01 store (the resting-bonus arm `20260810-185749_rppo_restprem_a01_n106`) | `results/analysis/hiding_drivers/<a01>/aggregate.npz` | golden.py REPRODUCED; fit-stage CSVs **byte-identical** to the pre-change script's fit on the same cache |
| G3 published values (printed precision) | computed from the G3 candidate + a new `aimed_response.py` sweep on the a01 store (same-row distances) | a01 doc Finding 2 and ranking table | univariate scent effect +1.6 pp/SD (rabbit), +1.7 (predator); extreme rows rabbit hides 14.9 % / 22.6 %, survived 193.3 / 175.6 steps; predator hides 29.7 % / 35.0 %, survived 88.9 / 115.4; aimed split +8.0 / +6.4 / **+23.1** pp, rabbit-near hiding 26.7 % → 49.8 %, time near rabbit 13.0 % vs 14.3 % |

The extreme-row columns *Food per step*, *Starved*, *Killed* are printed on the a01 page but their
producing code is not in the repo (`curves.py` computes only hiding and survival). The gate checks them
with the obvious definitions (below); a mismatch is **reported, not tuned** — see Checkpoint C6.

Existing results a01 cites were produced by `hiding_drivers.py` and archived scripts; the clue page's A3
by `collect_arm_data.py --manifest` → `a4_hypervigilance.py`, `rabbit_avoidance.py`. `d3_rabbit_scenes.py`
(clue page, controlled scenes) reads evaluation-probe histories, not trajectory stores; it has no smell
dependence and nothing here changes it (Q5).

### A5. Rule constants that must match the study text (§5.3, §5.2)

| Constant | Value | Where in the study |
|---|---|---|
| P1 predicted sign / minimum | + / 3 pp | §5.3 outcomes table |
| P2 predicted sign / minimum | + / 2 pp | same |
| P2d predicted sign / minimum | − / 1 pp; decides nothing alone | same |
| S1 predicted sign / minimum | + / 2 pp per nat | same |
| Stage 1 | 3 v 3, complete separation in predicted direction (one-sided exact p = 0.05) and \|Δ\| ≥ minimum; anything else → stage 2 | §5.3 Stage 1 |
| Stage 2 | 5 v 5, one-sided Mann–Whitney U ≤ 4 and \|Δ\| ≥ min → established; one-sided 95 % Welch bound of Δ on the predicted side short of the minimum, or U ≤ 4 the other way → refuted; else not established | §5.3 Stage 2 (+ N5 wording) |
| Contrast C (single-channel − matched) | **two-sided, descriptive**; 5 v 5 two-sided U ≤ 2 reported; never "established" at stage 1 | **user instruction 2026-10-01; plan-reviewer N1 — not yet in the study text** |
| S4 "unchanged" | predator proximity effect Δ not established either way **and** \|Δ\| < 3 pp | §5.2 S4 (N2(b)/(c) propose a revision — not yet in the text) |
| S3 groups | rabbit-like LLR < 0, predator-like LLR ≥ +0.67 (= 2/3 nat: control `x1−x2 ≥ 0.3`, single `x1 ≥ 0.9`, matched `x1+x2 ≥ 1.63`) | §5.2 S3 |
| S1 window | first 25 chosen steps | §5.2 S1 |

The rows in bold are the reason for **precondition P0** below: the verdict script anchors every
constant to the study text, and the contrast-C rule has no text to anchor to until the designer folds
plan-review N1 (and N2, N5) into §5.3.

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
     studies/hypervigilance/readings.py (NEW) — resolves a named population, runs the four sweeps
     (subprocess, guarded cache), assembles readings.json per run (P1…S6 + data accounting)
                          │
     studies/hypervigilance/verdict.py (NEW) — §5.3 over readings.json of a population;
     anchors its constants to the study text; needs the seed yardstick first
     studies/hypervigilance/golden_check.py (NEW) — G1–G3; on pass writes a stamp that
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

### Precondition P0 (blocks only Checkpoint C9)

`experiment-designer` folds plan-review **N1** (contrast C two-sided and descriptive), **N2** (S4 read
with sign on contrast B; "unchanged" defined by a bound) and **N5** (refutation bound "on the predicted
side") into study §5.3/§5.2 as a dated revision. `verdict.py` is implemented and unit-tested against a
fixture copy of the text meanwhile; its anchor list is finalised against the revised text, and C9 (the
anchor check on the real study doc passes) cannot be ticked before that revision lands. If the designer
decides differently from the user's "C two-sided descriptive", the discrepancy goes back to the user;
the developer does not pick.

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

- CLI: `--run`, `--store-root` (nargs+, required), `--checkpoint`, `--out` (required), `--max-blocks`.
- Layout from `core/env.slot_layout` + `scent_spec` on the run's saved config; stores via
  `hiding_drivers.find_stores`; the sweep via `core/store.open_run` + `core/scan.sweep` (the guarded
  scan: seed contiguity, shard alignment, reset-row handling, `fr.prev`).
- Episodes: exactly one predator and one rabbit (`animal_active`). Rabbit statistic from
  `animal_property_sampled` → LLR. Groups: `RABBIT_LIKE_BELOW_NATS = 0.0`,
  `PREDATOR_LIKE_AT_NATS = 2/3` (study "≥ +0.67"; 2/3 is the value that maps exactly to a01's `0.3` in the
  control: `0.3 × 0.4/0.18 = 2/3`). The statistic-space thresholds actually used are written to the output.
- Per chosen step: state = predator within 2 (Chebyshev, live) → "predator near"; else rabbit within 2 →
  "rabbit near"; else "nothing near" (a01 precedence). Computed **twice in the one sweep**: distances on
  the same row (`same_row`, a01's convention, used by the golden) and on the deciding row (`prev_row`,
  study §5 convention).
- Output JSON: spec, thresholds (nats and statistic space), group episode counts, per group × state:
  steps, bush steps, bush share; per-state differences (pp); time share per state; `NEAR = 2`;
  run/stores/seed range; data accounting (episodes used / available with the filter named).

#### 6. `scripts/analysis/studies/hypervigilance/readings.py` — NEW (three levels deep: `ROOT` walks four `..`)

Per-run assembly over a **named population**; run-agnostic (any run whose store and saved config exist).

- `--population {hvsmell, basicq2, l05body_w0000, cmp10m, a01}`, `--labels` (subset), `--checkpoint`,
  `--stage {sweep, assemble, all}`, `--reuse-cache`, `--max-blocks N` (smoke: writes under
  `results/analysis/hypervigilance/_smoke/`, never the real root).
- **Population resolution** (one function per population, returning cells
  `{label, run, stores, world, agent, seed, level, wave}`; refuses a missing or ambiguous match):
  - `hvsmell`: run dirs matching exactly
    `^\d{8}-\d{6}_rppo_(hv1ch|hv1chm|hv2ch)_(t1none|t16quad)_s(\d+)$` (anchored, so `hv1ch` never matches
    `hv1chm` — plan-review N4) plus the two seed-42 controls
    `20260927-053057_rppo_l05body_w0000_t1none_s42` / `20260927-053059_rppo_l05body_w0000_t16quad_s42`
    as world `hv2ch`; stores under `results/trajectories_hvsmell/`.
  - `basicq2`: Waves 1 and 2, levels 03–06, both agents, stores in `results/trajectories_basicq2_w{1,2}/`
    (levels 04–06 must resolve to the same store dirs as `results/analysis/basicq2_integrated/_manifest.json`
    — asserted).
  - `l05body_w0000`: the two older seed-42 stores in `results/trajectories_l05body/` (study §5.5: numerics
    comparison only).
  - `cmp10m`: the five `rppo_cmp10m_gaenorm_s42…s46` stores in `results/trajectories_nmngae/` (seed yardstick).
  - `a01`: the a01 run and its store (golden use).
- **Ground-truth checks per cell** (fail = refuse that cell): the saved config's top-level `seed` equals
  the tag's seed; the inferred layout matches the world (`hv2ch`, `basicq2`, `cmp10m`, `a01` →
  `difference`; `hv1ch` → `single`; `hv1chm` → `sum`); and **from the store itself**, on the first
  episodes shard: every `animal_property_sampled` channel outside the spec's emitting set is exactly 0
  for active animals, and the per-class empirical means of the emitting channels are recorded (verifies
  the store came from the world the config says).
- **Golden stamp gate:** refuses every population except `a01` unless
  `results/analysis/hypervigilance/_golden_pass.json` exists and its recorded sha256 of each analysis
  source (`core/env.py`, `core/scan.py`, `core/store.py`, `hiding_drivers.py`, `collect_arm_data.py`,
  `ladder/_ladder.py`, `rabbit_avoidance.py`, `aimed_response.py`, `readings.py`) equals the current file.
  Any edit to those files re-requires the golden check.
- **Sweeps** (stage `sweep`; `subprocess.run([sys.executable, …], cwd=ROOT, check=True)`, one cell at a
  time — the NAS is the bottleneck): `hiding_drivers.py --out <cell>/glm`; `collect_arm_data.py
  --manifest <cell manifest>` with `LADDER_OUT_ROOT=<population>/ladderstyle`; `rabbit_avoidance.py`;
  `aimed_response.py`. Output root `results/analysis/hypervigilance/<population>/<label>/`
  (`/ckpt_<N>/` when `--checkpoint` is given, for the §5.4 time course).
  **Stale-cache guard** (the trap `run_hiding_drivers.py` documents): refuse if any output exists unless
  `--reuse-cache`; with it, require each JSON's recorded `run`/`stores` to equal the requested ones and
  `aggregate.npz["seed"]` to equal `<label>_episodes.npz["seed"]`.
- **Assembly** (stage `assemble`) → `<label>/readings.json`:
  - `survival`: mean steps, termination shares (from the ladder JSON).
  - `P1` = `proximity_effect(rd_bush, rd_tot)`; `P2` = `hiding_shift(rd)` =
    `proximity_effect(..., (3,)) − proximity_effect(..., (0,))` (re-stated one-liner, identical to
    `a4_hypervigilance.py`); `P2d` = `rabbit_avoidance` `start.near_share_shift`.
  - `S1` (no predator, exactly one rabbit): episodes joined by seed (assert equal seed arrays);
    early bush share = `bush_early / steps_early`; LLR = `spec.llr(rab_predatorness)`.
    (i) quarter contrast: within start-injury quarters 0 and 3 (edges 25/50/75), weighted least-squares
    slope of the share on LLR (weights `steps_early`) × 100 → pp per nat; contrast = q3 − q0; per-quarter
    slopes and episode counts reported. (ii) GLM: `quasi_binomial_fit` with `Y = bush_early`,
    `L = steps_early`, regressors LLR, start injury, LLR × start injury, start nutrition, bushes, rocks,
    food, ambush predators, spawn distance to bush; product term reported as
    `coef × p̄(1−p̄) × 100 × 100` (pp per nat per 100 injury) with its SE. Repeated on
    one-predator-one-rabbit episodes (sensitivity). Estimator choice for (i): Q3.
  - `S2`: univariate rabbit (and predator) scent from `glm/univariate.csv`: pp per unit, **÷ k → pp per
    nat**, pp per SD, n; M3 row(s) from `multivariate.csv`; extreme rows on exactly-one-rabbit episodes
    (and exactly-one-predator for the predator table) — *hides* = pooled `bush_steps / n_steps`, *food
    per step* = `n_ate / n_steps`, *starved* / *killed* = termination shares, *survived* = mean
    `n_steps` — for (a) within-world population sextiles of the statistic (defined in every world) and
    (b) in the `difference` layout only, a01's fixed bins `< −0.2`, `≥ 0.6`; control matched reading
    (`difference` only): `quasi_binomial_fit` on exactly-one-rabbit episodes with `rab_olf_ch1` and
    `rab_olf_ch2`, reporting the channel-1 coefficient per unit and per SD.
  - `S3`: the `aimed_response.json` summary (both distance rows; group sizes).
  - `S4`: `proximity_effect(pd_bush, pd_tot)`, killed-by-predator share, confusion index = P1 ÷ S4.
  - `S5`: `hiding_shift(rdc)`; `rabbit_avoidance` `current.near_share_shift`.
  - `S6`: rabbit-on-square steps and share of rabbit-episode steps; P1/P2 without distance 0; P1/P2
    predator-free (start injury) and P2 predator-free on current injury.
  - Every NaN carries a `reason` ("bin below 1000 steps", "no rabbit slots", "deterministic smell: k
    undefined"); study §5.7 says such a reading is reported as not computable, never substituted.
  - `accounting`: a list of `{what, used, total, pct, reason}` rows per reading (episodes and steps),
    emitted by code — the artifact guide's data-accounting requirement is met at the source.
  - `code`: git HEAD, dirty flag, and the source sha256s.

#### 7. `scripts/analysis/studies/hypervigilance/verdict.py` — NEW

- Modes: `--yardstick` (population `cmp10m`: between-seed SD of P1, P2, P2d, S1, S2-univariate per nat →
  `results/analysis/hypervigilance/cmp10m/yardstick.json`, plus the power table re-stated with those SDs);
  default (population `hvsmell` → `results/analysis/hypervigilance/hvsmell/verdict.{json,md}`).
  The default mode **refuses** unless `yardstick.json` exists (study §5.3: the yardstick is frozen before
  any hv run is read).
- `RULES` constant block (A5) and `DOC_ANCHORS`: for each constant, the exact study sentence/table row
  it comes from. On start the script reads the study doc, collapses every whitespace run to one space
  (the study wraps lines mid-sentence), and refuses with the list of missing anchors if any is absent.
  It also imports `aimed_response.PREDATOR_LIKE_AT_NATS` and `readings`'s early window and anchors them.
- Per agent (ordinary, modulated — never pooled) × contrast × outcome (P1, P2, P2d, S1, S4, survival):
  per-seed values, world means, between-seed SDs, paired per-seed differences (secondary), Δ, and:
  - 3 v 3 → stage 1; not established → listed in `top_up_required` with the two worlds and seeds 45/46.
  - 5 v 5 → stage 2 (U with ties counted ½; one-sided Welch bound with Welch–Satterthwaite df).
  - Any other seed count, or a NaN seed value → `not evaluable under §5.3` (no invented rule).
  - Contrast C → descriptive fields only (Δ, sign, two-sided U ≤ 2 flag at 5 v 5); never "established".
  - P2d decides nothing alone; `H1b` flag = P2 established and P2d Δ of the predicted sign.
  - Survival: Δ with a 95 % Welch interval, no decision.
  - Verdict-map row per agent × contrast (A, B) from P1/P2 finals and the S4 condition, using the
    study's six row labels verbatim; absolute-sign reading of P2 (treated-world mean, one-sided 95 %
    lower bound, t with n−1 df).
  - S6 re-runs of P1/P2 through the same rule, reported beside the primary (study S6).
- Descriptive context (study §5.5): within-wave level 06 minus level 05 P1 and P2 per agent, from the
  `basicq2` readings, printed beside the contrasts; never pooled, never decided.
- `power(effect, sd, n_draws, rng_seed)` Monte-Carlo of the two-stage rule (used by the test and by
  the yardstick re-statement).

#### 8. `scripts/analysis/studies/hypervigilance/golden_check.py` — NEW

Runs G1–G3 (A4) into `results/analysis/hypervigilance/_golden_scratch/` (never a live output root; the
golden README forbids pointing a port at the live root), shells out to `core/golden.py` for every
file comparison and requires `REPRODUCED`, then checks the published values of A4 at their printed
precision. The pre-change fit for the CSV byte-identity check runs from
`git show <base-commit>:scripts/analysis/hiding_drivers.py` written to the scratch dir, on the **same**
`aggregate.npz`. Prints a table of every check; on all-pass writes `_golden_pass.json` (date, HEAD,
source sha256s, per-check result). Any failure: no stamp, non-zero exit.

#### 9. Tests (new or extended, `tests/analysis/`)

| File | Tests (each must fail on the pre-change code or on a planted defect) |
|---|---|
| `test_core_env.py` (extend) | the three study layouts (literal dicts copied from study §2.1 / Appendix B) → `layout`, `channels`, `midpoint` (0 / 0.6 / 1.2), `llr_scale` (0.4/0.18, 0.2/0.09, 0.28/0.18 exact; 2.22 / 2.22 / 1.56 at 2 dp); `statistic` on a small array is bit-identical to `x[...,a] − x[...,b]` in the difference layout; refusals: equal classes (existing test kept), two channels both predator-leaning but unequal (ratio informative), rabbit stronger on the only channel, three emitting channels with mixed signs, unequal class spreads, missing `properties_std`; `smell_channels` returns `(1, 2)` on the control and raises on single and sum. **Fails today**: `scent_spec` does not exist. |
| `test_hv_sensitivity.py` (new) | `accumulate_sensitivity` known answer on hand-built rows: distance-0 rows counted per quarter and absent from `rd_no0`; a row with a predator at distance 2 absent from `rdpf`, at distance 3 present, with no predator (inf) present; `aimed_response`'s state classifier gives predator-near precedence; statistic thresholds from 2/3 nat = 0.3 / 0.9 / 1.6286 for the three layouts. |
| `test_hv_readings.py` (new) | S1 quarter contrast recovers a planted slope difference (synthetic episodes, q3 slope 5 pp/nat, q0 1 pp/nat → 4 ± 0.3); GLM product term has the planted sign; the seed-join assertion fires on misaligned arrays; population regex: `…_rppo_hv1chm_t1none_s42` is **not** matched as world `hv1ch`; world/layout mismatch refused; golden-stamp gate refuses on a changed source hash. |
| `test_hv_verdict.py` (new) | stage 1: complete separation with \|Δ\| ≥ min → established; separation with \|Δ\| < min → top-up; one overlapping seed → top-up; stage 2: U matches `scipy.stats.mannwhitneyu` on random data; U ≤ 4 + min → established; Welch bound short of min → refuted; U ≤ 4 in the opposite direction → refuted; predicted-negative outcome (P2d) uses the lower side; contrast C is never "established"; 4 v 4 → "not evaluable"; anchor check refuses a `tmp_path` copy of the study doc with "**3 pp**" changed to "**2 pp**"; `power()` reproduces the study's power table rows within ±3 points at 40,000 draws, fixed seed: P1 +3 pp / SD 1.4 → 59 % established overall, 5 % wrongly refuted; P1 0 → < 1 % false positive, 92 % correctly refuted; P2 +2 pp / SD 1.5 → 51 %; P2 0 / SD 2.67 → 7 % false positive, 27 % correctly refuted. (That table was computed by the designer and independently reproduced by plan-reviewer; matching it is evidence the implementation is the rule the study registered, not a re-derivation of this code.) |

Unit tests must not read the 1 M-episode stores; the store-scale checks are the golden check and the
checkpoints below.

#### 10. Docs updated in the same change

- `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` (Maintenance Contract — files added under `scripts/`):
  - **new rows**: `scripts/analysis/aimed_response.py` (one level deep, cwd-relative like
    `rabbit_avoidance.py`; imports `hiding_drivers` and `core/{env,store,scan}`; subprocess callee of
    `readings.py`; unit-tested by `test_hv_sensitivity.py`); `scripts/analysis/studies/hypervigilance/`
    `readings.py`, `verdict.py`, `golden_check.py` (**three** levels deep, `ROOT` walks four `..` — the §0
    depth hazard; `readings.py` subprocess-invokes `hiding_drivers.py`, `collect_arm_data.py`,
    `rabbit_avoidance.py`, `aimed_response.py` with `sys.executable`; `verdict.py` reads the study doc and
    imports `readings`/`aimed_response` constants; `golden_check.py` shells out to `core/golden.py` and
    `git show`); the three new test files as callers.
  - **amended rows**: `core/env.py` (adds `scent_spec`; `smell_channels` is now a two-channel-only wrapper;
    new importers `hiding_drivers.py`, `figures/_common.py`, `aimed_response.py`, `readings.py`);
    `hiding_drivers.py` (the row at line 285 says it "imports only numpy/pyarrow/yaml/statsmodels/scipy" —
    it now `sys.path`-inserts `scripts/analysis/core` and imports `env`; `aggregate` takes a `ScentSpec`;
    `fit_glms` requires `layout=`; new module-level `quasi_binomial_fit`; writes `scent.json`; new
    subprocess caller `readings.py`, new importer `aimed_response.py`); `collect_arm_data.py` (writes
    `<arm>_sensitivity.json`; uses `scent_spec`; new subprocess caller `readings.py`);
    `rabbit_avoidance.py` (new subprocess caller `readings.py`); and the "Last updated" line.
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
- [ ] **C2 — Unit tests.** `pytest tests/analysis/test_core_env.py tests/analysis/test_hv_*.py` green;
  the full `tests/analysis/` suite still green. Each new test was seen to fail once against the pre-change
  code or a planted defect (record which).
- [ ] **C3 — CSV identity from the lifted fit (cheap, no sweep).** Run the fit stage of the old and new
  `hiding_drivers.py` on a copy of the existing a01 `aggregate.npz`: `univariate.csv` and
  `multivariate.csv` byte-identical (`cmp`).
- [ ] **C4 — G1 ladder gate.** Three sensor-ladder arms, `REPRODUCED` on JSON and npz.
- [ ] **C5 — G2 clue page.** Both Wave cells `REPRODUCED`; `hiding_shift` values equal; the fourteen
  published `hide_s` values span −1.9 … +0.3; `rabbit_avoidance` rerun equal.
- [ ] **C6 — G3 a01.** Aggregate `REPRODUCED`; published values match at printed precision. If *food per
  step*, *starved* or *killed* do not match with the definitions in File Changes §6, **stop and report**
  the definition tried and both values — do not search for a definition that fits.
- [ ] **C7 — Golden stamp written** only after C4–C6 all pass (`golden_check.py` exit 0).
- [ ] **C8 — Smoke on existing stores.** `readings.py --population basicq2 --labels w2_lvl05_control
  --max-blocks 2` completes; `readings.json` has every reading or a NaN with a reason; accounting rows
  present. Then the full `basicq2` and `cmp10m` populations (these are the combined page's existing-store
  inputs and the study's yardstick).
- [ ] **C9 — Anchors on the real study doc** (after precondition P0): `verdict.py --yardstick` runs on
  `cmp10m`; the anchor check passes on the revised study doc.
- [ ] **C10 — First treated store (after collection starts).** On the first `hv1ch` and the first
  `hv1chm` store: `readings.py --population hvsmell --labels <one each> --max-blocks 2` reports layouts
  `single` / `sum`, the store-side check finds channel 2 exactly 0 for every active animal in `hv1ch`,
  and the recorded empirical class means sit near study §2.2's clipped means (predator/rabbit total
  0.68/0.50 single-channel, 1.30/1.05 matched). This is the first time the new layouts touch real data;
  it is a check on the tooling, not a reading of results.
- [ ] **C11 — Timing.** Wall-clock of `collect_arm_data.py` on `w2_lvl05_control` before (from the G2
  run of the pre-change code, or a separate run) and after the S6 accumulators; and of one full
  `readings.py` cell. Record both.

**Speed.** Analysis-only change, no training path touched. The only hot-loop addition is S6 in
`collect_arm_data`; with `np.bincount` it should cost well under 10 %. A slowdown above 15 % on C11 is a
blocker to be discussed before merge.

## Open questions (for `experiment-designer`; the tooling computes every variant, so none blocks implementation except P0)

- **Q1 (= P0).** Fold plan-review N1/N2/N5 into study §5.3 (contrast C two-sided and descriptive; S4 read
  with sign on contrast B and "unchanged" defined by a bound; refutation bound on the predicted side).
- **Q2.** S2 "bottom vs top sixth" in the treated worlds: a01's sixths were fixed bins of the scent
  *range*, which cannot be carried to the single-channel world (its range tops out below a01's top bin
  on the evidence scale). Tooling reports within-world population sextiles everywhere, plus a01's bins
  in the control. Which is registered?
- **Q3.** S1 quarter-contrast slope: tooling uses a weighted least-squares slope of the early bush share
  on scent evidence (direct percentage points). The alternative is the quasi-binomial slope linearised at
  each quarter's own hiding rate, which lets a rate difference between quarters leak into the contrast.
  Confirm.
- **Q4.** S3 distances: same row (a01, needed for the golden) or deciding row (study §5 preamble)?
  Tooling reports both.
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

1. `plan-reviewer` reviews this plan before the user approves it.
2. `experiment-designer`: P0 (study Revision 2 with N1/N2/N5), Q2–Q4, and the back-link from study §5.6
   to this plan.
3. `developer` implements; `code-reviewer` optional (no JAX; NumPy/statsmodels only).
4. `senior-developer` verifies against this plan.
5. `experiment-analyzer` reads results only after C7 (golden stamp) and C9 (yardstick) are ticked.

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

**Verdict: NOT READY** — one Critical, six Moderate, three Low. The design (one `scent_spec` for
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
| R6 | 🟡 | Q2–Q4 | Primary variants (S2 bins, S1 estimator, S3 row) must be registered before the first treated store is read, or they are post hoc. | Gate C10 on a dated study revision naming them; anchor the choice in `verdict.py`. | `experiment-designer` |
| R7 | 🟡 | §6 sweeps, §8 | `_ladder.OUT_ROOT` defaults to the **live** `results/analysis/ladder` when `LADDER_OUT_ROOT` is unset; `<population>/ladderstyle` reads as a relative path. | Assert the root is set and under `results/analysis/hypervigilance/` before spawning; spell the absolute path. | `senior-developer` |
| R8–R10 | 🟢 | §7 anchors, §9 tests, §5, C2 | Anchor text `|Δ|` vs `\|Δ\|`; restrict anchors to §5.2–5.3 (the doc quotes superseded rules in its feedback sections); no test for `fit_glms(layout="single")`; `aimed_response.py`'s bare `hiding_drivers` import needs its dir on `sys.path`; C2 via the project interpreter. | wording / one test | `senior-developer` |

❓ Open: A1 the cmp10m yardstick's fairness for worlds with a different rabbit percept (print the hv
control arm's own seed SD beside it, labelled post hoc); A2 the extreme-row food/starved/killed
definitions; A3 the C01/C02 re-collection lands before `hvsmell` is swept; A4 S6 cost < 10 %.

**Cost of being wrong:** a lost day and a loosened golden gate (R1); a failed run read as a seed
(R3); a verdict map scored on a superseded S4 rule (R2). No raw-data loss; R7 is the only path to
losing re-derivable live aggregates.

**What flips it:** R1, R2, R3, R4, R7 in this plan; R5–R6 registered by the designer before C10.

*Reviewed by: plan-reviewer*
