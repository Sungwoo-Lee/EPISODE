---
title: "Multi-Task Reinforcement Learning with Soft Modularization"
slug: yang_2020_soft_modularization
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_classics.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 1. Yang et al. 2020 — *Multi-Task Reinforcement Learning with Soft Modularization*

**PDF:** `docs/project/references/modulation_in_rl/sources/Yang et al. 2020 - Multi-task reinforcement learning with soft modularization.pdf`
**Venue as printed (PDF p. 1 footer):** *"34th Conference on Neural Information Processing Systems (NeurIPS 2020), Vancouver, Canada."* arXiv stamp: `arXiv:2003.13661v2 [cs.LG] 7 Dec 2020`.
**Authors:** Ruihan Yang (UC San Diego), Huazhe Xu (UC Berkeley), Yi Wu (IIIS, Tsinghua), Xiaolong Wang (UC San Diego). Project page + code: `rchalyang.github.io/SoftModule/`.

### 1.1 Plain-English entry point

A robot arm is asked to learn 50 different manipulation jobs — open a drawer, press a
button, pick and place — with **one** network. Training them all together should help,
because opening and closing a drawer share most of their motor skill. In practice it
hurts: the gradient signals from different jobs pull the shared weights in
incompatible directions, and the paper's own benchmark (Meta-World) had already shown
that joint training can be *worse* than training each job separately.

This paper's fix is to stop asking the tasks to share *one* set of weights and instead
give them a **shared pool of small sub-networks ("modules") that each task wires up
differently**. A second, small network — the **routing network** — reads the task's
identity label together with the robot's current sensor readings, and outputs a set
of connection strengths saying how strongly each module on one layer should feed each
module on the next. Because those strengths are probabilities rather than hard
on/off choices ("soft" modularization), the whole thing is differentiable and trains
end to end with ordinary backpropagation.

**Headline result.** On the 50-task Meta-World benchmark the method reaches about
**60 % average success rate** against about **35 %** for the previous best baseline
(a shared trunk with one output head per task) — a gain of roughly 24 percentage
points — while using **fewer parameters**. On the easier 10-task benchmark the gain is
small (87.0 % vs 85.0 %); the advantage grows with the number of tasks.

**Why the project cares.** This is the canonical *discrete-composition* alternative to
FiLM inside RL: same conditioning signal (a task label), same goal (make one network
behave like many), completely different operator (choose a wiring, rather than rescale
activations). It is also the paper that establishes, with numbers, that the naive
*hard* version — an actual discrete choice, learned by RL — is not merely worse but
catastrophically unstable.

