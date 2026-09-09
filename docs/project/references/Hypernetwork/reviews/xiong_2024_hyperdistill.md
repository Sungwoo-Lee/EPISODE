---
title: "Distilling Morphology-Conditioned Hypernetworks (HyperDistill)"
slug: xiong_2024_hyperdistill
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_theory.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

# 4. Xiong et al. 2024 — HyperDistill: Distilling Morphology-Conditioned Hypernetworks

**Full title as printed:** *Distilling Morphology-Conditioned Hypernetworks for Efficient Universal
Morphology Control*
**PDF:** `docs/project/references/Hypernetwork/sources/Xiong et al. 2024 - Distilling morphology-conditioned hypernetworks (HyperDistill).pdf`
**Authors:** Zheng Xiong¹, Risto Vuorio¹, Jacob Beck¹, Matthieu Zimmer², Kun Shao², Shimon Whiteson¹ —
¹Department of Computer Science, University of Oxford, UK; ²Huawei Noah's Ark Lab, London, UK.
**Venue as printed:** page-1 footer — *"Proceedings of the 41ˢᵗ International Conference on Machine Learning,
Vienna, Austria. PMLR 235, 2024."*
**Code:** `https://github.com/MasterXiong/Universal-Morphology-Control`
**Note:** shares two authors (Xiong, Beck, Vuorio, Whiteson) with paper #3 — same Oxford group.

---

## Phase 1 — Foundational overview

### Introduction

**Universal morphology control** means one policy that can drive *many differently-shaped robots* — a
two-legged one, a six-legged one, one with an extra arm — including shapes it has never seen. The task
context here is the robot's own body: its limb topology tree and each limb's physical parameters.

The state of the art uses transformers, which treat each limb as a token and are expensive to run. A plain
MLP is cheap but performs badly across many robots. This paper proposes **HyperDistill**: a hypernetwork
reads the robot's morphology once, writes out a small MLP tailored to that robot, and then **the hypernetwork
is thrown away** — the robot runs the little MLP forever after.

**This is exactly the question the project cares about: can a plain MLP absorb what the hypernetwork
learned?** And this paper gives an unusually clean answer, because the deployed artifact literally *is* a
plain MLP.

### Key findings

- **Yes, for one robot — decisively.** HyperDistill matches the transformer teacher's return on both training
  and unseen test robots while the deployed policy is **6–14× smaller** and needs **67–160× fewer
  floating-point operations** per step.
- **No, across robots.** A single multi-robot MLP with **exactly the same architecture** as HyperDistill's
  generated MLP, but with the morphology context concatenated to its input instead of generating its weights,
  is *"significantly"* outperformed — and the gap is much larger on unseen robots than on training ones. So
  the hypernetwork is not redundant; it is where the *cross-robot* knowledge lives.
- **The explanatory idea is "knowledge decoupling".** A universal policy carries two kinds of knowledge:
  *inter-task* (how to generalize across robots) and *intra-task* (how to drive this particular robot). A
  transformer or MLP must store both in one parameter set; a hypernetwork puts the first in the generator and
  the second in the generated network, so only the second has to be present at run time.
- **Training the hypernetwork with RL directly fails.** The HN-RL baseline *"performs poorly on both training
  and test robots"*. The whole method depends on replacing RL with supervised behaviour cloning from a
  pre-trained teacher.
- **Attention turns out to be dispensable.** Once knowledge is decoupled, the authors note *"we may not need
  complicated attention modules to achieve good performance for universal morphology control"* — a compact
  generated MLP beats compressed transformers of matched size.

### Initial takeaway

**The honest answer to "was the modulation optimisation scaffolding or representational capacity?" is
"neither, exactly — it was a place to put the task-conditional part of the function".** A plain MLP fully
absorbs the per-task computation; what it cannot absorb is the *mapping from task to computation*. And note
the direction is the reverse of the usual scaffolding story: here the hypernetwork **makes optimisation
harder, not easier** — it could not be trained by RL at all and had to be handed a supervised target. Anyone
citing this as "hypernetworks are just optimisation scaffolding" would be citing it backwards.

---

## Phase 2 — Graduate-level deep dive

### 2.1 Problem formulation

Universal morphology control is a **contextual MDP** (Hallak et al. 2015) with context space `C` over
morphology configurations. For robot `k`: `S_k`, `A_k`, `T_k`, `R_k`. Robots come from a **modular design
space** — a morphology tree over limb nodes with homogeneous node-level state and action spaces:

