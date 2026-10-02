---
title: "HypeRL: Hypernetwork-Based Reinforcement Learning for Control of Parametrized Dynamical Systems"
slug: botteghi_2026_hyperl
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_apps.md
authors: ["Nicolo Botteghi", "Stefania Fresca", "Mengwu Guo", "Andrea Manzoni"]
attribution_note: "The batch review and the original local filename both said 'Cicci et al.'; no author named Cicci is on the paper. Corrected to Botteghi et al. from the PDF author list."
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 4. Botteghi et al. 2026 — HypeRL

> **Authorship note.** The local filename says "Botteghi et al. 2026", but **the author list printed in the
> PDF is Nicolò Botteghi, Stefania Fresca, Mengwu Guo, Andrea Manzoni.** No author named Botteghi appears on
> the paper. Cite as **Botteghi et al.**; the filename is wrong. (Ludovica Botteghi is a co-author on other
> Manzoni-group papers, which is the likely source of the mix-up.)

**Full title:** *HypeRL: Hypernetwork-Based Reinforcement Learning for Control of Parametrized Dynamical
Systems*
**Venue as printed in the PDF: none — the running header on every page reads "A PREPRINT — FEBRUARY 12,
2026".** Title page dates it February 12, 2026. Sidebar stamp: **arXiv:2501.04538v2 [cs.LG] 10 Feb 2026**.
**Mark as PREPRINT**; the PDF asserts no conference or journal.
**Affiliations:** MOX–Department of Mathematics, Politecnico di Milano (Botteghi, Manzoni); Department of
Mechanical Engineering, University of Washington (Fresca); Centre for Mathematical Sciences, Lund
University (Guo).
**PDF:** `docs/project/references/Hypernetwork/sources/Botteghi et al. 2026 - HypeRL - Hypernetwork-based reinforcement learning for control of parametrized dynamical systems.pdf`

### Plain-language entry point

**The question.** Engineers routinely need to control a physical system described by a partial
differential equation — damping out instabilities in a flame front, steering a particle through a
swirling flow. The equation has *parameters*: a coefficient in the PDE, the amplitude and frequency of the
flow, the target you are steering to. Classical optimal-control machinery has to re-solve the whole
problem from scratch for every new parameter value, which is prohibitive. Can a single reinforcement
learning agent learn a controller that works across the whole parameter range?

**What the paper does.** It takes TD3 — a standard continuous-control RL algorithm with one policy network
and two value networks — and replaces each of those three networks' *weights* with the output of a
hypernetwork. The hypernetwork reads the agent's state, which is the physical measurement **concatenated
with the known parameters**, and emits the weights, biases, and per-unit gains of a small two-layer
network. The contrast the paper draws is explicit: *"in contrast with the widely-used concatenation of
information in the agent's state"*, route the parameter information into the weights instead.

**Is this genuinely RL?** **Yes — and it is the most conventional RL setup in the batch.** Real TD3: two
critics, target networks, delayed policy updates, Polyak averaging, replay buffer, exploration noise, the
whole apparatus. The pseudocode (their Algorithm 2) is TD3 with the changed lines highlighted in blue.
The hypernetworks sit inside the RL training loop and their parameters are updated by the ordinary TD3
losses flowing back through the generated weights.

**What the baseline is.** Four TD3 variants, and the comparison is careful: plain TD3 (parameters
concatenated into the state — this is the conditioning baseline), TD3 with the Huber critic loss (to
control for HypeRL's loss change), TD3 with one hidden layer (to control for HypeRL's smaller main
network), and TD3 with no access to the parameters at all (to show the parameters matter). Across all four
test cases HypeRL wins on cumulative reward — e.g. on the parametric flow-navigation task, evaluation
reward **−110.06 ± 16.05** for HypeRL versus **−430.34 ± 153.73** for concatenation-TD3 and
**−152.05 ± 43.72** for the Huber-matched variant.

**The caveat that matters most.** The paper's headline claim is "generalization to unseen scenarios", but
**the parameters are drawn from the same uniform distribution during training and evaluation.** There is
no held-out parameter range. So what is demonstrated is generalization to *fresh draws from the training
distribution*, not out-of-distribution generalization in the sense HyPoGen (§1) and CASH (§3) demonstrate
with disjoint train/test parameter sets. This is a real weakness of the evidence, not a quibble about
wording, and it should be stated whenever this paper is cited for "generalization".

