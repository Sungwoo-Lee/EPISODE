---
title: "Plan review: single-channel smell hypervigilance study — NOT READY (Q2 rule underpowered at its own minimum effect; verdict map promotes the inconclusive)"
topic: hypervigilance
status: active
created: 2026-09-30
last_updated: 2026-10-01
reviewed_object: docs/experiments/active/hypervigilance/SINGLE_CHANNEL_SMELL_HYPERVIGILANCE.md @ 71b7480a
---

# Plan review: single-channel smell hypervigilance

## Verdict

**NOT READY.** The study asks whether taking away the rabbit's second odour (so predator and
rabbit differ only in how *strong* one shared odour is) makes the agent confuse the two animals
more, and whether that confusion grows with the injury the episode starts with. The two worlds
and the collection spec are sound and were validated on the trainer's own loader; nothing in the
configs blocks a launch. The block is in the decision rule: at the plan's own minimum effect on
the injury question (a +2 percentage-point shift on a control that sits at −1.8), and with the
seed-to-seed spread the plan itself cites, the pre-registered "established" rule is met only
9–16 % of the time and the result lands "inconclusive" about 80 % of the time — and the plan's
verdict map reads that inconclusive as the study's flagship substantive claim, "confusion alone
is not sufficient for hypervigilance". Fixing this needs a rewrite of §5.3 and the verdict map,
not a config change. Four moderate issues ride along: a pre-flight check that reads a seed key
the trainer never writes; the existing seed-42 control stores were collected under a different
collector numerics mode than the ten new ones will be; two known measurement quirks (rabbit on the
agent's cell counted as "near"; no predator-free filter in the hiding reading) are not carried
into the confound list; and a P1 null is read as "no confusion" without conditioning on whether
predator detection also fell.

Severity legend: 🔴 Critical = fix before going further · 🟡 Moderate = likely costs a re-run ·
🟢 Low = cosmetic · ❓ Open = an assumption nobody has verified yet.

## Findings

The table is reproduced verbatim in the plan's own `## Feedback from plan-reviewer` section; the
numbers behind C1 are below.

| # | Sev | Where | Issue (short) | Owner |
|---|---|---|---|---|
| C1 | 🔴 | §5.3 + verdict map rows 2/4 | Q2 rule unmeetable at its minimum effect; "inconclusive" promoted to a substantive reading; 3 v 3 "refuted" exempt from top-up | `experiment-designer` |
| M1 | 🟡 | §3 pre-flight 2 | Checks `training.seed`; trainer writes/reads top-level `seed` (`train.py:612`, `:786`) | `experiment-designer` → `training-runner` |
| M2 | 🟡 | §2.4 / §5.5 / spec | Seed-42 control stores predate the full-float32 collector (`2d54453d`); no `matmul_precision` in their manifests | `experiment-designer` |
| M3 | 🟡 | `collect_arm_data.py:123-133` | Distance-0 rows in the NEAR bin (bush blocks animals → never a hiding row); no predator-near exclusion in the `rd` grid | `experiment-designer` → `senior-developer` |
| M4 | 🟡 | Verdict map row 3 | P1 null read as "no extra confusion" without conditioning on S4 (detection loss pushes P1 the other way) | `experiment-designer` |
| L1 | 🟢 | comments / wording | §3.2 cross-ref, self-contradictory row 5, "no smell direction" for cmp10m, `hv1ch` root name | — |

## C1 in numbers

Monte-Carlo, 200 000 draws per cell, normal seeds, the plan's own rule (complete separation
**and** mean difference ≥ minimum effect; "refuted" = opposite separation or |Δ| below the floor
with overlapping ranges; "inconclusive" otherwise). SDs are the 2026-09-21 registry entry the
plan cites (1.4 pp on the rabbit response; 1.05–2.67 pp on the injury shift). P2 additionally
requires all three single-channel seeds > 0, with the control at −1.8 pp.

