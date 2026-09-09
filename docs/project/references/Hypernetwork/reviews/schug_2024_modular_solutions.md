---
title: "Discovering Modular Solutions that Generalize Compositionally"
slug: schug_2024_modular_solutions
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_theory.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

# 2. Schug et al. 2024 — Discovering Modular Solutions that Generalize Compositionally

**PDF:** `docs/project/references/Hypernetwork/sources/Schug et al. 2024 - Discovering modular solutions that generalize compositionally.pdf`
**Authors:** Simon Schug\*, Seijin Kobayashi\* (ETH Zurich, equal contribution); Yassir Akram (ETH Zurich);
Maciej Wołczyk (IDEAS NCBR); Alexandra Proca (Imperial College London); Johannes von Oswald (ETH Zurich /
Google Research); Razvan Pascanu† (Google DeepMind); João Sacramento† (ETH Zurich); Angelika Steger†
(ETH Zurich).
**Venue as printed:** running header on every page — *"Published as a conference paper at ICLR 2024"*.
**Relation to paper #1:** this is the paper that Schug et al. 2025 cites when it says "It has been
theoretically and empirically shown that hypernetworks support compositional generalization (Schug et al.,
2024)". The two form a deliberate pair: 2024 proves the guarantee, 2025 finds the mechanism already present
in attention.

---

## Phase 1 — Foundational overview

### Introduction

Suppose the tasks an agent faces are secretly built by mixing a small set of hidden "modules" — an agent has
learned to push green boxes and to jump over red boxes, and we would like it to jump over green boxes without
further training. A modular architecture *could* exploit that structure. The open question this paper closes
is: **under what conditions does a modular learner actually discover the true modules, rather than
memorising a separate solution per task it happened to see?**

The setup is a **teacher–student** experiment where the teacher is itself a hypernetwork, so the ground-truth
modules are known by construction. A teacher generates its first-layer weights as a sparse linear combination
of `M` hidden module matrices, selected by a task code the student never sees. The student — also a
hypernetwork — sees only input–output demonstrations, and must infer both its own task code and a module
set. The question becomes precise: does the student's module set match the teacher's?

The answer is a theorem with three named conditions, and — crucially — a **task-count** requirement that is
**linear in the number of modules**, not exponential in the number of combinations.

### Key findings

- **Three conditions are necessary and sufficient** for the student to recover the teacher's modules (up to a
  shared linear transformation) and thereby generalize to *every* module combination, including unseen ones:
  1. **Compositional support** — every module appears in at least one training task.
  2. **Connected support** — the task families must overlap; no group of modules may appear only in isolation
     from the rest. This one is the non-obvious condition and the paper's main contribution.
  3. **No overparameterization** — the student must not have substantially more hidden units or modules than
     the teacher, or it will spend one module per task and never notice the shared structure.
- **The sample-complexity result.** If the student fits `dim(span(Z_k)) + 1` tasks drawn from each task family
  `Z_k`, it generalizes compositionally **almost surely**. Because the number of families under connected
  support grows *linearly* with the number of modules, the total task count is linear in `M` while the set of
  combinations it then solves is exponential.
- **Identification and compositional generalization are the same thing.** Theorem 2 shows they are
  *equivalent*, not merely correlated — so "does it generalize?" and "did it find the real modules?" are one
  question.
- **Empirically confirmed on four settings**, including two grid-world settings with compositional rewards and
  compositional goals. Hypernetworks beat the monolithic baselines (MAML, ANIL) by very large margins **when
  the conditions hold**, and **lose to them when connected support is violated** — which is the strongest form
  of confirmation available, since the theory predicts the direction of failure, not just the success.

### Initial takeaway

This paper is the reason anyone is entitled to say "hypernetworks compose". It converts a vague architectural
intuition into a checkable property of the *training task distribution*: if your training tasks do not connect
your modules to each other, no amount of modular architecture will help, and a monolithic network may well do
better. **For this project the actionable content is not the architecture — it is the requirement on the task
distribution.** A modulator with `M` slots trained on contexts that never co-vary cannot be expected to learn
composable slots, and this paper says so precisely.

---

## Phase 2 — Graduate-level deep dive

### 2.1 The compositional data-generating process

For each task, sample a latent code `z ∈ ℝ^M` with at most `K` non-zero entries (`‖z‖₀ ≤ K`) from a pool of
`M` modules `(Θ^(m))_{1≤m≤M}`. The task-shared function `g` is parameterised by

$$\omega(z) = \sum_{m=1}^{M} z^{(m)} \Theta^{(m)}.$$

**This is composition in weight space** — modules are added as parameter matrices, not as feature maps. Note
immediately that this is *rung 3* of the capacity ladder: the code is `M`-dimensional, the emitted object is a
full weight matrix, and the module set is shared and learned rather than emitted.

