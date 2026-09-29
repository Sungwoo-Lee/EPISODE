# Algorithmic view of the modulator null — TODO

Running TODO list from the 2026-09-29 conversation on whether the modulated-vs-ordinary
null has an algorithmic cause. Source for a later artifact; items are added as they are
agreed. Evidence and reasoning behind them:
[[CROSS_STUDY_NULL_DOSSIER]],
[[20260929_nmn_null_algorithmic_film_conditions]],
[[20260929_nmn_null_algorithmic_rl_side]].

## Break the shared starting point

**Why.** Across very different worlds the modulated-minus-ordinary gap is not scattered
the way noise would scatter it — it is pinned near zero (level-05 factorial: +3.6 steps,
16 of 16 worlds the same sign). The code gives a reason the two arms are not independent
agents: the main network's layers are constructed *before* the modulator
(`src/models/recurrent_ppo_network.py`: encoder l.400, actor/critic l.424-429, modulator
l.458), deliberately so the RNG stream is untouched (`neuromodulator.py`, plan D11). With
the same seed the modulated agent's main network therefore starts with *exactly* the
ordinary agent's weights, sees the same environment stream, and FiLM starts near identity
(gain 1 ± 0.3, offset ≈ 0). Small clipped PPO steps can then keep both runs in the same
basin. Test whether the identical results come from that shared start or from a real
equivalence.

- [ ] **Train modulated agents whose main network starts from a different seed than their
      paired ordinary agent.** If the gaps then scatter at the size of ordinary
      seed-to-seed variation, the shared start produced the identical results; if they
      stay pinned near zero, the equivalence is real.
- [ ] **Or keep the same seed but give the modulator a stronger start:** zero-initialised
      heads so FiLM is exactly identity, combined with its own learning rate, so its early
      gradient is not swamped by the ~100x larger main network.

## Measure when the modulator wakes up

**Why.** FiLM's advantage in RL is mostly learning *speed*, yet the modulated agent does
not learn faster. One candidate reason: the modulator only becomes influential late. The
training-health audit found its share of the gradient *grows* over training (40-75% of
the squared gradient norm in encoder and four-site arms by the end, under MC). A
component that only starts working in the second half can shape the final solution —
consistent with the freeze cost — but cannot shorten the early climb, which is where a
speed advantage would appear. Make "wake-up" a measured quantity rather than a story.

Metrics, per run, over training (built run-agnostic so any modulated run can be scored):

- [ ] **Gradient share** — modulator's share of the total gradient per update,
      `‖∇θ_mod‖² / ‖∇θ_all‖²`, split by loss term (policy / value / entropy), since the
      value loss also trains the modulator. Check what the trainer already logs first.
- [ ] **Relative update size** — `‖Δθ_mod‖ / ‖θ_mod‖` against the same ratio for the main
      network. Adam normalises gradients, so gradient share alone can mislead about how
      fast the modulator's weights actually move.
- [ ] **Output activity** — the contextual fraction ρ and the reachable gain swing at each
      of the 50 checkpoints: when does the modulator's *output* start varying with the
      situation? (Swing is already known to grow ~1.64x over training.)
- [ ] **Functional influence** — the freeze-at-mean survival cost at a subset of
      checkpoints (e.g. every 5th): when does the modulation become load-bearing? This is
      the expensive one (paired replays per checkpoint).
- [ ] **Wake-up lag** — the summary number. `t_wake` = first checkpoint where a metric
      reaches 50% of its final value; `t_plateau` = first checkpoint where trailing-window
      survival reaches 90% of its final value. **Lag = t_wake − t_plateau.** A positive lag
      means the modulator wakes after learning has levelled off, so it structurally cannot
      speed learning.

Compare across arms: MC vs GAE_NORM (MC agents lean on the modulator ~2x more), and
body-only vs all-senses modulators. The same metrics are the success criterion for the
"stronger start" item above: exact-identity init plus the modulator's own learning rate
should pull `t_wake` earlier and shrink the lag — and if the lag shrinks but learning
speed does not change, late wake-up was not the cause.

Data note: newer runs (Wave 1/2, level-05 factorial, May replication) have 50 checkpoints
and load at HEAD; the site × input grid agents need Stage 1 of the saved-config compat
plan first. Gradient-share and update-size metrics need training logs — if the trainer
does not log them, they apply to future runs only.