$$S_k = S_k^1 \times \cdots \times S_k^{N_k}, \qquad A_k = A_k^1 \times \cdots \times A_k^{N_k}$$

with `N_k` the limb count. The context `c_k` comprises node-wise features `{c_k^i}` plus the topology tree.
Objective over `K` training robots:

$$\max_\theta\ \Big[\tfrac{1}{K}\sum_{k=1}^{K}\sum_{t=0}^{H} r_{k,t}\Big]$$

with zero-shot generalization to unseen morphologies also required.

**Context features (Appendix A):** per limb — initial position relative to parent; initial geometric
orientation relative to parent; mass and shape parameters; joint parameters (type, range, axis, motor gear).
**One transformation matters:** relative position is replaced by **absolute** position (computed by walking
the tree from the torso), because symmetric limbs can share a relative position while playing different roles.
Figure 7 (left) shows this transformation *"plays an important role in improving performance."*

### 2.2 The baseline architectures and their stated limitations

**Multi-robot MLP.** Limbs ordered by tree traversal (depth-first), zero-padded to `N_max`, context
concatenated per node: `x = [x¹, …, x^{N_k}, 0⃗, …, 0⃗]` with `xⁱ = [sⁱ, cⁱ]`.

$$h^{(0)} = \sigma\big(W^{\text{in}} x + b^{\text{in}}\big) = \sigma\Big(\sum_{i=1}^{N_k} W_i^{\text{in}} x^i + b^{\text{in}}\Big),
\quad h^{(l+1)} = \sigma\big(W^{(l)}h^{(l)} + b^{(l)}\big), \quad a^i = W_i^{\text{out}} h^{(L)} + b_i^{\text{out}}$$

**This is precisely the concatenation baseline**, and its architecture is set *identical* to HyperDistill's
generated base MLP (Appendix B.3). That makes the comparison a genuine matched-architecture
hypernetwork-vs-concatenation contrast — rare, and the most directly relevant thing in this paper for the
project's standing question.

**Two stated limitations:**

1. **Knowledge decoupling.** *"Since both TF and MLP use a single set of parameters to encode both kinds of
   knowledge, they cannot decouple them from each other."* Hence redundant knowledge at inference; hence a
   compact MLP that suffices for one robot cannot hold both inter- and intra-task knowledge for many.
2. **Order-invariance (MLP only).** A transformer is order-invariant since all limbs share parameters. In a
   multi-robot MLP *"only the limbs with the same index across different robots share the same subset of
   parameters in the input and output layers, so how we order the limbs influences the policy output"* —
   with no consistent cross-morphology ordering available, the MLP can overfit to spurious index patterns.

### 2.3 The HyperDistill architecture — what generates what, exactly

A hypernetwork is decomposed into a **context encoder** `f` and **linear output heads**. For a target layer
`y = Wx + b`, `W = HN_W(e)`, `b = HN_b(e)` with `e = f(c)`. If `W` is `M × N` and the embedding dimension is
`E`, then `HN_W` is a linear layer of input dimension `E` and output dimension `M × N`.

The specific difficulty: the base MLP's input and output dimensions **vary across robots**. Solution —
**generate limb-wise parameter blocks**, each of fixed dimension under the modular assumption.

**Input layer** (per-limb embedding `e_i = f(c_i)`):

$$h^{(0)} = \sigma\Big(\sum_i W_i^{\text{in}} x^i + b_i^{\text{in}}\Big), \qquad
W_i^{\text{in}} = \text{HN}_W^{\text{in}}(e_i), \quad b_i^{\text{in}} = \text{HN}_b^{\text{in}}(e_i)$$

**Output layer** (also per-limb):

$$a^i = W_i^{\text{out}} h^{(L)} + b_i^{\text{out}}, \qquad
W_i^{\text{out}} = \text{HN}_W^{\text{out}}(e_i), \quad b_i^{\text{out}} = \text{HN}_b^{\text{out}}(e_i)$$

**Hidden layers** (mean-pooled morphology-level embedding `e_m = (1/N) Σ_i e_i`):

$$h^{(l+1)} = \sigma\big(W^{(l)}h^{(l)} + b^{(l)}\big), \qquad
W^{(l)} = \text{HN}_W^{(l)}(e_m), \quad b^{(l)} = \text{HN}_b^{(l)}(e_m)$$

**Two consequences the paper draws out explicitly:**

- **Concatenation is eliminated.** *"As the whole policy conditions on the morphology context through HN, we
  no longer need to concatenate context features `c_i` to the network input, so we have `x_i = s_i`."* The
  generated policy sees state only; all context enters through the weights.