The naive learner treats every combination separately, and there are exponentially many.

### 2.2 Architectures compared

| Architecture | Form | Class |
|---|---|---|
| **Linear hypernetwork** | `ω = h(φ; θ)` with `h` linear in `φ` → a **linear combination** of module parameters | modular |
| **Nonlinear hypernetwork** | `h` is a 4-layer ELU MLP; its penultimate layer "can be thought of as selecting among the module parameters" | modular |
| **ANIL** (Raghu et al. 2020) | `f(x, φ, θ) = φᵀ g(x; θ)` — shared nonlinear encoder, task-specific **linear readout** | monolithic |
| **MAML** (Finn et al. 2017) | `f(x, φ, θ) = g(x; φ(θ))` — shared parameters initialise task-specific parameters | monolithic |

**Note for the project's purposes: ANIL is the closest thing here to a "static feature extractor + context
readout" baseline, and it is the honest stand-in for the concatenation-style control.** There is **no FiLM arm
in this paper.**

### 2.3 The meta-learning objective

With `P_z` over task codes, each task defines support and query sets
`D_z^support = {x_i,y_i}_{i=1}^{N_support}`, `D_z^query = {x'_i,y'_i}_{i=1}^{N_query}`. Bilevel:

$$\min_\theta\ \mathbb{E}_{z\sim P_z}\big[\mathcal{L}(\phi_z(\theta),\theta; D_z^{\text{query}})\big]
\quad \text{s.t.} \quad \phi_z(\theta) \in \arg\min_\phi \mathcal{L}(\phi,\theta; D_z^{\text{support}}) \tag{1}$$

For the theory they take the **infinite-data limit**, collapsing support and query into `D_z`, giving the
single-level multi-task objective

$$\min_\theta\ \mathbb{E}_{z\sim P_z}\Big[\min_{\phi_z} \mathcal{L}(\phi_z,\theta; D_z)\Big]. \tag{2}$$

In practice they run gradient descent on `φ_z` to convergence per outer step, which — usefully — **avoids
second-order gradients**.

### 2.4 The teacher–student construction

Teacher and student are both 2-layer MLPs with `h` hidden units, one output unit, first-layer weights
generated by a linear hypernetwork:

$$f(x; a, \Theta, z) = a^\top \psi\big(W(\Theta,z)\, x\big), \qquad
W(\Theta,z) = \sum_{m=1}^{M} z^{(m)} \Theta^{(m)}. \tag{3}$$

`a` is the task-shared readout, `ψ` the activation. **The student never observes `z`**; it infers its own
`M̂`-dimensional code `ẑ` by minimising

$$\mathcal{L}\big(\hat{z},(\hat\Theta,\hat a); D_z\big) = \tfrac{1}{2}\,\mathbb{E}_x\Big[\big\|f(x;\hat a,\hat\Theta,\hat z) - f(x;a,\Theta,z)\big\|^2\Big]. \tag{4}$$

Student quantities carry hats throughout.

### 2.5 The worked counterexample that motivates connected support

This is the clearest single argument in the paper and worth reproducing. Take `M = 6`, `K = 2`. Task families
are specified by binary masks marking which two modules are active. Train on four families:

`b₁ = (1,1,0,0,0,0)`, `b₂ = (0,1,1,0,0,0)`, `b₃ = (0,0,0,1,1,0)`, `b₄ = (0,0,0,0,1,1)`.

Assume infinite samples per task and a perfect fit. Now ask for `z* = (1,0,0,0,0,1)` — modules 1 and 6, both
of which the student has seen. **It fails.** The reason is a hidden-neuron alignment problem: a two-layer MLP
is identifiable only up to a permutation of its hidden units, and the student's permutation is fixed
*separately* within `{1,2,3}` and within `{4,5,6}`, because no training task ever forced those two groups to
agree. Module 1 and module 6 are each learned correctly, but in **mutually inconsistent neuron orderings**, so
their sum is meaningless.

Adding a fifth family `b₅ = (0,0,1,1,0,0)` bridges the two groups, and now compositional generalization holds
for every code including `z*`.

**This is the load-bearing intuition.** The failure is not about data volume or module coverage — the student
saw everything — it is about *the absence of a task that ties two subsets together*.

### 2.6 The two conditions, formally

Let `Z = {Z₁, Z₂, …}` be task families, each `Z_k ⊆ ℝ^M` non-empty with mask `b_k`, required to satisfy
`span(Z_k) = {v ⊙ b_k | v ∈ ℝ^M}`.

> **Definition 3.1 (Compositional support).** `P_z` has compositional support if all dimensions of `ℝ^M` are
> covered by at least one mask, i.e. `Σ_k b_k` has no zero entry.

> **Definition 3.2 (Connected support).** `P_z` has connected support if there is a path between any two task
> families, where `Z_k` and `Z_l` are connected iff their masks share a non-zero element, `b_k ∧ b_l ≠ 0`.

