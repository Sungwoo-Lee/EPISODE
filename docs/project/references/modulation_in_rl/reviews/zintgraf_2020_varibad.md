---
title: "VariBAD: A Very Good Method for Bayes-Adaptive Deep RL via Meta-Learning"
slug: zintgraf_2020_varibad
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_classics.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 3. Zintgraf et al. 2020 — *VariBAD: A Very Good Method for Bayes-Adaptive Deep RL via Meta-Learning*

**PDF:** `docs/project/references/modulation_in_rl/sources/Zintgraf et al. 2020 - VariBAD - A very good method for Bayes-adaptive deep RL via meta-learning.pdf`
**Venue as printed (running header on every page):** *"Published as a conference paper at ICLR 2020"*. arXiv stamp: `arXiv:1910.08348v2 [cs.LG] 27 Feb 2020`.
**Authors:** Luisa Zintgraf, Maximilian Igl, Sebastian Schulze, Yarin Gal, Shimon Whiteson (University of Oxford); Kyriacos Shiarlis (Latent Logic); Katja Hofmann (Microsoft Research). Code: `github.com/lmzintgraf/varibad`.

### 3.1 Plain-English entry point

An agent dropped into an unfamiliar environment faces a dilemma: spend time finding
out how the world works, or exploit what it already knows. The mathematically optimal
answer is known — it is called the **Bayes-optimal policy** — and it says: keep a
probability distribution over "which world am I in", act on that distribution, and
explore only to the extent that information is worth more than the reward it costs.
Computing it exactly is hopeless for anything bigger than a toy.

VariBAD's move is to **learn the distribution instead of computing it**. During
meta-training on a family of related tasks, the agent learns (a) a small recurrent
network that reads the history so far and outputs a *belief* — a Gaussian over a
5-dimensional "which task is this" vector — and (b) a policy that reads the current
observation **together with that belief** and acts. The belief is trained not by
telling the agent the task (no task labels are ever used) but by asking it to predict
the rewards and states of the **whole trajectory, past and future**, from the latent —
a variational autoencoder whose "data" is the agent's own experience.

**The conditioning signal is therefore an inferred quantity, not a given one.** No
task ID, no language description, no privileged label — just a posterior the agent
computed for itself, including its own uncertainty (the belief's variance, which the
policy also sees). That is what makes this paper the cleanest published alternative to
conditioning on a supplied label or on the raw observation.

**Headline result.** On a 5×5 gridworld with a hidden goal, VariBAD's exploration
visibly matches the hard-coded Bayes-optimal strategy and beats posterior sampling; on
four MuJoCo meta-RL benchmarks it is one of only two methods (with RL²) that adapt
**within a single episode**, and it comes close to an oracle policy given the true
task. All results are reported as **figures, not tables** — there is no numeric result
table anywhere in the paper.

**Why the project cares.** The project's held Beck et al. 2023 paper measures FiLM
against hypernetworks *on top of VariBAD*. To read those numbers, one must know what
the unmodified baseline does — and the answer is that VariBAD hands the policy a
**10-number vector (a 5-dim mean and a 5-dim standard deviation) alongside the state**
and lets a **2-hidden-layer, 128-unit tanh MLP** figure out the rest. §3.5 spells this
out, including the fact that the paper never actually writes down the combination
operator.