### 1.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | NeurIPS 2020 (34th Conference on Neural Information Processing Systems), Vancouver — printed in the p. 1 footer. |
| **RL algorithm** | **Soft Actor-Critic (SAC)**, off-policy, continuous control. Both actor and critic are rebuilt with the modular architecture. |
| **Conditioning signal** | **Two signals, combined multiplicatively before use**: (i) a **one-hot task ID** `z_T` (stated explicitly: *"We use an one-hot vector for `z_T` representing each task"*), passed through one fully-connected layer to give `h(z_T) ∈ ℝ^D`; and (ii) the **current observation** `s_t`, passed through a 2-layer MLP to give `f(s_t) ∈ ℝ^D`. **The routing is therefore state-dependent, not merely per-task** — the wiring can change within an episode. This is unusual and the paper ablates it (§1.6). |
| **What is modulated** | The **base policy network** (the actor) — its inter-layer connectivity. **And, separately, the critic**: *"we adopt similar architectures with soft modularization for Q-function as well. The weights for both the base policy network and the routing network are not shared or reused in the Q-function."* So actor and critic each get their **own** base network **and their own routing network**, trained independently. |
| **The operator** | **Soft routing (a per-layer, per-target-module convex combination over source modules)** — *not* affine modulation. There is **no additive offset** and **no per-unit gain**; a single scalar weight multiplies a whole module's output vector. Formally `g^{l+1}_i = Σ_j p̂^l_{i,j} · ReLU(W^l_j g^l_j)` with `Σ_j p̂^l_{i,j} = 1`. |
| **Granularity** | **Per-module (per-connection), not per-unit and not per-channel.** For `L` module layers of `n` modules each, layer `l` carries an `n × n` matrix of routing weights — `n²` scalars per layer, `(L−1)n²` in total (48 for the Deep variant). Every unit inside a module is scaled by the same scalar. |
| **Placement** | **Between every pair of consecutive module layers**, i.e. `L−1` injection sites. Deep variant: `L = 4`, `n = 4`, module width `d = 128`. Shallow variant: `L = 2`, `n = 2`, `d = 256`. Parameter count held equal between the two. The **final** layer is an unweighted sum: `µ, σ = Σ_j W^L_j g^L_j`. |
| **Ablated against concatenation?** | **Yes, and it is the primary baseline.** "Multi-task SAC (MT-SAC)" is defined as *"Using a one-hot task ID with the state as inputs"* — i.e. plain concatenation. Also ablated against a **multi-head** variant (MT-MH-SAC), a **mixture-of-experts** gating baseline, and a **hard-routing** baseline (Rosenbaum et al. style). Numbers in §1.5. |
| **Reported instability** | **Yes — attributed to the *hard* routing alternative, not to the proposed method.** *"joint training a multitask control policy and a routing policy suffers from exponentially higher variance in policy gradient due to the temporal nature in RL and leads to severe training instability."* The hard-routing baseline is the **worst** method in the paper (20.8 % on MT10-Fixed, below even plain concatenation at 44.0 %). The authors claim the soft version *"doesn't introduce additional variance, significantly stabilizes RL training"*. **No instability is reported for the soft method itself** — no gain blow-up, no entropy collapse. |
| **Single-task or multi-task** | **Multi-task only.** 10 and 50 simultaneous tasks. A single-task comparison is reported (§1.5) but as a reference ceiling, not as a setting where the method is used. |
| **Claim strength** | **Ablated** — against concatenation, multi-head, MoE, hard routing, network capacity, and two internal components. |

### 1.3 Phase 1 — Foundational overview

**The problem.** In multi-task RL you want one policy `π(a | s, z)` for a family of
MDPs indexed by a task `T`. Sharing all parameters is efficient but the tasks fight:
the gradient of task A's loss and the gradient of task B's loss point in different
directions and partly cancel. The field's earlier answers were (a) gradient surgery —
project away the conflicting components — which the authors dismiss as *"usually
unstable, especially when there is a large gradient variance within each task itself"*;
and (b) hierarchical RL with hand-specified sub-policies, which needs predefined
subtasks.

**The idea.** Replace "one shared trunk" with a **grid of modules**: `L` layers, `n`
modules per layer. Each module is a small linear-plus-ReLU block. What a task
*inherits* is not a set of weights but a **wiring**: how much each module on layer `l`
contributes to each module on layer `l+1`. The wiring is produced by a separate
routing network, and because it is a set of softmax probabilities rather than a hard
selection, gradients flow through it.

**Two auxiliary design choices** that the paper shows both matter:
- The routing network reads the **observation as well as the task label**, so the
  wiring can change moment-to-moment inside an episode.
- Task losses are **re-weighted automatically** using SAC's per-task learned
  temperature `α_i`, so that easy tasks (which converge fast, and whose `α` grows) get
  down-weighted relative to hard ones.

**The result.** Success rate on Meta-World MT50 goes from ≈35 % to ≈60 %; on MT10 the
gain is marginal in final success but large in sample efficiency (the curve rises
much earlier). A capacity control shows the gain is not just parameters: a baseline
with **4.2× the parameters** reaches 50.3 % against the method's 60.0 % at 1×.

