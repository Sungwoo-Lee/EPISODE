# Critique: the modulator null result, read from the reinforcement-learning and optimisation side

> One-line summary: in a task whose internal states are observed, whose reward already depends on them, and whose agent is recurrent, a forward-pass modulator cannot change the *optimal* policy — only the path training takes to it — so the project has spent a month measuring the one quantity (final survival level, one seed, last checkpoint) that theory says should coincide; the likeliest optimisation cause is that the shared advantage signal lets the 100×-larger trunk absorb every body-correlated pattern first, leaving the modulator a static re-tuning, and the cheapest test of that is a distillation experiment that needs no training run at all.

**Author**: professor-rl · 2026-09-29
**Scope**: the RL / optimisation / evaluation side of the question "why does the modulated agent perform and behave like an ordinary one?". The conditioning-architecture side (FiLM expressivity, gauge freedom of the affine parameters, redundancy of the conditioning signal) is `professor-dl-theory`'s, in a parallel memo; §6 says where the two arguments meet. The facts dossier by `experiment-analyzer` ([[CROSS_STUDY_NULL_DOSSIER]], `docs/experiments/active/modulator_clues/`) landed while this memo was being drafted; numbers are cited to their original documents, with the dossier's consolidated figures added where they sharpen a claim. The sibling architecture memo is [[20260929_nmn_null_algorithmic_film_conditions]] (`professor-dl-theory`, same day); §6 states where the two agree and where they divide the work.
**Builds on**: [[nmn_input_site_grid_optimisation_dynamics]] (the gauge identity and the per-term gradient gap, not repeated), [[20260518_film_as_hyperparameter_modulator_theoretical_audit]] (which of Doya's four knobs a forward-pass FiLM can reach), the two FiLM-in-RL surveys and the modulation-in-RL review, the return-normalisation survey and the PPO-implementation-details review. No edits to `src/`, `configs/` or `scripts/`.

---

## Verdict (plain language)

The project trains an agent to survive in a small grid world — eat, avoid predators, hide, keep its body within limits. One version of the agent carries a "neuromodulator": a 16-unit side network that reads the same senses and rescales the main network's layers. After a month of comparisons the modulated agent survives no longer and behaves no differently from the plain one. Every explanation so far has been about the world. This memo asks whether the learning algorithm is the reason.

Three things follow from reading the trainer rather than the environment.

**First, the task is one in which this kind of modulator cannot change what the best policy is.** The body signals are in the observation, the agent already has memory, and the reward is already computed from the body. A side network that reads the same inputs and rescales activations can only change *how* training gets to the best policy, not *where* that is. The published cases where such modulators help are exactly the cases where something is hidden, changing, or shared across tasks — and this project's main worlds have none of those. Its continual-world experiments do, and they are the only place the project has ever seen a positive result.

**Second, both networks are trained by one optimiser on one shared learning signal, starting from the same function.** The modulator receives no credit of its own for being state-dependent; a constant rescaling reduces the loss as well as a contextual one whenever the main network — a hundred times larger, on the same learning rate — has already absorbed the body-correlated part. That predicts precisely what was measured: about nine tenths of the modulator's output is static.

**Third, the comparisons could not have seen a real difference of the plausible size.** One seed per arm, read at the final checkpoint, on the mean of a coarse survival count — where the seed-to-seed spread alone is 2–4.5 steps and checkpoint churn is 2–19× the sampling error. Nobody has compared learning-curve area or time-to-threshold between a modulated and an ordinary agent with seeds, and that is the quantity the modulation literature's positive results are made of.

The ranked recommendations in §5 start with two diagnostics that cost no training at all.

---

## 1. What is actually being trained — the facts the argument rests on

Read from `src/models/recurrent_ppo_trainer.py`, `src/models/recurrent_ppo_network.py`, `src/models/neuromodulator.py`, `train.py` and `configs/models/recurrent_ppo/`. The loss and the gauge identity are already written down in [[nmn_input_site_grid_optimisation_dynamics]] §1; only what that memo did not need is added here.

| Fact | Where | Why it matters below |
|---|---|---|
| **One optimiser, one learning rate, every parameter.** `optax.chain(clip_by_global_norm(0.5), adam(lr))` with `lr = agent.lr_actor = 5e-4`, `wrt=nnx.Param`. The modulator's GRU, heads and per-unit baselines are in the same Adam as the trunk. `agent.lr_critic` (1e-4 in every config) is **never read** on the recurrent-PPO path. | `train.py:1253–1261`, `:774` | The modulator is not starved by a smaller learning rate; it gets the same per-parameter Adam step as everything else (§3.4). The dead `lr_critic` key is a config hygiene item for `bug-curator`. |
| **Full-batch updates.** The 128-env × 128-step rollout (16,384 samples) is one batch; `update_step` vmaps the loss over environments and takes one gradient step. Four epochs → **four gradient steps per rollout**, no minibatching. | `update_step`, `train_iteration` | PPO's clip at `ε = 0.1` on four full-batch steps is a very small trust region per iteration; the policy moves slowly and smoothly (§3.1). Approximate KL and clip fraction are not logged. |
| **MC mode: the advantage is the critic's residual against a z-scored window return.** `targets = z(G)`, `advantages = targets − V`, no separate advantage normalisation. GAE mode z-scores the advantage separately. | `train_iteration` | The scalar that weights the modulator's policy gradient and its value gradient is the same residual (§3.3). |
| **The temperature head divides the logits inside the loss**: `logits = logits / T`, then `log_softmax`, in both the surrogate and the entropy term. | `ActorCriticRNN.__call__` | `T` and the actor's output scale are not separately identifiable under this loss (§3.5). |
| **Pass-through initialisation, non-zero head weights.** Gain bias 1, offset bias 0, but head weight matrices are default-initialised. | `NeuromodulatorRNN.__init__` | The modulated run starts *near* the unmodulated function, not at it (per-unit spread ±0.3 at step 0, audit §8.1). |
| **Reward is already interoceptive.** `reward = drive(s_t) − drive(s_{t+1})`, drive = distance of (satiation, injury, temperature) from set-point; death penalty 100; episode cap 500 steps. | `src/environment/core.py:1186`, `calculate_drive`; [internal_state_reward page](../../experiments/active/internal_state_reward/internal_state_reward.template.html) | The homeostatic-RL objective (Keramati & Gutkin 2014) is **already in place**; recommending it (Q4) would be recommending the status quo. It also means the critic's target genuinely varies with the body — the criterion the modulation review said the project fails is in fact met (§2.3). |
| Six actions (four moves, rest, eat); logged entropy 0.48–0.67 nats against a 1.79-nat maximum, flat from the third decile of training. | `config_loader.py:2842`; [[TRAINING_HEALTH_AUDIT]] | The policy is peaked but not collapsed; the entropy bonus is a standing pressure, not a dead term (§3.5). |

---

## 2. Question 1 — is this a task in which modulation *can* help, from an RL standpoint?

### 2.1 The representational statement

Write the history as `h_t = (x_1, …, x_t)`. The ordinary agent is a policy of the history through a 128-unit GRU state `s_t`; the modulated agent is a policy of the history through `s_t` **and** a 16-unit GRU state `m_t` driven by the same inputs:

$$
\pi_\theta(a \mid h_t) = \mathrm{softmax}\big(f_\theta(s_t)\big), \qquad
\pi_{\theta,\phi}(a \mid h_t) = \mathrm{softmax}\big(f_\theta(s_t;\ \gamma(m_t), \beta(m_t))\big), \qquad
m_t = g_\phi(m_{t-1}, x_t).
$$

Because `m_t` is a deterministic function of the same history the trunk already sees, the modulated class is contained in the class of recurrent policies of slightly larger width (a 144-unit GRU carrying `(s_t, m_t)` with a bilinear readout). The task's internal variables — satiation, injury, temperature — are *in* `x_t`; the reward is a function of them; so the problem is Markov in what the policy sees up to the partial observability that the GRU is already there to handle. Hence

$$
\sup_{\theta,\phi} J(\pi_{\theta,\phi}) \;\approx\; \sup_{\theta} J(\pi_{\theta}),
$$

with equality up to capacity, and the **optimal policy is the same for both architectures**. A forward-pass modulator changes the parameterisation — the geometry of the loss surface, the conditioning of the gradient, the inductive bias — and therefore can change *the path* (speed, which basin, seed variance, robustness under shift). It cannot change *the destination*. This is the RL-side statement of the same fact the architecture memo will make from expressivity; the consequence for experimental design is the point: **every quantity the project has compared is a destination quantity.**

The contrast that matters: a modulator that changes the *objective* — the entropy temperature with the logit scale pinned, the discount, the risk level of a distributional critic — does change the fixed point, and a behavioural difference between architectures is then expected even in a Markov task. §5 ranks those.

### 2.2 Where conditioning helps in the literature, and whether this project's worlds contain it

The surveys already held ([[film_in_rl_survey]] §5, [[modulation_in_rl_lit_review]] Q4) sort the positive results by the regime that produced them. Restated as RL conditions and matched against the project's worlds:

| Regime in which conditioning / gating helps | Mechanism (RL terms) | Precedent | In the project's single-world runs? | In `continual_worlds`? |
|---|---|---|---|---|
| **Context hidden from the policy** (latent task, unobserved fault, belief state) | the modulator carries information the policy input lacks; concatenation vs multiplicative routing is then a real design choice | VariBAD/PEARL-style meta-RL; Marquis (fault vector only to the hypernetwork); HyperMARL | **No.** Body state is observed; the modulator reads the same vector | No |
| **Non-stationarity / distribution shift** within or across episodes | conditioning path adapts faster than the trunk; effect concentrated **out of distribution** | Marquis (in-distribution routes equivalent, OOD divergent); SplitAdapter (only beyond training range) | **No** — each world is stationary, and evaluation is in-distribution | **Yes** — A→B→A→B world switches |
| **Multi-task interference** | gating partitions the shared substrate; prevents gradient interference | Ben-Iwhiwhu; HN-PPO; Soft Modularization | No (one task) | Partially (worlds share the body, differ in ecology) |
| **Continual learning / forgetting** | frozen backbone + modulator; context-indexed subnetworks | ANML; HN-PPO with anchor; Xing 2022 | No | **Yes** — and this is where the project's one positive result came from ([[NMN_CONTINUAL_DOUBLE_RETURN_PROBE]]: +107–132 steps on return stages, one seed; 3-seed replication M1–M6 running today) |
| **Hard single task with within-episode phase structure** | conditioner carries structure the network exploits; benefit is in **sample efficiency / final success under a fixed budget** | Yuan 2024 (hard tasks only); PAPL (gait phase, actor and critic) | Weakly — injury/satiation are a "phase", but observed and slow | Same |
| **Exploration / risk control** (state-dependent temperature, quantile level) | changes the objective, not the parameterisation | CAT-SAC; IQN's `τ`-FiLM; CVaR-PPO | The temperature head exists but is gauge-absorbed (§3.5) | Same |

So: in the project's main comparisons **none of the four regimes in which the literature predicts a difference is present**, and the fifth (hard task, phase) predicts a *sample-efficiency* difference, which has not been measured (§4.4). `continual_worlds` and the May double-return probe are the only designs that supply a regime with a predicted effect; the pilots there show the two agents within a step of each other in the *new* worlds (Danger 76.8 vs 76.8, Fog 92.2 vs 92.0 — [[CONTINUAL_WORLDS]] Revision 1a), which is what one expects *within* a stationary stage; the prediction is about the *switches* and the *returns*, and the replication is the right test of it.

### 2.3 One correction to the reviewed literature's reading of us

The modulation review's Q5 says "our reward is not a function of the modulator's input" and concludes the critic has nothing to gain from modulation (PAPL's criterion). That was wrong when written and is wrong now: the reward is the drive difference, the drive is a function of satiation, injury and temperature, and those are in the modulator's input. PAPL's criterion — modulate the critic where the value function genuinely varies with the conditioner — is *met* here. The cheap diagnostic the review asked for (critic values conditioned on the phase variable separate?) is worth running anyway, because it is also the test of whether the *trunk* has already made the critic state-dependent without any modulator, which is what §3.3 predicts.

---

## 3. Question 2 — optimisation-side reasons two architectures land on the same performance

Ranked by how much of the observed pattern each explains. Each ends with the cheapest diagnostic that confirms or kills it.

### 3.1 Same destination, same road: PPO's trust region from a shared starting point

Both runs start from (nearly) the same function — the modulated network is the unmodulated one with identity gains — see the same data distribution at every iteration they agree on, and take four full-batch clipped steps per 16,384 samples with `ε = 0.1`. The clip bounds the per-iteration policy change; the effective step is small and smooth. Two optimisation trajectories that start at the same point on the same surface and take small steps down the same early gradient (dominated, early, by the trunk — §3.3) will tend to enter the same basin; the modulator's extra dimensions are then filled in *around* a solution the trunk found. **This predicts** near-identical survival curves *and* a non-trivial freeze cost (the modulator's dimensions have been co-adapted to), which is what was measured.

