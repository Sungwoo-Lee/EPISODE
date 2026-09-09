---
title: "Open-Work Handoff — carried-over work items"
topic: issues
status: active
created: 2026-07-04
last_updated: 2026-09-09
---

# Open-Work Handoff — carried-over work items

## What this is

A **handoff checklist** of work that is deferred rather than forgotten, written so
another Claude session can pick it up cold. It began as the leftovers from the
2026-07-04 v3.0-audit session (sections A-D) and now also carries deferrals from
later work (section E onward). Each item is a
one-line, actionable task with the file refs and links you need — **not**
re-analysis. For the full bug record and root-cause detail, see [[KNOWN_BUGS]]
(owned by `bug-curator`) and the [[v3_pipeline_correctness_diagnosis]].

Items are grouped by readiness:
- **A** — ready to implement, no user decision needed.
- **B** — needs a user decision before any code is written.
- **C** — latent / unconfirmed; triage before touching.
- **D** — experiment-ops / user-driven, not code.

Do the routing the normal way: write a senior-developer fix plan per item, hand
to `developer`, verify. Ask `bug-curator` to update the registry after a fix
lands — do not hand-edit [[KNOWN_BUGS]].

---

## A. Ready to implement (no user decision needed)

- [ ] **A1 — Regenerate 4 stale `observability_gates` parity fixtures.** `tests/env/test_unified_parity.py::observability_gates_S1-S4` are RED because the G2 fix (commit `84014e4`) changed those configs' start position, but the golden `.npz` fixtures were captured with the old one. The parity test is already migrated to `animal_*` keys (F fix, `0bebe06`), so regenerating these 4 fixtures against the new fixed start is safe. Goal: suite fully green. **Small.**
- [ ] **A2 — dreamer-srl checkpoint omits optimizer state.** `src/algorithms/dreamer_srl/checkpoint.py:85-88` saves only `world_model/actor/critic/target_critic` params via `nnx.state(.., nnx.Param)` — **no** `opt_state`. Effect: resuming/continuing a run silently restarts Adam momentum from zero (matters for continual learning). Needs a small fix plan → `developer`. Ref: memory `docs/llm_wiki/entries/env_entities/20260609_1726_doc_audit_surfaces_latent_bugs.md`. **Med.**
- [ ] **A3 — "chasing rabbit" rides the agent's cell after contact.** `src/environment/core.py:629` applies the post-contact pause only `where(at_damaging, ...)`, so a non-damaging animal gets no pause and stays at distance 0 — skews the chasing-rabbit / hypervigilance behaviour read. Needs a fix plan → `developer`. Ref: memory `docs/llm_wiki/entries/env_entities/20260609_1722_renderer_no_neutral_icon_and_attack_delay_ride.md`. **Med.**

## B. Needs a user decision first (do NOT implement blind)

- [ ] **B1 — M1/M2 behaviour-metric "episode-end rule".** Three conflicting documented semantics for events still in progress at episode end (finish them / drop them / exclude from denominator). One rule must be adjudicated before coding. Refs: [[v3_pipeline_correctness_diagnosis]] Finding M1/M2; `docs/reviews/diag_v3_pipeline_math.md`; `docs/experiments/active/behavior_measures/behavior_measure_toolkit_v1_design.md` §7.2; `docs/develop/active/behavior/behavior_measure_toolkit_v1_plan.md` line 382. *(Measures are OFF by default now → low urgency.)*
- [ ] **B2 — CLI model-size overrides not saved to config (L4).** `--hidden_size` / `--num_steps` / `--lr` aren't written into the saved config → re-eval rebuilds the model at the wrong size. The `--no-satiation` sibling was already fixed (`75976e2`). **Low** — decide whether it's worth doing.

## C. Latent / needs verification (triage before any fix)

- [ ] **C1 — Checkpoint Orbax↔NNX restore skew.** Recorded risk, never confirmed. Triage whether it's real. Ref: memory `docs/llm_wiki/entries/cluster_ops/20260509_1536_train_py_checkpoint_restore_nnx_skew.md`.
- [ ] **C2 — Env doc-audit: ~11 remaining sub-findings un-triaged** (beyond the 2 named in A2/A3 above — e.g. overeating-death never ends the episode; unreliable `termination_reason` when a body system is off). Triage which are real vs cosmetic. Ref: memory `docs/llm_wiki/entries/env_entities/20260609_1726_doc_audit_surfaces_latent_bugs.md`.

## D. Experiment ops (user-driven, not code)