**Initial takeaway.** Conditioning a policy on a task label works far better when the
label chooses a *computation graph* than when it is merely appended to the input
vector — but only if the choice is made **softly**. The hard version of the same idea
is the worst method tested.

### 1.4 Phase 2 — Graduate-level deep dive

#### 1.4.1 Setting

`M` tasks, each a finite-horizon MDP `(S, A, P, R, H, γ)` with continuous `s ∈ S`,
`a ∈ A`; tasks drawn from `p(T)`. SAC is the learner. The single-task policy objective
is

$$
J_\pi(\phi) \;=\; \mathbb{E}_{s_t \sim \mathcal{D}}\Big[\,\mathbb{E}_{a_t \sim \pi_\phi}\big[\alpha \log \pi_\phi(a_t \mid s_t) - Q_\theta(s_t, a_t)\big]\Big],
$$

with the temperature `α` itself learned by

$$
J(\alpha) \;=\; \mathbb{E}_{a_t \sim \pi_\phi}\big[-\alpha \log \pi_\phi(a_t\mid s_t) - \alpha \bar{\mathcal{H}}\big],
$$

`H̄` a target minimum entropy. Multi-task extends both by an outer expectation over
tasks:

$$
J_\pi(\phi) = \mathbb{E}_{\mathcal{T}\sim p(\mathcal{T})}\big[J_{\pi,\mathcal{T}}(\phi)\big],
\qquad
J_Q(\theta) = \mathbb{E}_{\mathcal{T}\sim p(\mathcal{T})}\big[J_{Q,\mathcal{T}}(\theta)\big].
$$

The policy is task-conditioned, `π(a \mid s, z)`, with `z` a task embedding.

#### 1.4.2 The two feature streams

Both streams are mapped to a common width `D`:

$$
f(s_t) \in \mathbb{R}^{D} \quad\text{(2-layer MLP on the state)},\qquad
h(z_\mathcal{T}) \in \mathbb{R}^{D} \quad\text{(1 fully-connected layer on the one-hot task ID)}.
$$

They are combined by **element-wise product**, `f(s_t) \odot h(z_\mathcal{T})`. This is
worth pausing on: the *routing network's own input* is formed by a multiplicative
gating of the state embedding by the task embedding. It is a gain-only, per-unit
modulation with no bias term — a FiLM-like operator hiding one level below the paper's
headline mechanism. The paper never calls it that.

#### 1.4.3 The routing network, derived layer by layer

The routing network has `L − 1` layers, mirroring the `L` module layers of the base
network. Its output at layer `l` is a vector `p^l ∈ ℝ^{n²}`, read as an `n × n` matrix.

**First layer.** With no previous routing state to carry, the input is just the gated
feature:

$$
p^{l=1} \;=\; W^{l=1}_d\big(\mathrm{ReLU}\big(f(s_t)\odot h(z_\mathcal{T})\big)\big),
\qquad W_d \in \mathbb{R}^{n^2 \times D}.
$$

**Recurrence for subsequent layers.** The previous routing vector is lifted back into
the `D`-dimensional feature space, gated by the same state–task product, and projected
back down:

$$
p^{l+1} \;=\; W^{l}_{d}\Big(\mathrm{ReLU}\Big(\;\underbrace{W^{l}_{u}\,p^{l}}_{\in \mathbb{R}^{D}} \;\odot\; \big(f(s_t)\odot h(z_\mathcal{T})\big)\Big)\Big),
$$

with `W_u^l ∈ ℝ^{D×n²}` the up-projection and `W_d^l ∈ ℝ^{n²×D}` the down-projection.
Three vectors are multiplied element-wise: the lifted routing state, the state
embedding, and the task embedding. The design is deliberate — each routing layer sees
*all three* of "what the previous layer decided", "where the robot is now", and "which
task this is".

**Normalisation.** The raw `n × n` matrix is turned into a set of convex weights by a
softmax taken **over the source index `j`** (the printed Eq. 7):