*Diagnostic (offline, on saved checkpoints).* On a fixed probe set of episodes, the KL divergence `KL(π_mod ‖ π_ctrl)` per checkpoint pair, compared against `KL(π_ctrl,s42 ‖ π_ctrl,s43)` from the five unmodulated seeds. If the modulated-vs-control divergence sits inside the seed-vs-seed band throughout training, the two architectures are in the same basin and the null is a basin fact, not a capacity fact. Needs no training.

### 3.2 The shared credit signal, and why static absorption wins — the cause I rate most likely

Every parameter in the network, modulator included, is trained on the same scalar per timestep: in MC mode the residual `r_t = z(G_t) − V_t`, in GAE mode the normalised advantage, both through the clipped surrogate, the value MSE and the entropy term. **Nothing in the objective rewards being state-dependent.** Decompose a site's gain into its time-average and its contextual deviation, `γ_t = γ̄ + δγ_t`, with `δγ_t = W(h^m_t − \bar h^m)` (this memo's notation follows [[nmn_input_site_grid_optimisation_dynamics]] §1.1). Writing `J_t` for the backpropagated error at the site times the pre-FiLM activation, the two gradients are

$$
\frac{\partial \mathcal L}{\partial \bar\gamma} = \sum_t r_t\, J_t
\qquad\text{(a sum)},
\qquad\qquad
\frac{\partial \mathcal L}{\partial W} = \sum_t r_t\, J_t\, (h^m_t - \bar h^m)^{\top}
\qquad\text{(a covariance)}.
$$