### 3.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | ICLR 2020 — *"Published as a conference paper at ICLR 2020"*, page header throughout. |
| **RL algorithm** | **A2C** for the gridworld; **PPO** (with a Huber value loss) for MuJoCo. On-policy in both cases; the paper flags off-policy extension as future work. |
| **Conditioning signal** | The **variational posterior over a task embedding**, `q_φ(m \| τ_{:t})` — an **inferred belief**, learned without any task label. Represented concretely by the Gaussian's parameters: a **5-dimensional mean and a 5-dimensional standard deviation**, both benchmarks. Updated **every timestep** from the full history `τ_{:t} = (s_0,a_0,r_1,s_1,…,s_t)` by a GRU. |
| **What is modulated** | **The policy** (and, in the actor-critic setup, the value head that shares its trunk). The **encoder is not modulated** — it is the thing producing the signal. The **decoder is training-time only** and discarded at test. There is no separate conditioning of a critic. |
| **The operator** | **Concatenation** — and, importantly, **the paper never says so in words.** The formal statement is only `π_ψ(a_t \| s_t, q_φ(m\|τ_{:t}))` (§3.2) plus *"the posterior can be represented by the distribution's parameters (e.g. mean and standard deviation if `q` is Gaussian)"*. A text search of the PDF finds the word "concatenate" **only** in the description of the RL² baseline. The concatenation is the reference implementation's choice, not a claim in the paper. No gain, no offset, no routing, no generated weights. |
| **Granularity** | **Whole-vector.** The 10 belief numbers enter once, at the policy's input. Nothing is per-unit or per-layer. |
| **Placement** | **A single site — the policy input layer.** Policy is 2 hidden layers of 128 tanh units (MuJoCo) or 32 tanh units (gridworld). This is exactly the architecture that later FiLM / hypernetwork papers replace. |
| **Ablated against concatenation?** | **No — the operator is never varied.** What *is* compared is the *signal*: RL² is described as *"if we remove the decoder and the VAE objective, variBAD reduces to this setting"*, and RL² is run as a baseline throughout. So the paper ablates **belief-latent vs. raw RNN hidden state**, not **concatenation vs. modulation**. |
| **Reported instability** | **Yes, three separate items.** (i) **RL²'s** 128-dimensional hidden state is unstable across episode resets — performance *"drops again after the fourth episode: this is likely due to instabilities in the 128-dimensional hidden state"*, and in CheetahVel *"RL² is sometimes unstable when it comes to maintaining its performance over multiple rollouts"*. VariBAD is claimed stable by contrast because its latent *"is concentrated and does not change with more data"*. (ii) **The fixed prior may be mis-specified**: in the gridworld the latent variance *increases* before the goal is found, so *"this prior might not be optimal"*; learning the prior is proposed as an extension. (iii) **Out-of-distribution tasks are an acknowledged failure mode**: *"the inference procedure will be wrong ... and the policy will not be able to interpret a changed posterior."* |
| **Single-task or multi-task** | **Meta-RL / task-distribution.** Train on `p(M)`, test on held-out tasks from the same distribution, scored on **online return during learning**. |
| **Claim strength** | For the **conditioning signal**: **ablated** (against RL², PEARL, E-MAML, ProMP, an oracle, hard-coded Bayes-optimal and hard-coded posterior sampling) — but **entirely in figures; no result table exists**. For the **conditioning operator**: **asserted**, never tested. |

### 3.3 Phase 1 — Foundational overview

**The formal object.** Take an MDP whose reward and transition functions are unknown.
Put a prior `b_0 = p(R,T)` on them and carry the posterior `b_t = p(R,T \| τ_{:t})`.
Glue the belief onto the state to get a **hyper-state** `s⁺_t = (s_t, b_t)`. The
resulting **Bayes-Adaptive MDP (BAMDP)** is an ordinary MDP over hyper-states, so its
optimal policy exists — and that policy is by construction Bayes-optimal, trading
exploration against exploitation exactly right *for the horizon it has left*. Three
things make it intractable: the true model's parameterisation is unknown, the belief
update is intractable, and planning in belief space is intractable.

**The three substitutions.** VariBAD replaces each:
1. *Unknown parameterisation* → replace the belief over `(R,T)` with a belief over a
   **low-dimensional latent `m`** that indexes them: `R_i ≈ R(·;m_i)`, `T_i ≈ T(·;m_i)`
   with `R`, `T` shared across tasks. Millions of model parameters collapse to a
   5-vector.
2. *Intractable belief update* → replace exact Bayes with an **amortised variational
   encoder** `q_φ(m \| τ_{:t})`, a GRU run online over the trajectory.
3. *Intractable planning* → **don't plan.** Train a model-free policy that reads the
   posterior, end to end, so the exploratory behaviour is compiled into the weights at
   meta-training time and test time is a forward pass.

**The training signal that makes the latent mean something.** The encoder is trained
by an ELBO whose decoder reconstructs the **entire trajectory including the future**
`τ_{:H⁺}` from a latent inferred from only the **past** `τ_{:t}`. That asymmetry —
possible only because training has the full trajectory in hand — is what forces the
latent to be a *task* description rather than a *history* summary, and it is what lets
the agent predict rewards at cells it has never visited.

**Initial takeaway.** If you want a conditioning signal that carries **uncertainty**
rather than identity, this is how to get one without labels: infer it, represent it as
a distribution, and hand the *distribution's parameters* to the policy. The
exploratory behaviour is then not engineered — it falls out of the policy having
learned what to do when the variance is large.

