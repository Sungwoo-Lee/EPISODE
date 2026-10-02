---
title: "Analysis-verdict review — 'Where Does the Modulator Matter?' clue page, before publish"
topic: basic_levels_q2_default
status: active
created: 2026-09-23
last_updated: 2026-09-23
---

# Review of the clue page "Where Does the Modulator Matter?" — do its claims hold?

**Verdict: NOT SUPPORTED BY THE EVIDENCE SHOWN, as published.** That is a statement about three
sentences and two leads, not about the page's central message. The survey's main reading — the
environment changes behaviour far more than the modulator does, and the two agents are close on
almost every measure — **is** supported. But three statements on the page are wrong against the
sources, and two of the five leads rest on sign-agreement counts that a page with this many rows
would produce by chance.

## Verdict (plain language)

The page compares an ordinary agent with a neuromodulated one across three worlds and reports,
figure by figure, where they differ. I recomputed every caption number from the analysis outputs on
disk (the ladder aggregates, the regression tables, the context-dependence JSONs at every late
checkpoint, the probe sweeps, the modulator gain distributions) and read the runs' own saved configs.

What is wrong:

1. **The page describes the modulator as "a small network that reads those internal signals"
   (injury, hunger, body temperature).** The modulated runs' saved config says
   `modulation.input_sensors: all`, and the model code documents `all` as "reads ALL of them" — the
   whole observation, including smell and vision. So the modulator has a direct pathway to the
   threat cue. That reverses the meaning of lead 2 ("clearest footprint is on threat identity, not
   on the body"): a network that reads smell directly amplifying smell evidence is the expected
   consequence of its input, not a clue about state dependence. It also weakens lead 3's "moves with
   the body" framing.
2. **Figure 4's one "consistent gap" has its sign backwards.** The caption says the modulated agent
   is "slightly less pulled by hunger in six of seven cells". The hunger span is negative (a hungry
   agent leaves cover); the modulated agent's span is *more* negative in six of seven cells (e.g.
   Wave 2 level 06: −24.7 against −22.9). Hunger pulls it out of cover *more*, by 0.4–3.5 points.
3. **Figure 2's caption is contradicted by data that landed after the figure was built.** The
   figure (built 22:49) has checkpoint ranges on only two cells; the caption says the gap "mostly
   straddles zero once its spread across checkpoints is drawn … in any world". The late-checkpoint
   JSONs now on disk (23:22) show one-signed gaps across all five checkpoints at exactly the levels
   built to need state dependence: Wave 1 levels 05 and 06 threat trend (−0.4 to −1.9 and −0.3 to
   −1.2 pp per injury band, modulated agent's predator response falling more steeply with injury),
   Wave 1 level 06 bush-entry change (−1.3 to −2.9), Wave 2 level 04 entry change (+0.2 to +1.2).
   The script also pairs checkpoints by position from the *start*, so the built Wave 2 level 05 cell
   compares the ordinary agent at 8.0 M steps with the modulated agent's final checkpoint.

What is overstated: Figure 3's "a hurt agent is already in cover" mechanism holds in Wave 2 (calm
hiding of the most-wounded quarter rises about 6 points) but not Wave 1 (everything moves under 1.5
points), and the positive criterion is mostly the arithmetic of subtracting a shift on a 40–55-point
effect from one on a 5–17-point effect; Figure 5's 6-of-7 is one of three rows on the page at 6-of-7
(the number-of-rabbits row and the hunger row are the others) and about two such rows are expected by
chance among the page's 17; Figure 9's "threat response" panel is the calm baseline moving (hiding
with a predator near sits at 60–65 % in every temperature band for both agents); Figure 10's "larger
cut in the modulated agent" is inside the within-run checkpoint spread on the nearest measure that
has one, and level 06 also adds injury-gated *visual* noise, not only smell noise.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Per-figure verdicts