The static direction is driven by the *mean* of the residual-weighted error; the contextual direction by its *covariance with the modulator state*. The second is smaller than the first by the correlation between what `h^m_t` encodes and what the residual wants — and that correlation is exactly what the trunk, reading the same input with ~100× the parameters and the same Adam step, removes first, because it lowers the loss along a much steeper direction. What is left for the contextual channel is the part of the residual that the trunk *cannot* explain from the observation — which, if the task is Markov in the observation, is noise. Under Adam the static direction then drifts at learning-rate speed with no restoring force (the gauge argument, §2.2 of the earlier memo), while the contextual weights are trained on a low-signal covariance.

**This predicts** (i) a modulator whose output variance is mostly static — measured: contextual fraction 0.148 ± 0.085 across the thirty modulated arms ([[CROSS_STUDY_NULL_DOSSIER]] §5.4), 5 % at the memory core, 8 % at the encoders, ~20 % at actor and critic ([state-dependence page](../../experiments/active/state_dependence/state_dependence.template.html) Fig. 3), i.e. ~85 % static; (ii) a freeze-at-mean cost that is large (47–180 of ~210 steps in the all-sensor arms; gain alone −63 ± 68, offset alone −73 ± 66, both −133 ± 71 across arms — dossier §5.4) because the trunk has co-adapted to the *specific* static and contextual values, not because the contextual part is doing work the trunk could not; (iii) a larger freeze cost under MC than GAE_NORM (measured ≈ 2×), because MC's longer-horizon residual carries more slow, body-predictable variance for the modulator's covariance to lock onto ([[nmn_input_site_grid_optimisation_dynamics]] §4.2) — with no survival consequence either way, since the trunk could have absorbed the same variance.