### 3.4 Phase 2 — Graduate-level deep dive

#### 3.4.1 The BAMDP, written out

An MDP is `M = (S, A, R, T, T_0, γ, H)`. Meta-training samples
`M_i = (S, A, R_i, T_i, T_{i,0}, γ, H) ∼ p(M)`; `i` is an unknown task description or
ID that the agent never sees.

Belief `b_t(R,T) = p(R,T \| τ_{:t})`, hyper-state `s⁺_t ∈ S⁺ = S × B`. The hyper-state
transition factorises into an environment part and a deterministic Bayes update:

$$
T^{+}(s^{+}_{t+1}\mid s^{+}_{t}, a_t, r_t)
= \underbrace{\mathbb{E}_{b_t}\big[T(s_{t+1}\mid s_t,a_t)\big]}_{\text{expected env.\ transition}}\;\cdot\;
\underbrace{\delta\big(b_{t+1} = p(R,T\mid \tau_{:t+1})\big)}_{\text{deterministic belief update}} ,
$$

and the hyper-reward is the posterior-expected reward **after** the transition:

$$
R^{+}(s^{+}_{t}, a_t, s^{+}_{t+1}) \;=\; \mathbb{E}_{b_{t+1}}\big[R(s_t,a_t,s_{t+1})\big].
$$

The objective is ordinary expected return in the BAMDP,

$$
J^{+}(\pi) \;=\; \mathbb{E}_{b_0, T^{+}_{0}, T^{+}, \pi}\left[\sum_{t=0}^{H^{+}-1}\gamma^{t}R^{+}\big(r_{t+1}\mid s^{+}_{t},a_t,s^{+}_{t+1}\big)\right].
$$

**The `H` vs `H⁺` distinction is load-bearing** and is easy to miss. `H` is the MDP
horizon; `H⁺` is the BAMDP horizon, typically `H⁺ = N × H` for `N` episodes.
*"Trading off exploration and exploitation optimally depends heavily on how much time
the agent has left."* Gridworld: `H = 15`, `H⁺ = 4H = 45`. MuJoCo: `H = 200`,
`H⁺ = 2H = 400`, with a `done` flag appended to the state so the agent knows a reset
happened.

**The BAMDP is a POMDP with a frozen hidden state.** The related-work section is
precise about this: a BAMDP is a special case of a POMDP in which the hidden state is
`(R,T)` and is **constant within a task**. VariBAD exploits exactly that by learning
*"an embedding that is fixed over time, unlike approaches ... which use filtering to
track the changing hidden state."* For the project, this is the boundary condition on
transplanting VariBAD-style belief conditioning: it assumes the thing being inferred
does not change during an episode.

#### 3.4.2 The ELBO, derived

Target: the model evidence of the trajectory under a learned model `p_θ`,

$$
\mathbb{E}_{\rho(M,\tau_{:H^{+}})}\big[\log p_{\theta}(\tau_{:H^{+}}\mid a_{:H^{+}-1})\big],
$$

with `ρ` the trajectory distribution induced by the current policy. Intractable, so
introduce `q_φ(m\|τ_{:t})` and apply importance weighting followed by Jensen
(Appendix A, reproduced with the steps):

$$
\begin{aligned}
\mathbb{E}_{\rho}\big[\log p_{\theta}(\tau_{:H})\big]
&= \mathbb{E}_{\rho}\left[\log \int p_{\theta}(\tau_{:H}, m)\,\frac{q_{\phi}(m\mid\tau_{:t})}{q_{\phi}(m\mid\tau_{:t})}\,dm\right]\\[2pt]
&= \mathbb{E}_{\rho}\left[\log \mathbb{E}_{q_{\phi}(m\mid\tau_{:t})}\!\left[\frac{p_{\theta}(\tau_{:H},m)}{q_{\phi}(m\mid\tau_{:t})}\right]\right]\\[2pt]
&\ \ \ge\ \mathbb{E}_{\rho,\,q_{\phi}}\left[\log \frac{p_{\theta}(\tau_{:H},m)}{q_{\phi}(m\mid\tau_{:t})}\right] &&\text{(Jensen)}\\[2pt]
&= \mathbb{E}_{\rho,\,q_{\phi}}\big[\log p_{\theta}(\tau_{:H}\mid m) + \log p_{\theta}(m) - \log q_{\phi}(m\mid\tau_{:t})\big]\\[2pt]
&= \mathbb{E}_{\rho}\Big[\underbrace{\mathbb{E}_{q_{\phi}(m\mid\tau_{:t})}\big[\log p_{\theta}(\tau_{:H^{+}}\mid m)\big]}_{\text{reconstruction}} \;-\; \underbrace{\mathrm{KL}\big(q_{\phi}(m\mid\tau_{:t})\,\Vert\, p_{\theta}(m)\big)}_{\text{regulariser}}\Big] \;=\; \mathrm{ELBO}_{t}.
\end{aligned}
$$