$$
\hat{p}^{\,l}_{i,j} \;=\; \frac{\exp\big(p^{l}_{i,j}\big)}{\sum_{j'=1}^{n}\exp\big(p^{l}_{i,j'}\big)},
\qquad\text{so}\qquad \sum_{j=1}^{n}\hat{p}^{\,l}_{i,j} = 1 \ \ \text{for every } i .
$$

Read this carefully, because it determines what the operator can and cannot express:
**each target module `i` on layer `l+1` receives a convex combination (a weighted
average) of the source modules `j` on layer `l`.** The weights are non-negative and sum
to one *per target*. Consequently:
- The routing **cannot amplify** — the total incoming mass at each target is fixed at 1.
  It reallocates, it does not scale. This is the sharpest structural difference from
  FiLM, where `γ` is unbounded and can raise or crush a channel's magnitude outright.
- The routing **cannot shift** — there is no `β`.
- Sparsity is *not* enforced. Nothing pushes `p̂` toward a one-hot; the "modularity" is
  emergent and, per the t-SNE analysis, is genuinely task-clustered but not disjoint.

#### 1.4.4 The base policy network

With `g^l_j ∈ ℝ^d` the input to module `j` of layer `l` and `W^l_j ∈ ℝ^{d×d}` that
module's weights,

$$
g^{l+1}_{i} \;=\; \sum_{j=1}^{n} \hat{p}^{\,l}_{i,j}\,\Big(\mathrm{ReLU}\big(W^{l}_{j}\,g^{l}_{j}\big)\Big).
$$

Note the ordering: **the module computes first, the routing weight scales the module's
output afterwards.** So all `n` modules run on every forward pass regardless of the
weights — there is no computational saving, unlike a sparse mixture-of-experts. The
routing is a *representational* device, not an efficiency device.

The final layer collapses to the action distribution's parameters, and — as printed —
**without** routing weights:

$$
\mu,\ \sigma \;=\; \sum_{j=1}^{n} W^{L}_{j}\, g^{L}_{j},
\qquad W^L_j \in \mathbb{R}^{d\times o}.
$$

This is why the routing network needs only `L − 1` layers rather than `L`.

**A useful equivalent view.** Fix a task and a state; then all `p̂` are constants and
the base network is an ordinary MLP whose layer-`l` weight matrix is the
`p̂`-weighted blend of the `n` module matrices. Writing `G^l = [g^l_1; …; g^l_n]` as
the stacked activations, the layer map is `G^{l+1} = (P̂^l ⊗ I_d)·ReLU(blkdiag(W^l)·G^l)`
with `P̂^l` row-stochastic. **Soft modularization is therefore a state- and
task-dependent, row-stochastic reparameterisation of a block-diagonal network** — a
constrained relative of a hypernetwork, in which the generated quantity is not the
weights themselves but `(L−1)n²` mixing coefficients over a fixed weight bank. That
framing is the honest way to place it next to hypernetworks in the report: same
"generate the computation from the context" family, drastically smaller generated
object (48 scalars, not a weight matrix).

#### 1.4.5 The task-balancing weights

Easy tasks converge faster and then dominate the average gradient. SAC's per-task
learned temperature `α_i` is repurposed as a difficulty proxy: as a task's policy
entropy falls (it has been solved), `α_i` rises. So down-weight by the exponential of
the negative temperature,

$$
w_i \;=\; \frac{\exp(-\alpha_i)}{\sum_{j=1}^{M}\exp(-\alpha_j)},
$$

and use `J_π(φ) = E_{T∼p(T)}[w_T · J_{π,T}(φ)]`, likewise for `J_Q`. A confident
(low-entropy, high-`α`) task gets a small weight; an unconfident task gets a large one.