*Diagnostic — the distillation test (offline, minutes of GPU).* Behaviour-clone a **fresh unmodulated** `ActorCriticRNN` onto the modulated agent's recorded rollouts (the million-episode trajectory stores hold observations and actions), then evaluate survival on the same probe worlds. If the clone reaches the modulated agent's survival, the modulated policy lies inside the unmodulated function class and the freeze cost is co-adaptation, not capability: **the null is representational and settled.** If the clone falls short by more than the seed band, the modulated policy uses history in a way the plain GRU does not learn to — which would be the first positive representational finding of the programme. This is the single most informative cheap experiment available and it has never been run.

*Second diagnostic (one logging change).* The modulator's gradient norm split by loss term and the **gradient signal-to-noise ratio** per parameter group: the cosine between successive iterations' gradients (or the gradient-noise scale of McCandlish et al. 2018), for the modulator heads versus the trunk. The earlier memo showed the modulator's *share* of the squared gradient norm rising to 40–75 % late in training; this asks whether that norm is signal or variance. A modulator whose successive gradients have near-zero cosine while the trunk's stay positive is being trained on noise — §3.2 confirmed.

### 3.3 Value-function interference when the critic is modulated

In every modulated arm the critic reads the modulated trunk; in the `crt` and `quad` arms its hidden layer is FiLMed directly. The value loss is dense (every timestep, weight 0.5, supervised) where the policy term is sparse in information (sign of an advantage); a modulator that can lower the value MSE by conditioning `V` on the body will do so, and under MC mode that *also* shrinks the advantage `z(G) − V` it feeds the actor. The earlier memo's numbers argue against this being the dominant effect — the value loss is flat at ≈ 0.23 in every arm, modulated or not, so the critic is already at its floor and the modulator did not lower it. Kept as a secondary candidate; the per-term gradient split of §3.2 settles it (growth in the value term → interference; in the policy term → §3.2).

### 3.4 Learning-rate starvation — excluded by the logs

The modulator sits on the same Adam(5e-4) as the trunk; Adam's step is per-parameter normalised, so its ~6 k parameters move as far per update as any trunk parameter. The audit's own numbers show its gradient *share* rising, not falling. Starvation is not the problem; the problem is what the gradient contains (§3.2). A per-group learning-rate sweep would be GPU-hours spent on a hypothesis the data already exclude.

### 3.5 Exploration and the temperature head — the one channel that could have mattered is gauge-absorbed

Two facts about the plateau. The unmodulated agent improves by +4.5 steps over the second five million episodes ([[return_mode_cmp_10M]]), the return-mode arms differ **ten-fold** in experience-to-threshold, and the textbook-convention arms at one million episodes sat still and starved. That is the signature of a plateau set by exploration and credit assignment, not by representational capacity — and a forward-pass modulator does not change the data distribution, so it cannot move such a plateau. The exception is the temperature head, the project's one Doya-style knob, and here the loss makes it inert. With `logits = W a / T` inside both the surrogate and the entropy term, the map `(W, T) → (cW, cT)` leaves the policy unchanged, so `T` and the actor's output scale are one degree of freedom, not two. The entropy bonus pushes `T` up at every step (raising `T` raises `H`); the surrogate pushes `W` up to compensate; the head rails at its clip — exactly v8 Finding 4 (all MC FiLM runs at `T = 3.0`, the ceiling). **A railed temperature is not "the modulator asking for more exploration"; it is the entropy regulariser pushing along a flat direction.** Only the *contextual* part of `T` is identifiable, and nothing pins the scale so that the contextual part has to carry the entropy. The RL-side fix is in §5 (rank 5): pin the logit scale, so that a state-dependent `T` is the only route to state-dependent entropy.

### 3.6 Return mode and scale

The MC/GAE_NORM pair is the best-controlled contrast the project has, and it says: the estimator changes how much the modulator is *relied on* (2× freeze cost under MC) without changing survival. Under §3.2 that is expected — MC's residual has a longer effective horizon (≈ 20 steps vs ≈ 10 for `γλ = 0.9`), so more of it is predictable from slow body variables, and the modulator's covariance term has more to lock onto. It does not follow that MC lets the modulator do more useful work; the distillation test (§3.2) run on an MC and a GAE_NORM checkpoint side by side would show whether the extra reliance is extra capability.

### 3.7 Ceiling and headroom