**Two non-standard choices inside this ELBO.**

*(a) Encode the past, decode the future.* The posterior is conditioned on `τ_{:t}` but
the reconstruction runs over `τ_{:H⁺}` — **the whole trajectory, including timesteps
after `t`**. The paper is explicit that this *"is different than the conventional VAE
setup (and possible since we have access to this information during training)"*, and
that it is what makes the agent able to *"perform inference about unseen states given
the past"*. The reconstruction factorises as

$$
\log p(\tau_{:H^{+}}\mid m, a_{:H^{+}-1}) = \log p(s_0\mid m) + \sum_{i=0}^{H^{+}-1}\Big[\log p(s_{i+1}\mid s_i,a_i,m) + \log p(r_{i+1}\mid s_i,a_i,s_{i+1},m)\Big],
$$

i.e. an initial-state term `T'_0`, a transition decoder `T'` and a reward decoder `R'`.

*(b) The prior is the previous posterior.* *"We set the prior to our previous
posterior, `q_φ(m\|τ_{:t−1})`, with initial prior `q_φ(m) = N(0, I)`."* So the KL term
is a **step-wise** regulariser penalising abrupt belief revision, not a pull toward a
fixed `N(0,I)`. This is the recursive-filter structure written as a variational
objective — and it is the mechanism that makes the latent settle rather than drift.
The appendix notes the fixed initial prior is a weak point (§3.6).

#### 3.4.3 The full objective and the gradient routing

Three parameter sets: encoder `φ`, decoders `θ` (transition `p^T_θ` and reward
`p^R_θ`), policy `ψ`. The joint objective sums the ELBO **over all context lengths**:

$$
\mathcal{L}(\phi,\theta,\psi) \;=\; \mathbb{E}_{p(M)}\!\left[\, J(\psi,\phi) \;+\; \lambda \sum_{t=0}^{H^{+}} \mathrm{ELBO}_{t}(\phi,\theta)\right].
$$

Summing over `t` is what teaches **online** inference: the same encoder must produce a
sensible posterior after 1 step and after 400. *"In practice, we may subsample a fixed
number of ELBO terms (for random time steps `t`) for computational efficiency if `H⁺`
is large."*

**The gradient-routing decision is the most transferable implementation detail in the
paper.** `λ` exists because `φ` is shared between the model and the policy — but:

> *"we found that backpropagating the RL loss through the encoder is typically
> unnecessary in practice. Not doing so also speeds up training considerably, avoids
> the need to trade off these losses, and prevents interference between gradients of
> opposing losses."*

So in the released setup the encoder is trained by the **VAE loss only**; the policy
sees the posterior as a **detached input**. Consequences: separate optimisers and
learning rates (policy 7e-4, VAE 1e-3 on MuJoCo); **separate replay buffers** — the
on-policy learner uses only recent data while the VAE keeps a larger trajectory
buffer; and a real speedup, because PPO minibatch updates need not recompute
embeddings (§C.4: VariBAD 48 h vs RL² 60 h on HalfCheetahDir, despite both being
recurrent). Note this is the *same architectural discipline* CARE reaches by a
different route (stop-gradient on the context inside the attention): **keep the
conditioner's training signal separate from the pathway it conditions.**

At meta-test time the **decoder is discarded** and **no gradient adaptation happens** —
*"the policy has learned to act approximately Bayes-optimal during meta-training."*

#### 3.4.4 VariBAD minus the VAE is RL²