| Outcome, true effect, seed SD | established | inconclusive | refuted |
|---|---|---|---|
| P1, +3 pp, 1.4 | 45 % | 51 % | 4 % |
| P1, +4 pp, 1.4 | 76 % | 23 % | <1 % |
| P1, 0 (null), 1.4 | <1 % | 33 % | 66 % |
| P2, +2 pp, 1.05 | 16 % | 81 % | 4 % |
| P2, +2 pp, 1.5 | 13 % | 78 % | 9 % |
| P2, +2 pp, 2.67 | 9 % | 79 % | 13 % |
| P2, +4 pp, 1.5 | 73 % | 27 % | <1 % |
| P2, 0 (null), 1.5 | <1 % | 63 % | 37 % |

5 v 5 top-up (one-sided Mann–Whitney U ≤ 4 plus the minimum effect): P1 at +3 pp / SD 1.4 →
50 %; P2 at +2 pp → 45 % (SD 1.5) or 26 % (SD 2.67).

Reading: the 3 v 3 design is a screen with a one-in-twenty false-positive rate, which the plan
states, and roughly coin-flip power on P1 and one-in-eight power on P2 at the minimum effects,
which it does not. That is acceptable **if** the verdict map treats "inconclusive" as
"not established". Row 2 does not: it names "P1 established, P2 refuted / inconclusive" as
*confusion without hypervigilance*, which the Research Question section calls "the key
informative outcome". Row 4 sends the same P2-inconclusive to the top-up, so the two rows also
contradict each other. And a 3 v 3 "refuted" — 4–13 % at a true minimum effect — never reaches
the top-up.

**Exit condition.** (a) Row 2 fires only on a P2 refutation *after* the top-up; P2 inconclusive
is reported as "not established". (b) §5.3 states the power at the minimum effects. (c) Either
5 v 5 up front (≈ 267 GPU-hours instead of 160) or a 3 v 3 refutation also triggers the top-up.
(d) The "positive in all three seeds" clause is reconsidered: at an expected +0.2 pp it passes
about one time in eight on its own, so it mostly converts true effects into "partial".

## Circularity and verification

The plan's config validation is not circular: it diffs resolved `EnvParams` through the same
`load_env_config → load_env_params` path `train.py:594` uses, and separately diffs the seed-42
runs' **saved** `models/config.yaml` (what actually trained) against the control twin. Pre-flight
2 reads the saved config — ground truth — but the wrong key (M1). The ladder-drift check 3 is the
right safeguard for staggered launches.

## Prior art

Known Bugs rows read for this area: "Chasing rabbit stays glued to the agent after contact"
(OPEN, `core.py:629`) → M3; "A trajectory store replays exactly only under the matmul precision
mode it was collected in" → M2; "Five unmodulated reference runs … use them for spread, never as
a baseline" — the plan complies (cmp10m is the yardstick only); "Environment reset is not
bit-identical … on `animal_property_sampled` (1 ulp)" — harmless to the pairing claim. No prior
plan on single-channel smell under `docs/llm_wiki/` or `docs/develop/`; the sameProp entries and
the injury-gated olfactory-noise entry the plan cites are the relevant ones. Nothing new for
`bug-curator`.

## Cost of being wrong

About 160 GPU-hours, the 4-run top-up, and two collection passes, to arrive — with roughly 80 %
probability at the plan's own minimum effect — at a P2 "inconclusive" that the verdict map as
written promotes into "confusion alone is not sufficient for hypervigilance", a claim that would
enter the project's hypervigilance narrative. No data-loss hazard anywhere in the plan.

*Reviewed by: plan-reviewer*

## Re-check of Revision 1 (2026-10-01, commit `298cfaba`)

**SOUND WITH CONCERNS.** C1 and M1–M4 are resolved (each re-verified independently — the revised
power table and the three-world simulation both reproduce). Two new Moderate findings concern how
the added matched-strength world is *read*, not the world itself: the strength contrast has no
stated direction while the plan's reasoning uses both signs, and the primary contrast holds the
class-average smell but leaves the rabbit 11 % quieter than in the control, so "removes the
detection confound by design" overstates it. Full table and the assumption list are appended to the
plan doc under "Feedback from plan-reviewer — re-check of Revision 1". No Critical remains; this
file's NOT READY verdict above applies to `71b7480a` only.

*Reviewed by: plan-reviewer*