**Caveat worth recording.** `w` is a softmax over `−α` across *all* `M` tasks, so it
sums to 1 and the *total* gradient magnitude is divided among the tasks. With `M = 50`
the mean weight is `0.02`; the effective learning rate is scaled down by ~`M` relative
to the unweighted sum. The paper does not discuss this rescaling, and it is confounded
with the balancing effect in the ablation.

### 1.5 Results, as printed

**Table 1 — average success rate, Meta-World.** `∗` = numbers as reported in the
Meta-World paper; unstarred rows are the authors' own re-implementation. 3 seeds,
100 evaluation episodes per task per seed.

| Method | MT10-Fixed | MT10-Conditioned | MT50-Fixed | MT50-Conditioned |
|---|---|---|---|---|
| MT-SAC∗ | 39.5 % | — | 28.8 % | — |
| **MT-SAC (concatenation baseline)** | 44.0 % | 42.6 % | 31.4 % | 28.3 % |
| MT-MH-SAC∗ | 88.0 % | — | 35.9 % | — |
| **MT-MH-SAC (multi-head)** | 85.0 % | 67.4 | 35.5 % | 34.2 % |
| **Mix-Expert (MoE gating, 4 experts)** | 42.8 % | 40.0 % | 36.1 % | 37.5 % |
| **Hard Routing** | 20.8 % | 27.0 % | 22.9 % | 29.1 % |
| **Ours (Shallow)** `L=2, n=2, d=256` | 87.0 % | **71.8 %** | 59.5 % | 60.4 % |
| **Ours (Deep)** `L=4, n=4, d=128` | 86.7 % | 68.4 % | **60.0 %** | **61.0 %** |

(The MT10-Conditioned MT-MH-SAC entry is printed as `67.4` without a percent sign in
the PDF; reproduced as printed.)

Reading of the table:
- **vs. concatenation**: +43 pp on MT10-Fixed, +29 pp on MT10-Conditioned, +29 pp on
  MT50-Fixed, +33 pp on MT50-Conditioned. Concatenating a one-hot task ID is a weak
  baseline in this benchmark.
- **vs. multi-head** (the strong baseline): +2 pp on MT10-Fixed (the authors concede
  the 10-task fixed-goal setting is *"quite simple"* and the win is in sample
  efficiency, not final score), +4.4 pp on MT10-Conditioned, and **+24.5 pp** on MT50.
  The gain grows with task count — the paper's central empirical claim.
- **vs. mixture-of-experts**: MoE beats multi-head on MT50 (36.1 vs 35.5) but is 24 pp
  below soft modularization. The authors' explanation is that a single-level gate
  *"is easy to degenerate to MT-SAC"* when the task count is small; multi-*layer*
  selection is what buys the difference.
- **vs. hard routing**: worst everywhere, below plain concatenation on MT10. Two
  reasons given — policy-gradient variance from the discrete router, and the fact
  that the hard router in Rosenbaum et al. is *"parameterized by tabular lookup table
  which can not encode high dimensional information like observation"*, so it cannot
  route on state at all.

**Table 2 — capacity control, MT50-Fixed.** Parameters are relative to Ours (Deep).

| Method | MT50-Fixed | Params | layers | units |
|---|---|---|---|---|
| MT-MH-SAC∗ | 35.9 % | 1.2× | 3 | 400 |
| MT-MH-SAC | 35.5 % | 1.2× | 3 | 400 |
| MT-MH-SAC-4 | 46.7 % | 1.6× | 4 | 400 |
| MT-MH-SAC-5 | 45.2 % | 2.0× | 5 | 400 |
| MT-MH-SAC-6 | 45.0 % | 2.4× | 6 | 400 |
| MT-MH-SAC-4-Wide∗ | 50.7 % | 3.3× | 4 | 600 |
| MT-MH-SAC-5-Wide∗ | 50.3 % | 4.2× | 5 | 600 |
| **Ours (Deep)** | **60.0 %** | **1×** | — | — |