- **Order-invariance is restored.** *"the parameters associated with each limb no longer depend on the limb
  index, but only condition on the limb's context representation."*

**Context encoder = a transformer.** Chosen because a limb's own features may be insufficient to distinguish
it from an identically-configured limb on a different robot; a TF encoder enriches each limb's representation
by attending to the rest of the morphology. Critically: *"Since the TF context encoder is also a part of the
HN, it is not needed at inference time, unlike a TF policy that uses TF as the controller."* Ablation
(Figures 7 right, 8): GNN encoder is worst (attributed to over-smoothing); MLP encoder is *"quite good"* on
flat terrain; TF encoder wins on the two harder environments.

**Capacity spectrum: rung 4 — full weight generation**, of *every* weight and bias of the base MLP, with the
generation structurally factored (per-limb for input/output layers, mean-pooled for hidden layers). The
conditioning signal is **static per robot** — this is the key structural difference from paper #3, where
weights are regenerated every timestep from a recurrent state, and it is what makes discarding the generator
possible.

### 2.4 Training via policy distillation — and the RL failure that forces it

**Why not RL?** Stated plainly: *"In principle, we can train a universal HN policy from scratch via RL.
However, empirically we find that the training process is unstable and the learned policy significantly
underperforms a TF policy, possibly because both HN and RL are known to be unstable during learning, and
combining them together further exacerbates the optimization challenges."* The **HN-RL** baseline in
Figures 2–3 *"performs poorly on both training and test robots, which reflects the optimization difficulty of
combining HN and RL, and validates the importance of training via PD."*

**The method.** Train a universal TF teacher `π_T` by RL; collect expert trajectories into `B_T`; train the HN
student by minimising the KL divergence between teacher and student action distributions on transitions
sampled from the buffer:

$$\mathcal{L}_\pi = \mathbb{E}_{s,c\sim B_T}\Big[\text{KL}\big(\pi_T(a|s,c)\,\big\|\,\pi(a|s,c)\big)\Big]$$

Plain behaviour cloning, no online student rollouts: *"empirically we find that this simple BC loss is
sufficient to learn a student policy that matches the teacher's performance on the training robots, without
having to collect further samples with the student."*

**Four factors identified as governing the teacher→student generalization gap** (the paper's secondary
contribution, and it claims to be first to study this systematically):
1. **Choice of teacher(s)** — one universal TF vs many single-robot MLPs.
2. **Student–teacher architecture alignment.**
3. **Number of PD robots** (robots used to collect distillation data — distinct from the robots the *teacher*
   was trained on).
4. **Regularization in task space** — dropout applied to the context embeddings `e_i` and `e_m`, motivated by
   the observation that *"we only have a few hundred different robots for PD, which is much less than the
   number of parameters in the HN, there is a high chance of overfitting."* Framed as encouraging an
   *ensemble* of MLP policies that all work on the same robot, and as domain randomization over morphology
   context.

### 2.5 Experimental setup

**Benchmark:** UNIMAL (Gupta et al. 2021) on MuJoCo — **100 training robots and 100 test robots**, three
environments of increasing difficulty: **Flat Terrain (FT)**, **Variable Terrain (VT)** (terrain reset each
episode), **Obstacle** (flat terrain with randomly positioned obstacles).

**Teacher:** **ModuMorph** (Xiong et al. 2023), the prior SOTA, trained on the 100 training robots. ModuMorph
differs from a standard TF in two ways: attention weights are **fixed and conditioned only on morphology
context** rather than computed from limb observations; and its embedding layer and MLP decoder are themselves
**HN-generated**. The paper is careful about the distinction: *"ModuMorph adopts HNs to better model the
diverse behaviors across limbs, but is still a large TF-based model with high inference costs. By contrast,
HyperDistill utilizes HNs to enable knowledge decoupling for efficient inference."*
**The RL algorithm used to train the teacher is not named anywhere in this PDF** — it is inherited from the
ModuMorph / UNIMAL setup. The student is trained by **supervised behaviour cloning**, not RL.

**Distillation data:** the 100 training robots are mutated (1–3 mutation steps, 9 variants each) into
**1,000 PD robots**; **8,000 transitions per PD robot** → an **8 M-transition** dataset.

**Distillation:** 150 epochs, mini-batch 5120, Adam at learning rate 3e-4, **gradient-norm clipping at 0.5**,
context-embedding dropout `p = 0.1`, **three random seeds** per method per environment, mean ± standard error.

