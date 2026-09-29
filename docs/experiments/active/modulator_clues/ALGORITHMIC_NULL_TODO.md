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