Stated by the authors: *"If we remove the decoder (Fig 2) and the VAE objective
(Eq (7)), variBAD reduces to this setting"* — RL², a recurrent policy fed the previous
action and reward. The differences are therefore exactly two: **a stochastic latent
variable** (an inductive bias for representing uncertainty) and **a reconstruction
decoder** acting as an auxiliary loss. Everything else — recurrence, online adaptation,
the conditioning being a vector handed to a feedforward policy — is shared. This makes
the RL² baseline the paper's *de facto* ablation of the conditioning signal.

### 3.5 The base architecture, exactly — for reading FiLM-vs-hypernetwork numbers on VariBAD

Reproduced verbatim from Appendices B.2 (gridworld) and C.6 (MuJoCo).

| Component | Gridworld | MuJoCo |
|---|---|---|
| RL algorithm | A2C, 60 policy steps, 16 parallel processes | PPO, batch 3200, 2 epochs, 4 minibatches, clip 0.1, **Huber** value loss |
| Discount `γ` | 0.95 | not listed |
| Max grad norm | 0.5 | 0.5 |
| Value loss coeff. | 0.5 | 0.5 |
| Entropy coeff. | 0.01 | 0.01 |
| GAE `τ` | 0.95 | — |
| ELBO / KL weight | ELBO loss coefficient **1.0** | weight of KL term in ELBO **0.1** |
| Policy LR | 0.001 | 0.0007 |
| VAE LR | 0.001 | 0.001 |
| **Task embedding size** | **5** | **5** |
| **Policy architecture** | **2 hidden layers, 32 nodes each, TanH** | **2 hidden layers, 128 nodes each, TanH** |
| **Encoder architecture** | FC layer, 40 nodes → **GRU hidden 64** → output layer with **10 outputs (µ and σ)**, ReLU | separate state/action/reward encoders (**32 / 16 / 16**-dim) → **GRU hidden 128** → output layer with **5 outputs**, ReLU |
| Reward decoder | 2 hidden layers, 32 nodes, **25 output heads** (one per grid cell), ReLU | 2 hidden layers, **64 and 32** nodes, ReLU |
| Decoder loss | binary cross-entropy | mean squared error |

**Four notes that matter for interpreting downstream comparisons.**