**Baselines (all as students):** ModuMorph (oracle) — same architecture as the teacher, an upper bound with no
architecture misalignment; TF (compressed) — standard TF with parameter count matched to HyperDistill's base
MLP; ModuMorph (compressed) — matched size but with HN-generated layers; **Multi-robot MLP** — architecture
identical to HyperDistill's base MLP, context concatenated to input; and **HN-RL** — the hypernetwork trained
by RL instead of distillation.

### 2.6 The distillation result — head-to-head numbers

**Efficiency (Table 1, page 7).** "Rel." is relative to HyperDistill.

| Env | Method | Model size (abs.) | Rel. | FLOPs (abs.) | Rel. |
|---|---|---|---|---|---|
| **FT** | ModuMorph (oracle) | 1.73 M | 14.0× | 39.86 M | 160.8× |
| | TF (compressed) | 0.14 M | 1.1× | 3.39 M | 13.7× |
| | ModuMorph (compressed) | 0.15 M | 1.2× | 1.78 M | 7.2× |
| | Multi-robot MLP | 0.23 M | 1.9× | 0.46 M | 1.9× |
| | **HyperDistill** | **0.12 M** | **1** | **0.25 M** | **1** |
| **VT** | ModuMorph (oracle) | 1.97 M | 6.6× | 40.33 M | 67.2× |
| | TF (compressed) | 0.31 M | 1.0× | 5.51 M | 9.2× |
| | ModuMorph (compressed) | 0.39 M | 1.3× | 2.26 M | 3.8× |
| | Multi-robot MLP | 0.41 M | 1.4× | 0.82 M | 1.4× |
| | **HyperDistill** | **0.30 M** | **1** | **0.60 M** | **1** |
| **Obstacle** | ModuMorph (oracle) | 2.02 M | 6.7× | 40.43 M | 67.4× |
| | TF (compressed) | 0.32 M | 1.0× | 5.61 M | 9.3× |
| | ModuMorph (compressed) | 0.44 M | 1.5× | 2.35 M | 3.9× |
| | Multi-robot MLP | 0.41 M | 1.4× | 0.82 M | 1.4× |
| | **HyperDistill** | **0.30 M** | **1** | **0.60 M** | **1** |

FLOPs computed as `2 × M × N` per linear layer (Hobbhahn & Sevilla 2021), omitting activations and layer
norms as negligible. Efficiency gains are largest on FT because VT and Obstacle add a high-dimensional
terrain input requiring a large MLP encoder shared by every method, adding a constant to all rows (Appendix
C.1).

**The one-time generation cost, which the headline ratio omits.** Appendix C.1: *"generating the base MLP with
HN takes 43M FLOPs in the FT environment, and 65M FLOPs in the VT and Obstacle environment. The FLOPs of
generating the base MLP with HN is just slightly larger than the FLOPs of a single inference step with a
universal TF controller."* So generation costs about **one transformer forward pass**, amortised over every
subsequent step on that robot. The 160× figure is therefore an asymptotic per-step number, honestly derived
but worth stating with its amortisation assumption attached.

**Performance (Figures 2 and 3 — curves, no numeric table).** Quoting the paper's own summary sentences:

| Comparison | Reported outcome |
|---|---|
| HyperDistill vs ModuMorph (oracle) and the teacher | *"HyperDistill achieves performance similar to ModuMorph (oracle), matching the teacher's performance on both the training and test robots in all the three environments, while reducing model size by 6-14 times, FLOPs by 67-160 times"* |
| HyperDistill vs **TF (compressed)** | *"TF (compressed) cannot match the performance of HyperDistill in all the three environments, as standard TF needs to trade off between performance and efficiency due to a lack of knowledge decoupling"* |
| ModuMorph (compressed) vs TF (compressed) | ModuMorph (compressed) *"consistently outperforms"* it — attributed to its HN-generated layers |
| HyperDistill vs ModuMorph (compressed) | ModuMorph (compressed) *"still lags behind HyperDistill w.r.t. both generalization performance and efficiency, as the knowledge encoded in the attention blocks still cannot be decoupled."* Gap larger in FT than VT/Obstacle, because in the latter ModuMorph has more HN-generated decoder layers, making it more HyperDistill-like |
| **HyperDistill vs Multi-robot MLP (= concatenation, matched architecture)** | *"HyperDistill also significantly outperforms multi-robot MLP, which validates the importance of the HN. Moreover, the performance gap between multi-robot MLP and other methods is much larger on the test robots than on the training ones, which may be overfitting due to the order-invariance issue"* |
| HyperDistill vs **HN-RL** | *"HN-RL performs poorly on both training and test robots"* |