**The detail most relevant to the FiLM question.** HypeRL's generated main network *contains a FiLM-shaped
term*: each layer computes `ReLU((1 + g)⊙ z W + b)` where the per-unit gain vector `g`, the weight matrix
`W` and the bias `b` are **all** emitted by the hypernetwork. So this architecture is a strict superset of
FiLM at every layer — it generates FiLM's multiplicative gain *and* the weights FiLM would have left
fixed. Nobody ablates the gain, so we cannot tell from this paper how much of the benefit is the FiLM part.

### Phase 1 — Foundational overview

**Setting.** A parametric PDE-constrained optimal-control problem, discretized in space and time into an
RL environment with deterministic transition and reward:

$$y_{k+1}=T(y_k,u_k;\mu),\qquad r_{k+1}=R(y_k,u_k;\mu),$$

where $y_k$ is the (possibly high-dimensional) discretized state, $u_k$ the control input, and $\mu$ a
parameter vector that "might describe a physical parameter of the system, a reference value, or a
navigation target". The agent's state is the concatenation $z_k=[y_k,\mu]$, and **exact knowledge of $\mu$
is assumed** (defended by pointing at recent work on estimating physical parameters from data, and flagged
as future work to relax).

**What generates what.**
- **Three hypernetworks** $h_\pi$, $h_{Q_1}$, $h_{Q_2}$ (plus their target copies), each reading
  $z_k=[y_k,\mu]$ and emitting the complete parameter set of one small main network.
- **Three main networks**: the policy $\pi(z_k;\theta_\pi)$ and two critics
  $Q_i(z_k,u_k;\theta_{Q_i})$, each with **one hidden layer of 256 units**.
- **Emitted per main network:** $\theta=[g^{(1)},W^{(1)},b^{(1)},g^{(2)},W^{(2)},b^{(2)}]$ — weights,
  biases, *and* per-unit gain vectors, for both layers.
- **Regenerated at every timestep**, since $z_k$ changes every step.

**Key findings.**
1. **HypeRL-TD3 beats every TD3 variant on all four problems**, on both training and evaluation cumulative
   reward, over 5 seeds.
2. **The parameters must be known.** TD3 without $\mu$ is catastrophic: on the first KS task its evaluation
   reward is $-17473\pm31416$ against HypeRL's $-175\pm21$ — two orders of magnitude worse with enormous
   variance, i.e. it fails outright.
3. **Concatenation alone is not enough, but it is not the whole gap either.** The Huber-loss-matched TD3
   closes roughly half the gap on some tasks (KS-1: $-249.76$ vs plain TD3 $-304.27$ vs HypeRL $-175.33$),
   which the authors acknowledge — "while it was beneficial... it is still not enough".
4. **Shrinking the baseline to match HypeRL's main-network size makes it worse, not better.** TD3(2 layers)
   is the *worst* of the informed baselines everywhere. The authors read this as evidence that the
   hypernetwork's advantage is not a matter of main-network capacity.
5. **Qualitatively, HypeRL exploits the flow physics.** In the gyre-flow task the TD3 variants' trajectories
   are deflected by ridges in the finite-time Lyapunov exponent field and oscillate around the target;
   HypeRL "smoothly and efficiently reaches the target by exploiting the stable regions of the gyre flow
   field". This is the one place the paper offers a mechanistic rather than a scoreboard argument.
6. **The total parameter count goes *up*, and the authors say so.** "Although the total learnable
   parameters are higher due to the presence of hypernetworks, the optimization of these learnable
   parameters becomes simpler, requires less data, and allows the learning of better controllers." Directly
   opposite to CASH (§3), which is smaller than its baselines. The two claims are compatible — CASH shrinks
   the shared trunk to pay for the generator; HypeRL does not — but the difference should be noted whenever
   "hypernetworks are parameter-efficient" is asserted.

**Initial takeaway.** In a setting where the context variable is a genuine physical parameter that changes
the *dynamics*, feeding it to the weights rather than the input measurably improves both sample efficiency
and performance under a standard off-policy actor-critic algorithm — with the caveat that the
"generalization" shown is within-distribution.

### Phase 2 — Graduate-level deep dive

#### 2.1 Hypernetwork formalism as the paper states it

A hypernetwork $h:\mathcal{Z}\subset\mathbb{R}^{|z|}\to\mathbb{R}^{|\theta_f|}$ produces the parameters
of a main network $f:\mathcal{X}\to\mathcal{W}$:

$$\theta_f=h(z^{(i)};\theta_h),\qquad \hat w^{(i)}=f\!\left(x^{(i)};\theta_f\right),$$

