# Plan review — "Interactions between internal states" simulation study (level 05)

## Verdict

**NOT READY.** One Critical finding, nine Moderate, four Low, six open assumptions.

**What the plan is, in plain language.** Before training any agent on new variants of the
campfire world (level 05), the project wants to know which body-rule settings make the *best*
action depend on a combination of body states (hungry *and* injured, cold *and* injured) rather
than on one state alone — because that is where a body-conditioned network ("modulator") should
matter. The plan builds a small numpy copy of the body rules, a five-place version of the map, and
an ideal planner (value iteration) that says what is best from every body state; two numbers per
world — how evenly the activities split ("need balance") and how much the best activity needs
more than one variable ("interaction share") — then pick the settings to train.

**Why it is not ready.** The planner's answer depends first of all on how far ahead it looks (the
discount factor). The plan does not state it; the code uses 0.99 and calls it the training
recipe's, but all 57 recurrent-PPO configs and a finished level-05 run's saved config use 0.95.
That is a 100-step horizon versus a 20-step one, and the settings being swept — slow healing,
longer trips — are exactly what a horizon changes. Fix that in the plan and the code and the
verdict moves to SOUND WITH CONCERNS, with the Moderate items to settle before any number is read.

Object reviewed: `docs/experiments/active/internal_state_interactions/STUDY_PLAN.md` plus the
scripts present at review time in `scripts/analysis/studies/internal_state_interactions/`
(`bodysim.py`, `planner.py`, `validate.py`, `sweep.py`). Passes run: 1–6 and 8; pass 7 skipped
(no analysis verdict exists yet).

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | plan §What is computed (item 3, no discount stated); `planner.py:17-18,44` (γ = 0.99, "the recurrent-PPO recipe's") | Every rPPO config (`grep '^\s*gamma:' configs/models/recurrent_ppo/` → 57 × 0.95) and the saved config of a finished level-05 run (`results/JAX_RecurrentPPO/20260922-182534_rppo_bq2cover_lvl05_t1none_s42/models/config.yaml:460`) use **0.95**. Under the drive-difference reward the discounted return is `d₀ − (1−γ) Σ γᵗ d_{t+1}`, i.e. the planner minimises the discounted average of future drive level, so γ sets the horizon over which "best" is judged (≈100 steps at 0.99, ≈20 at 0.95). Healing in the open (0.2/step ⇒ 500 steps for a full wound), trips of 5–9 steps, and B5's slow-heal runway are horizon-sensitive, so the label map — the study's only output — is computed for an agent the project does not train. | Pre-register γ in the plan; read it from the training agent config (not typed); headline at 0.95; 0.99 as a sensitivity appendix; report any verdict that flips between the two. Also state that γ < 1 is load-bearing: at γ = 1 the return telescopes to `d₀ − d_end` (−100 on death), every surviving path to the same end state ties, and "best activity" is pure tie-breaking. | experiment-designer |
| M1 | 🟡 | `planner.py:133` (`argmax` takes the first of exact ties); `planner.py:47-49` grid (injury step 4 units); `CATEGORY` maps `idle_O` → "wait", `rest_O` → "rest in the open" | At injury 0 (the whole I = 0 slice, 1/26 of start states) idle and rest are exactly identical, so the label is "wait" by insertion order. Elsewhere rest_O and idle_O differ by 0.2 injury per step, below the trilinear-interpolation error on a 4-unit grid, so the wait/rest split is partly interpolation noise. The two are different categories, so the split reads as injury dependence and can move the share by up to ~4 pp against a 5-pp threshold. | (a) Indifference margin ε: a state is "predicted correctly" if the predicted category's value is within ε of the best; report the ε-tied share. (b) Merge "wait" into "rest in the open" unless B3 is on (where idling to save food is the point). (c) Solve the baseline at two grid resolutions and publish the difference as the metric's noise floor; the +5 pp must exceed it. | experiment-designer |
| M2 | 🟡 | plan §What is computed item 4; `planner.py:165-167` | `1 − max single-variable accuracy` is bounded above by `1 − largest class share`. A setting that merely rebalances which activity wins can raise it without any combination dependence. `pair_accuracy` is already computed (`planner.py:158-164`). | Report and rank by the pair-over-single gain (`max pair acc − max single acc`) and the three-way share; keep interaction share as a secondary number. | experiment-designer |
| M3 | 🟡 | plan §What is simulated ("reduced to five places"), §Reading rule ("omits predators") | Level 05 has 2–12 hiding predators (15–45 damage on contact, per `recovery_in_bush_tuning/f06_env_validation.py`'s note) and 0–2 pouncing predators; bushes block animals. Moving is dangerous and cover is safe in the real world; the reduced world charges a trip only cold and −1 food per step. The bias is one-directional: cover is under-valued, eat / warm-up over-valued, so the "no activity > 80 %" clause passes more easily in the simulator than it would for a real agent — and in the direction the current "hide when injured" habit would exploit. | Add a per-travel-step damage hazard (probability × damage from the level-05 ambush entry, calibrated from the wave-1 level-05 trajectories: damage events per moving step vs per cover step) as one sweep axis, and say whether verdicts survive it. If not added, state the bias direction inside the reading rule. | experiment-designer |
| M4 | 🟡 | plan §What is simulated ("ignores depletion") | Not neutral: a food item gives 12 bites (`configs/environment/default.yaml:34`), so refilling 0 → 100 needs 20+ bites across 2+ items on a map with 1–4 items. The planner's food place gives unlimited bites, so "eat" is cheaper than reality and A4 "scarcer food" is modelled only as a longer trip. | Cap bites per visit (macro "eat up to 12, then the next item is a trip away"), or state the direction of the bias (hunger under-weighted). | experiment-designer |
| M5 | 🟡 | plan §Reading rule; `sweep.py:70` (both layouts solved) | Unfixed before data: (a) which layout is compared — warm bush present, absent, or the 43/57 mixture; (b) whether "rest in cover (warm)" counts as "rest in a bush" for the ≥ 10 % clause and whether "wait" is an activity for the 80 % clause; (c) whether baseline and setting are compared at matched layout. | Write the exact category list and the exact comparison into the reading rule now. | experiment-designer |
| M6 | 🟡 | plan §What is computed (two numbers per world) | No survival number. The planner knows deaths; a world where the ideal policy cannot survive from many starts (plausible at B3 cost 2, trip-to-food 9) would be recommended on interaction share alone, and a training run there measures lethality, not interaction. This is also the honest link to the project's survival-step rule: using the reward to define the planner is fine (it is the agent's objective), but any cross-world comparison must be in survival terms. | Report per world: share of start states from which the optimal policy survives, and the cause of death where it does not. Add a survival floor to the reading rule. | experiment-designer |
| M7 | 🟡 | `validate.py` (good: real `update_body` / `calculate_drive`, resolved level-05 params, refuses on constant mismatch); `sweep.py`, `s1_single_rules.py` (no gate) | Validation is non-circular but nothing requires it: the sweep and figures run without a passing validation JSON. The `--mechanics all` point (`validate.py:40-45`) is one parameter set; the sweep visits B3 c up to 2.0, B2 s up to 0.1, B4 g up to 2 and never `full` shortfall / `both` mode. | `build_page` refuses unless a validation JSON with `pass: true` exists for the same source root and commit; validate at the sweep's extreme values (and the modes the sweep uses). Run all of it with `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`. | developer |
| M8 | 🟡 | plan §Files | A new directory under `scripts/analysis/studies/` must get rows in `docs/environment/SCRIPTS_DEPENDENCY_MAP.md` in the same change (sibling studies have rows at lines 59–61, 135–141). Not mentioned. | Add the rows with the scripts. | developer |
| M9 | 🟡 | plan §What is simulated ("4 by default"); `planner.py:13,42`, `sweep.py:51` (3; "measured on 300 real level-05 resets, see the study plan") | Plan and code disagree, and the measurement the code cites is not in the plan. A4/A5 sweeps start from this number. | Record the measurement (script, per-place mean/median over N resets) in the plan, or fix 4. Same for the 43 % warm-bush figure in `sweep.py:5`. | experiment-designer |
| L1 | 🟢 | plan (+8.5), `planner.py:29` (+8.8), `validate.py:83` (8.5) | Three values for the warm-ring cell. | One number with its derivation (mechanics plan ring equilibrium +5.94 ⇒ cell ≈ 8.9 at k_ex 0.04 / k_loss 0.02). | experiment-designer |
| L2 | 🟢 | `planner.py:86` | The arrival step of a trip uses the travel cell (−30); in the env the post-move cell's temperature applies on the arrival step (`core.py:158-166`). ≤ 2 °C for one step. | Use the destination cell on the last travel step, or say so. | developer |
| L3 | 🟢 | plan §Question ("A1 … A4 … A5") | The labels are defined nowhere else (repo grep hits only this plan). | One-line definitions in the entry section (A1 = `thermal.metabolic_coupling`; A4 = food count / value; A5 = bush count). | experiment-designer |
| L4 | 🟢 | plan (no prior-art section) | Not cited: `scripts/analysis/studies/recovery_in_bush_tuning/recovery_math.py` + `f06_env_validation.py` (a body-recurrence transcription validated by driving a stripped real world with an always-Rest policy) and the `internal_state_reward` study. | Cite; consider f06's stripped-world closed-loop run as a second validation through `jax_step` (multi-step), alongside the single-step one. | experiment-designer |