Baseline performance **saturates** around 50 % and then declines slightly (3.3× beats
4.2×). The 10-point gap at 1/4 the parameters is the strongest single piece of
evidence in the paper that the mechanism, not the capacity, is doing the work.

**Single-task ceiling.** On MT10-Conditioned at 15 M samples: Ours (Shallow) 71.8 %,
average **single-task** policy **78.5 %**. So the multi-task policy does *not* beat
per-task specialists on final score — it approaches them with far fewer samples and
parameters. Honest framing, and worth carrying into the report: none of these
conditioning methods is claimed to exceed a dedicated network per task.

### 1.6 The internal ablation (§5.7, Fig. 6b–c)

Two components removed, on MT10-Conditioned, Ours (Shallow):
- **`w/o Balance`** — remove the temperature-derived loss weights (Eq. 10).
- **`w/o Obs & Balance`** — additionally remove the observation input to the routing
  network, leaving routing conditioned on the task ID alone.

Reported qualitatively only — *"If we remove one or both learning components, the
success rate is reduced by a large margin"* — **no numbers are printed in the text**;
the evidence is Figure 6b. **Record this as a numerically unquantified ablation.**

Two further points from that subsection are quotable:
- The authors themselves connect the observation-conditioning of the router to the
  failure of hard routing: the tabular hard router *"can not encode high dimensional
  information like observation"*.
- The balancing trick is **not** transferable: applied to the baseline
  (`MT-MH-SAC-Balance`), *"the baseline approach is not affected as much"*, so the
  authors *"do not apply balance training for baselines"*. That is a defensible
  choice but it does leave the headline comparison with one component present on the
  proposed method and absent on the baseline.

### 1.7 What the routing actually learns (§5.3)

- **Per-task wiring visualisation (Fig. 3):** different tasks produce visibly
  different connection patterns, but pairs of related tasks share sub-patterns
  (drawer-open / drawer-close; window-open / window-close). The authors read this as
  skill reuse.
- **t-SNE of routing vectors (Fig. 4):** the `(L−1)n² = 48`-dimensional routing vector,
  collected over many rollouts, clusters cleanly by task, with structurally similar
  tasks adjacent. So the routing is **task-discriminative** — which also means it is
  carrying task-identity information that the base network could otherwise have got
  from a concatenated one-hot. The visualisation demonstrates separation, not
  necessity; the necessity claim rests on Table 1.

### 1.8 Relevance to this project

- **It is the discrete-composition arm of the comparison.** If the report's question
  is "affine modulation vs. the alternatives", this is the RL-native routing exemplar
  with a clean head-to-head against concatenation on a 50-task benchmark.
- **The operator's ceiling is a real constraint, not a stylistic one.** Row-stochastic
  routing weights can reallocate mass but cannot amplify or suppress a pathway's
  magnitude. A modulator that is *supposed* to represent something like a gain change —
  e.g. a nociceptive signal turning a pathway's influence up — cannot be expressed by
  this operator without an extra scale. Worth stating explicitly if the report puts
  routing and FiLM on the same axis.
- **Two conditioning signals, multiplied.** The `f(s_t) ⊙ h(z_T)` gate is a gain-only
  self-conditioning of the state features by the task embedding. If the project is
  looking for precedent for "the modulator reads the observation too", this paper both
  does it and ablates it (qualitatively).
- **The instability evidence is about the *hard* variant.** Cite it as: discrete,
  RL-learned routing in an RL loop is unstable (20.8 % vs 87.0 %); the softened version
  is not reported unstable. Do not cite this paper as evidence that modulation in
  general is unstable — it says the opposite about its own method.
- **Actor and critic both modulated, with separate modulators.** No parameter sharing
  between the policy's routing network and the Q-function's. This is one concrete
  answer to the corpus's open question Q5 (actor vs. critic).