| figure / lead | verdict | what the sources say |
|---|---|---|
| Fig 1 survival & endings | SUPPORTED | survival gaps −3.1…+6.8 steps of 184–288; ending shifts ≤ 4.3 pp; shares sum to 100; over-eating 0.00–0.01 %. Over-eating is keyed by raw code `"3"` in the aggregates (no label) — 🟢 |
| Fig 2 wound, causally | **NOT SUPPORTED as captioned** (🔴 C3) | see above; 10 of 15 cell×measure ranges straddle zero, the 5 that do not are at W1 05/06 and W2 04 |
| Fig 3 hypervigilance | OVERSTATED (🟡) | "in every cell" — blind modulated predator shift is +0.1; mechanism holds only in Wave 2; sign survives on the log-odds scale so it is not a pure ceiling artefact, but proportionally the rabbit effect shrinks as much or more than the predator effect (W2 05 control: −24 % vs −14 %) |
| Fig 4 two drives | causal panels SUPPORTED; hunger sentence **NOT SUPPORTED** (🔴 C2) | injury spans W2 +7…+27 vs W1 −4…+8 — "quadruples" is fair; hunger gap sign reversed |
| Fig 5 hiding model | OVERSTATED (🟡) | pred-smell gaps +0.17…+0.79 pp/SD, 6/7; n_rabbits also 6/7; n_predators gap swings −0.9…+2.4 across cells, which is the only run-to-run scale available and the smell gaps sit inside it; per-fit SEs exist in `multivariate.csv` (z 2.8–11) but measure sampling noise within one run |
| Fig 6 gain tracking | SUPPORTED WITH CAVEATS (🟡) | 8–31 % correct; "highest at the decision heads in every world" false at Wave 2 level 05 (multimodal encoder 20.5–23.4 % > actor 17–19 %, critic 18–20 %); "moves with the body" unwarranted given `input_sensors: all` |
| Fig 7 level-04 scenes | SUPPORTED WITH CAVEATS | gaps −18…−30 confirmed; training-world hiding for uninjured, near-target episodes is 50.2 vs 50.8 % (first 25 steps), which strengthens "alike". Caveat: the *ordinary* agent is the erratic one on the empty scene (29.6 ± 27.2 across 20 checkpoints vs 11.5 ± 11.5) — "the modulated agent idles differently" is equally "the ordinary agent's idling flips between checkpoints" |
| Fig 8 thermal scenes | SUPPORTED WITH CAVEATS (🟡) | threat response higher in **7** of 8, not 6; calm gaps are on values of 0.5–5 % in six of eight cells; the noise-matched level-06 replays on disk (omitted) flip the calm sign in 3 of 4 (+0.2, −1.6, +0.4, +0.0) |
| Fig 9 body temperature | OVERSTATED (🟡) | hiding with a predator within two squares is 59–65 % in every band, both agents; only calm hiding moves; the coldest band is < 1 % of steps; two agents alike (±4 pp) |
| Fig 10 level 06 − 05 | OVERSTATED (🟡) | injury span cut: ctrl −9.7 / mod −13.1 (W1), −12.0 / −19.8 (W2). On the A2 state span with five checkpoints (W1, on disk): ctrl −3.0…−5.9, mod −1.5…−5.9 — fully overlapping. Level 06 also enables visual noise (σ 0.1, injury scale 2.0) and constant noise on collision / proprioception / location. "causal" tag misapplied to a between-run contrast |
| Clue table | SUPPORTED as computed | numbers reproduce; 6/7 rows are at the chance floor for 8 rows |
| Lead 1 | SUPPORTED for the Figure 4 leg; NOT for the Figure 9 leg | |
| Lead 2 | NOT SUPPORTED (🔴 C1 + Fig 5) | |
| Lead 3 | SUPPORTED WITH CAVEATS | 8–31 % holds; "follow the body" → "follow the moment" |
| Lead 4 | OVERSTATED | 2-of-2 signs; inside checkpoint noise on the spread-bearing measure |
| Lead 5 | SUPPORTED WITH CAVEATS | see Fig 7 |

## Findings