## Assumptions the plan rests on

| # | Assumption | Status |
|---|---|---|
| O1 | The level-05 agent can condition on all three body states. Satiation is observed directly; body temperature is observed (`thermal.body_temp_observable: true`); injury only through the interoceptive nociception kernel (τ 3, length 12), a lagged filtered copy (`default.yaml:462` `injury_observable: false`). | ❓ unverified whether the lag matters for combination-dependent choices |
| O2 | Trip lengths (3) and warm-bush probability (43 %) are measured on real resets. | ❓ claimed in code, not recorded anywhere |
| O3 | `bodysim.py`'s B1–B5 match what the developer lands. Source is Revision 3 of the mechanics plan; the page is blocked until `--mechanics all` validation passes. | verified-in-plan as a gate; interim sweep numbers must not be read |
| O4 | Measuring the policy over start states only is what matters. The modulator's advantage would be over all visited states; the real start position may be in a bush or on a ring. | ❓ stated scope, direction of effect unknown |
| O5 | 500-step truncation is ignorable (γ⁵⁰⁰ ≈ 0.0066 at 0.99; negligible at 0.95). | verified by arithmetic |
| O6 | Whatever trains level 05 resolves `extends:` as `load_env_config` does (the level-05 config cannot load raw). | ❓ not traced to the rPPO trainer's call site in this review |

