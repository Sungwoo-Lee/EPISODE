---
title: "HyperMARL: Adaptive Hypernetworks for Multi-Agent RL"
slug: tessera_2024_hypermarl
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_held_unreviewed.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 1. Tessera et al. — HyperMARL: Adaptive Hypernetworks for Multi-Agent RL

**PDF:** `docs/project/references/modulation_in_rl/sources/Tessera et al. 2024 - HyperMARL - adaptive hypernetworks for multi-agent RL.pdf`
**Venue as printed inside the PDF (page 1 footer, verified):** *"39th Conference on
Neural Information Processing Systems (NeurIPS 2025)."* The stamp on the left margin
of page 1 reads `arXiv:2412.04233v4 [cs.LG] 29 Oct 2025`. So: **NeurIPS 2025**, from a
2024 first preprint — the filename's "2024" is the arXiv-v1 year, as the folder's
README already notes. Authors: Kale-ab Abebe Tessera and Amos Storkey (Edinburgh),
Arrasy Rahman (UT Austin), Stefano V. Albrecht (DeepFlow). Code released.

### 1.1 What the paper is about, in plain words

In cooperative multi-agent RL it is standard to train **one** neural network and let
every agent use it, because training a separate network per agent is expensive and
wasteful. To let the shared network still behave differently for different agents, the
usual trick is to feed it a one-hot **agent ID** alongside the agent's observation.
This paper's finding is that this standard trick is *actively harmful*: because one
set of weights receives update signals from all agents at once, and those agents may
see near-identical things while needing to do opposite things, their gradients point
in opposing directions and partially cancel. The paper calls this **cross-agent
gradient interference**, and shows it is *worse* when the ID and the observation are
fed into the same network together than when they are separated.

The fix — HyperMARL — is to stop feeding the ID into the policy at all. Instead a
small **generator network** (a hypernetwork) reads only the agent's identity embedding
and emits that agent's entire set of policy weights; the policy itself sees only the
observation. Because the generator's input contains no observation, the part of the
gradient that depends on identity is a fixed matrix during any given update, while all
the sampling noise is confined to a separate per-agent term that gets averaged *before*
identity is applied. Agents' updates therefore stop fighting each other, without
changing the RL objective, without needing to be told how diverse the team should be,
and without updating agents one at a time.

**Headline verdict.** The paper is competent, well-controlled, and correctly
identified by the earlier appendix note as this corpus's best source on
**conditioner/observation entanglement**. Its central *architectural* claim — decouple
the generator's input from the policy's input — is supported by **two independent
ablations**, not one. Its *variance* claim is weaker than the abstract implies: the
decomposition it derives is a factorization identity, not an inequality, and no
proof that HyperMARL's gradient variance is lower than a shared network's appears
anywhere. The measurement that backs it is a single four-condition bar chart on a
single toy environment whose numbers are never printed.

### 1.2 Direct answers to the required questions

| Question | Answer |
|---|---|
| **Conditioning signal** (what the generator reads) | The **agent's identity, and nothing else**. Concretely $e_i$, which is a one-hot agent ID for the *linear* hypernetwork variant and a **learned, orthogonally-initialised embedding** for the *MLP* variant. Embedding dimension is tiny: **4** for IPPO and **8** for MAPPO on both Dispersion and Navigation (Tables 11, 14); swept over $\{4, 16, 64\}$ / $\{4, 8, 16, 64\}$. The observation **never** enters the generator — that is the entire point. |
| **What is generated** | **All weights and biases of the target network**, not a modulation. Which networks depends on the experiment (App. G.2): Dispersion + Navigation → **both actor and critic** are generated; MAMuJoCo/MAPPO → **actor only** (the centralised critic is left as a normal network conditioned on global state, to keep the comparison against HAPPO/MAPPO fair); SMAX recurrent IPPO → **the feedforward actor and critic weights only, not the GRU weights**. Target policy on Dispersion is a 2-hidden-layer MLP, `ACTOR_LAYERS [64, 64]`, `CRITIC_LAYERS [64, 64]`, ReLU (Table 10); on Navigation `[256, 256]`, tanh (Table 13). |
| **The operator, and where it sits on the capacity spectrum** | **Full weight generation** — the far end. $\theta_i = h^\pi_\psi(e_i)$ replaces the weights outright; there is no gain, no shift, no residual, no base network to modulate. Not FiLM, not low-rank, not parameter composition. The *linear* variant is a degenerate case worth naming: with a one-hot input, $\theta_i = \mathbf{1}_i W + b$ selects **row $i$ of $W$** and adds a shared bias $b$ — i.e. a per-agent weight bank plus one shared offset. The paper says explicitly that with $b$ removed this "effectively replicates training of separate policies for each task", i.e. collapses to no-parameter-sharing. |
| **RL algorithm** | **On-policy PPO variants**: IPPO (independent PPO) and MAPPO (centralised-critic PPO) are the backbone for HyperMARL and for all baselines except two. **MATD3** (off-policy) is used only for the Kaleidoscope comparison, because that is the only tuned implementation Kaleidoscope released. **A2C** is used only for the SePS comparison, for the same reason. The two toy games in §3 use plain **REINFORCE**. |
| **Environments** | 22 scenarios across five suites: **Dispersion** (VMAS, 4 agents, discrete, heterogeneous); **Navigation** (VMAS, 2/4/8 agents, continuous, homogeneous / heterogeneous / mixed goals); **Multi-Agent MuJoCo** (2–17 agents, continuous, heterogeneous — body parts as agents); **SMAX** (JaxMARL, 2–20 agents, discrete, homogeneous — two SMACv1 and two SMACv2 maps); **Blind-Particle Spread** (15–30 agents, discrete, heterogeneous, agents cannot see their own assigned colour). Plus two purpose-built normal-form games, the **Specialisation Game** (reward for picking distinct actions) and the **Synchronisation Game** (reward for picking identical actions), each in a temporal $n$-player form. |
| **Baselines** | Six named: **NoPS** (per-agent networks), **FuPS+ID** (one shared network fed the one-hot ID), **DiCo** (preset diversity level), **HAPPO** (per-agent actors, sequential updates), **Kaleidoscope** (learned masks + 5-critic ensemble + explicit diversity loss), **SePS** (autoencoder clustering of agents in a pre-training phase). Four further candidates (SEAC, CDAS, ROMA/RODE, SNP-PS) are named and explicitly declined with reasons (Table 6). |
| **Seed counts** | Toy games: **10 seeds**. Dispersion: stated as **10 seeds** in App. G.2.1 — but Table 10 lists exactly **five** seed values (`30, 1, 42, 72858, 2300658`). **These two statements contradict each other**; the paper never resolves it. Navigation, SMAX, MAMuJoCo: **5 seeds**, 10 M steps. BPS: **5 seeds**, 20 M steps. MATD3/Kaleidoscope and A2C/SePS comparisons: **5 seeds**. All aggregation is IQM (interquartile mean) with 95 % stratified bootstrap CIs, following Agarwal et al. |
| **Reported instabilities / failure modes** | (a) **Removing gradient decoupling breaks the method** — see §1.4. (b) **Initialisation scaling is load-bearing at scale**: dropping the reset-fan-in/out rescaling (`w/o RF`) badly damages 17-agent Humanoid but barely touches 4-agent Dispersion, so "principled initialisation becomes more vital with increased complexity". (c) **Embedding dimension is a real hyperparameter, and bigger is not better**: on 20-agent SMAX, embedding dim 4 reaches IQM win rate **0.4455**, embedding dim 64 reaches **0.1155** at the same learning rate — a 3.9× collapse from changing one number. (d) **Parameter count** is named as the paper's own principal limitation (App. A). (e) A residual honesty point the paper makes itself: MLP hypernetworks, unlike the one-hot linear variant, **do not guarantee distinct weights per agent**. |