Read Definition 3.2 as a **graph connectivity condition on the training-task distribution**: nodes are task
families, an edge exists when two families share a module, and the graph must be connected.

### 2.7 The identifiability result — the explicit ask

**Theorem 1 (Compositional generalization, informal, main text).** Assume `P_z` has compositional and
connected support, `P_x` has full support in the input space, and student dimensions match the teacher's:
`M̂ = M ≤ n`, `ĥ = h`. Then under an additional smoothness condition on `P_z` and non-degeneracy of `(Θ, a)`:

$$\mathbb{E}_{z\sim P_z}\Big[\min_{\hat z} \mathcal{L}\big(\hat z,(\hat\Theta,\hat a);D_z\big)\Big] = 0
\ \Longrightarrow\
\min_{\hat z} \mathcal{L}\big(\hat z,(\hat\Theta,\hat a);D_z\big) = 0 \quad \forall z \in \mathbb{R}^M.$$

In words: **zero loss on the training task distribution implies zero loss on every task code in `ℝ^M`,
including all held-out combinations.**

**The finite-task-count clause — the answer to "how many demonstrations".** Immediately after, the same
theorem states: *"if the student achieves zero loss on a finite number, `N = dim(span(Z_k)) + 1`, of i.i.d.
samples of tasks for each `Z_k` from `P_z`, it will generalize compositionally almost surely."*

The formal version is **Theorem 9** (Appendix A.4), whose second part reads: with `d_k := dim(span(Z_k))`, for
any `F = ∪_k F_k` with `F_k = {z_{k,1},…,z_{k,d_k+1}}` sampled i.i.d. from `P_{z ∈ Z_k}`,

$$\forall z \in F,\ \min_{\hat z}\mathcal{L}(\hat z,(\hat\Theta,\hat a);D_z) = 0
\ \Longrightarrow\ \forall z,\ \min_{\hat z}\mathcal{L}(\hat z,(\hat\Theta,\hat a);D_z)=0. \tag{62}$$

**Reading the count precisely — three things to get right:**

1. **It is per task family, not global.** You need `d_k + 1` *tasks* from **each** family `Z_k`. The total is
   `Σ_k (d_k + 1)`.
2. **`d_k` is the dimension of the span of that family**, which for a mask with `K` active entries is at most
   `K`. So each family costs at most `K + 1` tasks. Since the family count under connected support grows
   linearly in `M`, **total tasks scale as `O(M·K)` — linear in the number of modules** — while the resulting
   guarantee covers all `O(M^K)`-many combinations. The paper's own phrasing: *"fitting a number of tasks
   linear in the number of modules suffices to generalize to all exponentially many module combinations."*
3. **"Tasks", not "demonstrations".** The theorem is stated in the **infinite-data-per-task limit** (`P_x` has
   full support, `D_z` is the population distribution). It says nothing about how many `(x,y)` pairs per task
   are needed. The finite-sample-per-task question is handled only empirically (Figure A4 — reducing below
   `N = 256` shots degrades performance) and the discussion flags that *"the sample complexity appears to
   scale unfavorably as the number of teacher modules increases (c.f. Figure A3)"*.

**Theorem 9's full hypothesis list** (Appendix A.4), which the informal version compresses: `P_x` has full
support; `M ≤ n`; `M̂ = M`; `ĥ = h`; `Σ_i a_i Θ_i` is full rank; all `(a_i)_{1≤i≤h}` non-zero; **no two rows of
any module `Θ^(m)` are colinear** (the ReLU irreducibility condition, Definition A.1 and §A.1.2); `P_z` has
connected and compositional support.

**Theorem 2 (Linear identification, informal).** Under `P_x` full support, `M̂ = M ≤ n`, `ĥ = h`, and
non-degeneracy of `Θ` and `a`, the statement `min_ẑ L(ẑ,(Θ̂,â);D_z) = 0 ∀z` is **equivalent** to the existence
of an invertible `F`, a permutation `σ` and a sign flip `ε ∈ {−1,1}^h` with

$$a_{\sigma_i} \Theta_{\sigma(i)} = \epsilon_i\, \hat a_i\, \hat\Theta_i F \qquad \forall i \in [1,h].$$

Here `Θ_i` is the `n × M` slice mapping `z` to hidden-unit `i`'s weight vector, `w_i = Θ_i z`.

**Read the equivalence carefully.** It is what makes the paper's title honest: the student does *not* merely
happen to generalize; generalizing and having recovered the modules **up to one shared invertible `F`, a
neuron permutation and per-neuron signs** are the same event. The recovered modules are the true ones in a
rotated basis — good enough to compose, not good enough to read off individually without further work
(which the discussion flags as an interpretability question for future research).