trained jointly by minimizing a task loss (for regression,
$\mathcal{L}(\theta_f,\theta_h)=\sum_i\lVert w^{(i)}-\hat w^{(i)}\rVert_2^2$). The paper adopts Chauhan
et al.'s taxonomy of the context vector $z$ as **task-conditioned, data-conditioned, or noise-conditioned**.
**HypeRL's $z_k=[y_k,\mu]$ is both at once** — task-conditioned through $\mu$ and data-conditioned through
$y_k$. That is worth being precise about, because the paper's narrative is about $\mu$ while the
implementation also feeds the raw state.

#### 2.2 HypeRL-TD3

Hyper-policy and hyper-value functions:

$$\theta_\pi=h_\pi(z_k;\theta_{h\pi}),\qquad u_k=\pi(z_k;\theta_\pi),$$
$$\theta_{Q_i}=h_{Q_i}(z_k;\theta_{hQ_i}),\qquad q_{i,k}=Q_i(z_k,u_k;\theta_{Q_i}),\quad i=1,2 .$$

Note the main networks take $z_k$ as **input** as well — the conditioning is not removed from the input
path, it is *added* to the weight path. So HypeRL is strictly "concatenation **plus** weight generation",
not "weight generation **instead of** concatenation. There is no ablation removing $\mu$ from the main
network's input while keeping it in the hypernetwork's, which would have isolated the mechanism.

**Training objectives** are TD3's, with the hypernetwork parameters optimized jointly "by simply allowing
the gradient of the loss functions to flow through the hypernetworks":

$$\mathcal{L}(\theta_\pi,\theta_{h\pi})=\mathbb{E}_{z_k\sim\mathcal{M}}\!\left[-\nabla_{u_k} Q_1\!\left(z_k,\pi(z_k;\theta_\pi);\theta_{Q_1}\right)\right],$$

$$\mathcal{L}(\theta_{Q_i},\theta_{hQ_i})=\mathbb{E}_{(z_k,u_k,r_{k+1},z_{k+1})\sim\mathcal{M}}\!\left[\mathrm{Huber}\!\left(r_{k+1}+\gamma\min_{i=1,2}\bar Q_i(z_{k+1},u_{k+1};\theta_{\bar Q_i})-Q_i(z_k,u_k;\theta_{Q_i})\right)\right].$$

Two deviations from vanilla TD3, both flagged:
- **Huber loss replaces MSE for the critic**, "similarly to [62]" (Fujimoto et al. 2023, *For SALE*). They
  found this "beneficial to the agent's performance" — and, importantly, they **add TD3(Huber) as a
  baseline** so this change is controlled for.
- **Target networks are maintained at the hypernetwork level**: Polyak updates
  $\theta_{h\bar Q_i}=\rho\theta_{hQ_i}+(1-\rho)\theta_{h\bar Q_i}$ are applied to the *hypernetwork*
  parameters, and the target main-network weights are regenerated from the target hypernetwork. This is a
  non-obvious design choice with real consequences — the target network's weights are now a *function* of
  the target hypernetwork rather than an independently smoothed copy — and it is not ablated.

**The training loop (Algorithm 2)**, per step: set $z_k=[y_k,\mu]$ → sample policy weights
$\theta_\pi=h_\pi(z_k;\theta_{h\pi})$ → act with exploration noise → store the transition → on update,
sample target policy weights from $h_{\bar\pi}(z_{k+1})$, target critic weights from
$h_{\bar Q_i}(z_k)$, current critic weights from $h_{Q_i}(z_k)$, and take the TD3 steps. **Weight
generation happens four to six times per gradient step**, which is the computational price.

#### 2.3 The main-network architecture — and its FiLM content

Policy (their §3.2.1):

$$x_k=\mathrm{ReLU}\!\left(\big(1+g^{(1)}(z_k;\theta_{h\pi})\big)\odot z_k\,W^{(1)}(z_k;\theta_{h\pi})+b^{(1)}(z_k;\theta_{h\pi})\right),$$

$$u_k=\tanh\!\left(\big(1+g^{(2)}(z_k;\theta_{h\pi})\big)\odot x_k\,W^{(2)}(z_k;\theta_{h\pi})+b^{(2)}(z_k;\theta_{h\pi})\right),$$

and identically for the critics with $\upsilon_k=[z_k,u_k]$ as input and a linear output layer.

**Unpack the FiLM connection carefully, because this is the closest any paper in the batch comes to
running both mechanisms at once:**
- $g$ is an **elementwise multiplicative gain** — exactly FiLM's $\gamma$.
- It is written **$1+g$**, i.e. the residual parameterization: at $g=0$ the layer reduces to an ordinary
  linear layer. Same safety property as FiLM's $\gamma\to1$, and the same trick HyPoGen uses at the weight
  level ($\theta^0$ plus increments) and CASH uses at initialization (output scale 0.2 / 0).
