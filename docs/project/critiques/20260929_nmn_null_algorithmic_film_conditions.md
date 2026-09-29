---
title: "Why the modulator neither helps nor hurts — the conditional-architecture reading of the null"
status: draft
author: professor-dl-theory
audience: user + pi + experiment-designer + senior-developer
date: 2026-09-29
scope: "Critique / direction memo. Re-reads the project's FiLM, hypernetwork and modulation-in-RL literature with one question: under what conditions does conditioning beat an equally capable unconditioned network, and which of those conditions does our design satisfy? Builds on, and does not repeat, the May 2026 hyperparameter-modulator audit and the September optimisation-dynamics critique."
one_line_summary: "The literature's conditions for a conditioning benefit are (i) a regime variable under which the optimal input-to-action map itself changes, and (ii) a problem hard or shifted enough that a single shared map cannot cover all regimes. Our stationary single-world design has neither; the observation-redundancy suspicion is correct in form but names the wrong mechanism — redundancy is a variance cost, not the missing benefit. The 'load-bearing when frozen, no advantage when trained from scratch' puzzle is co-adaptation: the modulated network distributes the same solution across two pathways, one of which is a rank-16 bilinear shortcut with the highest effective learning rate in the network. Top recommendation: a three-seed 2×2 crossing conditioner exclusivity with world alternation, which separates the two hypotheses in one experiment."
related:
  - 20260518_film_as_hyperparameter_modulator_theoretical_audit.md
  - nmn_input_site_grid_optimisation_dynamics.md
  - ../references/FiLM/film_in_rl_survey.md
  - ../references/FiLM/film_rl_recent_variants_survey.md
  - ../references/modulation_in_rl/modulation_in_rl_lit_review.md
  - ../references/Hypernetwork/hypernetwork_lit_review.md
---

# Why the modulator neither helps nor hurts — the conditional-architecture reading of the null

> One-line summary: conditioning pays in the literature only when a *regime variable* changes the input-to-action map and the problem is hard enough that one shared map cannot cover every regime; our stationary single world supplies neither, so the modulator degenerates into a re-parameterisation the main network co-adapts to. The "same observation" suspicion is right that the conditioner carries nothing the policy lacks, but the missing ingredient is regime structure, not information asymmetry. One three-seed 2×2 experiment separates the two.

## 0. Question and verdict (plain language)

**The situation.** The agent is a recurrent network that forages, avoids predators and manages hunger and injury in a grid world. Bolted onto it is a much smaller network — the "neuromodulator" — that reads the same senses every step and emits, for each unit of up to four layers of the main network, a multiplier (a *gain*) and an added constant (an *offset*). This gain-and-offset scheme is what the literature calls FiLM. Over a month of comparisons, dozens of runs, several worlds, the modulated agent has survived no longer and behaved no differently than an ordinary agent without it. Every explanation tried so far has been about the environment. This memo asks whether the cause is *algorithmic* — a property of the architecture and how it is trained.

**What the literature says a conditioning benefit needs.** I tabulated twenty-three papers that compare a conditioned network against an unconditioned one (section 2). The pattern is consistent. Conditioning beats a plain network when the steering signal indexes a *regime* — a task label, a language instruction, a gait phase, an actuator fault, a load, a painting style — under which the *right way to map inputs to outputs itself changes*, and when the problem is hard enough, or shifted far enough from training, that a single shared mapping cannot serve every regime at once. Whether the main network can also see the steering signal turns out **not** to be decisive: in the skateboarding-robot paper the phase signal is both fed directly to the policy *and* used to modulate it, and modulation still wins. What is decisive is that within one regime nothing is gained — every paper that tests an easy or in-distribution or single-regime case reports a tie.

**Verdict on the "same observation" hypothesis.** Correct in form, wrong in mechanism. It is true that our modulator carries no information the main pathway lacks, and true that no published RL modulator is wired this way. But redundancy of the *signal* is not what removes the benefit; the absence of a *regime* is. Our world is one stationary task family: hunger and injury are slow state variables inside a single optimal policy, not switches between different policies. In that setting the literature predicts a tie for *any* conditioner, redundant or not. What redundancy does add is a cost: a second, fast, high-variance pathway from the observation to the action, which the field's most recent multi-agent work identifies as a source of gradient interference. Net effect: nothing gained, a little variance paid — which is what a month of "no difference" looks like.

**The puzzle — load-bearing inside, no advantage outside.** Freezing the modulator's output at its own average costs a trained agent 47–180 of its roughly 200 survival steps, yet an agent trained without a modulator does just as well. The explanation this memo defends is *co-adaptation*: the modulated network has spread one solution across two pathways rather than found a better one. The modulator's pathway is a cheap multiplicative shortcut (a rank-16 bilinear term between the memory state and a fast summary of the current observation) that sits at the highest effective learning rate in the network late in training, so the optimiser keeps routing function through it. Freezing it removes a component of the computation, not a benefit — much as removing one attention head from a trained transformer is costly even though a transformer trained without that head does equally well. Three cheap measurements would confirm or refute this (section 4).

**What to do.** Ranked in section 5. The top recommendation is a three-seed 2×2 experiment: conditioner *exclusive* (body signals go only to the modulator, removed from the main network) versus *redundant* (as now), crossed with a *stationary* world versus an *alternating* one. The redundancy hypothesis predicts an advantage in the exclusive arms; the regime hypothesis predicts an advantage only in the alternating arms. The existing continual-worlds line is the right testbed for the alternating half, with two caveats spelled out in section 5.

