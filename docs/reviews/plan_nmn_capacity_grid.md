# Plan review: modulator capacity grid at level 05

Reviewed by: plan-reviewer · 2026-10-06 · object: [[NMN_CAPACITY_GRID_L05]] (commit `1be6faab`)

## Verdict

**NOT READY: the decision rule needs revising. The training launch itself is not blocked.**

The experiment trains nine larger or coarser-grained versions of the agent's modulator at one seed. Only versions that clearly stand out get more seeds. If none stands out, the research direction is dropped for good. The configs, the controls and the launch mechanics are sound. The problem is the rule that decides what counts as "standing out". It is calibrated far more strictly than its own text says. It would pass a setting that adds 3 percentage points of injury-driven bush hiding only about 1 time in 10. That is the effect size stage 2 is built to accept. It would also pass a setting that adds 5 pp only about 1 time in 4. The doc's stated caveat for a null result is "effects under ~3 pp were not detectable". The real figure is that effects under roughly 7 pp are more likely to be missed than caught. The most likely outcome is null, and that outcome ends the direction. So the doc as written would record a wrong-sized negative conclusion.

Training the nine stage-1 runs does not depend on the rule. They can launch now, provided the revised rule is committed before any stage-1 test result is read.

## What would flip the verdict

1. Revise §5.1 to a rule whose detection rate at the stage-2 size of interest (3–5 pp) is stated and reasonable, e.g. option A below. Alternatively, keep the rule but correct every "~3 pp" caveat (§2.3 C6, §6 last row) to the true detection profile.
2. Compute the stage-2 size criterion (§5.2 rule 2) on the fresh seeds only.

## Findings

Legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run · 🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

### 🔴 F1. The stage-1 rule is much stricter than stated, and the null caveat is wrong by about 2×

I recomputed all six reference values from the replication folders with the page's own estimator. They reproduce §5 exactly. The across-run SD is 3.49 pp (no animal) and 3.48 pp (rabbit). The two neutral injury measures correlate at r = 0.87 across the six runs, and the own-scene SDs are about 1.0 pp. I then simulated a bivariate normal on these numbers, shifting both neutral measures by Δ. In the "own unchanged" variant only the neutral measures shift. The own-interval half-widths are resampled from the six references.

| True shift Δ (pp) | Rule 1 alone | Rules 1+2 | Rules 1+2+3 (own shifts too / own unchanged) | Option A |
|---|---|---|---|---|
| 0 (null) | 2.7 % | 1.5 % | 1.3 % | 17 % |
| 3 | 15 % | 10 % | 10 % / 7 % | 47 % |
| 5 | 32 % | 23 % | 23 % / 15 % | 67–70 % |
| 7 | 55 % | 44 % | 44 % / 24 % | 77–87 % |
| 10 | 84 % | 76 % | 76 % / 35 % | — |