- [ ] **D1 — Relaunch jump-reach (node 113)** with `attack_range: [2,3]` on corrected code (reward fix `ef0fd25` + range fix `7ff8d1f`) for clean {2,3} semantics.
- [ ] **D2 — Relaunch the 6-run basic ladder** on the corrected reward + range semantics when desired (current runs carry the old semantics).
- [ ] **D3 — 266 commits are unpushed** — decide whether to push.

---

## E. Temperature system — deferred by user decision (2026-09-09)

Both items are **user-deferred, not blocked**: the user asked for each to be handled as
part of a larger piece of work rather than as a one-off patch. Neither is broken today at
the shipped settings; both are traps for whoever changes those settings next.

- [ ] **E1 — Review every temperature setting together, including the two uncalibrated
  ones.** To be done as one pass over the whole `thermal:` block rather than
  value-by-value. Two known items to fold in. **(a) The energy cost of thermoregulation
  is uncalibrated.** `thermal.metabolic_coupling_rate` ships at `1.0` and is currently
  unread (`metabolic_coupling: false`; the loader forces the inert `0.0` when the gate is
  off). At `k_loss = 0.01` with a body at −12 it would add roughly **12%** on top of
  `metabolic_cost: 1.0`. Note the shape, not just the magnitude: the drain is
  `rate * |k_loss * (body_temp − temperature_setpoint)|`, so it grows with distance from
  the setpoint in **either** direction — at the campfire comfort ring the body settles
  near **+8.9**, so switching this on charges nearly as much for sitting at the fire as
  for freezing, and with the world baseline at −22 to −28 there is nowhere the agent can
  stand that is near setpoint. **(b) The thermal drive axis is mis-scaled unless the
  survivable band is symmetric about the setpoint.** `core.py:88-89` computes
  `t_axis = (body_temp − temperature_setpoint) * (max_satiation / max_temperature)`, but
  its own docstring defines that denominator as "the distance from the setpoint at which
  the agent dies" — true only when the setpoint is 0. At setpoint 37 / max 42 the real
  danger range is 5, so the thermal axis would weigh about **8× too little**, silently.
  **The obvious guard is the wrong one:** warning on a non-zero setpoint misses
  `setpoint 0, min −10, max +20`, where the setpoint *is* zero and full-scale cold still
  weighs half of full-scale heat. The condition is **asymmetry about the setpoint**, and
  the fix is a per-side scale or an enforced-symmetry rule — not merely swapping the
  denominator to `(max_temperature − setpoint)`, which still gets the cold side wrong.
  The loader today checks only `min < max` and `min <= setpoint <= max`
  (`config_loader.py:1530-1540`). Shipped values (`0 / −15 / +15`) are symmetric, so
  **nothing is wrong at today's settings**. Ref: [[thermal_handover]] Task 3.
- [ ] **E2 — Fold food-vs-fire separation into the entity-placement algorithm update.**
  The user intends to revise entity allocation generally, so this is a requirement for
  that work rather than a config tweak. Measured over 20,000 real resets of the campfire
  config: **28.66%** of episodes place food within 1 Manhattan cell of a fire (95% CI
  28.03-29.29), and **27.37%** put such food on a cell warm enough to occupy
  indefinitely — those episodes contain no warmth-versus-food trade-off at all, yet count
  as thermal episodes in every aggregate. Only **8.30%** of individual food items are
  affected, so the task is not broken; the cost is an optimistically biased and noisier
  estimate of thermal competence. The existing knob `thermal.food_min_fire_distance` is
  **verified genuinely wired** (mandatory read, real second placement pass) and binds at
  `2` with the food count unchanged and nothing hitting the cell-(0,0) fallback; `2` is
  the smallest binding value and sufficient because the comfort ring is one cell wide,
  while `3` would wrongly clear the genuinely-hard distance-2 band. Whether the new
  algorithm keeps this knob or subsumes it is the open design question. Changing it is a
  critical-settings change and needs a same-commit dated entry in
  [[CONFIG_CRITICAL_SETTINGS]]. Ref: [[FOOD_FIRE_SEPARATION_MEASUREMENT]].

---

## Reference block

**Key commits this session:** reward `ef0fd25`, GAE `3c60f6f`, dreamer continue-head
`5b093bf`, eval E `a3ab4cc` / A+L3 `2ad9104` / L2 `863052f`, parity F `0bebe06`,
measures-off `9eacf82`, true-obs recover `80d3b70`, range fix `7ff8d1f`.

**Full record:** [[KNOWN_BUGS]] · **Diagnosis:** [[v3_pipeline_correctness_diagnosis]]