**Caveat: no numeric returns are printed for Figures 2 and 3.** The only returns stated numerically anywhere
are the discussion's proof-of-concept (§2.8 below) and the percentage improvements in the ablations.

### 2.7 The ablations — with the numbers that are stated

Run for 50 epochs (most methods converge within that), FT only unless noted.

**Choice of PD teacher (Figure 4).** Universal TF teacher vs a set of single-robot MLP teachers; 80,000
transitions per training robot; tested with both HyperDistill and TF (oracle) students. *"when using
single-robot MLP teachers, although the student policies perform well on the training robots, they generalize
much worse than the students distilled from a universal TF teacher."* The rationale offered: separately
RL-trained single-robot teachers *"can be dramatically different from each other, which may exacerbate the
discontinuity of the distilled policy in the parameter space."*

**Architecture alignment — the cleanest inference in the paper.** Reading Figure 4 the other way: with a
universal **TF** teacher, the **TF student** generalizes better than HyperDistill; with **single-robot MLP**
teachers, **HyperDistill** (whose base MLP matches the teachers' architecture) generalizes better than the TF
student. And decisively: *"for the same teacher, both students achieve similar performance on the training
robots regardless of their architectures, indicating that the generalization gap is not caused by the
difference in model capacity of different student models, but is more likely the consequence of architecture
misalignment."* **Note what this concedes: HyperDistill is not the best-generalizing student available — the
architecture-matched TF student is. HyperDistill's claim is the best performance/efficiency trade-off, not the
best performance.**

**Number of PD robots (Figure 5).** 100 / 500 / 1,000 PD robots, with per-robot transitions scaled down so
total data is constant. *"HyperDistill's generalization performance increases by **6%, 15% and 13%** in the
three environments as the number of PD robots increases from 100 to 1,000. There is no significant improvement
in the TF student's generalization performance due to a ceiling effect and its better aligned architecture."*
Note this is free: it requires no change to teacher training, only more rollouts from the existing teacher.

**Task-space regularization (Figure 6).** *"applying dropout to the context embedding improves generalization
performance by **8.5%**, while applying dropout to the base MLP does not provide significant improvement,
which agrees with our intuition that regularization may be more important in task space than in state
space."* This is a hypernetwork-specific finding: regularise the **code**, not the generated network.

**Context representation (Figures 7, 8, Appendix C.2).** Absolute-position feature transformation matters;
GNN encoder worst (over-smoothing); MLP encoder adequate on FT; TF encoder better on VT and Obstacle.

### 2.8 Can a plain MLP absorb what the hypernetwork learned? — the precise answer

This is the paper's most valuable content for the project, and it needs three separate statements because a
one-word answer is wrong in both directions.

**(1) For a single robot: yes, completely.** The deployed artifact is literally a plain MLP — hidden size 256,
depth grid-searched to the smallest that matches the teacher (Appendix B.3) — with **0.12 M parameters and
0.25 M FLOPs per step**, matching a 1.73 M-parameter / 39.86 M-FLOP transformer's return on both training and
unseen robots. The hypernetwork, including its transformer context encoder, is **discarded after generation**.
Whatever the transformer's attention was computing per-limb, an MLP of 1/14 the size reproduces it. The
authors draw the conclusion themselves: *"we may not need complicated attention modules to achieve good
performance for universal morphology control."*

**(2) Across robots: no.** The multi-robot MLP — *identical architecture*, context concatenated instead of
generated — is *"significantly"* worse, and disproportionately so on unseen robots. So the thing an MLP cannot
absorb is not the per-robot control function but **the mapping from morphology to control function**. Two
mechanisms are offered: lack of knowledge decoupling (one parameter set must hold both), and loss of
order-invariance (a concatenating MLP ties limb roles to limb indices).

**(3) Supporting evidence from a targeted experiment (§5 Discussion).** If the story is right, then
compressing a universal TF into a **single-robot** TF should beat compressing it into a universal one, since
the former is relieved of carrying inter-task knowledge. Tested on Obstacle over 10 randomly sampled training
robots: compressed **single-robot** TFs average return **2345**, compressed **universal** TF averages
**2115** — *"but at the cost of losing the generalization ability to other robots."* This is the only
direct numeric return comparison in the paper and it supports the capacity-allocation account.

**So: scaffolding or capacity?** Neither label fits cleanly, and the paper's evidence points somewhere more
specific:

- **Not extra representational capacity at inference.** The final function on any given robot is representable
  by a small MLP. The transformer's capacity was, for that robot, redundant.
- **Not optimisation scaffolding either — the opposite.** The HN-RL result shows the hypernetwork makes
  optimisation *harder*: *"both HN and RL are known to be unstable during learning, and combining them
  together further exacerbates the optimization challenges."* It could only be trained by handing it a
  supervised target. **This directly contradicts a "hypernetworks help optimisation" reading**, and contrasts
  with paper #3, where a correctly-initialised recurrent hypernetwork trains fine under PPO. The difference
  between the two is worth noting: paper #3 uses Bias-HyperInit, paper #4 mentions no initialisation scheme
  at all.
- **What it actually is: a container for the task→parameters map.** The hypernetwork's job is to hold the
  *inter-task* function, which no fixed-parameter network of the deployed size can hold alongside the
  intra-task function. Once evaluated at a fixed context, it can be thrown away.

**The practical corollary for the project.** If a modulator's conditioning signal is **static within an
episode/task**, this paper's trick applies: the modulator can be evaluated once and folded into the policy
weights, buying inference efficiency at zero performance cost. If the signal **changes within an episode** —
which is the case for an interoceptive modulator that tracks a fluctuating internal state — **the trick does
not apply**, and the paper says so in its own limitations: *"if task context changes over time, such as
controlling a robot to solve different tasks by following language instructions, the HN can not be discarded
and needs to be called whenever a new instruction is given. This requires additional space to save the HN
parameters, and the inference efficiency gain may decrease as the HN will be called more frequently."*

### 2.9 Training-stability issues and reported fixes

1. **HN + RL is unstable and underperforms** — the paper's central stability finding. **Fix: replace RL with
   supervised policy distillation** from a pre-trained teacher. Note this is a *workaround*, not a repair:
   the underlying instability is never diagnosed or solved.
2. **Overfitting in task space.** The HN has far more parameters than there are distillation robots (a few
   hundred to 1,000). **Fix: dropout on the context embeddings `e_i` and `e_m`, `p = 0.1`** — worth **+8.5 %**
   generalization; dropout on the base MLP does essentially nothing.
3. **Standard optimisation hygiene:** Adam at 3e-4, **gradient-norm clipping at 0.5**.
4. **Context-representation collapse** — a failure mode named in §3.2: *"if `e_i` of different limbs are too
   similar, the policy will generate similar actions across different limbs, which is unlikely to be a good
   policy."* **Fixes:** discriminative feature transformations (absolute rather than relative position) and a
   transformer context encoder that lets limbs distinguish themselves through interaction.

**No initialization scheme is discussed anywhere in this paper** — no Bias-HyperInit, no fan-in analysis, no
variance-preservation argument. Given that papers #1, #2 and #3 all identify generated-weight scale as the
central stability lever, and that this paper reports HN+RL failing, the omission is conspicuous and worth
flagging as an unexplored explanation for the HN-RL failure.

### 2.10 Relevance and cautions for this project

**Useful.**
- **The matched-architecture hypernetwork-vs-concatenation comparison** is the most directly relevant control
  in these four papers. The multi-robot MLP baseline differs from HyperDistill's generated MLP in *exactly one
  respect* — context as input vs context as weight generator — with depth and width held identical. Very few
  papers isolate that.
- **The "regularise the code, not the network" finding** (+8.5 % from context-embedding dropout, ~0 % from
  base-network dropout) is a cheap and directly transferable design rule for any modulator.
- **The static-vs-dynamic context distinction** is a clean way to reason about when modulator cost is
  amortisable. For an interoceptive modulator it is not, and the paper says why.
- **The HN-RL failure is a real warning** about training a weight-generating modulator end-to-end under RL,
  and — read alongside paper #3 — points at initialisation as the untested difference between success and
  failure here.

**Cautions.**
- **No FiLM baseline.** The comparison ladder here is concatenation vs full weight generation, with nothing in
  between.
- **The student is trained by behaviour cloning, not RL.** The RL is confined to producing the teacher, and
  the algorithm used is not named in this PDF. Do not cite HyperDistill as an RL training result.
- **Figures 2 and 3 carry no numbers.** The only numeric returns are 2345 vs 2115 (10 robots, Obstacle) and
  the percentage ablation deltas.
- **HyperDistill never beats its teacher** — it matches. And by the paper's own Figure 4 analysis, an
  architecture-aligned TF student *generalizes better*. The claim is efficiency, not performance.
- **Three seeds.**
- The 67–160× FLOPs figure is per-step and excludes the one-time 43–65 M-FLOP generation.

---

## Appendix: Section-by-Section Backbone — Xiong et al. 2024

**Abstract.** A universal policy across morphologies improves learning efficiency and enables zero-shot
generalization, but high performance requires transformers with large memory and compute cost versus simpler
MLPs. Proposes HyperDistill: (1) a morphology-conditioned hypernetwork generating robot-wise MLP policies, and
(2) a policy-distillation approach essential for successfully training the HN. On UNIMAL, HyperDistill matches
a universal TF teacher on training and unseen test robots while reducing model size 6–14× and computational
cost 67–160×. Attributes the advantage to **knowledge decoupling** — separating inter-task from intra-task
knowledge — proposed as a general principle.

**1. Introduction.** RL for robotic control has progressed but generalization across robots remains hard;
policies transfer poorly across morphologies and per-robot training is sample-inefficient. Universal
morphology control as multi-task RL. MLPs suffice per robot but generalize poorly; GNNs and TFs outperform
them but cost more at deployment.

**2. Background.**
- **2.1 Problem formulation.** Contextual MDP; modular design space; factorised state/action spaces; context
  `c_k` = node-wise features + topology tree; average-return objective plus zero-shot generalization.
- **2.2 Architectures for universal morphology control.** Limb ordering by tree traversal; zero-padding to
  `N_max`; context concatenated per node; the MLP forward equations; GNN and TF handle variable limb counts
  natively, TF treating each limb as a token processed in parallel; typical TF = linear embedding + attention
  blocks + MLP decoder.
- **2.3 Hypernetworks.** Definition; decomposition into context encoder `f` and linear output heads; the
  `E → M×N` head-size accounting.

**3. HyperDistill.**
- **3.1 Limitations of existing architectures.** *Knowledge decoupling*: TF and MLP encode inter- and
  intra-task knowledge in one parameter set, so inference carries redundant knowledge and a compact MLP cannot
  hold both; the same holds when compressing a large TF. *Order-invariance*: TF is order-invariant, multi-robot
  MLP is not, so it can overfit to a spurious limb indexing.
- **3.2 HyperDistill architecture.** HN generates a per-robot MLP; the expensive HN is called once and the
  small base network runs thereafter; the generated MLP is order-invariant. Limb-wise generation for input and
  output layers from per-limb embeddings `e_i`; mean-pooled `e_m` for hidden layers; context concatenation
  removed (`x_i = s_i`). *Context representation learning*: embeddings must be discriminative and
  generalizable; achieved by feature transformations and a TF context encoder, which is discarded at inference.
- **3.3 HyperDistill training via policy distillation.** HN + RL is unstable and underperforms; distillation
  replaces RL with supervised learning and allows teacher reuse across algorithmic comparisons. KL behaviour-
  cloning loss; simple BC suffices without online student data. Four factors influencing the teacher–student
  generalization gap: choice of teacher(s); student–teacher architecture alignment; number of PD robots
  (distinguished from training robots); regularization in task space via dropout on `e_i` and `e_m`, framed as
  ensembling and as domain randomization.

**4. Experiments.**
- **4.1 Experimental setup.** UNIMAL on MuJoCo, 100 train + 100 test robots, environments FT / VT / Obstacle.
  Teacher: ModuMorph (fixed context-conditioned attention; HN-generated embedding and decoder), with the
  motivational distinction from HyperDistill stated. Data: 1,000 PD robots by mutation, 8,000 transitions each
  = 8 M transitions. Baselines: ModuMorph (oracle), TF (compressed), ModuMorph (compressed), Multi-robot MLP,
  HN-RL. Distillation: 150 epochs, batch 5120, Adam 3e-4, grad-norm clip 0.5, context dropout 0.1, 3 seeds.
- **4.2 Main results.** Figures 2–3 (train / test learning curves) and Table 1 (size and FLOPs). HyperDistill
  matches the oracle and teacher at 6–14× smaller and 67–160× fewer FLOPs; TF (compressed) cannot match it;
  ModuMorph (compressed) beats TF (compressed) but lags HyperDistill; HyperDistill significantly outperforms
  multi-robot MLP with a larger gap on test robots; HN-RL performs poorly. Remark that complicated attention
  modules may not be needed.
- **4.3 Ablation studies.** Teacher choice (universal TF ≫ single-robot MLPs for student generalization);
  architecture alignment (TF student better under a TF teacher, HyperDistill better under MLP teachers;
  equal training performance implicates misalignment rather than capacity); number of PD robots (100→1,000
  gives +6 %/+15 %/+13 % for HyperDistill, no significant change for the TF student); task-space
  regularization (context dropout +8.5 %, base-MLP dropout negligible).

**5. Discussion.** Re-examines the knowledge-decoupling hypothesis against results: efficiency benefit
confirmed; compressed universal TF underperforms as predicted; proof-of-concept on Obstacle over 10 robots —
compressed single-robot TFs average **2345** vs compressed universal TF **2115**, at the cost of
generalization. Relates the idea to mixtures-of-experts (Riquelme 2021; Shen 2023) and to sparse neural
activation in the brain (Barth & Poulet 2012). Proposes knowledge decoupling as a general inference-efficiency
principle.

**6. Related work.** *Universal morphology control* — MLP with zero-padding is outperformed by GNN and TF;
TF outperforms GNN by modelling distant-limb interactions; ModuMorph also uses HNs but only for embedding and
decoder layers inside a TF and for a different motivation. *Hypernetworks* — Ha 2016; in RL they model the
dependency between task context and optimal policy (Galanti & Wolf 2020; Sarafian 2021) and are widely used in
multi-task and meta-RL (Yu 2019; Peng 2021; Beck 2022; Rezaei-Shoshtari 2022; Beck 2023); prior work exploits
expressive power, this work exploits knowledge decoupling for efficiency. *Policy distillation* — used for
compression, acceleration and facilitation; little attention to the teacher–student *generalization* gap;
closest is Furuta et al. 2022 (single-robot MLP teachers → TF student) which does not compare against a
universal teacher and leaves a deployment-efficiency problem.

**7. Conclusion.** HyperDistill achieves both performance and inference efficiency; training via RL is hard so
distillation is used; key PD algorithmic choices systematically investigated. **Limitation named:** the
efficiency gain depends on the context being static, so the HN can be discarded; if context changes over time
(e.g. language instructions) the HN must be retained and called repeatedly, reducing the gain.

**Appendix A — Morphology context features and transformations.** Per-limb features (relative position,
relative orientation, mass and shape, joint type/range/axis/motor gear); the relative→absolute position
transformation and its motivation (symmetric limbs share relative positions).

**Appendix B — Further experimental setup.** B.1 PD-robot generation (1–3 mutation steps, 9 variants per
training robot → 1,000). B.2 FLOPs computation (`2MN` per linear layer; non-linear ops omitted as negligible).
B.3 architecture details (base MLP hidden size fixed at 256, depth grid-searched to the smallest matching the
teacher; multi-robot MLP set identical to it; compressed TFs tuned in attention layers, heads and inner
dimension to match parameter count; token embedding dimension 128 throughout); Table 2 model sizes.

**Appendix C — Further results and analysis.** C.1 inference efficiency (efficiency ratio smaller in VT and
Obstacle due to a shared large terrain encoder; multi-robot MLP slightly larger than the base MLP because it
must concatenate context features; **HN generation costs 43 M FLOPs on FT and 65 M on VT/Obstacle, roughly one
universal-TF forward pass**). C.2 context representation ablations (feature transformation important; GNN
encoder worst due to over-smoothing; MLP encoder good on FT; TF encoder better on VT and Obstacle, Figure 8).

---

## Cross-paper closing note

Read as a set, the four papers place the project's FiLM modulator on a ladder whose rungs are now
well-characterised, and they agree on three things that no single one of them states alone:

1. **The code dimension and the modulation capacity are independent.** Attention's latent code is `H ≈ 8–16`
   numbers, smaller than a FiLM code, but it indexes a matrix basis rather than a diagonal rescaling
   (paper #1). Schug 2024's identifiability argument turns on full-matrix composition and **does not transfer
   to FiLM**.
2. **Initialisation and code normalisation are the dominant source of variance in published
   hypernetwork-vs-baseline numbers.** Every paper here that trains a generator addresses it — RMSHead
   (#1), unit-norm codes + fan-in-correct init + NTK parameterisation (#2), Bias-HyperInit (#3) — and the one
   that does **not** mention initialisation at all (#4) is the one that reports its hypernetwork being
   untrainable by RL.
3. **A hypernetwork's advantage is about *where knowledge lives*, not about reaching functions a smaller
   network could not represent.** Paper #4 demonstrates the deployed function is MLP-representable; paper #2
   proves that what is really being learned is a module library plus a task→code map; paper #3 shows a large
   part of a measured architecture gain was input plumbing. **The pre-registered control this implies for any
   project experiment: match the inputs, match the initialisation, and only then attribute the residual to the
   architecture.**