- $b$ is a generated **additive shift** — FiLM's $\beta$, except generated per-instance rather than
  learned per-context-embedding.
- **On top of that, $W$ is also generated.** So per layer, the emitted object is
  $(\gamma\text{-like } g,\ \beta\text{-like } b,\ \text{full } W)$.

**Consequence for the standing question:** HypeRL is a *superset* of FiLM applied to the same layer, and
because $g$ is never ablated, the paper provides **no evidence about how much of the benefit comes from
the FiLM-shaped part versus the full-weight part**. If anyone wanted a clean FiLM-vs-hypernetwork
experiment, this architecture is one line away from it — drop $W^{(\ell)}$ and $b^{(\ell)}$ from the
hypernetwork output, keep $g^{(\ell)}$, and you have FiLM. That experiment does not exist in the
literature reviewed in this batch, and **this is the single most valuable gap identified across all four
papers.**

The architecture is credited to Littwin & Wolf, *Deep meta functionals for shape representation* (ICCV
2019) — i.e. it comes from implicit-shape-representation work, not from RL.

#### 2.4 Hypernetwork architecture and initialization

"The hypernetworks use the same architecture and weight initialization proposed in [39]" — Sarafian,
Keynan & Kraus, *Recomposing the Reinforcement Learning Building Blocks with Hypernetworks* (the first
work to put hypernetworks inside DRL value/policy networks, and the source of the known
initialization-sensitivity analysis for this setting). Structure:

- Each hypernetwork = **three blocks**, mapping $z_k$ to $g^{(1)},W^{(1)},b^{(1)}$ and
  $g^{(2)},W^{(2)},b^{(2)}$ respectively.
- Each block = **one linear layer followed by two residual blocks**.
- Each residual block = **two linear layers with ReLU and a skip connection**.

**This is the stability story of the paper, and it is inherited rather than investigated.** The mitigations
present are: (i) a residual hypernetwork body, (ii) a specific published initialization scheme adopted
wholesale, (iii) the $1+g$ residual gain parameterization in the main network, and (iv) the Huber critic
loss (which bounds the influence of large TD errors — relevant because a badly generated weight matrix can
produce a huge Q-error that would blow up an MSE gradient). **No LayerNorm is reported** — contrast CASH
(§3), which found LayerNorm essential and speculated that hypernetworks fed a strong pretrained encoder
can get away without it. HypeRL's hypernetwork is fed a **raw physical state vector plus parameters**, i.e.
exactly the "no preprocessing encoder" condition CASH identified as the hard case — yet HypeRL trains
without normalization. The two papers are in tension here; the difference may be the residual hypernetwork
body, the small $|z|$, or the smoother reward landscape. **Not resolved by either paper.**

#### 2.5 Experiments

**Protocol (all four cases).** 2000 training episodes; 100 warm-up episodes with actions drawn uniformly
from $\mathcal{U}(-u_{\min},u_{\max})$, excluded from the reported scores; evaluation every 200 episodes;
evaluation metric = mean cumulative reward over 10 evaluation episodes under the deterministic policy;
**5 random seeds**.

**Case A — Kuramoto–Sivashinsky stabilization.** The KS equation with an added parametric symmetry-breaking
cosine forcing:

$$\frac{\partial s}{\partial t}+s\frac{\partial s}{\partial x}+\frac{\partial^2 s}{\partial x^2}+\frac{\partial^4 s}{\partial x^4}+\nu\cos\!\left(\frac{4\pi x}{L}\right)=u(x,t),$$

with distributed control through $N_a=8$ equally spaced Gaussian actuators,
$u(x,t)=\sum_{i=1}^{N_a}a_i(t)\psi(x,m_i)$, $\psi(x,m_i)=\tfrac12\exp\!\big(-((x-m_i)/\sigma)^2\big)$,
$\sigma=0.8$, $a_i\in[-1,1]$. Domain $D=[0,22]$ with periodic BCs, $N_x=64$ grid points, $T=300$ s,
$dt=0.1$, control activated after 100 timesteps. Reward = negative discretized running cost:

$$R(y_k,u_k;\mu)=-\underbrace{\lVert y_k-y_{\text{ref}}\rVert_2^2}_{\text{state cost}}-\alpha\underbrace{\lVert u_k\rVert_2^2}_{\text{action cost}},\qquad \alpha=0.1 .$$