**What this memo does not do.** It does not touch code or configs; every recommendation is a named hand-off. It does not re-derive the gauge identity of the September critique or the four-hyperparameter reachability analysis of the May audit; it uses both. All project numbers it quotes come from single-seed runs and inherit that caveat.

---

## 1. What this builds on, and what it does not repeat

Two prior critiques already established results this memo takes as given.

- The **May audit** ([[20260518_film_as_hyperparameter_modulator_theoretical_audit]]) showed that a forward-pass FiLM operator cleanly reaches a policy temperature and a per-context action prior; reaches a learning-rate-like effect only as a *coupled* gain-and-gradient gate acting upstream of the FiLM cut; and reaches a discount only when paired with an explicit context-dependent discount in the return estimator. I do not revisit hyperparameter modulation except to place it in section 5's ranking.
- The **September optimisation-dynamics critique** ([[nmn_input_site_grid_optimisation_dynamics]]) proved the per-unit affine gauge — the time-averaged gain and offset at any site can be absorbed into the modulated layer's own weights without changing the function — and predicted that under Adam without weight decay those averages drift indefinitely. The representation analysis that followed ([repr_analysis](../../experiments/active/nmn_input_site_grid/repr_analysis.html)) confirmed the gauge literally (the head bias `b` and the per-unit baseline `g` receive identical gradients at group size 1 and stay exactly 1.0 apart for ten million steps) and measured the three quantities that critique asked for: reachable gain swing ≈ 11, contextual fraction ρ ≈ 0.15, freeze-at-mean cost 47–180 steps.

The literature base is the project's own: the corpus FiLM-in-RL survey, the 2024–26 variants survey, the ten-paper full-text modulation-in-RL review with its thirteen adjacent reviews, the hypernetwork review, and the per-paper FiLM reviews. Where those documents already concluded something I cite rather than restate; where I disagree I say so.

**Two places this memo contradicts earlier project documents.**

1. The corpus survey's verdict that "if the modulator has no information the policy lacks, a null result is the expected outcome" ([film_in_rl_survey §9.2](../references/FiLM/film_in_rl_survey.md)) is too strong. Section 3.1 shows two published counter-examples where the conditioner is fully redundant and modulation still wins, and identifies the variable that actually predicts the outcome.
2. The representation page's closing line — "the move which would make the modulator matter is an environment where context has to matter — not a finer instrument" — is right about the environment but stops short of the algorithmic half. Section 4 argues the freeze result is itself an algorithmic finding about *where the optimiser puts function*, and that it can be tested without a new world.

---

## 2. When does conditioning beat an equally capable unconditioned network?

### 2.1 The conditions table

Columns: what the conditioner was; whether the main pathway could see it anyway; the task structure; how large the reported advantage was; and what the authors attributed it to. "Regime?" asks whether the conditioner indexes a variable under which the optimal input→output map changes. Numbers come from the project's per-paper reviews; where a review flags a figure as reconstructed or unverified I say so.

| Paper | Conditioner | Also visible to main path? | Task structure | Advantage over unconditioned / concat | Attributed to | Regime? |
|---|---|---|---|---|---|---|
| Perez 2018 FiLM | question embedding | no (vision stream) | single VQA task, many questions | halves CLEVR error (4.5 → 2.3 %); FiLM without norm still 93.7 % | conditioning reaching every block | **yes** (question) |
| Chaplot 2018 Gated-Attention | instruction | **yes** in the concat baseline (same info, different fusion) | single task, many instructions, 3 difficulty levels | hard mode: 83 / 73 % vs concat 24 / 12 %; easy modes near tie | multiplicative selection of feature maps | **yes** (instruction) |
| BabyAI 2019 | instruction | no | gridworld language RL | **no ablation** — architecture description only | — | yes |
| BC-Z 2022 / RT-1 2022 | language embedding | no | multi-task imitation | FiLM never ablated; conditioner *type* ablated | — | yes |
| Vecoven 2020 NMN | history **minus** current obs | no, by construction | meta-RL, 3 benchmarks | faster, higher, lower seed variance vs param-matched RNN; 3 % from Bayes-optimal | `z` as learned task descriptor | **yes** (hidden task parameter) |
| Ben-Iwhiwhu 2022 NPN | the layer's own input | **yes** (self-conditioned) | meta-RL | wins on Meta-World ML45 / CT-graph depth 4; **ties on 2-D nav and half-cheetah**; wider/deeper param-matched baselines do not close the gap | representational diversity per task (CKA) | yes; benefit only when regimes are dissimilar |
| Beck 2023 (VariBAD) | inferred task belief | no (belief replaces concat) | meta-RL | hypernet 42.9 % vs FiLM 34.2 % vs concat-baseline; **initialisation moves FiLM 5.5 → 34.2**; easy tasks tie | init dominates; modularity on hard tasks | yes |
| Schöpf 2022 HN-PPO | learnable task ID | no | continual RL, 6 tasks | 0.81 accuracy vs 0.20 fine-tuning — **but hypernet without the L2 anchor: 0.24** | the output-anchoring regulariser, not the hypernet | yes |
| Rezaei-Shoshtari 2023 HyperZero | explicit MDP descriptor | no | zero-shot transfer | beats concat out-of-distribution | modularity; supervised regression (no bootstrapping) | yes |
| IQN 2018 | quantile level τ | no | single-task Atari | Hadamard "robust and slightly best" vs concat | — | yes (risk knob) |
| Γ-nets 2020 | discount γ | no | single task | **no clear winner; concat recommended** | — | yes (horizon knob) |
| Nikulin 2023 SAC-RND | state, modulating the action stream | different stream | offline RL | FiLM 95–100 vs concat 89.6 D4RL | smoother bonus gradient field | partial |
| CARE 2021 | language metadata | no | multi-task (MT10/MT50), 10 seeds | FiLM-SAC 0.75 vs MT-SAC 0.49 vs CARE 0.84 | task relatedness via metadata | yes |
| Soft Modularization 2020 | task ID + state | task ID also concatenated in baseline | multi-task | MT50: ~60 % vs ~35 %; **MT10: 87 vs 85** | per-task wiring; gain grows with task count | yes |
| Beukman 2023 Decision Adapter | given dynamics context | no | contextual MDP, 16 seeds, param-matched | **with clean relevant context all methods tie**; adapter wins only on extrapolation and with distractor context dims; **FiLM-style gate loses to concat** on 2-D ODE (85 vs 109) | separating context from state matters only when context is noisy or extrapolated | yes |
| HyperMARL 2024/25 | agent identity | no — and the `w/o GD` ablation (observation into the generator) **degrades** | multi-agent PPO | competitive across 22 scenarios; variance claim directional only | gradient decoupling | yes |
| PAPL 2026 | gait phase (2-D) | **yes** — concatenated to actor and critic *and* used as FiLM conditioner | single skill with within-episode modes | FiLM > No-FiLM (graphical); critic modulated because the reward is phase-conditioned | routing, not information | **yes** (within-episode) |
| Yuan 2024 (Diffusion Policy components) | observation | no other route into the denoiser | 8 single tasks, imitation | +16 to +62 points on 6 hard tasks; **≈ 0 on 2 easy** | difficulty | partial |
| Marquis & Farhood 2026 | actuator-fault vector (6-D) | no (concat baseline gets it) | single task, within-episode faults, PPO | **in-distribution near-tie**; out-of-distribution 26.7 m vs MLP 159.9 m; FiLM-on-critic halves error, LoRA-on-critic doubles it | distribution shift; mechanism-dependent critic effect | yes |
| SplitAdapter 2026 | load + dynamics latents | no | single task | all methods saturate at 2/4 kg; separation only at 6 kg (beyond training range) | out-of-range load | yes |
| TacFiLM 2026 | tactile embedding | no (concat baseline appends tokens) | real-robot imitation | 86.7 % vs concat 64.8 vs cross-attn 48.0 | feature-level fusion preserving priors | partial |
| GEAR 2026 | task command | — | multi-task drone RL | `FiLM Only` **degrades** Flip 58 → 34 %; needs per-task value heads | conditioning actor without disentangling values is harmful | yes |
| DyMoDreamer 2025 | motion mask | no — and it is **concatenated, not modulated** | single-task Atari | new Atari-100k record; larger latent alone does not help | a second stream carrying what the encoder discards | partial |