### 1.3 Headline numbers

Every number below is quoted from a table in the paper unless flagged **[digitized]**.

**Multi-Agent MuJoCo, MAPPO variants (Table 3; IQM of mean episode return, 95 % CI; 5 seeds).**
HyperMARL takes the top IQM in 3 of 4 scenarios. `*` in the paper marks CI overlap with the top score.

| Scenario | HAPPO | FuPS+ID | Independent actors | **HyperMARL** |
|---|---|---|---|---|
| Humanoid-v2 17×1 | 6501.15* | **566.12** | 6188.46* | **6544.10** |
| Walker2d-v2 2×3 | 4748.06* | 4574.39* | 4747.05* | **5064.86** |
| HalfCheetah-v2 2×3 | 6752.40* | 6771.21* | 6650.31* | **7063.72** |
| Ant-v2 4×2 | 6031.92* | **6148.58** | 6046.23* | 5940.16* |

The row that matters is **Humanoid**: the shared-network-plus-ID baseline scores
**566**, versus **6544** for the same shared-parameter budget routed through a
generator — a **11.6×** gap, and the only condition in the table where any method
fails outright. HyperMARL is the only *shared-actor* method that learns this task
at all; HAPPO and Independent Actors both use per-agent actors.

**Blind-Particle Spread, A2C variants (Table 8; IQM final total reward, 5 seeds, higher = less negative = better).**

| Scenario | NoPS | FuPS+ID | SePS | **HyperMARL** |
|---|---|---|---|---|
| BPS-1 (15 agents, 3 groups) | −216.8 | −228.2 | −201.8* | **−190.8** |
| BPS-2 (30 agents, 3 groups) | −415.4* | −429.7 | −407.1* | **−397.8** |
| BPS-3 (30 agents, 5 groups) | **−403.4** | −835.2 | −422.1* | −417.7* |
| BPS-4 (30 agents, 5 uneven groups) | −410.8* | −780.5 | −411.6* | **−389.5** |

Here FuPS+ID collapses specifically when the number of required roles rises to five
(−835.2 and −780.5 versus roughly −410 for everything else) — i.e. the shared-network
failure is **a function of how many distinct behaviours are needed**, not of agent count
(BPS-2 and BPS-3 both have 30 agents; only the 5-group one breaks).

**MAMuJoCo off-policy, MATD3 variants (Table 7):** HyperMARL matches Kaleidoscope
(Ant 5886.58* vs 6160.70; HalfCheetah **7057.44** vs 6901.00*; Walker2d **7057.68** vs
6664.32*; Swimmer-10×2 **465.91** vs 462.48*) while using two critics instead of five
and no diversity loss.

**SMAX (homogeneous tasks, the "does it hurt when you don't need diversity" check):**
comparable to FuPS on all four maps, "some FuPS variants might exhibit marginally
faster initial convergence on simpler maps". No table of final values in the main text;
interval plots in Fig. 22.