Two sub-cases: (A1) arbitrary reference $y_{\text{ref}}\sim\mathcal{U}(-3,3)$ with $\nu=0$; (A2) the same
plus $\nu\sim\mathcal{U}(-0.25,0.25)$. Here $\mu=[y_{\text{ref}},\nu]$ — i.e. **the "physical parameter"
vector mixes a task specification (the tracking reference) with a genuine PDE coefficient.** The paper
notes that small changes in $\nu$ produce vastly different uncontrolled solutions.

**Case B — particle navigation in a double-gyre flow.** Stream function
$\phi(x,y,t)=A\sin(\pi f(x,t))\sin(\pi y)$ with
$f(x,t)=[\epsilon\sin(\omega t)]x^2+[1-2\epsilon\sin(\omega t)]x$, giving

$$\dot x=-\pi A\sin(\pi f(x,t))\cos(\pi y)+u_x,\qquad \dot y=\pi A\cos(\pi f(x,t))\sin(\pi y)\frac{\partial f}{\partial x}+u_y .$$

Domain $[0,2]\times[0,1]$, $T=80$ s, $\Delta t=0.1$ s, controls clipped to $u_{x},u_y\in[-0.2,0.2]$ —
**deliberately weaker than the flow's own velocity ($\approx A\pi$), forcing the controller to exploit the
flow rather than fight it.** Reward $=-\lVert p_k-p_{\text{target}}\rVert^2-\alpha\lVert u_k\rVert_2^2$,
$\alpha=0.1$. State $z_k=[x_k,y_k,k,\mu]$ with $\mu=[x_{\text{target}},y_{\text{target}},A,\omega]$.
Sub-cases: (B1) fixed flow $A=0.1$, $\omega=2\pi/10$, $\epsilon=0.25$, random start and target;
(B2) additionally $A\sim\mathcal{U}(0.1,0.4)$, $\omega\sim\mathcal{U}(2\pi/10,2\pi/2)$.

The **finite-time Lyapunov exponent (FTLE)** field is computed (Appendix A) as an analysis tool, not part
of training: high-FTLE regions require more control effort, and small parameter changes produce large FTLE
changes — this is how the paper argues the parametric task is genuinely hard.

#### 2.6 Head-to-head numbers

**The baselines**, and note how carefully they are chosen:

| Baseline | What it controls for |
|---|---|
| **TD3** | the conditioning mechanism — same input $z_k=[y_k,\mu]$, concatenated into the state, standard architecture (2 hidden layers × 256) |
| **TD3 (Huber)** | HypeRL's critic-loss change |
| **TD3 (2 layers)** | HypeRL's smaller *main* network (1 hidden layer) |
| **TD3 (no $\mu$)** | whether the parameter information is needed at all |

**All four tables: mean ± std cumulative reward over 5 seeds. Less negative is better.**

*(A1) KS, arbitrary reference, $\nu=0$ (Table 1)*

| Method | Training | Evaluation |
|---|---|---|
| **HypeRL-TD3** | **−180.41 ± 62.97** | **−175.33 ± 20.85** |
| TD3 (concat) | −313.17 ± 116.74 | −304.27 ± 63.11 |
| TD3 (Huber) | −263.78 ± 93.49 | −249.76 ± 37.31 |
| TD3 (2 layers) | −344.13 ± 119.91 | −344.52 ± 68.47 |
| TD3 (no µ) | −12522.60 ± 25874.76 | −17473.19 ± 31416.09 |

*(A2) Parametric KS, arbitrary reference, $\nu\sim\mathcal{U}(-0.25,0.25)$ (Table 2)*

| Method | Training | Evaluation |
|---|---|---|
| **HypeRL-TD3** | **−223.70 ± 74.20** | **−210.50 ± 18.04** |
| TD3 (concat) | −396.56 ± 133.33 | −395.40 ± 92.77 |
| TD3 (Huber) | −329.48 ± 94.98 | −326.36 ± 30.47 |
| TD3 (2 layers) | −450.86 ± 188.58 | −446.20 ± 138.94 |
| TD3 (no µ) | −4598.64 ± 2294.87 | −4222.67 ± 485.95 |

*(B1) Gyre-flow navigation, fixed flow (Table 3)*

| Method | Training | Evaluation |
|---|---|---|
| **HypeRL-TD3** | **−40.08 ± 18.45** | **−39.16 ± 6.00** |
| TD3 (concat) | −102.50 ± 60.46 | −114.04 ± 41.10 |
| TD3 (Huber) | −57.77 ± 26.71 | −57.55 ± 10.82 |
| TD3 (2 layers) | −131.81 ± 71.74 | −131.48 ± 25.24 |
| TD3 (no µ) | −344.34 ± 131.50 | −346.58 ± 25.93 |