### 2.2 Bottom line of the table

Read across the rows, the papers that report a large advantage share two properties, and the papers that report a tie are exactly the ones missing one of them.

**Condition 1 — a regime variable.** The conditioner indexes something under which the *mapping* from inputs to outputs must change: a different question, task, instruction, phase, fault, load, style, agent, horizon. In every one of these the target is genuinely a *family* of functions $\{f_c\}_{c \in C}$, and the affine or generated parameters are the coordinates of that family.

**Condition 2 — the family is too wide for one shared map.** Ben-Iwhiwhu ties on 2-D navigation and half-cheetah (similar solutions across tasks) and wins on Meta-World and CT-graph (dissimilar ones); Beck ties on easy meta-RL and wins on hard; Yuan ties on easy manipulation and wins on hard; Marquis ties in-distribution and wins under flutter faults; SplitAdapter ties within the training load range and wins beyond it; Soft Modularization gains 2 points on 10 tasks and 25 on 50; Beukman finds *everything ties* when the context is clean and relevant. The benefit is concentrated where a single shared parameterisation would have to represent interaction terms between regime and input that it cannot learn from shared gradients — and it vanishes where it could.

**What is *not* a condition — signal exclusivity.** Chaplot's concatenation baseline sees the instruction; PAPL feeds the phase to the policy directly *and* modulates with it; Soft Modularization's baseline gets the task ID; Marquis's MLP gets the fault vector. All still lose to the modulated route. What the field has settled on is narrower: keep the conditioning path **low-dimensional** (corpus-wide, 1–32 dimensions; ours is 27 raw channels through a 16-unit recurrent core) and keep its **gradient path separate** from the observation's (HyperMARL's `w/o GD` ablation is the only direct negative). Exclusivity is a hygiene convention, not the mechanism.

**Honest negatives and sample-efficiency-only results.** Γ-nets (no winner, concat recommended); Beukman's clean-context tie and the FiLM-style gate losing to concatenation; Ben-Iwhiwhu's two easy-benchmark ties; Beck's easy-task ties; Yuan's two easy tasks; Marquis in-distribution; Soft Modularization MT10; Schöpf without the regulariser (worse than fine-tuning); GEAR's `FiLM Only` degradation; and MENTOR / SoftMoE, whose gains are sample efficiency in single-task visual RL from conditional *computation*, not conditional *gain*. BabyAI, BC-Z, RT-1 and GR00T supply no evidence at all — architecture descriptions only.

**Theory behind the pattern.** Galanti & Wolf's modularity theorem (hypernetwork review, Paper 2) is the cleanest statement of why conditioning helps, and it makes Condition 1 precise. For a target $y(x, I)$ with input $x \in \mathbb{R}^{m_1}$ and context $I \in \mathbb{R}^{m_2}$ in a Sobolev class of smoothness $r$, an embedding method (which includes FiLM on a fixed primary) needs a primary of size

$$
N_{\text{emb}} = \Omega\!\left(\epsilon^{-(m_1 + m_2)/r}\right),
$$

whereas a hypernetwork primary needs only $N_g = O(\epsilon^{-m_1/r})$, with the context absorbed by the generator at cost $O(\epsilon^{-m_2/r})$ — a sum instead of a product. The advantage lives entirely in $m_2$, the dimension of the *separate* context argument. That is the theorem's version of Condition 1: there must be a second argument. Section 3.3 shows what happens to it when $I$ is a function of $x$.

---

## 3. Which conditions does our design satisfy, and which does it violate?

The design, read from `src/models/neuromodulator.py` and `src/models/recurrent_ppo_network.py` and the saved site-grid configs: observation $o_t \in \mathbb{R}^{27}$ (2 interoceptive, 19 exteroceptive, the rest collision / olfaction summary channels), symlog-compressed, fed to a 128-unit task GRU and — in the "all" arms — unchanged to a 16-unit modulator GRU with state $h^m_t \in (-1,1)^{16}$. Per site $s$ and unit $i$,

$$
\gamma^{s}_{it} = g^{s}_i + b^{s}_i + \sum_{j=1}^{16} K^{s}_{ji}\, h^m_{jt}, \qquad
\beta^{s}_{it} = g'^{s}_i + b'^{s}_i + \sum_{j} K'^{s}_{ji}\, h^m_{jt},
$$

applied pre-activation at the actor and critic hidden layers, on the LayerNorm output at both encoder stages, and on the task GRU's emitted output. Group size 1 in every run analysed, so $g$ and $b$ are one degree of freedom stored twice (verified to float precision on the checkpoints).

### 3.1 Redundant conditioning signal — a real property, but not the missing condition

**The fact.** In the "all" arms the information set of the modulator is identical to the main pathway's: both are functions of the same observation history, $\sigma(o_{\le t})$. Nothing the modulator computes is unavailable to the task GRU. The intero-only and extero-only arms restrict the modulator to a *subset*, which is still contained in the main pathway's information.

**Why this is not the mechanism.** If redundancy alone removed the benefit, PAPL and Chaplot could not have found one. Both did, because their conditioners index a regime and their tasks have more than one. Conversely, the site grid's intero-only arms are the closest thing we have to the literature's convention — a 2-dimensional, slow, body-derived conditioner, routed separately — and they were no better than the "all" arms or the baseline. Under the redundancy hypothesis they should have been the best arms; under the regime hypothesis they are predicted to tie, and they tied.

**What redundancy *does* cost.** HyperMARL's variance decomposition (adjacent review in the modulation-in-RL folder) needs the generator's Jacobian to be deterministic within a mini-batch; a generator that reads the observation violates that, and their `w/o GD` ablation degrades on both environments. Our own logs show the signature: the wide-input arms hit the gradient clip in 83–87 % of windows against 4.5 % for the body-only arms ([[nmn_input_site_grid_optimisation_dynamics]] §5–6). So self-conditioning on 19 fast channels buys a second, shallow, high-frequency observation-to-action pathway and pays for it in gradient variance. That is a cost with no compensating benefit in a stationary world — which is consistent with "no difference" rather than "worse", because the cost is small at this scale.

**Verdict.** The suspicion is right that the conditioner is redundant and unprecedented; it is wrong that this is why the modulator does not help. Redundancy is a variance tax. The absent benefit is the absent regime.

### 3.2 A single stationary task — the condition we actually violate

In a contextual-MDP reading (Benjamins et al. 2023, on the survey's gap list), our world has one context. Satiation and injury are *state* variables: they enter the reward and dynamics the same way in every episode, so the optimal policy is a single function $\pi^\star(s)$ on the enlarged state that includes them. There is no $c$ such that $\pi^\star_c \ne \pi^\star_{c'}$. Hunger changes *what the best action is*, not *what function computes it* — and a recurrent network with hunger as an input represents the former directly.

This is the case every paper in the table ties on. It is also the case the corpus survey and the representation page already flagged from the neuromodulation side ("both neuromodulation papers report their benefit only where context matters for the reward"). The FiLM-side reading adds a sharper statement: modulation's inductive bias is a *separable multiplicative factorisation* of the target,

$$
\pi(a \mid x, c) \;=\; f\!\big(\gamma(c) \odot \phi(x) + \beta(c)\big),
$$

which is the right prior exactly when the family $\{f_c\}$ has (approximately) that structure and the wrong prior — a re-parameterisation with a variance tax — when there is one $f$ and $c$ is just another coordinate of $x$.

The one project result that *did* show an advantage fits this reading precisely: the May continual probe, where the predator's behaviour switched between stages, gave the modulated agent +107 to +132 survival steps on the return stages (one seed, ~25× the seed-noise floor). That is a between-episode regime. Its three-seed replication is in flight ([[MAY_DOUBLE_RETURN_REPLICATION]]); if it holds, it is the project's Marquis pattern — in-distribution tie, out-of-distribution win — inside one architecture.

### 3.3 Expressivity — FiLM here is a re-parameterisation, with one bilinear exception

**Function class.** The modulated network computes some $F_\theta(o_{\le t})$; the unmodulated one computes $G_\psi(o_{\le t})$. Both are GRU-based and both read the same history, so in the universal-approximation sense the two classes coincide: there is no function of the observation history the modulated architecture can represent that a sufficiently wide plain recurrent network cannot. FiLM adds no *capacity* here; it adds a *parameterisation*.

**Galanti–Wolf collapses.** With $I = \psi(o_{\le t})$ the target $y(x, I) = y(x, \psi(x))$ is a function of $x$ alone, and the relevant Sobolev class is $\mathcal{W}_{r, m_1}$, not $\mathcal{W}_{r, m_1 + m_2}$. The embedding lower bound and the hypernetwork upper bound both become $\Theta(\epsilon^{-m_1/r})$: the exponential modularity advantage is identically zero. The theorem does not say self-conditioning hurts; it says the argument for conditioning does not apply.

**The one thing the plain layer cannot do cheaply.** Expand the modulated actor pre-activation:

$$
\gamma_{it}\,(W_1 x_h)_{it} \;=\; (g_i + b_i)\,(W_1 x_h)_{it} \;+\; \sum_{j=1}^{128}\sum_{k=1}^{16} W_{1,ij}\,K_{ki}\; x_{h,jt}\; h^m_{kt}.
$$

The second term is a **rank-≤16 bilinear form** between the task GRU's output and the modulator's state — products of a memory feature with a fast summary of the current observation. A single ReLU hidden layer reading $x_h$ alone approximates such products only piecewise-linearly, and the task GRU's own multiplicative gates act between its state and input at the gate level, not at the actor's pre-activation. So the modulated actor has *cheap* access to 128 × 16 second-order terms that the plain actor would have to synthesise. Whether the task rewards those terms is empirical; what the representation page shows is that the network *uses* them — the all-senses arm's contextual fraction (0.33 at the actor) is driven by the fast exteroceptive channels, the body-only arm's is 0.08, and the freeze cost is largest at the actor. The modulator is functioning as a bilinear shortcut, which is a parameter-efficiency effect, not a capacity effect, and it is exactly what one expects a gradient-driven optimiser to exploit whether or not it improves the optimum.

**Fiber-bundle reading, kept honest.** A fiber bundle is a space that locally looks like a product but may have a global twist — the Möbius band is the standard example. The modulator is a section $s: B \to E$ of the trivial bundle $E = B \times \mathbb{R}^{2 \cdot 128}$ per site, with base $B = (-1,1)^{16}$ (the modulator's reachable state box) and the section linear in the base coordinate. A trivial bundle with a linear section is a re-parameterisation, which is the geometric restatement of the paragraph above. The only structure a fixed weight matrix cannot imitate is a *sign change* of a unit's gain across the base — the analogue of the Möbius twist — and the representation page finds about a third of units at every site do take both signs within an episode. **Empirical signature that would make the geometry load-bearing rather than decorative:** the per-site freeze cost should track the number of sign-flipping units, and the plain network at the same site should show no equivalent sign-reversal in its effective input weights. If freeze cost tracks *total* contextual variance instead, the sign structure is incidental and the bundle reading is metaphor.

### 3.4 The gauge redundancy — harmless to the function, not harmless to the dynamics

The September critique's per-unit affine gauge is exact, and the representation page's analysis 01 shows the modulator's *width* of action (reachable swing ≈ 11) is unaffected by the constant part. So the 85 % of gain variance that is fixed per-unit re-tuning is invisible to behaviour and cannot be a cause of the null.

What it can do is shape *where the optimiser puts function*. Three facts from the two prior documents compose:

1. Under Adam with no weight decay, the loss is flat along the gauge direction, so the head bias, the per-unit baseline and the modulated layer's own weights drift together at learning-rate speed regardless of the loss.
2. As the mean gain falls (0.2–0.9 at the end of training) and downstream weights grow to compensate, the modulator heads become the highest *relative*-learning-rate parameters in the layer.
3. The modulator's share of the squared gradient norm rises from 15–45 % early to 40–75 % late; at ten million episodes it is the steepest part of the network.

A pathway that is both cheap to move and steep is where a first-order optimiser routes function. That does not make the solution better; it makes the *distribution* of the solution lean on that pathway. This is the mechanism half of section 4.

### 3.5 Too small, too slow, too weakly driven?

The reachable-swing analysis rules out "too small": a 16-unit core with linear heads can move any gain by ~11 and the range only grows over training. "Too slow" is the wrong axis — a body-state conditioner *should* be slow, and the literature's successful within-episode conditioners (phase, fault, load) are slow too. "Too weakly driven" is answered by the gradient share: the modulator receives *more* of the gradient late in training, not less. None of these is a violated condition.

### 3.6 The critic — a criterion we currently fail, and a positive control that passed

PAPL modulates the critic because its reward is structurally different per phase and the critic-value histogram separates by phase; Marquis's isolated test shows FiLM-on-critic halving error under PPO because the value of a state genuinely changes with the fault. Our reward is not a function of anything the modulator reads that the critic does not also read, and no one has checked whether critic values separate by body state. The freeze test's zero effect at the critic site is a correct positive control (a greedy replay cannot see the critic), not evidence either way about training.

### 3.7 Scorecard

| Condition from section 2 | Our design | Status |
|---|---|---|
| C1 — a regime variable indexes a family of maps | one stationary task family; body state is a state variable | **violated** — the load-bearing one |
| C2 — the family is too wide for one shared map | not applicable without C1 | **violated** (vacuously) |
| Hygiene — low-dimensional conditioner | 27 raw channels (2 in the body-only arms) | violated in "all" arms; met in body-only arms, which also tied |
| Hygiene — separate gradient path | conditioner reads the observation the modulated stream reads | violated; measurable as clip-rate and gradient variance |
| Identity initialisation | half-applied: bias at 1, head weights not zeroed (±0.3 per-unit spread at step 0) | minor |
| Critic modulated only when values separate by conditioner (PAPL) | never checked | unknown |
| Expressivity beyond the plain network | none in class; a rank-16 bilinear shortcut in parameterisation | re-parameterisation |

---

## 4. The puzzle: load-bearing when frozen, no advantage from scratch

### 4.1 The explanation this memo defends — co-adaptation into a cheap pathway

Let the modulated policy be $\pi_{\text{mod}}(a \mid o_{\le t}) = f\big(x_{h,t},\, \gamma(h^m_t),\, \beta(h^m_t)\big)$ and the plain one $\pi_{\text{plain}}(a \mid o_{\le t}) = g(x'_{h,t})$. Equal survival says the two implement policies of equal quality on the same information; it does not say they implement them the same way. Training the modulated network jointly, from an identity initialisation, in the presence of a pathway that (i) can realise bilinear terms cheaply, (ii) has the highest effective learning rate in the network, and (iii) carries the largest late-training gradient share, is a recipe for a solution in which part of the input-to-action map lives *in* the modulation. Freezing $\gamma_t$ at $\bar\gamma$ then evaluates the network at a point $(\bar\gamma, W)$ that was never on its training trajectory: the downstream weights were fitted to the joint distribution of $(\gamma_t, x_{h,t})$, not to the marginal. The cost is the cost of removing a component, and it says nothing about whether that component made the optimum better.

Three features of the data fit this reading and not its rivals:

- **MC-trained agents lean on the modulation about twice as hard** (freeze cost −82 vs −44 for the gain) while emitting *the same* modulation signal (contextual fraction 0.146 vs 0.151). The prior critique found the modulator's gradient grows under MC and is flat under GAE. Where the gradient goes, the function follows — the dependence tracks *training pressure on the pathway*, not the pathway's information content.
- **The gain matters at the actor, the offset at the recurrent site, both at the encoder.** A benefit-carrying signal would have one dominant coordinate; a re-parameterisation takes whatever coordinate is cheapest at each site. The actor's pre-activation is where the bilinear term lives (gain); the recurrent output has no nonlinearity after FiLM, so the offset is a free shift of the actor's and critic's input (offset).
- **Every frozen agent ends up worse than the plain agent**, which the page deliberately left uninterpreted. Under co-adaptation this is expected: the plain agent's solution is complete in one pathway; the frozen agent's is missing a piece.

### 4.2 The rivals

- **R-a: the modulator computes something the plain network cannot, and the task does not reward it.** Predicts the freeze cost is real *and* the modulated agent is no better — but then the "something" must be a function outside the plain class, which section 3.3 rules out for the class and reduces to the bilinear term for the parameterisation. Distinguishable from co-adaptation by the recovery test below.
- **R-b: the freeze cost is an artefact of freezing at the mean rather than at a typical value.** The gauge argument makes freeze-at-mean equivalent to removal-plus-folding, so the intervention is the right one; but the point $\bar\gamma$ may sit in a low-density region if $\gamma_t$ is bimodal (sign-flipping units). Distinguishable by freezing at the per-unit median or at a sampled typical value.
- **R-c: single-seed noise.** The freeze test is paired within-agent (128 seeds, sign-test p < 0.001 for the large effects), so it survives; the *absence* of a between-architecture advantage rests on one seed per configuration and ±4.4-step noise, which is the standing caveat on every comparison in the project.

### 4.3 Measurements that separate co-adaptation from its rivals

All three are runnable on existing checkpoints or as short fine-tunes; none needs a new world.

1. **The recovery test (decisive).** Freeze the modulator's output at its mean and *fine-tune the main network only* for a small fraction of the original budget (1–5 %). Co-adaptation predicts survival recovers to the plain agent's level quickly, because the lost component is cheap to re-absorb into $W_1$ and the GRU. R-a predicts it does not recover within the budget. Report recovery curves against the plain agent's level, not against the modulated agent's.
2. **Cross-architecture decodability.** $\gamma^{\text{ctx}}_t = K^\top(h^m_t - \bar h^m)$ is a 16-dimensional signal. Regress it, per unit, from the *plain* agent's task-GRU state on matched episodes. High $R^2$ means the information the modulator carries is present in the plain agent's memory — same solution, different distribution. Low $R^2$ with high freeze cost is the R-a signature.
3. **The learning-rate-ratio intervention (algorithmic, cheap).** Retrain one arm with the modulator's learning rate lowered 10× (or with weight decay on the heads and baselines only). Co-adaptation predicts the freeze cost falls substantially while survival is unchanged; the dependence is a property of training pressure, not of the task. This is the single intervention that changes the first half of the puzzle without touching the second, and it is the cleanest direct test.

Two cheaper companions the representation page already lists: run the freeze test on the body-only and external-only arms (co-adaptation predicts the freeze cost scales with the pathway's contextual fraction, so body-only arms lose far less); and count sign-flipping units per site against freeze cost (section 3.3's bundle signature).

---

## 5. Algorithmic changes, ranked

Ranked by how directly each attacks a violated condition (section 3.7) and how cheaply it can be tested. Every item names its mechanism, its prediction, the minimal experiment, and what a null would mean. All experiments should run at three seeds; the project's ±4.4-step noise floor makes single-seed architecture comparisons uninformative below ~15 steps.

| Rank | Change | Condition attacked | Cost | Owner |
|---|---|---|---|---|
| 1 | 2×2: conditioner exclusive vs redundant × stationary vs alternating world | C1 and the redundancy hypothesis, jointly | configs + one small input-mask change | experiment-designer, senior-developer |
| 2 | Modulator-specific optimiser (10× lower LR or head-only weight decay) + the freeze/recovery diagnostics | the puzzle (§4), gauge dynamics (§3.4) | one config key + offline scripts | senior-developer, experiment-analyzer |
| 3 | A within-episode regime: make the reward or dynamics structurally injury-dependent, gated by the critic-value-separation check | C1 within an episode; PAPL's critic criterion | env config; one diagnostic script | experiment-designer, professor-rl |
| 4 | Parameterisation hygiene: zero-init the head weights, drop the duplicate baseline at group size 1, damp the gain to $1 + 0.1\tanh(\cdot)$ | gauge drift, identity init | code, small | senior-developer |
| 5 | Operator swaps: sigmoid gate, low-rank weight modulation, full hypernetwork, adaLN | none until C1 holds | code, moderate | defer |
| 6 | Meta-parameter modulation (learning rate, entropy, discount) | different bundle (May audit) | code, invasive for discount | defer; professor-rl |

### 5.1 The 2×2 — exclusive-vs-redundant conditioner × stationary-vs-alternating world

**Mechanism.** The two live hypotheses make opposite predictions on the two axes. Redundancy says: give the modulator a signal the policy cannot otherwise see and the benefit appears. Regime says: give the world a switch and the benefit appears, whatever the conditioner sees.

**Arms.** *Exclusive*: the two body channels are removed from the main network's input and given only to the modulator; the plain baseline keeps all channels (same information, different routing — the Marquis / PAPL comparison). *Redundant*: as now, "all" input. Crossed with the stationary home world and an alternating A-B-A-B schedule from the continual-worlds line.

**Predictions.** Redundancy: exclusive arms beat their baselines in both worlds. Regime: a tie in the stationary world in both routing arms; an advantage in the alternating world in both routing arms. Both true: advantage only in the exclusive-alternating cell. Neither: ties everywhere, and the modulator question moves to a different architecture class entirely.

**What a null means.** If even the exclusive-alternating cell ties at three seeds, then the May probe's single-seed win was noise or schedule-specific, and FiLM-style modulation has no regime to serve in this task family at this scale. That is a publishable negative given the field's conditions.

**Is continual-worlds the right testbed for the alternating half?** Yes, with three caveats. (a) Its body rules are stationary by design, so the regime lives in the *external* world and must be inferred from exteroceptive history — the body-only conditioner is structurally handicapped there; use the "all" or exteroceptive conditioner for the alternating arms and say so. (b) Forgetting resistance in hypernetwork continual RL comes from an output-anchoring regulariser (Schöpf: hypernet alone, 0.24; with anchor, 0.81). Our modulator has no such mechanism, so any advantage must come from a re-usable context attractor in $h^m$ — measure it (cluster $h^m$ by world; check the boundary transient) rather than assume it. (c) The line's own Revision 2a already found that "who recovers faster" flips sign depending on the reference level; keep both readings.

### 5.2 A separate optimiser regime for the modulator, plus the puzzle diagnostics

**Mechanism.** Section 3.4: the modulator is the cheapest-to-move and steepest part of the network late in training. Lowering its relative step (or restoring a restoring force along the gauge direction with weight decay on heads and baselines only) reduces the pressure that routes function into it. Sarafian et al. report the hypernetwork's learning rate must be re-tuned separately from the base algorithm's; we have never done so.

**Prediction.** Survival unchanged; freeze cost falls; contextual fraction possibly falls; gradient clip-rate in the wide-input arms falls. If survival *improves*, the variance tax of section 3.1 was larger than assumed and the redundancy hypothesis regains a mechanism.

**Minimal experiment.** One "all"-input, all-sites arm, MC recipe (the one that leans hardest), three seeds, modulator LR ÷10, with the freeze and recovery tests of section 4.3 run on the result.

**What a null means.** If the freeze cost is unchanged at a 10× lower modulator learning rate, the dependence is not an optimiser-pressure effect and rival R-a (the bilinear term is doing something the plain layer cannot cheaply do) gains ground; the cross-architecture decodability test then decides.

### 5.3 A within-episode regime — injury that changes the function, not just the input

**Mechanism.** PAPL's within-episode phase is the closest successful precedent to what H1 and H3 want: one skill, two modes, a reward that measures *different quantities* per mode, a critic whose values separate by mode, and a 2-dimensional conditioner routed both ways. Our injury state changes the reward's *value* but not its *structure*. An injured-mode in which, say, predator contact costs differently and foraging returns differently would create a genuine $\{f_c\}$ with $c \in \{\text{healthy}, \text{injured}\}$.

**Gate before running.** PAPL's diagnostic is cheap: plot the plain agent's critic values conditioned on injury; if the histograms do not separate, the critic has nothing to gain and the environment change is not creating a regime. Run this on existing checkpoints first.

**Prediction.** Modulated beats plain only once the two modes need different maps; the modulator's $h^m$ should cluster by mode at the boundary. The body-only conditioner is the natural arm here, not the "all" one.

**What a null means.** Either the two modes still admit one shared map (C2 fails — the family is not wide enough), or the phase signal's slowness makes the shared map easy. Both are informative for the biological framing, which is `professor-neuromodulation`'s and `professor-pain-modeling`'s call. The existing injury-dependence plan under `modulator_clues` is the natural home; I have not audited it.

### 5.4 Parameterisation hygiene

Zero-initialise the head weight matrices (Beck's Bias-HyperInit; the 2024–26 default), remove the duplicate per-unit baseline at group size 1 or keep only the baseline, and consider Marquis's damped gain $\gamma = 1 + 0.1\tanh(\cdot)$ with spectral normalisation on the modulator's matrices. **Prediction:** no change in survival; smoother early training; a gauge direction that no longer drifts if weight decay is added. This is low priority for explaining the null — the gauge is function-invariant — but it is a prerequisite for interpreting any of the above cleanly, and Beck's Table 2 (initialisation moving FiLM from 5.5 to 34.2 %) is a warning that init can dominate architecture. Do not change it mid-experiment.

### 5.5 Other gating operators — defer

Sigmoid multiplicative gates (Chaplot, Ben-Iwhiwhu), low-rank weight modulation (Beukman's adapter, Marquis's LoRA), full hypernetworks (Beck, Schöpf) and adaLN differ in *capacity* and *gradient geometry*, not in whether they need a regime. Beukman is the controlled result: with clean relevant context all operators tie, the FiLM-style gate loses to concatenation on one benchmark, and the adapter wins only under extrapolation and distractor dimensions. Beck: initialisation moves FiLM six-fold; architecture moves it eight points with overlapping error bars. Swapping the operator in the stationary world predicts another tie. Revisit only if the alternating arms of 5.1 show an advantage, at which point the operator sweep has something to measure.

### 5.6 Meta-parameter modulation — a different bundle, not a fix

The May audit's verdict stands: temperature is the one forward-pass-native hyperparameter and we already have that head (it railed at its ceiling; a zero-mean constraint in the CAT-SAC style is the published discipline). A context-dependent discount would *manufacture* a regime in the objective — a different Bellman fixed point per context — which is a way of creating Condition 1 by fiat rather than discovering it in the task. That is a research direction (γ-conditional UVFA, per the audit's second addendum), not a repair of the null, and it changes the task definition. Route to `professor-rl` if pursued.

---

## 6. Relation to project anchors

- **Hypotheses H1–H5** ([[NEUROMODULATION_ALGORITHM]] §1.4). H1 and H3 are within-episode regime claims and need section 5.3's environment before they are testable as *advantages*; as within-agent signatures they remain testable now, but only on the identifiable part $\delta\gamma_t$ (September critique §9). H4 (coordinated response across sites) is, in this memo's terms, the statement that the sites share a base — trivially true by construction (one $h^m$) and therefore not a hypothesis until sites are given separate generators. H5 (modulator timescale) interacts with the co-adaptation reading: a slower modulator is a less attractive shortcut, which is a prediction the LR-ratio test in 5.2 can check indirectly.
- **The diagnosis series and the v8 null.** The four-cause section of the project plan that the agent profile anchors to has been rewritten out of the plan; the operative prior is [[NMN_PERFORMANCE_DIAGNOSIS_v8]] with [[mc_return_units_bug_severity_and_repair]] §10. This memo adds an algorithmic cause the series has not carried: no regime for the conditioner to index, plus optimiser-driven co-adaptation into a redundant pathway.
- **Phase 2 / Phase 3.** The FiLM-variant probe (grouping size) sweeps the axis with the least literature evidence; this memo says the axis with the most is *task regime*, and that the variant probe should wait for 5.1.
- **Paper 2 framing.** If 5.1's alternating arms win and its stationary arms tie, the honest claim is Marquis's pattern in an interoceptive setting: a conditioned agent that is indistinguishable in-distribution and better under shift. The "modulation as a hypernetwork-class object" framing should then be stated as a *parameterisation* claim (section 3.3), not a capacity claim.

---

## 7. References this memo needs that the corpus lacks

- Benjamins et al. 2023, *Contextualize Me — The Case for Context in RL* (TMLR) — the contextual-MDP vocabulary section 3.2 leans on; on the survey's gap list.
- Dumoulin et al. 2018, *Feature-wise transformations* (Distill) — umbrella citation for the family; on the gap list.
- Kunin et al. 2021, *Neural Mechanics*; van Laarhoven 2017 — for the gauge-drift-under-Adam argument (already requested by the September critique).
- Peebles & Xie 2023, *Scalable Diffusion Models with Transformers* — the adaLN-Zero mechanism citation the modulation-in-RL review says GR00T cannot supply.
- Any paper measuring *co-adaptation* of a conditioning pathway by freeze-then-fine-tune — I do not recall one that does exactly section 4.3's recovery test in a conditional architecture; if none exists, the test is a small contribution in itself.

---

## Next steps

- **`experiment-designer`** — design the three-seed 2×2 of section 5.1 (exclusive vs redundant conditioner × stationary vs alternating world), reusing the continual-worlds schedule machinery for the alternating half and the home world for the stationary half; pre-register the four-cell prediction table verbatim. Add the critic-value-separation gate of 5.3 as a prerequisite check before any within-episode regime arm is built.
- **`senior-developer`** — (a) a main-network input mask so the body channels can be routed to the modulator only (the exclusive arm); (b) a modulator-specific learning-rate multiplier and optional head-only weight decay (5.2); (c) the offline recovery-test and cross-architecture-decodability scripts of section 4.3, on top of the existing freeze-test tooling; (d) the hygiene items of 5.4 as a separate, non-blocking plan.
- **`experiment-analyzer`** — run the freeze test on the body-only and external-only arms; count sign-flipping units per site against freeze cost; once the LR-ratio arm exists, report freeze cost and survival side by side.
- **`professor-rl`** — the variance-tax argument of section 3.1 (a second high-frequency observation-to-action pathway inflating policy-gradient variance) is an RL-update claim; please check it against the clip-rate evidence and say whether the effect size could reach behaviour at this batch size. Also the γ-conditional-discount direction of 5.6 if the user wants it scoped.
- **`professor-neuromodulation` / `professor-pain-modeling`** — whether an injured mode that changes the reward's *structure* (5.3) is biologically and construct-validly defensible, since it is the only route by which H1/H3 become advantage claims rather than within-agent signatures.
- **`literature-reviewer`** — the five items in section 7.
- **`plan-reviewer`** — before 5.1 launches: the exclusive arm removes information from the *main* network, so its baseline must be the plain agent with *all* channels, not a plain agent with the same mask; that asymmetry is the easiest thing to get wrong.