1. **The conditioning vector handed to the policy is 10 numbers** — `(µ, σ)` for a
   5-dimensional latent. Gridworld says so explicitly (*"output layer with 10 outputs
   (µ and σ)"*); the MuJoCo table says *"output layer with 5 outputs"* for the same
   stated embedding size of 5, which is **an apparent inconsistency in the PDF** — most
   plausibly the MuJoCo row lists the latent dimensionality rather than the head width.
   Record it as printed and flag it.
2. **The policy is small and tanh.** A 2×128 tanh MLP. Any claim that FiLM or a
   hypernetwork "improves VariBAD" is a claim about modifying *this* network — not a
   deep residual stack. Effect sizes should be read with that in mind.
3. **The combination operator is unstated in the paper.** Whatever a follow-up paper
   calls its "concatenation baseline" on VariBAD is a reconstruction from the released
   code, not a quotation from this PDF. If the report attributes concatenation to
   VariBAD, attribute it to the implementation.
4. **The encoder is not trained by the RL loss.** A follow-up that inserts a modulator
   between the belief and the policy is inserting it **downstream of a detached
   signal** — the modulator's gradients do not reach the inference network. That is a
   materially different situation from FiLM in a supervised network, and it constrains
   what a "FiLM vs hypernetwork on VariBAD" result can be evidence for.

### 3.6 Results, as printed

**There are no result tables in this paper.** Everything quantitative is a figure.
What can be stated verbatim:

*Gridworld (5×5, hidden goal, sparse reward −0.1 / +1, `H = 15`, `H⁺ = 4H`, 20 seeds).*
- VariBAD's behaviour *"closely matches"* the hard-coded Bayes-optimal policy and
  matches optimal performance **from the third rollout**; hard-coded Bayes-optimal
  matches it from the second; posterior sampling needs **six** rollouts (Fig. 1e).
- The decoder's per-cell reward predictions progressively zero out visited cells; the
  5-dim latent's variance collapses and its mean settles the moment the goal is found
  (Fig. 3b, 3c).
- Exact-solution counting (§B.3): *"variBAD learned the Bayes-optimal solution for 4
  out of 20 seeds, RL² zero times."* Both otherwise land close to Bayes-optimal.
- Trained on 4 episodes, evaluated on 6: **RL²'s performance drops after the fourth**;
  VariBAD's does not.

*MuJoCo (AntDir, HalfCheetahDir, HalfCheetahVel, Walker with randomised system
parameters; 5 seeds; Fig. 4).*
- *"Only variBAD and RL² are able to adapt to the task at hand within a single
  episode."* PEARL, E-MAML and ProMP *"are not designed to maximise reward during a
  single rollout, and perform poorly in this case"*; PEARL *"only starts performing
  well starting from the third episode"*.
- *"RL² underperforms variBAD on the HalfCheetahDir environment, and learning is
  slower and less stable."*
- VariBAD's first rollout, exploratory steps included, *"matches the optimal oracle
  policy (which is conditioned on the true task description) up to a small margin"*.
- Honest caveats: PEARL *"is more sample efficient during meta-training"* because it is
  off-policy, and PEARL slightly outperforms the oracle *"likely since our oracle is
  based on PPO, and PEARL is based on SAC"*.
- Runtime (§C.4, self-described as rough): ProMP/E-MAML 5–8 h, PEARL 24 h, **VariBAD
  48 h**, RL² 60 h.

*Latent-space behaviour (§C.5, HalfCheetahDir).* Posterior mean and log-variance adapt
*"within just a few environment steps"*; variance decreases monotonically as certainty
grows; *"the values of the latent dimensions swap signs between the two tasks"* —
i.e. for a binary task family the 5-dim latent uses sign as the task code.

*Acknowledged weakness in the prior (§B.1).* In the gridworld the latent starts near
mean 1 / variance 0, and *"the variance increases for a little bit before the agent
finds the goal"*, so *"this prior might not be optimal. A natural extension of variBAD
is therefore to also learn the prior."*

### 3.7 Relevance to this project

- **The belief-as-conditioner precedent.** If the project wants a modulator that reads
  something the agent *infers* rather than something it is *told*, VariBAD is the
  canonical citation, and the mechanism is fully specified: a GRU over
  `(s, a, r)` history, a Gaussian head, and the `(µ, σ)` pair handed to the policy.
  The **variance is part of the conditioning signal**, which is the piece most
  reimplementations drop.
- **Uncertainty enters the policy as an ordinary input, not as a gate.** Nothing in
  VariBAD scales, gates, or routes. If the project's framing is "uncertainty modulates
  processing", VariBAD is precedent for the *signal*, not for the *operator* — and
  saying so protects the report from a common miscitation.
- **The prior-is-the-previous-posterior trick.** Regularising each step's belief toward
  the previous step's rather than toward a fixed `N(0,I)` is a cheap way to get a
  stable, slowly-varying latent out of a recurrent encoder. Directly transferable to
  any project component that maintains a running internal state a policy conditions on.
- **Keep the conditioner's gradients out of the RL loss.** Two independent papers in
  this batch (VariBAD §3.2, CARE's stop-gradient) arrive at the same discipline for
  different stated reasons — VariBAD for stability and speed, CARE for
  interpretability. Worth stating as a corpus-level pattern.
- **Scope limit to carry into any transplant.** The BAMDP assumption is that the hidden
  variable is **constant within an episode**. A project quantity that changes during an
  episode (a physiological state, a drifting context) violates it, and the paper itself
  names filtering approaches as the alternative for that case.
- **Do not cite this paper for effect sizes.** It has no result tables. Any number
  attributed to VariBAD comes from a follow-up paper's reimplementation.

### 3.8 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Bayes-optimal policies condition on the agent's *uncertainty about the environment*, not just the state; computing them is intractable. Introduces **variBAD**: meta-learn approximate inference in an unknown environment and *"incorporate task uncertainty directly during action selection"*. Gridworld shows structured online exploration as a function of task uncertainty; MuJoCo shows higher **online** return than existing methods. |
| 1 | **Introduction** | Exploration/exploitation framed as maximising return **during** learning, motivated by healthcare and education. BAMDP = MDP augmented with a belief; Bayes-optimal agent *"systematically seek[s] out the data needed to quickly reduce uncertainty, but only insofar as doing so helps maximise expected return"*, upper-bounded by the oracle policy. Posterior sampling is the tractable shortcut and is *"highly inefficient and far from Bayes-optimal"* — Fig. 1 contrasts the two on the gridworld. Two contributions: **(1)** a VAE inferring the posterior over `m` online, **(2)** a policy conditioning on that posterior. Prior BAMDP work is tractable only in tiny spaces *"or rel[ies] on privileged information about the task during training"*. Footnote: environment / task / MDP used interchangeably. |
| 2 | **Background** | MDP `(S,A,R,T,T_0,γ,H)` and the standard return objective. |
| 2.1 | Training Setup | Meta-learning setup: `p(M)` over MDPs, `M_i` with varying `R_i, T_i` that *"share some structure"*; index `i` is an unknown task description (goal position, natural-language instruction) or task ID. **Meta-test evaluation is average return *during* learning.** Two requirements: incorporate prior knowledge from related tasks, and reason about task uncertainty when acting. |
| 2.2 | Bayesian Reinforcement Learning | Prior `b_0 = p(R,T)`, posterior `b_t = p(R,T\|τ_{:t})`, hyper-state `s⁺ ∈ S × B`. Eq. 1 hyper-transition = expected environment transition × deterministic Bayes update. Eq. 2 hyper-reward = posterior-expected reward. Eq. 3 BAMDP return, with the `H` vs `H⁺ = N×H` distinction and the observation that optimal exploration depends on remaining time. BAMDP is a **belief MDP** whose hidden state (the model) is **constant per task**. Three named intractabilities: unknown parameterisation, intractable belief update, intractable belief-space planning. Promises to learn all three jointly, end-to-end, **with no planning at test time and no privileged task information**. |
| 3 | **Bayes-Adaptive Deep RL via Meta-Learning** | Introduce the latent `m_i` standing in for the unknown task index: Eq. 4 `R_i ≈ R(·; m_i)`, Eq. 5 `T_i ≈ T(·; m_i)` with `R,T` shared. Eq. 6 defines the trajectory `τ_{:t}`. Argument for latents: reward/transition functions may have millions of parameters, *"but the embedding `m` can be a small vector"*. Fig. 2 = architecture (RNN over `(s,a,r)` → posterior → policy; decoder predicts past **and future**). |
| 3.1 | **Approximate Inference** | Exact posterior unavailable; learn model `p_θ(τ_{:H⁺}\|a)` plus amortised `q_φ(m\|τ_{:t})`. Eq. 7 the intractable model objective. Eq. 8 the ELBO. **Prior set to the previous posterior**, initial prior `N(0,I)`. **Encode the past, decode the whole trajectory including the future** — different from a conventional VAE, only possible at training time, and necessary so the agent can *"perform inference about unseen states given the past"*. Eq. 9 factorises the reconstruction into initial state, transition and reward terms. |
| 3.2 | **Training Objective** | The three networks: encoder `q_φ`; approximate transition `p^T_θ` and reward `p^R_θ`; **policy `π_ψ(a_t \| s_t, q_φ(m\|τ_{:t}))`, dependent on `φ`.** *"The posterior can be represented by the distribution's parameters (e.g. mean and standard deviation if `q` is Gaussian)."* Eq. 10 the joint objective with `λ` trading model against RL loss, summing ELBO over **all** context lengths `t` so inference is learned online; subsample terms if `H⁺` is large. RNN encoder as in RL², with set-encoders / neural processes named as alternatives. **The RL loss is not backpropagated through the encoder in practice** — separate optimisers, learning rates and data buffers (policy on recent on-policy data, VAE on a larger trajectory buffer). At meta-test: forward passes only, **decoder unused, no gradient adaptation**. |
| 4 | **Related Work** | *Meta-RL*: RL² (recurrence, previous action+reward as auxiliary input) — **variBAD minus decoder and VAE objective is RL²**; MAML / Reptile / E-MAML / ProMP (gradient adaptation; lightweight feedforward policies; separate exploration and exploitation phases by design). *Skill/task embeddings*: Hausman, Arnekvist, Co-Reyes, Zintgraf 2019, Zhang 2018, Perez 2018, Lan 2019, Sæmundsson, plus imitation-learning embeddings — variBAD differs *"mainly in what the embedding represents (i.e., task uncertainty) and how it is used"*. *Bayesian RL*: exact methods restricted to small/discrete spaces; variBAD *"lacks the formal guarantees"* of those; closest relative **Humplik et al. 2019**, which also conditions the policy on a posterior but **meta-trains it with privileged task descriptions**, whereas variBAD is unsupervised. Posterior sampling described and dismissed as less efficient. *Contextual MDPs and HiP-MDPs* related but assume given context / need a longer inference period. *Variational inference and meta-learning*: neural processes etc. *POMDPs*: BAMDP is the special case with a **fixed** hidden state, exploited by learning a time-invariant embedding rather than filtering. |
| 5 | **Experiments** | Roadmap: didactic gridworld for properties, four MuJoCo tasks for scale. |
| 5.1 | Gridworld | 5×5, goal uniformly random and unobserved, never adjacent to the start (bottom-left); actions up/right/down/left/stay, deterministic; reset after 15 steps; `H = 15`, `H⁺ = 4H = 45`; reward −0.1 off-goal, +1 on-goal; latent dim 5. Fig. 3a rollout with posterior visualised as background shading; 3b per-cell reward predictions progressively zeroing out; 3c latent variance collapsing and mean settling at goal discovery. Concludes behaviour closely matches Bayes-optimal and outperforms posterior sampling. |
| 5.2 | MuJoCo Continuous Control | AntDir and HalfCheetahDir (two tasks: forward/backward), HalfCheetahVel (target velocity), Walker (randomised system parameters); environments taken from the PEARL codebase. Fig. 4, 5 seeds, first 5 rollouts. Only variBAD and RL² adapt within one episode; RL² underperforms on HalfCheetahDir and is slower and less stable; first rollout matches the PPO oracle up to a small margin; PEARL/E-MAML/ProMP need many more interactions; PEARL is more sample-efficient in meta-training (off-policy) and slightly beats the PPO-based oracle because it is SAC-based. |
| 6 | **Conclusion & Future Work** | Summary. Future: use the decoder at test time for model-predictive planning or as an out-of-distribution detector; **out-of-distribution task generalisation is explicitly flagged as a failure mode** — the inference will be wrong and *"the policy will not be able to interpret a changed posterior"*, likely requiring further training of encoder, decoder, policy, or explicit planning. |
| A | Full ELBO Derivation | Eq. 11: importance-weighted rewriting, Jensen, split into reconstruction minus KL. Four lines, reproduced in §3.4.2 above. |
| B | Experiments: Gridworld | **B.1** the prior may be sub-optimal (variance rises before the goal is found); learning the prior proposed. **B.2** hyperparameters (A2C; `γ=0.95`; latent 5; policy 2×32 tanh; encoder FC 40 → GRU 64 → 10 outputs (`µ`,`σ`); reward decoder 2×32 with **25 output heads**, binary cross-entropy) plus RL²'s (state→FC 32, reward→FC 8, concatenate → GRU 128 → FC 32 → actions, tanh throughout). **B.3** RL² comparison: trained on `H⁺ = 4H = 60`, evaluated on 6 episodes; variBAD hits the exact Bayes-optimal solution in **4/20 seeds**, RL² in **0/20**; RL² degrades after episode 4 *"due to instabilities in the 128-dimensional hidden state"*, variBAD does not. |
| C | Experiments: MuJoCo | **C.1** learning curves; oracle trained with PPO, PEARL/E-MAML/ProMP from reference implementations. **C.2** `H = 200` but trained at `H⁺ = 400`; a `done` flag added to the state so resets are visible; RL² instability in CheetahVel analysed — a sudden state shift at reset can wreck the hidden state, and once running at the right velocity RL² can read the task off its own velocity and *"stop doing inference"*; variBAD is less exposed because its latent is trained to represent *"the task, and only the task"*. **C.3** HalfCheetahDir test-time behaviour: variBAD and RL² adapt online, PEARL follows its current sample and can walk the wrong way for two rollouts. **C.4** runtimes: ProMP/E-MAML 5–8 h, PEARL 24 h, variBAD 48 h, RL² 60 h; variBAD is faster than RL² under PPO precisely because the RL loss is not backpropagated through the recurrent encoder. **C.5** latent-space visualisation: mean and log-variance adapt in a few steps, variance falls, latent dimensions **swap sign** between "go left" and "go right"; notes that a ground-truth task predictor could be trained separately for analysis but is deliberately not used for meta-training. **C.6** hyperparameters (PPO, batch 3200, clip 0.1, Huber value loss, KL weight 0.1, policy LR 7e-4, VAE LR 1e-3, latent 5, policy 2×128 tanh, encoder 32/16/16 → GRU 128 → 5 outputs, reward decoder 64→32, MSE). |

---