| # | Sev | Location | Issue | Suggested fix | Owner |
|---|---|---|---|---|---|
| C1 | 🔴 | page §01 ("reads those internal signals"); lead 2; lead 3 heading | `models/config.yaml` of every modulated run: `modulation.input_sensors: all`; `src/models/recurrent_ppo_network.py:27-60` documents `all` as every observation index. The modulator reads smell and vision directly | State the input in §01 ("reads the whole observation, senses included"); rewrite lead 2 as "the modulator, which reads smell directly, weights the predator's smell a little more in 6 of 7 cells — the restricted-input arm is the test"; retitle §08 "moves with the moment" | experiment-designer |
| C2 | 🔴 | Fig 4 caption, last sentence | sign reversed; sources: `ladderstyle/*_episodes.npz` via `_common.spans` | "the modulated agent is pulled *out of cover by hunger slightly more* in six of seven cells (0.4–3.5 pp)" | experiment-designer |
| C3 | 🔴 | Fig 2 caption; `a2_injury_dose.py` pairing (`sm[t] - sc[t]` for `t < min(len)`) | caption written from a 2-cell spread; five one-signed cells now on disk; positional pairing from the start mis-pairs when one arm's stores lag | Rebuild after all stores land; pair by matched step (or from the end) and refuse unequal counts; caption: "small — under 3 pp — and in most cells the range crosses zero; at Wave 1 levels 05/06 the modulated agent's predator response falls more steeply with injury at every checkpoint (about 1 pp per band), and its bush-entry change at level 06 is lower at every checkpoint" | developer / experiment-designer |
| M1 | 🟡 | Fig 3 caption | "every cell" false (blind modulated +0.1); mechanism Wave-2-only; scale arithmetic | "…lowers it in every sighted cell. In Wave 2 the hurt agent's calm hiding rises about 6 points, so a predator's approach adds less; in Wave 1 both quantities move under 1.5 points. The criterion comes out positive because the predator effect is five to eight times the rabbit effect and both shrink; in proportion the rabbit response shrinks at least as much" | experiment-designer |
| M2 | 🟡 | Fig 5 caption; lead 2 | 6/7 at chance floor; n_rabbits row equally consistent; magnitudes inside the between-cell swing of other rows | "the row with the most consistent sign … one of three rows at 6 of 7 on this page, about what chance gives; a candidate to test, not a footprint" | experiment-designer |
| M3 | 🟡 | Fig 9 caption; lead 1 | hide_threat flat 59–65 %; cold band < 1 % of steps; direction unreadable | "calm hiding rises from a tenth to a half in the rare steps below −10°, identically in both agents; hiding with a predator near stays at 60–65 % in every band, so the lower panel is the baseline moving. Cold may cause hiding or hiding may cause cold; either way the agents do not differ" — and drop Figure 9 from lead 1's evidence | experiment-designer |
| M4 | 🟡 | Fig 10 caption, "How it is computed", `causal` tag; lead 4 | overlapping checkpoint ranges on the A2 span; visual noise also enabled at 06 (`perceptual_noise.modalities.visual: state_dependent σ 0.1 scale 2.0`) | Tag "between runs"; say level 06 adds injury-gated noise on smell *and vision*; show the 06−05 difference of the A2 span with its five-checkpoint range; lead 4 → "same direction in both waves, inside one run's checkpoint spread; a seeded replication is the only test" | experiment-designer |
| M5 | 🟡 | Fig 6 caption | "highest at the decision heads in every world" false at Wave 2 level 05 | "highest at the actor or critic in seven of eight runs; at Wave 2 level 05 the combined-senses encoder leads" | experiment-designer |
| M6 | 🟡 | Fig 8 caption | 6 of 8 → 7 of 8; calm gaps near zero; noise-matched level-06 replays flip the sign | State 7 of 8; add "the calm gap holds sign on values mostly under 5 %, and not in the noise-matched level-06 versions" | experiment-designer |
| M7 | 🟡 | Fig 5 provenance | `scripts/analysis/hiding_drivers.py` slot-layout fix (`_alloc`) is **uncommitted** in the working tree and the GLMs were produced with it; a fresh checkout cannot reproduce the figure | Commit the fix (with its `SCRIPTS_DEPENDENCY_MAP.md` row) before publishing | developer |
| M8 | 🟡 | Fig 7 caption; lead 5 | ordinary agent's empty-scene hiding SD 27 pp across checkpoints | "…and it is the ordinary agent whose idle hiding swings between checkpoints (SD 27 points), so the lead is as much about the ordinary agent's instability as the modulated agent's default" | experiment-designer |
| L1 | 🟢 | Fig 1 script | over-eating keyed by raw termination code `"3"`; no sum-to-100 assert (Known-Bugs row "how episodes end hardcodes three outcomes" — same pattern, four keys) | map the code to its label; assert the shares | developer |
| L2 | 🟢 | Fig 2 data table | "four 100k stores plus the final 1M store" mixes two sample sizes in one range; the power check (`context_power100k/`, shifts 0.02–0.34 pp) supports this but say it in the caption | — | experiment-designer |

## Assumptions the verdict rests on

| assumption | status |
|---|---|
| The modulator reads only interoceptive signals | **false** — `input_sensors: all` (saved configs) |
| Level 06 differs from level 05 only in injury-gated smell noise | **false** — visual noise also injury-gated; small constant noise on three more modalities (config diff) |
| Late-checkpoint gaps mostly straddle zero | **false on current data** for 5 of 15 cell×measure |
| 100k-episode stores reproduce the coarse measures | verified — shifts 0.02–0.34 pp on four runs |
| Training-world hiding is alike at level 04 in Wave 2 | verified — 31.4 vs 31.6 % overall; 50.2 vs 50.8 % in matched state |
| Term shares sum to 100 | verified — all 14 cells |
| Per-cell checkpoint pairing is matched by step | **false while an arm's stores lag** (a2 script) |
| Six-of-seven sign agreement is rare | **false** — ≈12.5 % per row under a null; 3 rows at 6/7 among 17 |

## Cost of being wrong

Nothing here costs compute; the page is the artefact the user will use to pick the next
architecture direction. Published as is, it would send the next experiment after "the modulator
gates threat identity" on a chance-level count from a modulator that already reads smell directly,
and would record the hunger effect with the wrong sign — a mis-steered direction and a wrong row in
the project's record, both cheap to fix now.

Reviewed by: plan-reviewer (2026-09-23)