- The doc says about 5 % false advance per measure and one in five to one in three across nine cells. Under the same normal model, the actual figure is about 1.5 % per cell and about 13 % across nine (assuming independence). The rule spends its error budget on the cheap mistake. A false advance costs 2 GPU-days, and stage 2 catches it. A false drop is final.
- Rule 2 (the run's own interval lower bound must clear the six-run maximum) raises the threshold again by that run's half-width, which is 1.4–5.3 pp in the references. That interval measures checkpoint-to-checkpoint noise within one run, not seed-to-seed variation. It penalises a noisy trajectory, not a weak effect, and the "share of checkpoints positive" flag already guards against late spikes.
- Rule 3 is called "does not reverse", but it requires the own-scene effect to be at least the seed-42 reference value. That is a superiority test against a single run, not a non-inferiority test. When a real neutral-scene effect does not carry into the compressed own scenes (all six sit between 8.8 and 11.9), rule 3 removes most true positives (Δ = 10: 76 % → 35 %).
- **The user's question about whether the six-run maximum is inflated by the ordinary agents.** The inflation is small: 0.8 pp on the rabbit measure (ordinary s43 9.2 vs modulated max 8.4) and 0.2 pp with no animal. The strictness comes from the +3 margin, rule 2 and rule 3, not from the envelope.
- **Requiring both injury measures.** At r = 0.87 they are close to the same measurement taken twice. Requiring both adds little protection (null 4.3 % → 2.7 %) and costs a little power. It also contradicts stage 2, which treats the rabbit measure as primary. It is justifiable as a direction check, not as a second full-height bar.

**Caveat on these numbers.** The SD comes from six runs, so its 95 % interval is roughly 2.2–8.6 pp. A normal model and an independence assumption are used. The shape of the conclusion holds across that range: power at Δ = 3 stays far below 50 % under the current rule. The exact percentages do not hold.

**Fix (owner: experiment-designer; thresholds are the user's call).** Option A, simpler and calibrated:

> Advance a cell if (i) its neutral rabbit injury effect is at least the six-run maximum (9.2 pp, no margin); (ii) its neutral no-animal effect is at least the six-run median (10.65 pp), as a direction check; (iii) both own-scene injury effects are at least the six-run minimum (8.8 / 9.1 pp), as true non-inferiority; (iv) the survival guard holds. Advance at most the top 3 by rabbit effect.

Under the null, a cell passes about 17 % of the time. If all nine cells are null, roughly 1–2 cells pass, which costs at most 6 stage-2 runs. Power is about 47 % at +3 pp and about 67 % at +5 pp. Stage 2 is the actual filter.

A middle option keeps the current structure, drops rule 2, sets the margin to +1.5 pp and uses option A's (iii). If the user prefers the current rule as it stands, that is a legitimate choice. In that case, §2.3 C6 and §6 must say "effects smaller than about 7 pp are more likely to be missed than detected", not "under ~3 pp".

### 🟡 F2. The stage-2 size criterion uses the selected seed

§5.2 rule 2 takes the 3-seed mean of (cell − current modulated), including seed 42. Seed 42 is the seed that was selected for being high, which contradicts §2.3 C3 ("fresh seeds must pass on their own"). The "1 time in 8 per comparison" in §5.2 also counts the selected seed. For the two fresh seeds it is 1 in 4 per reference, and about 1 in 9 for beating both at once (the cell must be the highest of three). **Fix:** compute the size on seeds 43–44 only, and report the 3-seed mean beside it. Owner: experiment-designer.

### 🟡 F3. The survival guard's training threshold is not numerically pre-registered

§5.1 rule 4 requires training survival steps to be "not more than 10 % below the lowest of the six reference runs", but that value is not written down. **Fix:** compute the six reference values (WandB `Episode/Steps`, checkpoint-wise mean over 2–10 M) now, and write the number into §5.1.

### 🟡 F4. The readout script does not exist yet, so the pre-registered rule is applied by unwritten code

§5.4 defers the stage-1 study script to the analysis phase. **Fix:** build it before stage-1 results exist. Validate it by reproducing the §5 reference table from the healrep folders (the reference values do reproduce with `figures.effect()`, as checked here). Then commit it. Owner: developer or experiment-analyzer.

### ❓ F5. Shared initialisation (question 3): a minor confound, but the paired comparisons should not be read as matched pairs

- What is shared: the task network's starting weights, the first world and the training key. What differs from step 1: the FiLM head kernels use the default random initialisation, not zeros (`src/models/neuromodulator.py:177-186`). Only the biases start the network as a pass-through. Because `h_mod` starts at zero, the forward pass is identical at step 0 only, and the cells' policies diverge immediately.
- Weak evidence that seed coupling is loose: in the replication, same-seed ordinary vs modulated is 5.3 vs 11.0 (s42) and 10.3 vs 3.7 (s43). Whether the ordinary agent shares the task initialisation is itself unverified, because it builds `nnx.GRUCell` and the modulated agent builds `ModulatedGRUCell` (`src/models/recurrent_ppo_network.py:463-465`).
- Two consequences. First, the nine stage-1 cells are not nine independent draws, so the family-wise false-advance estimate and any "row/column pattern" at stage 1 may partly reflect seed 42 itself. Second, if the shared initialisation does pull cells toward the seed-42 modulated reference (11.0 / 8.4, upper half of the envelope), then a null cell starts about 2 pp above the six-run mean.
- **Fix:** treat every seed-42 comparison against the modulated reference as descriptive only. That covers rule 3 (replaced in option A) and the per-checkpoint "share positive" view. State in the verdict that the stage-1 cells share an initialisation.

### ❓ F6. Grouping (question 2): the per-neuron baseline does not undermine the test, but it changes what "grouping" and "larger" mean

- Confirmed at `src/models/neuromodulator.py:235-245`. Each head is linear in the modulator state `h_mod`. Its output is repeated over each group and added to a 128-wide per-neuron baseline. So the state-dependent gain per site lies in a subspace of dimension at most min(H, 128/G).
- Reference (16, 1): at most 16. G8 cells: at most 16. G16: at most 8. G32: at most 4. **No cell has a higher-dimensional state-dependent signal than the reference**, and increasing H above 128/G adds only recurrent memory and nonlinearity, not output dimensions.
- The "larger modulator" in the title is therefore larger in memory only, and the grid tests "fewer, coarser state-dependent channels plus a wider modulator memory".
- Keeping the baseline per-neuron is the right choice for the dossier's hypothesis. Grouping the baseline as well would also remove the static re-tuning, which is the dominant part of the modulator's output, and would confound the test with an unrelated degradation.
- A second interpretation point: under Adam, one step on a group's gain moves G neurons at once. Coarser grouping therefore also means a larger effective step in function space for the state-dependent part.
- **Fix:** one sentence in §2.1 or §2.3 stating the dimension bound, and verdict wording that avoids "more capacity" for the G16 and G32 cells.

### 🟢 F7. Minor

- `spectral_bound.py` uses a fallback for `grouping_size` (already noted in §7.6). A known-bug row may be warranted; owner `bug-curator`.
- The known bug "rPPO critic learning rate is a lie" means the modulator trains at `lr_actor`. This is identical in every cell, so it does not affect the comparison.
- The known bug "A fast batch launch collapses several runs' log files into one" is handled by the per-run `--log` instruction, and `run_command.py --log` exists.

## Checks that turned up nothing

- The eval specs match the healrep level-05 specs in everything except the nodes and the run list.
- The output folder is new, so the reference results are not overwritten.
- No commit to `src/`, `train.py`, `configs/train` or the level-05 world config since the reference launch (2026-10-05 15:00).
- The seed path: top-level `seed` feeds `trainer_init_keys` (`train.py:787,1161`).
- No data-loss hazards: no git operations and no deletions.
- The prior June grouping screen ran on a different task (the continual curriculum), so the two designs do not collide.

## Assumptions

| Assumption | Status |
|---|---|
| Configs differ from the reference only in the two keys | Verified (generator [1] and [2], plus post-launch saved-config check) |
| Seed-42 task initialisation is shared with the reference | Verified by `--verify` [3] |
| Shared initialisation does not couple outcomes strongly | Unverified (weak contrary evidence, F5) |
| Six-run spread is the right null for a seed-42 cell | Unverified (F5) |
| Across-run SD is about 3.5 pp | Point estimate from n=6, wide interval |
| No training-code drift since the reference launch | Verified for now; re-check at launch time |
| Rule-applying script reproduces the reference table | Not yet built (F4) |

## Cost of being wrong

If the rule stays as written, the likely null outcome permanently drops the capacity direction after about 9 GPU-days. It would also put on record that "no ≥3 pp effect exists", when the screen could not detect effects of 3–5 pp. The compute is cheap. The cost is a false negative in the project record, which is expensive to undo. Revising the rule costs nothing in compute.