In the 10×10 basic/04 world both architectures plateau at ≈ 165 of a 500-step cap, so the cap is not binding; in the deliberately safe Forage world both reach 475/500 and the cap *is* binding, so no comparison there can show anything ([[CONTINUAL_WORLDS]] Revision 1a). What the best achievable level in the main worlds is has never been measured: no oracle agent, no privileged-information upper bound, no longer-budget run to see whether 165 is an asymptote or a slow climb. Deaths in the pilot worlds split ≈ 45 % injury / 40–45 % starvation, so neither hazard is solved. A cheap headroom probe — an unmodulated agent given the true state (predator positions, no sensory noise) — would bound the room a modulator could possibly occupy; if the privileged agent also sits near 165, the plateau is a credit-assignment limit and no representational change will move it.

---

## 4. Question 3 — evaluation-side reasons a real difference could be invisible

### 4.1 One seed against the seed-to-seed spread

Every modulated-vs-ordinary contrast in the site grids, the state-dependence study, the injury-dependence study and the May probe is one training run per arm. The project's own dispersion measurements: five unmodulated MC seeds finished 162.4–166.9 steps (spread 4.5, SD ≈ 1.8) at 10 M episodes; five GAE_NORM seeds within 1.3; the temperature-ceiling rerun found ± 4.4 steps in a different world; the state-span behavioural measure has a 1.25-point seed SD. For a two-arm comparison at 80 % power and two-sided 5 % the required seeds per arm are

$$
n \approx 2\,(z_{0.975} + z_{0.8})^2\,\frac{\sigma^2}{\Delta^2} \approx 15.7\,\frac{\sigma^2}{\Delta^2},
$$

which gives **3 per arm** to see a 5-step survival difference at σ = 2, **13 per arm** at σ = 4.4, **10 per arm** for a 2.5-step difference at σ = 2, and **9 per arm** for the 1.7-point behavioural difference the state-dependence page reports against its 1.25-point σ. At n = 1 the power to see any of these is at the false-positive rate. The measured gaps are all inside these bands: site grid under MC, modulated mean +1.7 steps (SD 2.2 across cells) on a control of 164.5; under GAE_NORM, −0.2 (SD 1.6) on 170.6; level-05 body-rules factorial +3.6 (16 of 16 cells positive, but every ordinary run shares one initialisation and every modulated run another, so seed and initialisation are confounded) — [[CROSS_STUDY_NULL_DOSSIER]] §3 rows 1, 2, 6. Read against the arithmetic above, a consistent +2 to +4-step lead is exactly the size a single seed cannot adjudicate and ten seeds could. The M1–M6 replication (3 seeds per arm) is the first modulator contrast in the programme with power against a large effect; it has none against a moderate one, and its design already says so.

### 4.2 Last checkpoint versus window

The project has already been bitten: reading a behaviour measure off the final checkpoint manufactured a 60-percentage-point level-04 effect that is 0.8 points (p = 0.92) over the last ten checkpoints, and checkpoint-to-checkpoint policy variation is 2–19× the 30-episode sampling error (diary 2026-09-23, "The Last Checkpoint Lies"). This is policy **churn** — the per-update drift of a PPO policy under a fixed data distribution — and it is intrinsic to the optimiser, not to the environment; more evaluation episodes per checkpoint buy nothing. The state-dependence page's Fig. 5 (four-from-four that flips sign across worlds) and its own §8 caveat are the same phenomenon. Rule: every survival or behaviour number for a modulator contrast is a **trailing-window mean over the last ≥ 10 checkpoints**, and its error bar is the across-checkpoint SD *plus* the seed band, never the within-run interval.

### 4.3 Survival steps as a coarse proxy

Mean survival is a scalar summary of a censored distribution (cap 500). A modulator that changes *risk* — fewer catastrophic early deaths, same median; or a longer tail with more early deaths — is invisible in the mean and is precisely the kind of change an interoceptive modulator is supposed to make. Report survival **quantiles** (10th, 50th, 90th), the **conditional mean of the worst decile** (the CVaR-style statistic), and the cause-of-death split, per arm, per window. These are free from data already on disk.

### 4.4 Sample efficiency has not been tested for the modulator contrast

The FiLM-in-RL positives are budget-limited results: Yuan's hard-task success rates under a fixed number of demonstrations, MENTOR's sample efficiency, PAPL's convergence, Marquis's out-of-distribution robustness. The project *has* the tooling — [[return_mode_cmp_10M]] measured experience-to-threshold (6–14× between return modes), the Dreamer curriculum study measured episodes-to-200-steps, and the site-grid design registered "time to reach 100 survival steps" and "late-training slope" as secondary outcomes. **No modulated-versus-ordinary comparison has reported learning-curve area or time-to-threshold with seeds.** The one anecdote — v8's per-neuron FiLM "led early then crashed" — is the shape a sample-efficiency effect would take, and it was read as a failure rather than measured as a rate. The answer to "has sample efficiency been tested?" is no.

---

## 5. Question 4 — algorithmic changes, ranked by expected information per GPU-hour