*(B2) Parametric gyre flow (Table 4)*

| Method | Training | Evaluation |
|---|---|---|
| **HypeRL-TD3** | **−112.38 ± 70.55** | **−110.06 ± 16.05** |
| TD3 (concat) | −398.12 ± 332.63 | −430.34 ± 153.73 |
| TD3 (Huber) | −147.08 ± 109.23 | −152.05 ± 43.72 |
| TD3 (2 layers) | −801.62 ± 576.11 | −942.89 ± 245.60 |
| TD3 (no µ) | −457.47 ± 266.10 | −441.75 ± 84.12 |

**Reading these honestly.**
- **HypeRL wins all 8 cells.** The margin over plain concatenation-TD3 is large: 1.7× to 3.9× better mean
  evaluation reward.
- **The right comparison is against TD3(Huber), not plain TD3**, because that is the variant matched on
  loss function. That gap is smaller but consistent: 1.42× (A1), 1.55× (A2), 1.47× (B1), 1.38× (B2).
  Roughly a **40–55 % improvement in mean cost** attributable to the conditioning mechanism once the loss
  change is controlled for. That is the number to quote.
- **HypeRL's seed-variance is dramatically lower at evaluation** — e.g. B2: ±16.05 vs ±153.73 (concat) and
  ±43.72 (Huber). Across all four cases HypeRL has the smallest evaluation standard deviation. This
  reliability-across-seeds result is arguably more convincing than the mean improvement, and the paper
  underplays it.
- **The `no µ` rows are not informative about the mechanism.** They show the task is parameter-dependent
  (which we knew from the construction) and produce absurd numbers with std larger than the mean
  ($-12522\pm25875$), indicating some seeds diverge entirely. Do not cite these as a mechanism comparison.
- **5 seeds, one architecture size, no hyperparameter sweep reported.** No learning rates, batch sizes,
  buffer sizes, $\gamma$, $\rho$, or exploration schedules appear anywhere in the paper or appendices —
  only the network shapes and the episode budget. **The paper is not reproducible from its text.** No code
  link is given either.
- **No parameter counts are reported**, despite the discussion's claim that "the total learnable parameters
  are higher".

#### 2.7 What "generalization" means here — and does not

The abstract and conclusion both claim generalization "to unseen scenarios". Precisely what is
demonstrated:

- Both training and evaluation episodes sample $y_{\text{ref}}\sim\mathcal{U}(-3,3)$,
  $\nu\sim\mathcal{U}(-0.25,0.25)$, targets from $\mathcal{U}(0.1,1.9)\times\mathcal{U}(0.1,0.9)$, and
  $A,\omega$ from their training ranges. **The distributions are identical.**
- So the agent is evaluated on *parameter values it never saw exactly* (measure-zero repeats), but from
  the *same distribution* it trained on. This is generalization across a continuum in the
  interpolation sense — real and non-trivial for a continuous parameter, but categorically weaker than
  HyPoGen's disjoint specification split (§1: 20 % train / 80 % test with no overlap) or CASH's
  out-of-distribution teams (§3: capabilities sampled from ranges *outside* the training ranges).
- **There is no extrapolation test anywhere in the paper.**