### 1.9 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Multi-task RL optimisation is non-trivial: unclear which parameters to reuse, gradients interfere. Proposes explicit modularization of the policy representation. A **routing network** estimates routing strategies to reconfigure a **base policy network** per task; routes are combined **softly** rather than selected, which *"makes it suitable for sequential tasks"*. Robotics manipulation in simulation; improvements in sample efficiency and performance *"by a large margin"*. |
| 1 | **Introduction** | Deep RL is sample-hungry and single-task. Meta-World [43] showed joint training with a shared trunk + per-task heads **hurts** relative to independent training. Prior fix = compositional models / HRL, but HRL needs predefined subtasks or subgoal discovery. This paper: soft combinations of modules, no explicit hierarchy, module roles **emerge**. Two networks: base policy (state → action) and routing (task embedding + state → routing strategy). Because the combination is differentiable, both train jointly. Fig. 1 previews per-task routing patterns for four tasks. Claims near-doubling of performance on the harder benchmark. |
| 2 | **Related Work** | Three strands. (i) *Multi-task learning* — policy distillation needs separate nets + a distillation stage; gradient-similarity methods (GradNorm, gradient surgery / PCGrad) are *"usually unstable, especially when there is a large gradient variance within each task itself"*. (ii) *Compositional learning and modularization* — pre-defined modules (Devin et al.) don't scale; Rosenbaum et al.'s routing networks learn a router **by RL**, i.e. a hard version of this method, which is declared **infeasible for RL** because joint training of a control policy and a routing policy *"suffers from exponentially higher variance in policy gradient due to the temporal nature in RL and leads to severe training instability"*. (iii) *Mixture of experts* — Singh's gating over Q-functions selects **one-time** among whole experts; this method instead performs **multi-layer** selection over sub-modules that are not policies by themselves, increasing sharing flexibility and reducing mutual interference. |
| 3 | **Background** | Per-task finite-horizon MDP `(S,A,P,R,H,γ)`, `M` tasks, continuous state and action, tasks drawn from `p(T)`. |
| 3.1 | Reinforcement Learning with Soft Actor-Critic | SAC as the learner; three parameter groups (policy `φ`, Q `θ`, temperature `α`). Eq. 1: policy objective. Eq. 2: temperature objective with target entropy `H̄`. |
| 3.2 | Multi-task Reinforcement Learning | Extend SAC to a single task-conditioned policy `π(a\|s,z)` with task embedding `z`. Eq. 3 and Eq. 4: expectations of the SAC objectives over `p(T)`. |
| 4 | **Method** | Overview + Fig. 2. Single base policy network of modules; instead of discrete routing paths, a routing network takes **task identity embedding and observed state** and outputs probabilities weighting the modules. Q-function uses the same structure, **initialised and trained independently**. Also flags the second contribution: automatic per-task loss weighting because tasks converge at different speeds ("reaching" vs "pick and place"). |
| 4.1 | **Soft Modularization** | The architecture. One-hot `z_T`; state → 2-layer MLP → `f(s_t) ∈ ℝ^D`; task → 1 FC layer → `h(z_T) ∈ ℝ^D`. *Routing network*: `L−1` layers for `L` module layers, output `p^l ∈ ℝ^{n²}`. Eq. 5 recurrence `p^{l+1} = W_d^l(ReLU(W_u^l p^l ⊙ (f(s_t)⊙h(z_T))))`, with `W_u ∈ ℝ^{D×n²}`, `W_d ∈ ℝ^{n²×D}`; three-way element-wise product combines previous probabilities, observation and task. Eq. 6 first layer `p^{l=1} = W_d(ReLU(f(s_t)⊙h(z_T)))`. Eq. 7 softmax normalisation over the source index. *Base policy network*: `L` layers × `n` modules; Eq. 8 `g^{l+1}_i = Σ_j p̂^l_{i,j} ReLU(W^l_j g^l_j)`; Eq. 9 final unweighted sum → `µ, σ`. Q-function mirrors the architecture with **no shared or reused weights**. |
| 4.2 | **Multi-task Optimization** | Loss balancing. Reuse SAC's per-task temperatures `{α_i}` as difficulty proxies (low entropy ⇒ large `α`). Eq. 10 `w_i = exp(−α_i)/Σ_j exp(−α_j)`; objectives become `E_T[w_T · J_{π,T}]` and `E_T[w_T · J_{Q,T}]`. |
| 5 | **Experiments** | Roadmap: environment, baselines, visualisation, quantitative results, ablations. |
| 5.1 | Environment | **Meta-World**: 50 Sawyer-arm continuous manipulation tasks in MuJoCo. Two challenges, MT10 and MT50. Authors **extend** both to flexible goals, giving MT10-Conditioned / MT50-Conditioned alongside the original MT10-Fixed / MT50-Fixed. |
| 5.2 | Baselines and Experimental Settings | Five baselines: (i) Single-task SAC; (ii) **MT-SAC** — one-hot task ID concatenated with the state; (iii) **MT-MH-SAC** — MT-SAC plus per-task heads; (iv) **Mix-Expert** — 4 experts each with MT-SAC's architecture plus a learned gating network; (v) **Hard Routing** — 4 layers × 4 modules, one module selected per layer by a task-dependent controller, following Rosenbaum et al. Two variants of the method (Shallow `L=2,n=2,d=256`; Deep `L=4,n=4,d=128`) with **equal parameter count**. Metric: success rate, averaged across tasks, 3 seeds, 100 episodes per task per seed. Sample budgets: baselines 20 M (MT10) / 100 M (MT50); the method, Mix-Expert and Hard Routing 15 M / 50 M *"they converge much faster"*. |
| 5.3 | Routing Network Visualization | Fig. 3 — per-task connection maps, related tasks share sub-patterns. Fig. 4 — t-SNE of the 48-dim routing vector, clear per-task clusters with structurally similar tasks adjacent. |
| 5.4 | Quantitative Results | Table 1 and Fig. 5. MT10-Fixed: +2 pp final, large sample-efficiency gain, authors concede the setting is *"quite simple"*. MT10-Conditioned: >4 pp. MT50 (both): ≈24 pp. Deep > Shallow on MT50, Shallow > Deep on MT10 — attributed to simple topology aiding sharing at low task counts and richer topology preventing interference at high task counts. MT50-Conditioned > MT50-Fixed because flexible goals give more training variety. MoE degenerates toward MT-SAC at low task count; Hard Routing is worst and *"the optimization with hard routing is extremely challenging"*. |
| 5.5 | Effects on Network Capacity | Table 2 + Fig. 6a. Baselines with 1.2×–4.2× parameters; best baseline 50.7 % (3.3×) and 50.3 % (4.2×) vs 60.0 % at 1×. Gains **saturate fast** with width/depth. |
| 5.6 | Comparison with Single Task Policy | MT10-Conditioned, 15 M samples: Ours (Shallow) 71.8 % vs average single-task 78.5 %. Framed as "reasonably close with far fewer examples and parameters". |
| 5.7 | Analysing Learning Components | Removes (i) temperature-based balancing, (ii) balancing **and** the observation input to the router. Both hurt *"by a large margin"* — **qualitative only, Fig. 6b, no table**. Links the observation-routing finding to Hard Routing's tabular controller. Applies balancing to the baseline (`MT-MH-SAC-Balance`, Fig. 6c): *"the baseline approach is not affected as much"*, so balancing is not applied to baselines. |
| 6 | **Conclusion** | Soft modularization improves sample efficiency and success rate; the advantage grows with task diversity; opens the door to zero-shot generalisation to unseen tasks. |
| 7 | **Potential Broader Impact** | Skill/component reuse; zero-shot transfer; sample efficiency lowers energy cost and the barrier to entry. No risks section beyond this. |

---