**Necessity, not just sufficiency.** The paper states that compositional support, connected support and
`h = ĥ` are *"not only sufficient, but also necessary conditions for the implication to hold (all other things
being equal), since we can construct counterexamples, detailed in Appendix A.3, when one of the conditions is
violated."*

**The honest limitation, stated by the authors.** *"we characterized the solutions of the modular
teacher–student setting at equilibrium in the infinite data limit. Even when the modular solution constitutes
a global optimum, we cannot provide any guarantees that it can be reached with gradient-based learning."*
This theorem is about the **structure of global minima**, not about optimisation reaching them. It is
therefore the exact complement of Beck 2023 (paper #3), which is entirely about whether optimisation gets
there.

### 2.8 Empirical verification in the theoretical setting (§3.3)

**Module alignment metric.** `min_i ( max_j |s(Θ_i, Θ̂_j F)| )` where `s` is cosine similarity and `F` is
obtained by regressing `ẑ` on `z`. Alignment `= 1` means linear identification. Note the outer `min` — this
is a *worst-module* score, so it is a strict measure.

- **Connected support is required (Fig. 2C).** High alignment for both continuous (`z ∈ ℝ^M`) and discrete
  (`z ∈ {0,1}^M`) task distributions when support is connected; "noticeable degradation" when disconnected.
- **Overparameterization hurts (Fig. 2D).** Slight overparameterization is *beneficial* (it is needed for
  optimisation to succeed at all), but beyond `ĥ = 8h` and `M̂ = 2M` identification degrades noticeably for
  **discrete** task distributions. For **continuous** distributions overparameterization appears harmless,
  which the authors read as "the learning dynamics introduce a beneficial inductive bias."
- **Weight decay does not rescue it (Table A1, 5 seeds).** Module alignment in the heavily overparameterized
  regime, varying weight-decay strength:

  | Weight decay | `M̂=16M, ĥ=16h` | `M̂=16M, ĥ=32h` | `M̂=32M, ĥ=16h` | `M̂=32M, ĥ=32h` |
  |---|---|---|---|---|
  | 0.001 | 0.7704 | 0.7165 | 0.8369 | 0.8144 |
  | 0.0001 | 0.7699 | 0.6752 | 0.8483 | 0.8043 |
  | 0.00001 | 0.7633 | 0.6727 | 0.8346 | 0.8292 |
  | 0 | 0.7542 | 0.7109 | 0.8421 | 0.8076 |

  Alignment is flat in weight decay to within ~0.02 — regularisation is not the lever.

### 2.9 Head-to-head numbers — hyperteacher (Tables A2–A8)

The hyperteacher generalises the teacher to a hypernetwork that modularly parameterises **multiple layers** of
a target network, with **sparse discrete** module combinations and limited data per task. 3 seeds throughout.

**These are the paper's cleanest head-to-head numbers. There is no FiLM arm; the comparison is
hypernetwork vs. ANIL / MAML.** Highlighting OOD accuracy, the row that matters:

| Setting | ANIL | MAML | Linear hypernet | Nonlinear hypernet |
|---|---|---|---|---|
| `M=4, K=1` (A2) | **46.52 ± 0.80** | 20.53 ± 0.72 | 20.42 ± 1.64 | 20.93 ± 2.22 |
| `M=4, K=2` (A3) | 60.78 ± 0.24 | 55.41 ± 0.80 | 76.35 ± 10.11 | **90.90 ± 0.26** |
| `M=4, K=4` (A4) | 63.14 ± 0.70 | 63.29 ± 0.60 | 88.61 ± 6.15 | **94.90 ± 0.23** |
| `M=8, K=1` (A5) | **55.80 ± 0.26** | 47.42 ± 2.16 | 26.67 ± 3.12 | 26.91 ± 0.40 |
| `M=8, K=2` (A6) | 59.76 ± 0.27 | 60.60 ± 0.37 | 87.45 ± 2.55 | **96.05 ± 0.34** |
| `M=8, K=4` (A7) | 60.63 ± 0.21 | 62.78 ± 0.24 | 93.50 ± 0.24 | **95.68 ± 0.55** |
| `M=8, K=8` (A8) | 61.53 ± 0.26 | 64.11 ± 0.24 | 91.65 ± 0.72 | **94.75 ± 0.24** |

**The headline gap:** at `M=8, K=2` the nonlinear hypernetwork reaches **96.05 %** OOD accuracy against
MAML's **60.60 %** — a **+35.5 point** margin — with train accuracy 96.91 % vs 61.33 %, i.e. the monolithic
models are not merely failing to transfer, they cannot even fit the training tasks.

**The theory-predicted reversal, which is the more valuable result.** At `K = 1` exactly one module is active
per task, so no task ever connects two modules and **connected support is violated by construction**. The
theory predicts hypernetworks should fail. They do, and they lose to ANIL: `M=8, K=1` → hypernetworks
**26.67 / 26.91** vs ANIL **55.80**; `M=4, K=1` → **20.42 / 20.93** vs ANIL **46.52**. A theory that predicts
the sign of its own failure case is doing real work; this is the strongest evidence in the paper.

**The overfitting-to-`K` caveat.** Models overfit to the *number* of modules composed in training. From
Table A6 (trained at `M=8, K=2`), evaluating at larger `K`:

| Eval `K` | ANIL | MAML | Linear hypernet | Nonlinear hypernet |
|---|---|---|---|---|
| K=1 | 59.53 | 60.76 | 86.73 | 96.01 |
| K=2 | 59.76 | 60.48 | 87.49 | 95.90 |
| K=4 | 59.84 | 60.01 | 82.56 | 77.79 |
| K=8 | 58.60 | 57.99 | 60.60 | **33.08 ± 1.94** |

At `K=8` the nonlinear hypernetwork (33.08) falls **well below both monolithic baselines** (58.60 / 57.99).
The paper reports this openly: *"learners overfit to the particular number `K` of modules combined within a
task"*, partially but not fully alleviated by more task-inference gradient steps at evaluation.

**Module decodability (Fig. 3C/D).** Training a linear decoder to predict ground-truth `z` from the student's
learned embeddings gives `R²` close to 1 on the OOD set when support is compositional *and* connected;
reduced when non-compositional; drops "significantly" when disconnected. Notably this holds even for the
**nonlinear** hypernetwork, where there is architectural mismatch and no a-priori reason for the relation to
be linear — an unexplained but consistent extension of the theory.

### 2.10 The two grid-world settings — and why they are not RL

Both settings are grid worlds and both are *about* reinforcement learning objects, but **neither trains with
an RL algorithm.** State this precisely when citing:

**Compositional preferences (§4.2, Appendix C.3).** A 5×5 grid, 5 actions (4 moves + terminate), 4 objects
each of one of 8 colours, walls, deterministic dynamics. A task samples up to `K = 3` of `M = 8` preference
modules and sums them into a hidden preference vector mapping colour → reward. **The optimal action-value
function is computed exactly** (discount 0.9, horizon 8); a greedy agent rolls out; the dataset is
`(observation, action-value vector)` pairs. **The learning problem is supervised regression on `Q`-values with
MSE loss**, meta-learned bilevel. 32 environment instances per task, 16 support / 16 query.
- *Result (Fig. 4C):* both hypernetworks achieve lower OOD MSE than ANIL and MAML under compositional support.
- *Result (Fig. 4B):* constructing **disconnected** clusters of preference vectors noticeably raises OOD loss
  for both hypernetworks *"despite the number of observed combinations being comparable"* — a controlled
  confirmation that it is connectivity, not task count, doing the work.
- *Overparameterization (Fig. A8):* no negative effect within the tested range, consistent with the
  **continuous** teacher-student finding, since preferences are continuous combinations.

**Compositional goals (§4.3, Appendix C.4).** 11×11 mazes, 5 objects, moves plus object-interaction actions.
A goal is a 4-factor composition — maze layout (5) × target object (5) × target interaction (2) × goal
quadrant (4) = **200 possible goals**; 25 % held out with every factor still present in training. **The loss
is cross-entropy against the optimal action** — i.e. **behaviour cloning / imitation of a computed optimal
policy**, not policy improvement.
- *Result (Fig. 4E):* both hypernetworks achieve higher OOD accuracy w.r.t. the optimal policy than ANIL and
  MAML. Figure A9 corroborates with a stricter metric — the fraction of episodes where the learned policy
  follows the optimal path *exactly* end-to-end and therefore collects the only environment reward.
- *Result (Fig. 4F):* holding out an entire goal quadrant (non-compositional support) hurts the hypernetworks
  **more** than ANIL/MAML — which the authors correctly read as evidence that the hypernetworks' advantage
  *comes from* exploiting compositional structure rather than from generic capacity.
- *Overparameterization (Fig. A10):* stable OOD accuracy across hidden and module dimension, **contrary** to
  the discrete teacher-student prediction. The authors flag this as an open discrepancy.
- *Parameter matching:* hyperparameters chosen so total parameter counts are "approximately comparable" —
  hypernetworks `ĥ = 32`, `M̂ = 8`, `L = 2`; MAML `ĥ = 384`; ANIL `ĥ = 512`. Inner steps 10 for all except
  ANIL at 100.

**Figures 4B/C/E/F have no accompanying numeric table**; only the hyperteacher tables A2–A8 give numbers.
Quote the grid-world results qualitatively.

### 2.11 Training stability — initialization and normalization (Appendix D)

This paper's stability treatment is entirely in the parameterisation, and it is unusually explicit. For the
**linear hypernetwork** (D.3):

1. **NTK parameterization of the base network.** Pre-activations at each layer are rescaled by `1/√H` with
   `H` the layer's input dimension. Stated purpose, quoting: *"if at initialization the hypernetwork outputs
   weights that are centered and unit variance, the forward pass would be approximately variance preserving."*
2. **The embedding is normalized to unit norm** before being multiplied by the hypernetwork parameters. This
   removes code-magnitude drift as a source of generated-weight scale variation — structurally the same fix as
   HYLA's RMSHead in paper #1, applied to the code rather than the attention scores.
3. **Hypernetwork weights initialized truncated-normal, mean 0, std `1/√M`**, with `M` the **embedding
   dimension** — i.e. the fan-in of the hypernetwork is the code, so the standard fan-in rule is applied at
   the hypernetwork level, which is exactly the correction Beck (paper #3) argues is usually got wrong.
4. **Biases are not generated** by the hypernetwork; they are fast parameters of the base network.
5. **Three separate hypernetworks** generate first-layer weights, all hidden-layer weights, and last-layer
   weights respectively, each with its own embedding — so three codes in total, not one.
6. Embedding initial values drawn uniform with unit variance; biases initialized to 0.

For the **nonlinear hypernetwork** (D.4): a **4-layer MLP with ELU**, **LayerNorm applied before every
activation and to the input**, weights truncated-normal std `1/√H` (fan-in), biases 0.

**Also used throughout:** AdamW, outer weight decay 0.001, inner weight decay 0.0001, and **outer gradient
clipping tuned over {1, 2}** (Tables A10–A12) — gradient clipping is grid-searched as a first-class
hyperparameter for every model, hypernetwork and monolithic alike.

Taken together: **unit-norm code, fan-in-correct hypernetwork init, NTK-parameterized base network, LayerNorm
inside the nonlinear generator, and tuned gradient clipping.** No instability is reported in the results,
which is consistent with these five measures being adequate — but note that nothing here is *ablated*, so the
paper is evidence that these choices work, not evidence that each is necessary.

### 2.12 Where this sits on the capacity spectrum

**Rung 3 → 4 boundary, and the paper is explicit about which side it is on.** The linear hypernetwork emits
`ω(z) = Σ_m z^(m) Θ^(m)` — an `M`-dimensional code selecting from a shared learned module library, i.e.
**parameter composition**, exactly as in paper #1 but with the code inferred by optimisation rather than read
off attention scores. The nonlinear hypernetwork sits one notch higher: `h` is a 4-layer MLP, so the map from
code to weights is nonlinear, but the *output* is still the full weight tensor of the base network — closer to
rung 4.

Two observations relevant to the FiLM comparison:

- **The theory is stated for the linear (rung 3) case and does not cover FiLM.** FiLM applies a diagonal scale
  to *activations*; the composition `Σ_m z^(m) Θ^(m)` is in *weight space* over full matrices. The
  identification argument turns on hidden-neuron permutation consistency across modules, which has no
  counterpart in a diagonal activation rescaling. **Do not cite this theorem as covering FiLM.**
- **The nonlinear hypernetwork consistently beats the linear one** on the hyperteacher (e.g. 96.05 vs 87.45 at
  `M=8,K=2`; 90.90 vs 76.35 at `M=4,K=2`) and has **much tighter error bars** (±0.26 vs ±10.11). Since the
  teacher is *linear*, this is a case where **more generator capacity than the ground truth requires still
  helps**, presumably for optimisation reasons — a small piece of evidence pointing the same direction as
  papers #3 and #4.

### 2.13 Relevance and cautions for this project

**Useful.**
- The connected-support condition is a **design requirement on the training distribution** that transfers
  directly. If the project trains a multi-slot modulator on contexts that never co-occur, the theory says the
  slots will be learned in mutually inconsistent internal bases and will not compose — regardless of
  architecture. Checkable before any training run.
- The **linear-decodability probe** (regress ground-truth latent from learned embeddings, evaluate on held-out
  combinations) is a cheap, directly reusable diagnostic and complements the probe in paper #1.
- The **overparameterization warning** is unusual and worth carrying: more modules than the world has is
  actively harmful for identification in the discrete case, and weight decay does not fix it.
- The **`K`-overfitting** result is a concrete failure mode to test for: a modulator trained on
  two-factor contexts degrades badly when asked to combine eight.

**Cautions.**
- **Not RL.** Grid worlds, but supervised `Q`-value regression and behaviour cloning of a computed optimal
  policy. Citing this as an "RL result" would be wrong.
- **No FiLM baseline**; the monolithic arms are ANIL and MAML.
- **Theory is infinite-data, equilibrium-only**, and the authors explicitly disclaim any guarantee that
  gradient descent reaches the modular optimum.
- **Identification is up to an invertible `F`**, so recovered modules are not individually interpretable
  without extra work.
- **3 seeds**; the linear hypernetwork's error bars reach ±10 accuracy points in places.
- Sample complexity in `M` "appears to scale unfavorably" empirically (Fig. A3), which is a real gap between
  the linear-in-`M` *task-count* theorem and practice.

---

## Appendix: Section-by-Section Backbone — Schug et al. 2024

**Abstract.** Studies a teacher–student setting with a modular teacher to relate compositional generalization
to module identification. Studies modularity in hypernetworks as a general class of multiplicative
interactions. Shows theoretically that identification up to linear transformation from demonstrations alone is
possible without learning exponentially many module combinations; demonstrates empirically that under those
conditions meta-learning from finite data discovers compositionally generalizing modular policies.

**1. Introduction.** Modularity in artificial and biological systems; the push-green-box / jump-red-box
example of compositional generalization. Monolithic architectures lack a decomposition mechanism and may need
to learn exponentially many combinations. Open question whether large language models compositionally
generalize beyond the training distribution (Srivastava 2023; Press 2023; Dziri 2023).

**2. Methods.** *Compositionality*: each task recombines up to `K` of `M` modules, `ω(z) = Σ_m z^(m) Θ^(m)`,
`‖z‖₀ ≤ K`. *Modular vs monolithic architectures*: hypernetworks (Ha 2017) as the modular choice, expressing a
wide class of multiplicative interactions (Jayakumar 2020); linear hypernetwork = linear combination of
modules, nonlinear hypernetwork = separate network whose penultimate layer selects among modules; monolithic
choices ANIL (`f = φᵀg(x;θ)`) and MAML (`f = g(x;φ(θ))`). Held-out module combinations define the OOD test.
*Meta-learning*: bilevel objective Eq. 1; infinite-data multi-task simplification Eq. 2; inner loop run to
convergence, avoiding second-order gradients; test-time distribution `P_z^test` may be disjoint from `P_z`.

**3. Theory.** Core idea: extend teacher–student (Gardner & Derrida 1989) to multi-task; relate compositional
generalization to parameter identification as a necessary and sufficient condition. Lists the three conditions
(compositional support, connected support, no overparameterization).
- **3.1 Multi-task teacher-student setup.** Eq. 3 defines the 2-layer MLP with hypernetwork-generated first
  layer; Eq. 4 the student loss. Student sees `x` but not `z`; infers `ẑ` of dimension `M̂`.
- **3.2 Identification & compositional generalization.** The `M=6, K=2` worked counterexample with masks
  `b₁…b₄`, the failure at `z* = (1,0,0,0,0,1)` due to inconsistent neuron permutations across module groups,
  and the repair by adding `b₅`. Definitions 3.1 and 3.2. Theorem 1 (compositional generalization, informal)
  with the `N = dim(span(Z_k)) + 1` finite-task clause. Statement that the conditions are necessary as well as
  sufficient (counterexamples in Appendix A.3). Theorem 2 (linear identification, informal) with the
  `a_{σi}Θ_{σ(i)} = ε_i â_i Θ̂_i F` equivalence.
- **3.3 Empirical verification in the theoretical setting.** Module-alignment metric. Identification requires
  connected support (Fig. 2C, continuous and discrete). Identification is sensitive to overparameterization
  (Fig. 2D): slight overparameterization helps optimisation, but beyond `ĥ = 8h`, `M̂ = 2M` identification
  degrades for discrete task distributions and weight decay does not help (Table A1); continuous distributions
  are unaffected.

**4. Experiments.**
- **4.1 Hyperteacher.** Teacher hypernetwork parameterises multiple layers; sparse discrete module
  combinations; limited data per task. (i) Modular but not monolithic architectures compositionally generalize
  (Fig. 3B) — hypernetworks fall below ANIL/MAML when support is non-compositional. (ii) Requires `K > 1`;
  at `K = 1` connected support fails and hypernetworks generalize poorly as predicted (Fig. 3E). (iii) Modules
  are linearly decodable from student embeddings when support is compositional and connected, `R²` near 1
  (Fig. 3C/D), including for the architecturally mismatched nonlinear hypernetwork. (iv) Compositional
  generalization is sensitive to overparameterization (Fig. 3F). (v) Meta-learning overfits to the number `K`
  of composed modules (Table A6).
- **4.2 Compositional preferences.** 5×5 grid world inspired by Barreto et al. (2020); up to `K = 3` of
  `M = 8` preference modules summed into a colour→reward preference vector; agent infers preferences from
  optimal trajectories and predicts the action-value function for resampled configurations. Hypernetworks beat
  ANIL/MAML in OOD MSE under compositional support (Fig. 4C); disconnected clusters raise OOD loss (Fig. 4B).
- **4.3 Compositional goals.** 11×11 maze; goal = maze × target object × target interaction × goal quadrant;
  accuracy measured against the optimal policy. Hypernetworks beat ANIL/MAML on held-out goal compositions
  (Fig. 4E); holding out a goal quadrant hurts hypernetworks more (Fig. 4F), evidencing that their advantage
  derives from compositional structure.

**5. Related work & discussion.** Grounded in teacher–student analysis (Gardner & Derrida 1989) building on
characterisations of MLP global minima in the infinite-data limit (Tian 2020; Simsek et al. 2021). Extends it
to multi-task with a hidden latent and a linear-hypernetwork teacher. Identification shown to be necessary and
sufficient for compositional generalization; new identifiability result requiring compositional and connected
support. Complements Lachapelle et al. (2023) on L1-regularized disentangled identification. Broad
compositional-generalization literature surveyed. Emphasis on **compositionality in weight space** (Kumar &
Daume III 2012; Ruvolo & Eaton 2013; Perez et al. 2018 — i.e. FiLM — Jayakumar 2020; Dimitriadis 2023). Notes
that linearly combining parameters can capture nonlinear latent structure, raising interpretability questions.
Limitations: theory is infinite-data; sample complexity scales unfavorably with module count (Fig. A3);
amortized inference (Zhmoginov 2022) suggested for scaling; overparameterization effects unclear outside the
teacher–student setting; **no guarantee that gradient descent reaches the modular global optimum**, with
Jarvis et al. (2023) cited as a first step on learning dynamics, and the open question of "why even modular
architectures often collapse to monolithic solutions".

**Appendix A — Theoretical result.** A.1 single-task parameter identification for ReLU MLPs (Definition A.1
irreducibility; Theorem 3; Theorem 4 for `ĥ ≥ h`; A.1.2 the ReLU irreducibility condition and the
positively-colinear-weight fusion pathology). A.2 multi-task parameter identification (A.2.1 ReLU MLP:
Theorem 5, Lemma 6, Corollary 6.1; A.2.2 infinitely differentiable activations: Theorem 7 restating Simsek
et al. 2021, Theorem 8). A.3 example failure cases to build intuition. A.4 compositional generalization:
Theorem 9 with the finite-task-sample clause Eq. 62 and supporting Lemma 10.

**Appendix B — Additional experiments.** B.1 multi-task teacher-student: OOD loss mirrors identification
degradation under overparameterization (Fig. A2); weight decay does not improve alignment (Table A1). B.2
hyperteacher: sample complexity vs number of tasks (Fig. A3); sensitivity to finite train shots, `N = 256`
default (Fig. A4); sensitivity to held-out fraction; full accuracy tables A2–A8 across `M ∈ {4,8}`,
`K ∈ {1,2,4,8}`; training curves (Fig. A7). B.3 compositional preferences: overparameterization has no
negative effect within tested range (Fig. A8). B.4 compositional goals: exact-optimal-path metric (Fig. A9);
overparameterization stable (Fig. A10).

**Appendix C — Experimental details.** C.1 multi-task teacher-student (data generation, student model,
training/evaluation, experiments, hyperparameters; Table A9 task distributions). C.2 hyperteacher (Table A10
grid search). C.3 compositional preferences — full environment spec, exact optimal `Q` with discount 0.9 and
horizon 8, MSE inner and outer loss, 32 instances per task split 16/16, connected vs disconnected mask
constructions chosen to equalise task counts, Table A11. C.4 compositional goals — 11×11 mazes, 200 goals,
25 % held out with every factor still covered, cross-entropy against the optimal action, one optimal-trajectory
demonstration per support/query instance, `B_outer = 128`, `B_inner = 256`, `N_outer = 200000`, AdamW, outer
weight decay 0.001 / inner 0.0001, inner steps 10 (ANIL 100), Table A12 grid over outer lr {0.001,0.003},
inner lr {0.1,0.3} (ANIL/MAML {0.01,0.03}), grad clip {1,2}.

**Appendix D — Meta-learning models.** D.1 MAML (all parameters are fast; `θ = φ₀`; truncated-normal `1/√H`
init, zero biases). D.2 ANIL (only readout is fast; same init). D.3 linear hypernetwork (NTK-parameterized
ReLU MLP base with `1/√H` pre-activation rescaling; unit-norm embedding; linear map to flattened weights;
biases not generated; three hypernetworks / three embeddings for first, hidden and last layers; hypernetwork
weights truncated-normal std `1/√M` with `M` the embedding dimension; embeddings uniform unit variance).
D.4 nonlinear hypernetwork (4-layer ELU MLP generator with LayerNorm before every activation and on the input;
truncated-normal `1/√H` init).

**Appendix E — Extended related work.** Connectionist compositionality debate (Rumelhart & McClelland 1986;
Fodor & Pylyshyn 1988; Smolensky 1991; Hadley 1994; Phillips 1995) and the benchmark literature.

**Appendix F — Additional details.** F.1 compute resources. F.2 software and libraries.

---
---