| Rank | Change | GPU cost | What a positive means | What a null means |
|---|---|---|---|---|
| 1 | **Distillation test** — clone an unmodulated net onto the modulated agent's rollouts (§3.2) | ≈ 0 (supervised, minutes) | modulated policy is outside the plain class: first representational positive | representational null settled; freeze cost is co-adaptation |
| 2 | **Re-read existing runs**: trailing-window survival, AUC, time-to-threshold, quantiles, policy-KL vs seed band, per-term gradients where logged | 0 | a sample-efficiency or tail effect the endpoint mean hid | the null holds on every destination *and* path quantity the logs allow |
| 3 | **Auxiliary body-dynamics objective** on the modulator state | 3 seeds × 2 arms × 1 world ≈ 6 runs | modulator becomes contextual (ρ ↑) *and* survival/AUC moves: the credit signal was the problem | modulator can be made to encode the body and the policy still gains nothing: the task is the problem |
| 4 | **Blind the trunk to interoception; modulator alone reads it** | 3 seeds × 3 arms ≈ 9 runs | multiplicative routing beats concatenation on our task (Yuan-type result) | the two routes are equivalent here; H5 is a routing-indifference finding |
| 5 | **Meta-parameter modulation done identifiably**: pin the logit scale so `T(m_t)` is the only entropy route; optionally risk level `τ(m_t)` on a quantile critic | temperature: contained, ≈ 6 runs; distributional critic: invasive | state-dependent entropy / risk aversion tracks injury: an *objective*-changing modulator differs where a forward-pass one cannot | exploration is not state-limited; risk sensitivity not what the task rewards |
| 6 | **Non-stationary schedules with powered AUC read-outs** (M1–M6, `continual_worlds`) | in flight | forgetting / recovery advantage replicates: a plasticity mechanism, publishable | May result was a seed |
| 7 | **Interoceptive reward term** | — | **already implemented** (drive difference); nothing to add unless the objective is made risk-sensitive (rank 5) | — |

### 5.1 Distillation (rank 1)

*Mechanism.* Behaviour cloning is a supervised projection of the modulated policy onto the unmodulated function class; the projection error, measured in survival on the same probe worlds, is the representational gap. *Prediction under §3.2:* zero gap within the seed band. *Minimal experiment:* one modulated checkpoint per return mode (MC, GAE_NORM), one clone each, evaluated on the same 2,000-world probe as [[return_mode_cmp_10M]] §4.9. *Null:* a gap larger than the seed band — then and only then is the architecture doing something the trunk cannot, and the programme has its first representational lead.

### 5.2 Auxiliary objective on the modulator (rank 3)

*Mechanism.* Add to the loss a prediction head on `h^m_t` with a stop-gradient into the trunk:

$$
\mathcal L_{\text{aux}} = \lambda_{\text{aux}}\ \mathbb E_t\Big\|\, \hat y(h^m_t) - y_{t+k} \,\Big\|^2,
\qquad y \in \{\Delta\text{drive},\ \text{injury}_{t+k},\ \text{drive}_{t+k},\ \mathbb 1[\text{bite in } (t, t+k]]\},
$$

so the modulator state is forced to be a sufficient statistic of body dynamics rather than free to become a static rescaler. This is the SPR / UNREAL / auxiliary-task pattern applied to the conditioner, and it gives the modulator a learning signal that is *not* the shared advantage — the direct remedy for §3.2. *Prediction:* contextual fraction ρ rises from ≈ 10 % toward the majority; the body-state `R²` of the gains becomes large; survival or AUC moves only if the policy then uses the state. *Minimal experiment:* `λ_aux ∈ {0.1, 1}`, `k = 5`, three seeds, the level-05 world (where injury dependence was largest), trailing-window AUC as primary. *Null:* ρ rises and nothing behavioural moves — the decisive version of the representational null, because the modulator has been *shown* to carry the body signal. Contained change (one head, one loss term); `senior-developer`.

### 5.3 Information restriction (rank 4)

*Mechanism.* Remove the interoceptive channels from the trunk's input (`Injury`, `Nutrition`, temperature) and route them **only** through the modulator (`input_sensors: [Injury, Nutrition, …]`). Now the modulator carries information the policy genuinely lacks — the configuration every positive precedent shares (Vecoven, Marquis, Yuan) — and the design becomes identifiable. Three arms: (a) full-observation ordinary agent, (b) trunk-blinded ordinary agent (the floor), (c) trunk-blinded modulated agent. *Prediction:* (c) ≫ (b) trivially; the comparison that carries information is (c) vs (a). Equal → multiplicative routing and concatenation are equivalent here (a clean routing-indifference result, and the end of H5 as a survival claim). (c) > (a) → the Yuan routing win, on a hard-enough task. (c) < (a) → FiLM is a lossy channel for a slow scalar. *Cost:* config-only for the modulator side; blinding the trunk is a small encoder change. Three seeds per arm.

### 5.4 Meta-parameter modulation, done identifiably (rank 5)

The May theoretical audit sorted Doya's four knobs: temperature and TD-gain are forward-pass-reachable, learning rate only via gradient gating, discount only via a γ-conditioned critic. The RL-side addendum is that **reachable is not the same as identifiable under this loss** (§3.5). Ordered by cost:

- **Temperature with a pinned logit scale** (contained). Normalise the actor's logits to fixed norm (or constrain `‖W‖` of the last layer) so that `T(m_t)` is the sole scale. Then the entropy bonus can only be satisfied by moving `T`, and a body-dependent `T` is a body-dependent entropy — H3 becomes testable. *Prediction:* entropy co-varies with injury (H3's direction is itself a hypothesis: lower entropy when injured). *Null:* `T` still rails or is flat — per-state exploration is not what the plateau is about. Precedent: CAT-SAC's state-dependent `α(s)` with a zero-mean constraint; Agent57's policy family indexed by an exploration knob.
- **Risk level on a distributional critic** (invasive). Replace the scalar critic by a quantile critic and let the modulator set the quantile level `τ(m_t)` at which the advantage is read — IQN's own cosine-FiLM on `τ`, with `τ` now interoceptive. Injury → lower `τ` → risk-averse policy. This is the **one design in which an interoceptive modulator changes the optimum**, so a behavioural difference is predicted even in a Markov task; and it is the correct RL formalisation of "a hurt animal weighs bad outcomes more". Cross-cuts critic, advantage and return target; `senior-developer` plan required. Read-out: survival *quantiles*, not the mean (a risk-averse policy can lower the mean while raising the worst decile — §4.3).
- **Discount `γ(m_t)`** — invasive (γ-conditional value function, Γ-nets), and the 5-HT branch is the corpus's weakest; not recommended now.
- **Learning-rate gating** — a meta-gradient / gradient-reparameterisation mechanism (Xu et al. 2018; Rodriguez-Garcia 2026), not a forward-pass FiLM; belongs to a different architecture and to Paper 2.

### 5.5 Non-stationary schedules (rank 6)

The regime with a predicted effect is already in flight. Two RL-side additions to its analysis: (i) read **area under the recovery curve** and time-to-threshold on every return stage, not only the plateau, because the mechanism the literature proposes (Rodriguez-Garcia's stability-gap attenuation; Lee 2024's forgetting resistance) is a *rate* effect; (ii) log the **dormant-unit fraction** at stage boundaries for both agents ([[nmn_input_site_grid_optimisation_dynamics]] §3.1). If the modulated agent recovers faster *and* keeps more units alive, the mechanism is plasticity preservation — a real, publishable optimisation effect, but it is not "state-dependent behaviour" and should not be written up as if it were.

### 5.6 Interoceptive reward (rank 7) — already there

The objective is `r_t = drive(s_t) − drive(s_{t+1})`; internal state already shapes the objective, not only the input. What is *not* there is any risk-sensitivity in how that reward is aggregated — which is rank 5's second item. Recommending "add a homeostatic reward" would recommend the status quo; the review that said the critic has nothing to gain from the body was mistaken on this point (§2.3).

---

## 6. Where this memo meets the architecture memo

`professor-dl-theory`'s sibling memo ([[20260929_nmn_null_algorithmic_film_conditions]]) reaches the same verdict from the architecture side — no *regime* variable, so any conditioner ties; the freeze cost is co-adaptation through a rank-16 bilinear shortcut — and recommends a three-seed 2×2 crossing conditioner exclusivity with world alternation. The two memos divide cleanly: §5.3 here is the *exclusive* half of that 2×2 and §5.5 the *alternating* half, so one design (theirs, with `experiment-designer`) serves both; the distillation test (§5.1) and the credit-signal mechanism (§3.2) are this memo's additions and are what would tell co-adaptation from capability. That memo owns the statement that the static part of a FiLM output is a gauge freedom absorbable into the modulated layer, and the expressivity argument that a self-conditioned modulator is redundant. This memo takes both as given and adds what the *training loop* does with them: (a) under a shared advantage signal and a shared Adam, the gauge direction is *where the modulator's gradient goes* (§3.2), so redundancy is not merely possible but the predicted outcome; (b) the temperature head has its own gauge with the actor's output scale, and it is the entropy term of the loss that drives it to the rail (§3.5); (c) representational equivalence (§2.1) means the destination quantities the project measured cannot separate the architectures, so the experimental remedy is on the measurement side (§4) or on the objective side (§5.4), not on the conditioning-architecture side. Where the two memos would disagree is if the architecture memo argues for more expressive conditioning (hypernetwork, LoRA); §2.1 says that changes nothing unless the *objective* or the *information* changes.

---

## 7. Relation to the project's anchors

- **The v8 null and its causes.** The "four causes in `project_plan.md` §4" anchor no longer resolves (the plan is now organised by paper; noted already in the earlier memo). Against v8's own findings: Finding 4 (temperature saturation) is explained by the logit-scale gauge under the entropy bonus (§3.5); Finding 5 (the modulator widens the MC–GAE gap) is consistent with a modulator adding gradient variance to a critic that reads it (§3.3, §3.6); Finding 1 (no benefit under noise) is what §2.1 predicts for any stationary, observed-context world.
- **Phase 2 / Phase 3.** The temperature head and any distributional-critic variant are the two items in §5.4; the RL-side verdict is that Phase 2's FiLM-variant characterisation cannot produce a survival difference in the current worlds and should be re-scoped to path quantities (AUC, seed variance, contextual fraction) or to objective-changing variants.
- **H1–H5.** H1, H2, H4 are parameterisation hypotheses and are subject to §2.1: testable only as within-run, event-locked contrasts, never as survival. H3 (exploration suppression via temperature) is currently untestable because `T` is gauge-absorbed; §5.4 makes it testable. H5 (chronic-pain analogue through modulator timescale) interacts with GAE λ: the modulator's contextual channel is driven by the residual's horizon (§3.6), so a slow modulator state will only be *trained* to persist if the return estimator's horizon exceeds the healing timescale (≈ 20 steps in cover); under `γλ = 0.9` (≈ 10 steps) it will not, under MC it might. That is a concrete, cheap prediction: H5-type persistence, if it ever appears, appears under MC and not under GAE_NORM.
- **Continual worlds / May replication.** The only regime with a predicted effect; §5.5 says what to read.