## Checks that passed

- Survival-step rule: using the environment's reward to define the ideal planner is legitimate (it is the objective the trained agent optimises); no conflict, provided cross-world claims are made in survival terms (M6).
- No fallback defaults: `Body` hard-codes level-05 values, but `validate.py:57-72` refuses on any mismatch with the resolved params and on the accel-0 / satiation-equals-nutrition assumptions — acceptable for an analysis tool once validation gates (M7).
- Well-posedness at γ < 1: linear interpolation preserves the contraction; deaths are absorbing with the −100 applied on the death step using the dead body's drive, matching `core.py:1069-1079`; the reward's `eating_reward_penalty` is 0 at level 05.
- Known-bugs registry (grep for thermal / heal / bush / drive / campfire): no collision; no undocumented bug found. The "contemporaneous binning" class (three recorded instances) is a hazard for the *later* step of comparing planner labels with agent trajectories — note it then.
- Data-loss / rollback: writes only under `results/analysis/…` and `docs/`; resumable; no git operations.
- Entry-point framing: the plan's §Question reads cold.

## Cost of being wrong

The study costs minutes; its output chooses which level-05 variants get multi-seed training, each variant days of GPU. As written, the choice would be made for a 100-step-horizon oracle rather than the 20-step agent the project trains, and the tie / balance artefacts can pass or fail a setting by a margin the size of the pre-registered threshold — a week of training answering a slightly different question. No data-loss hazard.

Reviewed by: plan-reviewer
