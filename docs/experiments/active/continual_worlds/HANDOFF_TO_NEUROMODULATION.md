---
title: Continual worlds and May replication — hand-off to the neuromodulation training session
created: 2026-09-30
last_updated: 2026-09-30
status: active
---

# Continual worlds and May replication — hand-off

## Purpose

The user is reorganising the work. From 2026-09-30, all modulator-vs-ordinary training studies are
owned by the **"Training: neuromodulation"** session, and the continual-worlds session moves to
hypervigilance. This doc hands over everything the continual-worlds session built, ran and found, so
nothing has to be rediscovered: what was asked, what is done, what the results say, where every file
is, and what is still open.

**In one paragraph:** we tested whether the neuromodulated agent (t16quad) copes better than the
ordinary agent (t1none) when the outside world keeps changing while the body's rules stay fixed.
Two studies ran. **(1) Continual worlds**: three A-B-A-B sequences (Winter ↔ Famine, Danger-A ↔
Famine, Fog-B ↔ Danger-A), one seed, both agents branching from one pre-trained seed-42 pair. The
pre-registered rule is **not decisive**: it says "supported" only if the Forage world (learned before
the alternation) counts in the forgetting vote, and "refuted" if only the alternating worlds count.
The robust differences are that the modulated seed-42 checkpoint plays unseen worlds better zero-shot
(+2 to +18 steps) and keeps its Forage skill after Winter (+114 steps, sampled actions, 95 % CI +103
to +125) — properties of **one initialisation pair** (shared start confirmed bitwise). **(2) May
double-return replication**: May's hunting/harmless predator switch rebuilt with today's body, 3 seeds
per agent. **Not replicated** (+1.5 steps on returns vs May's +107/+132), but **ceiling-limited**
(90–97 % of episodes hit the 500-step cap), so it is an underpowered null. Two exploratory hints
(lower death rate on hunting stages; faster from-scratch learning, ~half the size on the env-step
axis) are hypotheses for a pre-registered test, not findings.

## Pages (published artifacts)

| Page | URL | Source |
|---|---|---|
| Continual Worlds (plan, pre-results record) | https://claude.ai/artifact/Xvd13TcMHMcG31FbspxKfP | `continual_worlds_plan.template.html`, builder `scripts/analysis/studies/continual_worlds/page/build_page.py` |
| Continual Worlds: Results (both studies) | https://claude.ai/artifact/2PfinPyZD791PzX3Lrokfj | `continual_worlds_results.template.html`, builder `scripts/analysis/studies/continual_worlds/results_page/build_page.py --figures` |

Both pages are in this folder. Republish from the same file path (or pass the URL) to keep the links.

## Design docs (owners of every rule and verdict)

- [[CONTINUAL_WORLDS]] — design (§2 hypotheses, §3 worlds/sequences/pilots, §3.7 Revisions 2/2a and
  user decisions §3.7.7, §4 manifest, §5 analysis plan), results §10, conclusions §11, reviewer
  feedback at the end. §3.4 correction: the two agents share their initial main-network weights.
- [[MAY_DOUBLE_RETURN_REPLICATION]] — design, pre-data revision (2026-09-29), decisions §8.1,
  results §10, conclusions §11, reviewer feedback.
- Reviews: `docs/reviews/plan_continual_worlds_rev2.md`, `docs/reviews/plan_continual_worlds_main_verdict.md`.
- Cross-study note appended (signed) to `docs/experiments/active/modulator_clues/CROSS_STUDY_NULL_DOSSIER.md`.

## Runs (all finished; WandB group `continual_worlds`)

| Set | Tags | Where the details are |
|---|---|---|
| Pilot 1 (single switches from the pre-trained Home pair) | `rppo_cw_pilot1_<world>_{t1none,t16quad}_s42` | CONTINUAL_WORLDS §4 rows 1–12 |
| Pilot 1 softened re-pilots | `rppo_cw_pilot1s_<world>_soft_*` | rows 31–36 |
| Exploratory scouts | `rppo_cw_scout_*` (39–41 relaunched as `_r2`) | rows 37–43 |
| Pilot 2 (short A-B-A-B shakedown) | `rppo_cw_pilot2{a,b}_*` | rows 13–16 |
| Pilot 3 Nursery (seed 43) + Home legs | `rppo_cw_nursery_*_s43`, `rppo_cw_home_*_s43` | rows 17–18, 27–28 (both pass the competence gate) |
| **Main sequences** | `rppo_cw_p3_*` (Winter↔Famine), `rppo_cw_p1_danger_scout_a_famine_*`, `rppo_cw_p2_fog_scout_b_danger_scout_a_*` | rows 19–24; branch checkpoints `results/JAX_RecurrentPPO/cw_branchpoint_forage_{t1none,t16quad}_s42` |
| **May replication** | `rppo_cw_mayrep_{t1none,t16quad}_s{42,43,44}` | MAY_DOUBLE_RETURN_REPLICATION manifest M1–M6 |

Pre-trained seed-43 pair (Nursery → Home, 10 M episodes) is ready to use as a second starting pair.
Seed-44 Nursery/Home legs (rows 25–26, 29–30) were never launched.

## Code and data

| What | Path |
|---|---|
| World configs (8 concepts, softened, scouts, May active/passive) | `configs/environment/experiment/continual_worlds/` |
| Continual schedules (+ `_stages/`) | `configs/continual/continual_worlds/` |
| Read-out: pilot/main measures, shared-yardstick dip/recovery, votes, tie rule, `--study mayrep`, ceiling check, exploratory outcomes | `scripts/analysis/studies/continual_worlds/pilot_readout.py` (test `tests/analysis/test_cw_readout_tie_rule.py`) |
| Memory/forgetting matrix (stage-end checkpoints × worlds; `--extra-world`; `--eval-policy-mode`) | `scripts/eval/continual_forgetting_matrix.py` |
| May retention rule | `scripts/analysis/studies/continual_worlds/retention_readout.py` |
| Outputs | `results/analysis/continual_worlds/` (gitignored) |
| Main-verdict scoring not yet in the read-out script (per-switch yardsticks, rules R1–R8, zero-shot table, shared-start check) | `tmp/20260929_cw_main_verdict.*`, `tmp/20260930_cw_sensitivity_extra.*`, `tmp/20260930_cw_zeroshot_relative.*`, `tmp/20260930_cw_shared_start_l05.*` (gitignored — move into a committed script) |

## Known issues found on the way

- Known Bug A2 (later stage with more hunter slots than stage 0 crashes) — avoided by starting every
  sequence in Forage (0 hunters).
- Registered in KNOWN_BUGS on 2026-09-29: continual path alphabetises saved configs; quarter-restricted
  animals roam a 6×6 box (kept for May fidelity); `perceptual_noise.enabled` falls back silently.
- Node 114 hung under three simultaneous compiles (2026-09-28); stagger launches.
- Memory matrices default to greedy evaluation (7–12 steps above training); use `--eval-policy-mode stochastic` for between-agent claims.

## Open items (for the neuromodulation session to decide)

1. **Pre-register before any replication**: how per-switch votes combine; which worlds count for
   forgetting (the hinge); greedy vs sampled evaluation; ceiling-free outcomes.
2. **Break the shared start**: cross-seed pairs, and ordinary-42 vs ordinary-43/44 as the noise
   yardstick (CONTINUAL_WORLDS §11.5 checklist). The seed-43 pair is ready; seed 44 is not.
3. **A harder world** with room below the 500-step cap for the May-style test.
4. **Learning speed with seeds on the env-step axis** as a pre-registered outcome (addresses
   candidate 4 of "What Both Agents Compute").
5. Move the main-verdict scoring from `tmp/` into `pilot_readout.py`.
6. D7: the Harsh ↔ Forage sequence is impossible as designed (Harsh dropped).