---

## 8. Precedents and missing references

Held and used: Andrychowicz et al. 2021 and Engstrom et al. 2020 (what matters in PPO; area-under-curve as the score in the 250,000-agent study — the project's endpoint-only convention is the outlier), Huang et al. 2022 (the health metrics this trainer does not log), Yuan 2024 / PAPL / Marquis / SplitAdapter (single-task FiLM positives and their regimes), Vecoven 2020 and Ben-Iwhiwhu 2022 (conditioner information content), CAT-SAC (state-dependent temperature), IQN (FiLM on the quantile level), Doya 2002 and Lee 2024 (meta-parameter mapping), Sokar 2023 / Abbas 2023 / Lyle 2022–24 (dormancy and plasticity), Keramati & Gutkin 2014 (the homeostatic reward already implemented).

Not held, needed to cite §3.1, §3.2, §4.2 and §5 properly — for `literature-reviewer`:

- Tang & Berseth 2024, *Improving Deep Reinforcement Learning by Reducing the Chain Effect of Value and Policy Churn* (NeurIPS) — the churn mechanism behind "The Last Checkpoint Lies"; and the ICML 2025 churn-reduction paper already listed in the recent-variants survey.
- McCandlish, Kaplan, Amodei & OpenAI Dota team 2018, *An Empirical Model of Large-Batch Training* — the gradient-noise scale used as the per-group SNR diagnostic (§3.2).
- Jaderberg et al. 2017, *Reinforcement Learning with Unsupervised Auxiliary Tasks* (UNREAL, ICLR) and Schwarzer et al. 2021, *Data-Efficient RL with Self-Predictive Representations* (SPR, ICLR) — the auxiliary-objective pattern of §5.2.
- Rusu et al. 2016, *Policy Distillation* (ICLR) — the distillation test of §5.1 as a representational probe.
- Tamar, Glassner & Mannor 2015, *Optimizing the CVaR via Sampling* (AAAI) and Dabney et al. 2018 (IQN, held) — the risk-level modulation of §5.4; Chow & Ghavamzadeh 2014 for CVaR policy gradient.
- Agarwal et al. 2021, *Deep RL at the Edge of the Statistical Precipice* (NeurIPS) — interquartile-mean and stratified bootstrap over seeds; the evaluation protocol §4 should adopt.
- Badia et al. 2020, *Agent57* / *Never Give Up* — the policy-family-indexed-by-exploration-knob precedent for an identifiable temperature (already on the FiLM survey's gap list).

The closest published design to "a self-conditioned forward-pass modulator trained end-to-end through the PPO loss on a Markov single task" remains PAPL and Marquis, and neither measures the quantity this memo says is decisive (the representational gap by distillation, or path quantities with seeds). If §5.1 and §5.2 are run and reported, the result — positive or null — is a small but genuinely unreported one.

---

## Next steps

- **`senior-developer`** — plan (i) the distillation script (§5.1: load a modulated checkpoint's trajectory store, behaviour-clone a fresh unmodulated `ActorCriticRNN`, evaluate on the standard probe), (ii) the policy-KL-vs-seed-band replay (§3.1), (iii) the per-term modulator gradient norms and per-group gradient SNR logging (§3.2), (iv) the auxiliary body-dynamics head with stop-gradient (§5.2), (v) pinned-logit-scale temperature (§5.4, contained). Items (i)–(ii) need no `src/` change beyond reading what the model returns. Flag the dead `agent.lr_critic` key to `bug-curator`.
- **`experiment-designer`** — (a) add trailing-window survival, AUC, time-to-threshold, survival quantiles and the CVaR-style worst-decile mean as pre-registered outcomes to M1–M6's analysis and to `continual_worlds` (§4, §5.5); (b) design the three-arm information-restriction study (§5.3) and the auxiliary-objective study (§5.2), three seeds per arm, level-05 world, with the seed-count arithmetic of §4.1; (c) a privileged-information headroom probe (§3.7).
- **`experiment-analyzer`** — fold §2.3 (the reward is already interoceptive; the critic-has-nothing-to-gain reading is wrong) and §4.4 (sample efficiency never tested for the modulator contrast) into the cross-study dossier; re-read the existing site-grid curves for time-to-100 and late slope, which the design registered and which cost nothing.
- **`professor-dl-theory`** — §6 names the three points where this memo relies on the gauge argument; the temperature/logit-scale gauge (§3.5) is a second instance of the same symmetry and is theirs to formalise if it goes into Paper 2.
- **`professor-bayesian-nn`** — if rank 5's distributional critic is taken up, the quantile head's calibration is theirs; this memo owns how `τ(m_t)` enters the advantage.
- **`literature-reviewer`** — the seven references in §8.
- **`pi`** — the portfolio call this memo implies: Phase 2 as currently scoped (FiLM-variant sweeps read on final survival) cannot succeed by §2.1; the choice is between re-scoping it to path quantities and information restriction (cheap, decisive either way) and moving to objective-changing modulators (rank 5, invasive, the only route to a behavioural difference in a stationary world).