**Dispersion (Figs. 4a–b, 18):** FuPS variants fail to reach the optimal specialised
policy; NoPS and both hypernetwork variants converge. Fig. 19 rules out the obvious
objection — MAPPO-FuPS run for **40 M** steps (double the hypernetwork's budget) still
converges to the same suboptimal plateau. Fig. 15 rules out the capacity objection —
FuPS scaled up to *match HyperMARL's trainable parameter count* still underperforms,
"despite generating 10× smaller networks".

**Parameter scaling (Fig. 14, log-log, 4 → 1024 agents):** NoPS, the linear
hypernetwork and FuPS+one-hot all grow **linearly** in agent count; the MLP
hypernetwork grows **nearly flat**, because each new agent costs only one
fixed-size embedding. This is the paper's actual efficiency argument and it is
about *scaling*, not about absolute size — at small agent counts HyperMARL uses
**more** parameters than either NoPS or FuPS, which App. A concedes.

### 1.4 The entanglement mechanism — extracted carefully

This is the part the project actually needs, so it gets stated precisely.

#### (a) The two ablations — there are two, not one

The earlier §17 note cited only `HyperMARL w/o GD`. The paper's evidence for
conditioner/observation entanglement being harmful is in fact **two separate
manipulations at two different levels of the architecture**, and the *first* one is
the cleaner of the two.

**Ablation 1 — `FuPS+ID (No State)`, §3.2.** A *monolithic* shared policy (no
hypernetwork anywhere) is stripped of its observation input: $\pi_\theta(a^i \mid id_i)$
instead of $\pi_\theta(a^i \mid o^i, id_i)$. It **outperforms** the full-input policy
at every team size tested, in an environment where the observation is a legitimate
input. Digitized values from Fig. 3a (Specialisation Game, average evaluation reward,
markers with 95 % CI; precision ±0.01):

| $n$ agents | NoPS (drawn as a reference line) | FuPS+ID | **FuPS+ID (No State)** | HyperMARL (MLP) |
|---|---|---|---|---|
| 2 | 0.885 | 0.645 [0.593, 0.697] | **0.700** [0.623, 0.778] | 0.820 [0.750, 0.890] |
| 4 | 0.740 | 0.397 [0.364, 0.432] | **0.600** [0.562, 0.638] | 0.687 [0.667, 0.707] |
| 8 | 0.677 | 0.247 [0.234, 0.261] | **0.600** [0.554, 0.646] | 0.594 [0.580, 0.608] |
| 16 | 0.640 | 0.131 [0.119, 0.143] | **0.463** [0.428, 0.497] | 0.568 [0.555, 0.583] |

*(Digitization check: the FuPS+ID column reproduces the paper's own Table 1 values
0.64 / 0.40 / 0.25 / 0.13 to within 0.005, and the NoPS reference line reproduces
0.88 / 0.74 / 0.68 / 0.64 exactly. That is the calibration evidence for the whole
digitized table.)*

**At 16 agents, deleting the observation from a shared policy raises its reward from
0.131 to 0.463 — a 3.5× improvement, with non-overlapping intervals.** This is the
single strongest number in the paper for the entanglement claim, and it is not in the
paper's text; it exists only as plotted points.

The accompanying gradient measurement, Fig. 3b — **mean inter-agent gradient cosine
similarity**, defined in App. E.4 as
$\cos\!\big(g^{(i)}_t, g^{(j)}_t\big) = \frac{\langle g^{(i)}_t, g^{(j)}_t\rangle}{\lVert g^{(i)}_t\rVert\,\lVert g^{(j)}_t\rVert}$
with $g^{(i)}_t = \nabla_\theta \mathcal{L}^{(i)}(\theta_t)$ — digitized (precision ±0.005):

| $n$ agents | FuPS+ID | FuPS+ID (No State) | HyperMARL |
|---|---|---|---|
| 2 | −0.186 [−0.372, 0.000] | +0.008 | −0.031 |
| 4 | −0.060 [−0.137, +0.017] | −0.010 | −0.029 |
| 8 | −0.099 [−0.155, −0.045] | −0.003 | −0.003 |
| 16 | −0.107 [−0.169, −0.046] | −0.013 | +0.003 |

Three things follow that the paper does not say:
- The conflict is **real but small in magnitude** — worst case ≈ −0.19 cosine
  similarity on an axis the figure itself annotates from +1 to −1. "Destructive
  interference" is a directional statement about the sign, not about magnitude.
- The interval **excludes zero only at $n = 8$ and $n = 16$**. At $n = 2$ and $n = 4$
  the CI straddles zero. The gradient-conflict evidence is therefore a
  **large-team** result, even though the *performance* gap is present at every size.
- HyperMARL and `No State` are indistinguishable on this metric, which is exactly the
  paper's thesis: the generator buys you the near-orthogonal gradients of a
  observation-blind policy *while keeping the observation in the policy*.

**Ablation 2 — `HyperMARL w/o GD`, §6.1.** Here the generator's input is changed from
$e_i$ to $[o_t, e_i]$, so the generator now reads the same observation the generated
policy reads. Result (Fig. 8a, 8b): degrades performance on **both** tested
environments — 17-agent Humanoid and Dispersion — and the caption states *"Gradient
decoupling (a,b) is consistently critical across both environments."* Fig. 23 repeats
it on Dispersion alongside the other variants and reaches the same conclusion. **No
numerical values are printed for either figure**, and unlike Fig. 3 the curves are
time series with shaded bands rather than point markers, so they are not usefully
digitizable. The strength of this ablation is therefore *qualitative*: consistent
direction on two environments, magnitude unstated.

#### (b) The variance decomposition, and exactly which assumption fails

The paper's structural argument, §4.3 and App. F.2. Start from the standard
multi-agent policy gradient with a centralised critic, for agent $i$'s own parameters:

$$\nabla_{\theta_i} J(\theta_i) = \mathbb{E}_{h_t, a_t \sim \pi}\Big[ A(h_t, a_t)\, \nabla_{\theta_i} \log \pi_{\theta_i}(a^i_t \mid h^i_t) \Big],$$

with $A(h_t,a_t) = Q(h_t,a_t) - V(h_t)$. Under HyperMARL there is no $\theta_i$ to
optimise — there is only $\psi$, and $\theta_i = h^\pi_\psi(e_i)$. The chain rule gives

$$\nabla_\psi J(\psi) = \sum_{i=1}^{I} \underbrace{\nabla_\psi h^\pi_\psi(e_i)}_{J_i \;(\text{agent-conditioned})} \; \underbrace{\mathbb{E}_{h_t,a_t\sim\pi}\Big[A(h_t,a_t)\,\nabla_{\theta_i}\log \pi_{\theta_i}(a^i_t\mid h^i_t)\Big]}_{Z_i \;(\text{observation-conditioned})}. \tag{4}$$

The empirical estimator over $B$ i.i.d. trajectories of length $T$ is

$$\hat g_{\mathrm{HM}} = \sum_{i=1}^{I} J_i \Big(\tfrac{1}{B}\sum_{b=1}^{B}\sum_{t=0}^{T-1} A\big(h^{(b)}_t, a^{(b)}_t\big)\, \nabla_{\theta_i}\log\pi_{\theta_i}\big(a^{i,(b)}_t \mid h^{i,(b)}_t\big)\Big) \;=\; \sum_{i=1}^{I} J_i \hat Z_i .$$

**The paper's three assumptions, as literally printed:** (A1) trajectories are i.i.d.;
(A2) all second moments are finite; (A3) $\psi$, $\theta$, $e_i$ are **fixed during
the backward pass**.

The derivation is three steps, each of which the paper labels:

$$\operatorname{Var}(\hat g_{\mathrm{HM}}) = \operatorname{Cov}\Big(\sum_i J_i \hat Z_i,\ \sum_j J_j \hat Z_j\Big) \quad \text{[definition } \operatorname{Var}(X)=\operatorname{Cov}(X,X)\text{]}$$
$$= \sum_{i,j} \operatorname{Cov}\big(J_i \hat Z_i,\ J_j \hat Z_j\big) \quad \text{[bilinearity of } \operatorname{Cov}\text{]}$$
$$= \sum_{i,j} J_i \operatorname{Cov}\big(\hat Z_i, \hat Z_j\big) J_j^\top \quad \text{[pull deterministic matrices out of } \operatorname{Cov}\text{]} \tag{11}$$

Equation (12) restates (11) for the mini-batch case and adds the interpretive claim:
HyperMARL "first averages noise within each agent ($\hat Z_i$) and only then applies
$J_i$", whereas FuPS+ID "updates the shared weights $\theta$ with every raw sample
$A\nabla_\theta \log\pi_\theta[h, id]$, leaving observation noise and agent ID
entangled".

**Which assumption fails when the observation enters the generator — a correction.**
The earlier §17 note says the decomposition "requires the generator Jacobian $J_i$ to
be deterministic with respect to the mini-batch (assumption A3), which fails the
moment the observation enters the generator." That is the right conclusion attached to
the wrong assumption, and the distinction is worth getting right because it changes
what a citation of this paper can support.

A3 as printed says only that the *parameters* are held fixed during the backward pass.
That remains true in `w/o GD` — nobody is updating $\psi$ mid-backward-pass. What
actually breaks is the **premise of the factorization step**, which is the third line
above. $J_i$ is pull-out-able from the covariance only because $J_i = \nabla_\psi
h^\pi_\psi(e_i)$ is a function of $(\psi, e_i)$ **alone** — the §4.3 bullet that
states this ("This Jacobian depends only on the fixed embedding $e_i$ and the
hypernetwork weights $\psi$") is an *architectural* fact, not an assumption in the A1–A3
list. Under `w/o GD` the generator's input is $[o_t, e_i]$, so

$$J_i \;\longrightarrow\; J_i(o_t) = \nabla_\psi h^\pi_\psi([o_t, e_i]),$$

which is a random variable over the mini-batch. Line 3 of the derivation is then simply
invalid — $\operatorname{Cov}(J_i(o)\hat Z_i, J_j(o)\hat Z_j)$ does not factor, and the
resulting variance picks up cross-terms between the generator's own sampling noise and
the policy gradient's, including a $\operatorname{Cov}(J_i(o), \hat Z_i)$-type
contribution that has no counterpart in Eq. (11). **So: cite the factorization premise
in §4.3, not assumption A3.**

**A second, larger correction: this derivation is not a variance-reduction proof.**
Equation (11) is an *identity*. It says where the noise lives; it does not say there is
less of it. The paper proves no inequality of the form $\operatorname{Var}(\hat
g_{\mathrm{HM}}) \le \operatorname{Var}(\hat g_{\mathrm{FuPS}})$, never writes down the
FuPS+ID estimator's variance in comparable form, and the comparison in the text is
verbal ("leaving observation noise and agent ID entangled"). The abstract's
"empirically reduces policy gradient variance" is accurate precisely because of the
word *empirically*. Anyone citing HyperMARL for "hypernetworks reduce policy-gradient
variance" is citing a measurement, not a theorem.

#### (c) The variance measurement — "directional only" was right about the text, but the numbers are recoverable

The prior digest recorded the variance claim as **"directional only — Fig. 4c is a bar
chart and no numerical value appears in the text."** A full-text search confirms the
second half exactly: the strings "variance"/"Variance" occur 12 times in the paper and
**not once with a number attached**. So the digest's factual statement is correct.

It is, however, an understatement of what the figure contains, because Fig. 4c's bars
and error bars are vector geometry. Digitized (units of $\times 10^{-4}$; axis
resolution ≈ 0.0013 per pixel; error bars are the plotted intervals):

| Method | IPPO | MAPPO |
|---|---|---|
| FuPS+ID | 0.0345 [0.0183, 0.0508] | 0.0156 [0.0070, 0.0240] |
| Linear hypernetwork | 0.0079 [0.0058, 0.0097] | 0.0064 [0.0045, 0.0084] |
| MLP hypernetwork | 0.0012 (no interval drawn) | 0.0007 (no interval drawn) |

In absolute terms: FuPS+ID's mean actor gradient variance is ≈ $3.4\times10^{-6}$
(IPPO) against ≈ $1.2\times10^{-7}$ for the MLP hypernetwork — roughly a **29×**
reduction under IPPO and **22×** under MAPPO, with FuPS+ID's plotted interval lying
entirely above both hypernetwork means. So the claim is stronger than "directional":
it is a measured, interval-bearing, order-of-magnitude effect.

Three limits on it, all of which matter more than the size of the number:
1. **One environment.** Fig. 4c is Dispersion only — a 4-agent, sparse-reward, discrete
   toy. No variance measurement is reported for MAMuJoCo, Navigation, SMAX or BPS.
2. **The metric is under-specified.** "Actor gradient variance" is described only as
   "lower mean policy gradient variance … across actor parameters". Whether this is
   the mean over parameters of a per-parameter across-minibatch variance, at which
   training step, and averaged over how many steps, is never stated.
3. **The ablation and the mechanism are never connected.** `HyperMARL w/o GD` — the
   condition that supposedly re-entangles the two gradient sources — is **never
   measured on the variance metric**. Fig. 4c compares FuPS+ID against HyperMARL;
   Fig. 8 compares HyperMARL against `w/o GD` on *return*. There is no cell of the
   design in which the manipulation the theory is about is scored on the quantity the
   theory predicts. That gap is the single most citable weakness of the paper's
   causal story, and it was not recorded in the earlier note.

#### (d) A confound in `w/o GD` that the earlier note got backwards

The §17 entry lists as a confound that the manipulation "regenerates an entire weight
tensor **per timestep** (far heavier than emitting $(\gamma, \beta)$)". Half of that is
right and half is not, and the direction of the error matters for the project.

Algorithm 1 makes the timing explicit: $\theta_i \leftarrow h^\pi_\psi(e_i)$ and
$\phi_i \leftarrow h^V_\phi(e_i)$ are computed in the **outer loop, once per training
iteration**, *before* trajectory collection begins (lines 7–10, then line 11 "Interact
with environment using $\{\pi_{\theta_i}\}$"). Baseline HyperMARL therefore regenerates
weights **once per update, not per timestep** — the generated policy is a fixed network
for the whole rollout.

Under `w/o GD` the generator's input becomes $[o_t, e_i]$, which *necessarily* makes
the weights a function of time: they must now be regenerated **at every environment
step**. So the ablation changes **two** things at once — (i) the generator now reads
the observation, and (ii) the target network stops being a per-iteration constant and
becomes a per-timestep object with a correspondingly different (and much larger)
compute and gradient graph. The paper attributes the resulting degradation entirely to
(i). It never runs the control that would separate them.

For the project this cuts *toward* relevance rather than away from it: a per-step FiLM
modulator reading $o_t$ shares property (ii) with `w/o GD` by construction. The real
confound to carry forward is **tensor size** — a full weight matrix versus a
$(\gamma,\beta)$ pair — not regeneration frequency, which the earlier note had the
wrong way round.

#### (e) A construct limitation worth flagging

The environment in which entanglement is demonstrated most cleanly (§3.2, Fig. 3) is
the temporal Specialisation Game, where the observation is the previous joint action
and the optimal policy is a **fixed distinct-action assignment**. In such a task the
observation is close to a distractor for the optimal policy, which is why an
observation-blind policy can win at all. The authors are candid — "discarding
observations is not a general solution (most tasks require state information)" — but a
reader should not generalise Fig. 3a's 3.5× gap to settings where the observation is
genuinely needed. The `w/o GD` ablation on Humanoid and Dispersion is the evidence that
covers that case, and it is the one with no numbers.

A related note on parameter matching: `FuPS+ID (No State)` is **not** parameter-matched
to `FuPS+ID` — 2,128 versus 18,512 parameters at $n=16$ (Table 9). It wins with 8.7×
fewer parameters, which strengthens rather than weakens the qualitative conclusion, but
means the comparison is not a clean single-factor manipulation either.

### 1.5 Phase 1 — foundational overview

**The problem.** A team of agents learns faster if they share one network, but a shared
network struggles to make them behave *differently* when the task demands it. The usual
patch is to hand the network a tag saying which agent is asking. This paper shows the
patch is part of the problem.

**Why the patch fails.** One set of weights receives gradient updates from all agents
simultaneously. If two agents see similar things but need to do different things, their
updates push the same weights in opposite directions, and the network settles on a
compromise that suits neither. Measured as the cosine similarity between different
agents' gradients, this shows up as a consistently negative value.

**The fix.** Separate the two jobs into two networks. A small generator reads only
*who* the agent is and produces that agent's weights; the produced policy reads only
*what the agent sees*. Identity and observation never meet in the same forward pass, so
their gradients never mix.

**Key findings.**
- A shared policy that is denied its observation entirely learns the specialisation
  task **better** than one that gets both observation and ID — the cleanest possible
  demonstration that it is the *mixing* that hurts, not the lack of information.
- HyperMARL matches per-agent-network diversity while sharing parameters, wins 3 of 4
  MuJoCo scenarios, is the only shared-actor method that learns 17-agent Humanoid at
  all (6544 vs 566 for shared-plus-ID), and does not hurt on tasks where uniform
  behaviour is optimal.
- The mechanism ablation is decisive in direction: feed the observation back into the
  generator and the method degrades on both tested environments.

**Initial takeaway.** If a conditioning signal and a modulated pathway must both
influence one network, keeping them in *separate* computational streams is not a
stylistic choice — in this paper it is the difference between learning the task and
not learning it. That statement is about full weight generation with a *discrete*
conditioner; whether it transfers to a low-dimensional continuous conditioner emitting
a scale-and-shift is exactly the open question the wider report exists to answer.

### 1.6 Phase 2 — graduate-level deep dive

**Setting.** Dec-POMDP $\langle I, S, \{A_i\}, R, \{O_i\}, O, T, \rho_0, \gamma\rangle$
with $n=|I|$, shared reward $R$, per-agent partial observation $o^i_t$, action-observation
history $h^i_t = (o^i_0, a^i_0, \dots, o^i_t)$, decentralised policies $\pi^i(a^i \mid h^i)$.
Objective $\pi^* = \arg\max_\pi \mathbb{E}_{s_0\sim\rho_0, h\sim\pi}[G(h)]$ with
$G(h) = \sum_{t=0}^\infty \gamma^t R(s_t,a_t)$.

**Definition of a specialised environment (App. C, Def. 1).** An environment is
*specialised* iff (i) the optimal joint policy $\pi^*$ contains at least two distinct
agent policies, $\exists i,j: \pi^i \ne \pi^j$; and (ii) for any permutation $\sigma$
of the policies in $\pi^*$, $\mathbb{E}_{h\sim\pi^\sigma}[G(h)] \le
\mathbb{E}_{h\sim\pi^*}[G(h)]$, strictly for non-symmetric joint policies. Condition
(ii) — non-interchangeability — is what rules out the trivial case where agents differ
but their roles could be swapped freely.

**Impossibility result for ID-free sharing (Thm. 1, App. E.3).** In the two-player
non-temporal Specialisation Game, let $\alpha = P(a^i = 0)$ under a single shared
stochastic policy. Enumerating the payoff matrix (0.5 for matching actions, 1 for
distinct):

$$\mathbb{E}[R(\pi)] = 0.5\alpha^2 + \alpha(1-\alpha) + (1-\alpha)\alpha + 0.5(1-\alpha)^2$$
$$= 0.5\alpha^2 + 2\alpha(1-\alpha) + 0.5(1-\alpha)^2$$

Expanding: $0.5\alpha^2 + 2\alpha - 2\alpha^2 + 0.5 - \alpha + 0.5\alpha^2 = -\alpha^2 + \alpha + 0.5$.
Completing the square,

$$\mathbb{E}[R(\pi)] = -(\alpha - 0.5)^2 + 0.75 \;\le\; 0.75 \;<\; 1,$$

with equality at $\alpha = 0.5$. A shared ID-free policy therefore cannot exceed
0.75 against an optimum of 1. Note the scope: this proves that *sharing without any
identity signal* is insufficient. It says nothing about FuPS+ID, which is a universal
approximator and *can* represent the optimum — the paper's point about FuPS+ID is
purely optimisational, not representational.

**The two generator families.** Linear, with one-hot input $\mathbf{1}_i \in \mathbb{R}^{1\times n}$:

$$\theta_i = h^\pi_\psi(\mathbf{1}_i) = \mathbf{1}_i W + b, \qquad W \in \mathbb{R}^{n \times m},\; b \in \mathbb{R}^{1\times m},$$

with $m$ the flattened per-agent parameter count. Because $\mathbf{1}_i$ is one-hot,
$\theta_i = W_{i,:} + b$: an explicit per-agent weight bank plus a shared offset. Setting
$b = 0$ recovers NoPS exactly, which is why $b$ is the only thing making this
"parameter sharing" at all. MLP, with a learned embedding:

$$\theta_i = h^\pi_\psi(e_i) = f^\pi_{\psi_1}\big(g^\pi_{\psi_2}(e_i)\big),$$

$g^\pi_{\psi_2}$ an MLP over the agent context, $f^\pi_{\psi_1}$ a final linear output
layer. The paper flags the trade explicitly: this variant does **not** guarantee
distinct $\theta_i$ for distinct $i$ (two embeddings can map to the same weights — which
is a feature when homogeneity is optimal and a hazard otherwise), and it adds
parameters.

**Initialisation.** $\psi, \varphi$ are initialised so that the *generated* $(\theta_i,
\phi_i)$ match the distribution a direct initialiser would have produced — orthogonal
for PPO, preserving fan-in/fan-out. This is the `RF` (reset fan-in/out) component. It
is the standard hypernetwork-initialisation concern (Chang, Flokas & Lipson, ICLR
2020, cited as [8]): a generator's output distribution is *not* automatically the
distribution a well-initialised network wants, because the generator's own
initialisation composes with its architecture. Ablating it costs little on Dispersion
and a great deal on 17-agent Humanoid.

**Agent embeddings adapt (§6.2).** Learned embeddings are orthogonally initialised, so
mean pairwise cosine *distance* starts at exactly 1.0. After training on 4-agent
Navigation with identical dynamics and only the goal structure changed:
- *same goal for all agents* (homogeneity optimal): distance contracts to
  $0.882 \pm 0.042$, one-sample $t$-test against 1.0 giving $p = 0.0079$;
- *unique goal per agent* (specialisation optimal): $1.010 \pm 0.017$, i.e.
  indistinguishable from the orthogonal initialisation.

This is the paper's neatest secondary result: the *conditioner's own representation*
learns how much diversity the task wants, rather than the diversity level being a
hyperparameter (as it is for DiCo, whose `SND_des` had to be swept — and, per Table 15,
swept unsuccessfully for $n > 2$, where the best value found was the "disabled"
setting $-1$ in five of six configurations).

**Diversity metric.** System Neural Diversity, over the observation space:

$$\mathrm{SND}\big(\{\pi^i\}_{i\in I}\big) = \frac{2}{n(n-1)|O|}\sum_{i=1}^{n}\sum_{j=i+1}^{n}\sum_{o\in O} D\big(\pi^i(o), \pi^j(o)\big),$$

with $D$ the Jensen–Shannon distance, range 0 (identical) to 1 (maximally diverse).
Estimated from 1 M observations subsampled from a 16 M-observation pool generated by
rolling out IPPO-NoPS and IPPO-FuPS checkpoints for 10,000 episodes. Fig. 4d: both
hypernetwork variants reach NoPS-level SND while FuPS variants sit visibly lower.
Note the estimator quirk — the observation distribution used to score *all* methods is
drawn from **two of them**, so SND is measured on a state distribution that HyperMARL
did not generate.

**Cost.** App. F.4, JAX on one T4, GRU policy, 64-d embeddings and hidden layers, batch
128, 64 parallel envs, 100 forward passes × 10 trials: HyperMARL's forward-pass time
and GPU memory sit between NoPS and FuPS across 4 → 512 agents. The authors note NoPS's
measured advantage understates its true cost, since data-transfer and synchronisation
overheads for per-agent networks are excluded from the benchmark.

### 1.7 What changes in the project's existing record

Five statements in the master review's §17 entry should be revised when this is merged.

1. **"Retained in §17 — its gradient-interference result is the principal
   counter-evidence on self-conditioning"** — still true, but **incomplete**. The
   principal counter-evidence is `FuPS+ID (No State)` (§3.2), which is earlier, cleaner,
   larger in effect (3.5× at $n=16$), *and* carries a gradient-conflict measurement.
   `w/o GD` is the corroborating second ablation, at the generator level. Cite both.
2. **"assumption A3, which fails the moment the observation enters the generator"** —
   **mis-located**. A3 is "$\psi, \theta, e_i$ are fixed during the backward pass" and
   continues to hold under `w/o GD`. What fails is the §4.3 premise that $J_i$ depends
   only on $(\psi, e_i)$, which is what licenses the "pull deterministic matrices out
   of $\operatorname{Cov}$" step in Eq. (11).
3. **"Variance claim is directional only — no numerical value appears in the text"** —
   **correct as to the text**, but the plotted values are recoverable and amount to a
   ~29× (IPPO) / ~22× (MAPPO) reduction with FuPS+ID's interval clear of both
   hypernetwork means. The more useful caveat is a different one: the `w/o GD`
   condition is never scored on the variance metric, so the ablation and the mechanism
   are never joined up.
4. **"regenerates an entire weight tensor per timestep"** — **wrong for baseline
   HyperMARL**, which regenerates once per training iteration (Alg. 1, lines 7–11).
   Per-timestep regeneration is a property of the `w/o GD` ablation, and is therefore
   an *unacknowledged second manipulation* inside that ablation.
5. **"out of scope as a mechanism"** — no longer true under the widened scope. The
   paper is now in scope as the corpus's canonical **full-weight-generation** entry,
   with a documented conditioner dimensionality of 4–8 and a documented failure when
   the conditioner is widened to include the observation.

Two additions with no prior record: the **embedding-dimension sensitivity** (0.4455 →
0.1155 IQM win rate on 20-agent SMAX from changing embedding dim 4 → 64) is a concrete
warning that conditioner *capacity* is a tuned quantity, not a free choice; and the
**seed-count contradiction** on Dispersion (App. G.2.1 says 10, Table 10 lists 5)
should be recorded when the headline Dispersion result is cited.

### Appendix: Section-by-Section Backbone

Preserving the paper's own order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Adaptive cooperation needs homogeneous / specialised / mixed behaviour. Parameter sharing suppresses diversity via cross-agent gradient interference, "surprisingly exacerbated by the common practice of coupling agent IDs with observations". Proposes an agent-conditioned hypernetwork that decouples the two gradient sources. 22 scenarios, up to 30 agents, six baselines, NoPS-level diversity, "empirically reduces policy gradient variance". Code public. |
| 1 | **Introduction** | NoPS specialises but is sample-inefficient; FuPS is efficient but struggles with diversity. Prior remedies (intrinsic rewards, roles, pruning, sequential updates, clustering) all add machinery — altered objectives, preset diversity levels, agent-specific parameters. Poses the central question and lists three contributions. Page-1 footer: **NeurIPS 2025**. |
| 2 | **Background** | Dec-POMDP tuple; per-agent partial observation and action-observation history; joint objective. Defines "specialised environment" informally, deferring Def. 1 to App. C. |
| 3 | **Are Independent or Fully Shared Policies Enough?** | Introduces the Specialisation Game (reward for distinct actions) and Synchronisation Game (reward for identical actions), in temporal $n$-player form. |
| 3.1 | Limitations of shared and independent policies | Table 1, REINFORCE, 10 seeds, $n \in \{2,4,8,16\}$: NoPS wins Specialisation (0.88 → 0.64 as $n$ grows), FuPS wins Synchronisation (1.00 at all $n$); neither wins both, and the gaps widen with team size. Points to the impossibility proof in App. E.3. |
| 3.2 | **Why FuPS+ID fails to specialise** | The entanglement diagnosis. FuPS+ID is a universal approximator, so the failure is optimisational. Introduces `FuPS+ID (No State)` — shared policy conditioned on the ID *only*. It outperforms full FuPS+ID at every $n$ (Fig. 3a), including small $n$ where observation spaces are small, "suggesting the issue is not merely observation size". Fig. 3b: `No State` shows near-zero inter-agent gradient cosine similarity; FuPS+ID shows negative. Concedes discarding observations is not a general solution. |
| 4 | **HyperMARL** | The method: shared paradigm, gradient decoupling, no objective change, no preset diversity. |
| 4.1 | Hypernetworks for MARL | $\theta_i = h^\pi_\psi(e_i)$, $\phi_i = h^V_\varphi(e_i)$ for policy and critic. Linear variant $\theta_i = \mathbf{1}_i W + b$ (row selection + shared bias; $b=0$ ⇒ NoPS). MLP variant $\theta_i = f^\pi_{\psi_1}(g^\pi_{\psi_2}(e_i))$, more expressive, no guarantee of distinct weights, more parameters. |
| 4.2 | Agent embeddings and initialisation | One-hot for linear; learned orthogonally-initialised embedding for MLP, trained end-to-end. Generator initialised so generated parameters match standard direct-initialisation distributions (orthogonal, fan-in/out preserving). |
| 4.3 | **Gradient decoupling** | Eq. (4): $\nabla_\psi J = \sum_i J_i Z_i$ with $J_i = \nabla_\psi h^\pi_\psi(e_i)$ agent-conditioned and $Z_i$ observation-conditioned. Key bullet: $J_i$ "depends only on the fixed embedding $e_i$ and the hypernetwork weights $\psi$, therefore it is deterministic with respect to mini-batch samples". Noise is averaged per agent *before* identity is applied. Named as the MARL analogue of the task/state decomposition in meta-RL. |
| 5 | **Experiments** | Two questions — Q1 can it specialise, Q2 does it hurt when homogeneity is optimal. 22 scenarios, ≥ 5 seeds. |
| 5.1 | Setup | Table 2 environment summary. Baselines: FuPS+ID, NoPS, DiCo, HAPPO, Kaleidoscope, SePS. IPPO/MAPPO backbone except Kaleidoscope (MATD3) and SePS (A2C). Original codebases and hyperparameters; HyperMARL generates capacity-matched architectures on identical observations. SND with Jensen–Shannon distance for diversity. |
| 5.2 | **Q1: specialised policy learning** | *Dispersion*: FuPS variants fail, NoPS and both hypernetwork variants reach optimum (Figs. 4a–b); FuPS still fails at 40 M steps (Fig. 19) and at matched parameter count (Fig. 15). *Gradient variance*: Fig. 4c, hypernetworks below FuPS+ID for both IPPO and MAPPO, no numbers printed. *Diversity*: Fig. 4d, hypernetworks at NoPS-level SND. *MAMuJoCo*: Table 3, top IQM in 3/4, Humanoid 6544 vs FuPS+ID's 566. *Navigation*: Fig. 6, robust across shared / unique / mixed goals, strongest at $n=8$; FuPS stays competitive at $n \in \{2,4\}$, attributed to dense rewards; DiCo's diversity level could not be tuned for $n>2$. |
| 5.3 | **Q2: homogeneous tasks** | SMAX, four maps, recurrent IPPO and MAPPO with a GRU backbone. Comparable final performance everywhere; FuPS sometimes converges marginally faster early on simple maps. Establishes (i) compatibility with recurrence and (ii) no intrinsic bias toward specialisation. |
| 6 | **Ablations and embedding analysis** | |
| 6.1 | Ablations | `w/o GD` conditions the generator on $[o_t, e_i]$ — degrades on **both** Humanoid-v2 (17 agents) and Dispersion; "gradient decoupling is consistently critical across both environments". `w/o RF` removes fan-in/out rescaling — critical on Humanoid, minor on Dispersion, so principled initialisation matters more as complexity grows. Figures only, no numbers. |
| 6.2 | Learned embedding analysis | Orthogonal init ⇒ pairwise cosine distance 1.0 at step 0. After training on 4-agent Navigation: same goal ⇒ $0.882 \pm 0.042$ ($p=0.0079$); different goals ⇒ $1.010 \pm 0.017$. Embeddings contract for homogeneity and stay separated for specialisation. |
| 7 | **Related work** | QMIX used a *state*-conditioned hypernetwork to mix Q-values, leaving per-agent GRUs untouched. CASH conditions on local observations plus capability descriptors for zero-shot generalisation across heterogeneous action spaces — "a mechanism absent in CASH" is the explicit contrast on gradient decoupling. Parameter-sharing variants (SePS, SNP-PS, Kaleidoscope, AdaPS, GradPS) all need clustering, pruning hyperparameters, auxiliary losses or conflict thresholds. Diversity methods (mutual-information objectives, roles, HAPPO) alter the objective or the update order. |
| 8 | **Conclusion** | Interference is exacerbated by ID–observation coupling; decoupling enables adaptivity to 30 agents and is linked to reduced gradient variance. Names parameter count as the chief limitation, remediable by chunked hypernetworks. |
| A | Limitations | High-dimensional generator outputs; more parameters than NoPS/FuPS at low agent counts but near-constant scaling in agent count; chunking or low-rank approximation proposed. |
| C | Specialised policies | Def. 1: distinct agent policies **and** non-interchangeability under permutation. |
| D | Measuring diversity | SND definition and choice of Jensen–Shannon distance. |
| E | Games | E.1 descriptions, E.2 general-$n$ payoffs, **E.3 the $\le 0.75 < 1$ impossibility proof**, **E.4 the gradient-conflict metric** (inter-agent gradient cosine similarity), E.5 normal-form results — where, unlike the temporal case, FuPS+ID retains near-optimal Specialisation performance and NoPS degrades with scale. |
| F | Method details | F.1 pseudocode — **weights are generated once per training iteration, before rollout collection**. F.2 the variance decomposition, Eqs. (11)–(12), assumptions A1–A3. F.3 parameter scaling, Fig. 14, and the matched-parameter control Fig. 15. F.4 speed/memory on a T4. **F.5 sensitivity: learning rate matters as usual; embedding size is important and smaller won here (0.4455 at dim 4 vs 0.1155 at dim 64, LR 5e-4); width has limited effect beyond a modest size.** |
| G | Experiment details | G.1 the five environments. **G.2 which networks the hypernetwork generates in each experiment** (actor+critic on VMAS; actor only for MAPPO MAMuJoCo; feedforward-only, not GRU, on SMAX). Table 6 baseline selection with reasons for the four exclusions. G.2.1 seeds, budgets, evaluation cadence. G.2.2 SND estimation protocol. |
| H | Detailed results | H.1 MATD3 vs Kaleidoscope (Table 7). H.2 A2C vs SePS on BPS (Table 8). H.3 Dispersion interval estimates and the 40 M-step control. H.4–H.6 MAMuJoCo / Navigation / SMAX plots. H.7 Fig. 23, all Dispersion ablations together — `HyperMARL-S`, `w/ One-Hot`, `w/o RF`, `w/o GD` — **`HyperMARL-S` is never defined anywhere in the text**. |
| I | Hyperparameters | Tables 9–20: toy-game settings and parameter counts; Dispersion IPPO/MAPPO config (LR 5e-4, 20 M steps, `[64,64]` actor/critic, 5 listed seeds); hypernetwork embedding dims 4/8 with hidden dim 64; Navigation config; DiCo `SND_des` sweeps; per-environment sweeps. |
| J | Computational resources | Hardware, execution time and total GPU hours per experiment category. |
| — | NeurIPS Paper Checklist | Standard. |

---