Given that all three other papers in this batch found the mechanism's advantage to be concentrated
*out-of-distribution* and to shrink or vanish in-distribution, HypeRL's in-distribution-only win is
noteworthy in the other direction: it suggests the weight-generation advantage here is about
**optimization** (their words: "the optimization of these learnable parameters becomes simpler, requires
less data") rather than about generalization.

#### 2.8 Notes for this project

- **The most citable thing in this paper is the baseline design, not the result.** Four ablated TD3
  variants — matched loss, matched main-network depth, and no-context — is a template worth copying for
  any conditioning-mechanism comparison we run. In particular, matching the *loss function change* is the
  kind of control that is easy to forget.
- **The `1+g` residual gain is a FiLM inside a hypernetwork**, and its non-ablation is the clearest open
  experiment across this whole batch. If we want to answer "FiLM or hypernetwork?" empirically, the
  cheapest decisive experiment is this architecture with the $W$ generation switched off.
- **Reward is the objective here, so cumulative reward is a legitimate metric** — the reward *is* the
  quadratic tracking cost being minimized. That is not the case in our own environment, where the project
  rule is to measure survival steps; do not import the metric along with the method.
- **Reproducibility is poor** (no hyperparameters, no code, preprint status). Treat conclusions as
  suggestive. If a plan cites HypeRL as evidence for a design decision, that plan should not lean on the
  exact numbers.
- **Contrast with CASH on parameter cost:** HypeRL's total parameter count goes up, CASH's goes down 60–80 %.
  The difference is architectural (CASH narrows its shared trunk to pay for the generator; HypeRL adds
  generators to a full-size stack). "Hypernetworks are parameter-efficient" is therefore an architecture
  choice, not a property of hypernetworks.

### Appendix: Section-by-Section Backbone

- **Abstract.** A general-purpose RL strategy for optimal control of parametric dynamical systems.
  Traditional methods (adjoint-based iterative minimization; dynamic programming via HJB) must re-solve
  the OC problem for each parameter instance and become infeasible in high dimensions. HypeRL approximates
  the optimal control policy directly, bypassing HJB and adjoint solves; uses an actor-critic DRL approach
  to learn a feedback control law generalizing across the parameter range; **two additional NNs
  ("hypernetworks") learn the weights and biases of the value function and policy networks**. Validated on
  (i) a 1D parametric Kuramoto–Sivashinsky equation with in-domain control and (ii) navigation of particle
  dynamics in a parametric 2D gyre flow.
- **§1 Introduction.** PDE-constrained optimal control; why HJB is intractable at high dimension and long
  horizon; why the Pontryagin Maximum Principle requires repeated forward/backward solves of state and
  adjoint equations; RL as an alternative that avoids both. DRL's two named drawbacks — **sample
  inefficiency** and **limited generalization** — and why they bite hardest for parametric PDEs where each
  state measurement costs a forward solve. Survey of remedies (imitation learning, transfer learning,
  unsupervised representation learning, meta-learning) and the claim that none has been developed for
  parametric PDE control. Hypernetworks introduced with a citation to Ha et al. and to Chauhan et al.'s
  review; prior hypernetwork+DRL work named as Sarafian et al. (first use), plus meta-RL / zero-shot RL /
  continual RL (Beck et al.; Rezaei-Shoshtari et al.; Huang et al.); the claim that **no one has tackled
  control of parametric dynamical systems with hypernetworks and DRL**. Statement of the discretized
  environment, the agent state $z_k=[y_k,\mu]$, and the hyper-policy / hyper-value formulation.
- **§2 Preliminaries.** §2.1 optimal-control problems (state equation, running cost, terminal cost).
  §2.2 from dynamic programming to RL. §2.2.1 Twin-Delayed DDPG (TD3). §2.3 hypernetworks — formal
  definition, the context vector taxonomy (task- / data- / noise-conditioned), joint optimization, MSE loss
  for the regression case.
- **§3 Methodology for HypeRL.**
  - *§3.1 Problem settings.* Deterministic parameter-dependent transition and reward; $\mu$ as physical
    parameter, reference value, or navigation target; explicit Runge–Kutta discretization
    $y_{k+1}=y_k+\Delta t\,\Phi(t_k,y_k,u_k;\Delta t,F,\mu)$; the assumption of accurate knowledge of $\mu$
    with a defence pointing to ML-based parameter estimation; the two-loop episodic interaction scheme
    (Algorithm 1); **the explicit contrast with "the widely-used concatenation of information in the
    agent's state"**.
  - *§3.2 HypeRL-TD3.* Three hypernetworks for the two critics and the policy; joint optimization by
    letting gradients flow through; TD3 objectives with the **Huber loss replacing MSE** for the critics
    (following Fujimoto et al. 2023); note that the method "can be easily and directly applied to other RL
    algorithms, such as PPO and SAC" (asserted, not demonstrated). Algorithm 2 = TD3 with the changes
    highlighted in blue, including **Polyak updates applied at the hypernetwork level**.
  - *§3.2.1 Neural network architectures.* Main policy: input $z_k\in\mathbb{R}^{|y|+|\mu|}$, one hidden
    layer of 256 units, $\tanh$ output; both layers computed as
    $\mathrm{ReLU}\big((1+g)\odot z W+b\big)$ with $g,W,b$ all hypernetwork outputs; architecture credited
    to Littwin & Wolf 2019. Critics identical with input $[z_k,u_k]$ and scalar linear output. Hypernetwork
    architecture and weight initialization taken from Sarafian et al.: three blocks
    ($z_k\mapsto g^{(1)},W^{(1)},b^{(1)}$ and $g^{(2)},W^{(2)},b^{(2)}$), each block = a linear layer plus
    two residual blocks, each residual block = two linear layers with ReLU and a skip connection.
- **§4 Numerical experiments.** The four baselines (TD3, TD3-Huber, TD3-2layers, TD3-no-$\mu$); protocol
  (2000 episodes, 100 warm-up episodes with uniform random actions, evaluation every 200 episodes over 10
  deterministic episodes, 5 seeds).
  - *§4.1 KS equation.* PDE with the parametric $\nu\cos(4\pi x/L)$ term; 8 Gaussian actuators; $N_x=64$;
    $T=300$ s, $dt=0.1$; control activated after 100 steps; quadratic tracking reward with $\alpha=0.1$;
    two sub-problems (arbitrary reference at $\nu=0$; arbitrary reference with random $\nu$).
    §4.1.1 results (Table 1, Figs. 4–5); §4.1.2 parametric results (Table 2, Figs. 6–7).
  - *§4.2 Gyre flow.* Double-gyre stream function and the resulting ODE system; control clipped below the
    flow speed to force flow exploitation; **finite-time Lyapunov exponents** introduced as a diagnostic
    for where control is expensive, with the observation that small parameter changes produce large FTLE
    changes. §4.2.1 fixed-flow results (Table 3, Figs. 10–12); §4.2.2 parametric-flow results (Table 4,
    Figs. 13–15). Qualitative claim in both: TD3 variants are deflected by FTLE ridges and oscillate around
    the target, HypeRL exploits stable regions.
- **§5 Discussion and conclusion.** Summary; the assumption of perfect parameter knowledge and the plan to
  add a parameter-estimation stage; the architecture-ablation narrative (removing a layer from TD3 hurts;
  Huber helps but is not enough); and the admission that **total learnable parameters are higher** but
  optimization is easier and needs less data.
- **Appendix A.** Numerical computation of the finite-time Lyapunov exponent
  ($T=10$ s, $dt=0.1$ s, $N_x=300$, $N_y=150$).
- **Appendix B.** Additional KS results — state and action costs separately over training and evaluation
  (Figs. 16, 19) and further controlled-solution examples (Figs. 17, 18, 20, 21), including the
  TD3-without-$\mu$ curves.
- **Appendix C.** Additional gyre-flow results — state and action costs (Figs. 22, 27) and controlled
  trajectories overlaid with the flow field and with the FTLE (Figs. 23–26, 28–31).

---

## Cross-paper note (applications half)

Four observations that only appear when the four are read together. These are stated here rather than in
the per-paper sections because they are comparative, and they are the honest summary of what this batch
does and does not settle for the standing question.

1. **Not one of the four papers contains a FiLM baseline.** The nearest rung consistently evaluated is
   *concatenation* — HyPoGen's "Cond Policy", Hyper-GoalNet's GCBC/C-BeT, CASH's RNN-EXP, HypeRL's plain
   TD3. Any claim of the form "hypernetworks beat FiLM" cannot be sourced to this batch. What the batch
   supports is "**weight generation beats input concatenation**", which is a different and weaker claim
   about a different rung of the ladder.
2. **The advantage is concentrated out-of-distribution, and CASH shows this most cleanly.** CASH ties
   concatenation in 4 of 6 in-distribution cells and wins 6 of 6 out-of-distribution. HyPoGen's baselines
   fit their training tasks fine (HyperZero 78 % train vs 26 % test) and fail on transfer. HypeRL is the
   exception, but only because it never tests out-of-distribution at all — its win is in-distribution and
   the authors attribute it to easier optimization rather than to generalization.
3. **Every paper reports a stability intervention at the point where generated weights meet the target
   network, and they are all the same idea in different clothes.** CASH: LayerNorm before every ReLU, plus
   output-scale 0.2 / 0 at initialization. Hyper-GoalNet: the residual iterative form removes the need for
   the Scalar-Init / Bias-Init schemes its HyperZero baseline required. HyPoGen: learnable $\theta^0$ plus
   bounded increments. HypeRL: the $1+g$ residual gain plus Sarafian et al.'s initialization plus a Huber
   critic loss. **The common principle: make the generated network start at, and stay near, a sane default,
   and normalize what flows into the generator.** That is the engineering lesson to carry forward.
4. **The decisive experiment is missing and is cheap.** HypeRL's main network already generates a FiLM-shaped
   gain $g$ alongside $W$ and $b$. Ablating $W$ and $b$ from the hypernetwork's output while keeping $g$
   yields exactly FiLM, in an otherwise identical RL pipeline with identical conditioning. Nobody has run
   it. If this project wants a defensible answer to "FiLM or hypernetwork?", that is the experiment — and
   the design of it belongs to `senior-developer` / `experiment-designer`, not to this review.
