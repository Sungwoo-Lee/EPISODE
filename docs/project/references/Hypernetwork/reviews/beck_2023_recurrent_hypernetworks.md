---
title: "Recurrent Hypernetworks are Surprisingly Strong in Meta-RL"
slug: beck_2023_recurrent_hypernetworks
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_theory.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

# 3. Beck et al. 2023 — Recurrent Hypernetworks are Surprisingly Strong in Meta-RL

**PDF:** `docs/project/references/Hypernetwork/sources/Beck et al. 2023 - Recurrent hypernetworks are surprisingly strong in meta-RL.pdf`
**Authors:** Jacob Beck, Risto Vuorio, Zheng Xiong, Shimon Whiteson — all Department of Computer Science,
University of Oxford.
**Venue as printed:** page-1 footer — *"37th Conference on Neural Information Processing Systems
(NeurIPS 2023)."* Margin stamp: `arXiv:2309.14970v4 [cs.LG] 26 Dec 2023`.
**Code:** `https://github.com/jacooba/hyper`

---

## 0. This is a DIFFERENT paper from the one already in the corpus — confirmed from the PDFs

The library already holds `Beck et al. 2023 - Hypernetworks in Meta-Reinforcement Learning.pdf`. **They are
distinct papers.** Verified directly from both PDFs:

| | **Already held** | **This paper (new)** |
|---|---|---|
| Title | *Hypernetworks in Meta-Reinforcement Learning* | *Recurrent Hypernetworks are Surprisingly Strong in Meta-RL* |
| Authors | Jacob Beck, **Matthew Jackson**, Risto Vuorio, Shimon Whiteson | Jacob Beck, Risto Vuorio, **Zheng Xiong**, Shimon Whiteson |
| Venue as printed in the PDF | page-1 footer: *"6th Conference on Robot Learning (CoRL 2022), Auckland, New Zealand."* | page-1 footer: *"37th Conference on Neural Information Processing Systems (NeurIPS 2023)."* |
| arXiv | 2210.11348 (per the corpus filename convention) | **2309.14970v4**, 26 Dec 2023 |
| Central question | **Does hypernetwork initialization matter in meta-RL, and what is the right scheme?** | **Is a plain recurrent hypernetwork competitive with specialised meta-RL methods?** |
| Contribution | Proposes **Bias-HyperInit**; shows naive init yields poor performance; benchmarks architectures | Uses Bias-HyperInit **as a given**; runs a much larger baseline comparison against four task-inference methods with equal tuning compute |
| **Contains a FiLM baseline?** | **Yes** — FiLM is an explicit arm in Table 2 | **No — the word "FiLM" does not appear anywhere in this paper** |
| Relationship | cited by the new paper as `Beck et al. [2022]` throughout | supersedes the earlier paper's single-environment RNN+HN result |

The new paper describes the old one as: *"In meta-RL, only Beck et al. [2022] have investigated training a
hypernetwork end-to-end to arbitrarily modify the weights of a policy… However, their study shows a
task-inference method to be superior, and the recurrent hypernetwork is evaluated only on a single task with
results that are statistically insignificant."* The new paper then **overturns that conclusion** on the same
benchmark (see §2.7).

**Note on the corpus filename.** Both PDFs are filed under "Beck et al. 2023", but the older one prints
**CoRL 2022** on its own footer. The existing master review's footnote ᶠ¹ flags this; the PDF settles it —
the older paper's venue is CoRL 2022.

### ⚠ Correction to a number circulating in the project's digests

While confirming the distinction, I re-read Table 2 of the **older** (CoRL 2022) paper with
coordinate-preserving extraction, because the existing `digest_hypernet.md` calls it *"the single most
decisive number in the whole corpus"*. **The table has been misread.** Its true layout:

**Table 2 (Beck et al., CoRL 2022) — meta-test success percentage. Pick-Place ML1 = ten seeds; ML10 = three seeds.**

| Architecture | Init | Pick-Place (VariBAD) | ML10 (VariBAD) | ML10 (RL²) |
|---|---|---|---|---|
| Standard | — | 4.4 ± 2.41 | 10.2 ± 3.0 | 7.2 ± 5.0 |
| **FiLM** | Normc | 5.5 ± 4.8 | — | — |
| **FiLM** | **Bias-HyperInit** | **34.2 ± 15.9** | — | — |
| Hypernetwork | HFI | 25.5 ± 14.5 | 28.4 ± 6.0 | 7.1 ± 2.4 |
| Hypernetwork | **Bias-HyperInit** | **42.9 ± 16.3** | 23.9 ± 6.2 | 14.2 ± 7.2 |

The digest states *"hypernet 42.9 % vs FiLM 25.5 %, both with Bias-HyperInit; 4.4 % vs 5.5 % under default
init"*. Three errors:
1. **25.5 is Hypernetwork + HFI, not FiLM.** FiLM under Bias-HyperInit is **34.2**.
2. So the like-for-like hypernetwork-vs-FiLM gap under the same initialisation is **42.9 vs 34.2 = 8.7 points,
   with error bars of ±16.3 and ±15.9 over ten seeds** — i.e. **not a significant difference**, rather than
   the decisive 17-point gap the digest reports.
3. **4.4 is the Standard architecture** (no modulation at all), not a hypernetwork under default init.

The paper's own summary sentence is consistent with the corrected reading: *"Bias-HyperInit improves the FiLM
architecture and exceeds the performance of HFI."* — it claims FiLM+Bias-HyperInit beats Hypernet+HFI, which
only makes sense if FiLM+Bias-HyperInit is 34.2.

Also note that on the **ML10/VariBAD** column the ordering **reverses**: HFI (28.4 ± 6.0) beats Bias-HyperInit
(23.9 ± 6.2). Quoting only the 10.2 → 23.9 improvement, as the digest does, omits that a different init scheme
scored higher on that same column.

**Recommendation for the parent:** the corrected numbers still support "initialisation dominates architecture
choice" — a 6× swing (5.5 → 34.2) from changing FiLM's initialisation, versus an 8.7-point non-significant
gap from changing the architecture, is arguably a *stronger* version of that thesis. But the specific
"42.9 vs 25.5" figure should not be repeated. I have **not** edited
`Hypernetwork/hypernetwork_lit_review.md` or the digests, per instructions.

---

## Phase 1 — Foundational overview

### Introduction

**Meta-RL** means using slow, sample-hungry reinforcement learning to *learn a fast learner*: after
meta-training on a family of related tasks, the agent should solve a new task from the family within a handful
of episodes. Two camps exist. **Black-box / recurrent** methods just run a recurrent network over the agent's
history and train the whole thing end-to-end on return — simple, but widely believed to be weak.
**Task-inference** methods add machinery that explicitly tries to identify *which* task the agent is in —
auxiliary prediction losses, variational information bottlenecks, pre-training with privileged task labels.

The field's consensus was that the specialised machinery wins. A 2022 study argued the recurrent baseline is
competitive; this paper considers that study's evidence too thin and re-runs the comparison properly, with
**equal hyperparameter-tuning budget for every method** and four task-inference baselines rather than one.

The result: **a recurrent network that emits the policy's weights (rather than feeding a context vector into a
fixed policy) beats every specialised method tested.** The architecture is a plain recurrent hypernetwork —
much simpler than the alternatives — and the paper argues its potential had been missed because nobody had
evaluated it beyond a single environment.

### Key findings

- **RNN+HN wins broadly.** It achieves the best asymptotic return *and* the best sample efficiency on all
  three grid worlds; beats every baseline by a wide margin on two of four MuJoCo domains; ties on a third;
  loses slightly on the fourth (Walker, the hardest task space); and clearly beats the leading task-inference
  method on a visual long-term-memory MineCraft task.
- **The plain RNN without a hypernetwork is a genuinely weak baseline** — on some environments it fails to
  learn at all (Figure 1).
- **Part of the gain is a confound the authors found themselves and controlled for.** A hypernetwork policy
  receives the state *twice*: once through the history that generates the weights, and again as the policy's
  own input. A plain RNN policy sees the state only through the recurrent latent. The **RNN+S** ablation feeds
  the state in twice *without* a hypernetwork — and it recovers a substantial part of the gap. But **not all
  of it**: RNN+HN still matches or beats RNN+S everywhere and beats it on most environments.
- **Initialization is decisive.** With standard Kaiming initialization instead of the hypernetwork-specific
  **Bias-HyperInit**, RNN+HN is among the *worst* methods tested.
- **A mechanistic hypothesis with preliminary evidence.** The two worst-performing models also have the
  largest gradient norm with respect to the trajectory latent. Good methods start with a low norm and lower it
  further during training; the failing plain RNN raises it. The authors suggest low sensitivity to the latent
  is what makes training stable.

### Initial takeaway

This is the one paper of the four that runs actual reinforcement learning, and its practical message is
blunt: **before adopting a specialised conditioning architecture, check whether a simpler one that emits
weights — correctly initialised, and given the raw state as well as the context — already wins.** For this
project it also supplies a control worth copying: any modulator that changes what the policy *sees* as well as
how it computes must be compared against a baseline with the same inputs, or the measured "modulation" gain is
partly an input-plumbing gain.

---

## Phase 2 — Graduate-level deep dive

### 2.1 Problem setting

Standard MDP `(S, A, R, P, γ)`, return `R(τ) = Σ_{r_t ∈ τ} γ^t r_t`. A meta-RL algorithm learns
`f(τ)` mapping data `τ` sampled from a single MDP `M ∼ p(M)` to policy parameters `φ`. Here `τ` is a
**meta-episode** — a trajectory `τ_t ∈ (S × A × R)^t` that may span *multiple* episodes within one MDP. The
policy is `π_θ(a | φ = f_θ(τ))`; `θ` are the **meta-parameters**. The objective:

$$\arg\max_\theta\ \mathbb{E}_{M\sim p(M)}\Big[\mathbb{E}_\tau\big[R(\tau)\,\big|\,\pi_\theta(\cdot|f_\theta(\tau)),\, M\big]\Big] \tag{1}$$

`f_θ` is the **inner loop** (produces `φ`), and the outer loop produces `θ`.

**RL algorithm: PPO.** Not named in a dedicated line, but established by the appendix ("we find 100 **PPO**
updates for training the multi-task policy to be optimal") and by "for all other hyperparameters, we default
to those in Beck et al. [2022]", whose codebase is VariBAD's PPO implementation. Policy-gradient meta-RL
methods (MAML-family) are **excluded** from comparison on the stated grounds that policy-gradient estimation
"requires more data than in our benchmarks".

### 2.2 The two recurrent architectures — what generates what

**RNN (= RL² / L2RL).** `π_θ(a | φ = f_θ(τ))` where `f` is a recurrent network and `π` a feed-forward
network, using **distinct subsets** of `θ`. The recurrent output `φ` is a **context vector consumed as input**
by a fixed-weight policy. The current state reaches the policy **only** through `φ`.

**RNN+HN (the method).** *"the recurrent network produces the weights and biases for the policy directly:
`π_φ(a|s)`."* So:

- **Generator:** a single-layer GRU of width 256, running over the meta-episode `τ`.
- **Conditioning input:** the **full agent history** — states, actions and rewards across the meta-episode —
  summarised recurrently. Not a task label, not a static per-task embedding: it changes **every timestep**.
- **What is emitted:** *"the weights and biases"* of the feed-forward policy `π`, i.e. **all** its parameters.
  Sizes: state embedding 256, then MLP 256 → 128 — the "XL" configuration of Beck et al. 2022.
- **Injection site:** the entire policy network.
- **Crucially:** *"The state must be passed as input again to this policy for the feed-forward policy to
  condition on an input."* This is the structural asymmetry that motivates the RNN+S control.

**Capacity spectrum: rung 4 — full weight generation.** Every weight and bias of the policy MLP is emitted.
This is the maximum-capacity end of the ladder, and — importantly — it is emitted **per timestep from a
recurrent state**, not once per task.

**Bias-HyperInit** (adopted from Beck et al. 2022): *"the hypernetwork's final linear layer is initialized
with a zero weight matrix and a non-zero bias, so that the hypernetwork produces the same base-network
parameters for any trajectory at the start of training."* At initialisation the hypernetwork is therefore
**functionally a constant** — an ordinary policy — and task-dependence has to be learned in. Note the direct
consequence the paper flags: Bias-HyperInit *"ignores trajectories at the start of training"*, which is
exactly why they also test Kaiming as a contrast.

### 2.3 The four task-inference baselines

All are given **equal tuning compute**, with unspecified hyperparameters defaulted to values that *favour* the
task-inference methods.

**TI Naive.** Inner loop additionally predicts the task `ĉ_M` from a known task representation `c_M`, with a
variational information bottleneck:

$$\mu = P^\mu(\text{RNN}(\tau)), \qquad \sigma = P^\sigma(\text{RNN}(\tau)), \qquad \text{IB} = \mathcal{N}(z;\mu,\sigma)$$
$$\hat c_M = P^c(z \sim \text{IB}), \qquad \phi = \text{ReLU}\big(P^{\phi\perp}(\mu,\sigma)\big)$$
$$J_{\text{infer}}(\theta) = \mathbb{E}_M\big[\mathbb{E}_{\tau|\pi}[-\|c_M - \hat c_M\|_2^2]\big]$$
$$J_{\text{prior}}(\theta) = \mathbb{E}_M\big[\mathbb{E}_{\tau|\pi}[D(\text{IB}\,\|\,\mathcal{N}(z;0,I))]\big]$$

`⊥` is a stop-gradient; `D` is KL divergence. `J_infer + J_prior` is the VariBAD evidence lower bound and
trains the bottleneck; `P^φ` and `π(·|φ)` train on Eq. 1. Following Zintgraf et al. 2020, `φ` conditions on
**both `μ` and `σ`**, so the policy sees task *uncertainty* explicitly for exploration.

**TI.** As TI Naive plus a **pre-trained multi-task policy** `π'` learning a task representation `g_θ(c_M)`:

$$\hat g = P^g(z\sim\text{IB}), \qquad
J_{\text{multi}}(\theta) = \mathbb{E}_{M\sim p(M)}\big[\mathbb{E}_\tau[R(\tau)\,|\,\pi'_\theta(\cdot|g_\theta(c_M)), M]\big]$$
$$J_{\text{infer}}(\theta) = \mathbb{E}_M\big[\mathbb{E}_{\tau|\pi(\cdot|\phi)}[-\|g_\theta(c_M) - \hat g\|_2^2]\big]$$

**Pre-training is charged against the meta-RL budget** — total samples held constant. Only ~100 PPO updates
(2.4 % of meta-training frames, 20 % of what fully training `π'` would need) are optimal, which the authors
read as evidence that a good task representation is cheap.

**TI++HN.** TI plus three additions, the first two novel: (1) initialise the meta-policy `π` from the
pre-trained multi-task policy `π'`; (2) train `J_infer` on multi-task-phase trajectories as well;
(3) a hypernetwork emitting `φ` as policy weights, `φ = h(ReLU(P^{φ⊥}(μ,σ)))`. With (1)+(2) present, the
meta-policy's *hypernetwork* is initialised from the multi-task policy's hypernetwork rather than sharing
policy parameters directly.

**VI+HN (= VariBAD + hypernetwork, Beck et al. 2022).** Infers the MDP by reconstructing full trajectories
including future transitions:

$$J_{\text{infer}}(\theta) = \mathbb{E}_M\big[\mathbb{E}_{\tau|\pi(\cdot|\phi)}[-\|\tau_{0:T} - \hat\tau_{0:T}\|_2^2]\big]$$

Additional appendix ablations: VI (VariBAD without hypernetwork), TI++ (without hypernetwork), TI+HN, and
**BI++HN** — a novel variant where task inference reconstructs the multi-task hypernetwork's *base-network
parameters* `φ'` rather than a task representation:
`φ̂' = P^{φ'}(z∼IB)`, `J_infer = E_M[E_{τ|π}[−‖φ' − φ̂'‖²₂]]`.

**Table 1 (appendix) — the component matrix, which is the cleanest statement of what is being controlled:**

| Method | Inference target | Policy conditions on state | Hypernetwork | Inference training in multi-task phase + parameter reuse |
|---|---|---|---|---|
| RNN | None | **No** | No | N/A |
| RNN+S | None | Yes | No | N/A |
| **RNN+HN** | None | Yes | **Yes** | N/A |
| TI Naive | Given | Yes | No | N/A |
| TI | Learned | Yes | No | No |
| TI++ | Learned | Yes | No | Yes |
| TI+HN | Learned | Yes | Yes | No |
| TI++HN | Learned | Yes | Yes | Yes |
| VI | Transitions | Yes | No | N/A |
| VI+HN | Transitions | Yes | Yes | N/A |
| BI++HN | Base Net | Yes | Yes | Yes |

Note the "conditions on state" column: **RNN is the only method that does not**, which is precisely the
confound §2.6 addresses.

### 2.4 Benchmarks and protocol

**Protocol (stated in §4):** meta-episode return, **optimised over five learning rates**
`[3e-3, 1e-3, 3e-4, 1e-4, 3e-5]`, **averaged over three seeds** (four on MineCraft), with a **68 % bootstrap
confidence interval**. Task-inference learning rate fixed at 0.001 (varying it "seemed to have little effect").
Task / `(μ,σ)` projections size 25 (10 on Ant-Dir); trajectory-encoder state embedding 32; all RNNs a single
GRU layer of size 256. ~5,400 GPU-hours total on GTX 1080Ti → RTX A5000 machines.

**Grid-worlds.** *Grid-World* (Zintgraf et al. 2020): 5×5, goal in one cell, agent starts bottom-left, 15
steps per episode, +1 per timestep at goal and −0.1 otherwise, goal fixed across a meta-episode of 4 episodes.
*Grid-World Show*: goal position **visible at the first timestep of each episode** — deliberately designed to
*favour* task-inference methods, since they explicitly encourage storing that information while end-to-end
methods must learn to store it through its effect on the policy. *Grid-World Dense*: reward equals Manhattan
distance to goal and is observed — designed to be *easier* for end-to-end methods.

**MuJoCo** (all four VariBAD variants; 200-step episodes; meta-episodes of 2 episodes for Walker, 1 otherwise).
*Cheetah-Dir* (17-D obs, 6 joints, non-parametric direction); *Cheetah-Vel* (target velocity ~ U[0,3]);
*Ant-Dir* (27-D obs, 8 joints, plus contact penalty and survival bonus); *Walker* (17-D obs, tasks are uniform
samples of **65 different physics coefficients** — the largest task space, expected *a priori* to favour task
inference).

**MineCraft MC-LS** (Beck et al. 2020): 16 rooms, navigate left or right around a diamond-or-iron column
(reward 0.1 each), then at the end move right or left per a red/green signal shown **before the first room**
(+4 correct, −3 incorrect). Tests long-term memory from visual observations. Two consecutive episodes per
meta-episode; four seeds and a linear learning-rate decay added due to high variance.

**Meta-World ML10** (appendix): 10 non-parametric training tasks, 5 distinct test tasks.

### 2.5 Head-to-head results

**A structural caveat first: this paper reports learning curves, not tables.** Figures 5, 6, 7, 9, 10, 11 are
all curves; the only numbers printed anywhere in the paper are the Meta-World ML10 returns in §8.4. Every
comparison below is therefore quoted as the paper states it in prose, and no invented values are supplied.

**Grid-worlds (Fig. 5).** *"Surprisingly, on all three grid-worlds, RNN+HN achieves both the greatest
asymptotic return and greatest sample efficiency."* Notably it achieves the **fastest learning on Grid-World
Show** — the environment built to disadvantage it. TI++HN dominates the other task-inference baselines.

**MuJoCo (Fig. 6).** *"On Cheetah-Dir and Ant-Dir, RNN+HN achieves greater returns than all other baselines
by a wide margin."* On Cheetah-Vel all methods are similar with RNN+HN highest "by a small margin". On
**Walker**, RNN+HN loses — *"only TI outperforms RNN+HN in terms of efficiency, and only TI Naive outperforms
RNN+HN in terms of asymptotic return; however, the effect size is small"*, and both of those methods are among
the worst on Cheetah-Dir and the grid-worlds. The authors predicted this loss in advance from Walker's 65-
parameter task space, which is a point in their favour.

**MineCraft MC-LS (Fig. 7).** *"RNN+HN significantly outperforms VI+HN"*: VI+HN learns to navigate the rooms
but does not reliably learn the long-term-memory behaviour; RNN+HN adapts reliably within two episodes, and
one seed within a single episode.

**Meta-World ML10 (§8.4) — the only numeric results, and they are honestly reported as inconclusive.**

| Source | Method | ML10 result |
|---|---|---|
| Beck et al. 2022, as published | VI+HN | mean return **23.9** from seeds [12.48, 25.69, 33.61] |
| **This paper, re-running the same experiment with different seeds** | VI+HN | mean return **18.35** from seeds [32.80, 3.32, 18.93] |
| Beck et al. 2022, as published | RNN+HN | seeds [11.31, 3.37, 27.77] |
| This paper, own experiment (latent size 25) | **RNN+HN** | final average **test success 17.22 %** |
| This paper, own experiment (latent size 25) | VI+HN | final average **test success 13.87 %** |

The seed-level spread (3.32 to 32.80 within one configuration) is the story. The authors' conclusion:
*"Using different seeds from Beck et al. [2022] resulted in worse performance, indicating that the results
truly were insignificant due to variance."* And on their own run: *"the variance is still too large to draw
firm conclusions… the confidence interval for RNN+HN lies almost entirely within that of VI+HN."* They claim
only a **match**, and argue a match is itself significant because it shows the complicated machinery is
unnecessary.

**No FiLM comparison, no concatenation-vs-hypernetwork comparison in the FiLM sense.** The closest available
control is RNN (context vector consumed as policy input — a concatenation-style conditioning) vs RNN+HN
(weight generation), and the RNN+S ablation between them.

**A combined-objective negative result (§8.3).** Adding task-inference objectives *on top of* the end-to-end
objective **decreased** return versus end-to-end alone, for every variant tested, under both RNN+HN and RNN+S,
and with relative weightings of 10 % and 50 %. Combined methods land between the two pure methods.

### 2.6 Is the gain initialization/normalization rather than architecture class? — the careful answer

**The framing needs correcting, and the correction matters.** The paper's central claim is *not* that
initialisation explains the gain. Its central claim is that **recurrent hypernetworks outperform specialised
task-inference methods**. It then makes two *subsidiary* claims about where the gain comes from, and they
point in **different** directions. Both are needed:

**(a) Initialization is necessary — strongly supported.** In Figure 11 the authors test RNN+HN under
**Kaiming initialization** (He et al. 2015) instead of Bias-HyperInit. Quoting: *"First, we confirm the
finding of Beck et al. [2022] that Bias-HyperInit is crucial for performance (Figure 11). Second, we see the
two models that perform worst, RNN and RNN+HN Kaiming, also have the greatest norm."* So a
Kaiming-initialised recurrent hypernetwork is **among the worst methods in the study** — the architecture
alone buys nothing. Corroborated by the older paper's Table 1 (Cheetah-Dir return: Standard architecture
2104 ± 87, hypernetwork with **Kaiming** 378 ± 169, hypernetwork with **Normc** 356 ± 134, with
**Bias-HyperInit** 2300 ± 32).

**(b) The architecture still contributes independently — this is the authors' explicit conclusion, and it
contradicts a pure "it's all initialisation" reading.** The **RNN+S** ablation, `π_θ(a | s, φ)`, feeds the
state to the policy directly *without* a hypernetwork, isolating the input-plumbing confound. Result: *"while
RNN+S does perform favorably relative to RNN alone, RNN+HN still outperforms RNN+S (Figures 9 and 10). In
particular, RNN+HN achieves similar returns to RNN+S on Ant-Dir and Cheetah-Vel, and outperforms RNN+S on all
other environments, in terms of asymptotic return and sample efficiency."* And the conclusion sentence:
**"These results confirm that to achieve the strongest performance, re-conditioning on state directly is not
sufficient, and that the hypernetwork architecture itself is still critical."**

**(c) The mechanistic hypothesis — latent gradient norms — is explicitly preliminary.** They measure the
gradient norm of the first hidden layer of the hypernetwork w.r.t. the trajectory latent, on Walker
(Figure 11):
- The two worst models (RNN, RNN+HN with Kaiming) have the **greatest** norm.
- RNN+HN and RNN+S **start** with a low norm and **decrease** it through training; RNN **increases** it.
- Hypothesis: *"a low norm, i.e., low sensitivity to the latent variable, is crucial for stable training and
  … the RNN model increases this norm to remain sensitive to the state, since the state is only encoded in
  the latent for this model."*

The conclusion labels this honestly: *"Since the gradient analysis is preliminary and investigates state and
latent variables in isolation, future work could investigate the interaction between these variables."* It is
**correlational across four models on one environment** — treat it as a hypothesis, not a finding.

**Net verdict on the ask.** Split the claim in three:
- *"Naive initialization destroys hypernetwork performance in meta-RL"* — **strongly supported**, twice, by
  two papers.
- *"Some of the apparent architecture gain is really an input-plumbing gain"* — **supported and quantified**
  by RNN+S, which closes a substantial part of the RNN→RNN+HN gap and fully closes it on Ant-Dir and
  Cheetah-Vel.
- *"The gain is initialization/normalization rather than the architecture class"* — **not what this paper
  concludes.** It concludes the opposite of the second half: after controlling for both initialisation (all
  arms use Bias-HyperInit) and state re-conditioning (RNN+S), a residual hypernetwork advantage remains on
  most environments. Stating this paper as an "it was all initialisation" result would misrepresent it.

The strongest fair summary: **initialisation is a necessary condition that the literature routinely gets
wrong, and it dominates the *variance* between published results; architecture is a real but smaller residual
effect once initialisation and inputs are controlled.**

### 2.7 Training-stability issues specific to hypernetworks, and the reported fixes

1. **Initialization — the primary issue.** Naive schemes (Kaiming, Normc, Orthogonal) leave a hypernetwork
   worse than no hypernetwork at all. **Fix: Bias-HyperInit** — zero the final linear layer's weight matrix,
   keep a non-zero bias, so the generator outputs a constant (and thus a well-initialised ordinary policy) at
   step 0. Trade-off named by the authors: it *"ignores trajectories at the start of training"*, i.e. it buys
   stability by starting with zero task-sensitivity, which must then be learned.
2. **Gradient magnitude w.r.t. the latent.** High sensitivity of the generator's first hidden layer to the
   trajectory latent tracks failure across models. No explicit fix is proposed — the observation is offered as
   diagnostic and as motivation for why Bias-HyperInit (which starts at zero sensitivity) works.
3. **Numerical instability at high learning rate — a concrete incident.** §8.4: *"while tuning
   hyper-parameters, one of the seeds for the largest learning rate (3e-3) of RNN+HN encountered numerical
   instability and was ignored."* Handled by learning-rate selection (1e-4 was chosen as optimal), not by a
   fix. Worth carrying: full weight generation narrows the usable learning-rate range.
4. **High-variance environments.** On MineCraft they add a fourth seed and a **linear learning-rate decay**
   specifically because of variance.

**No normalization scheme is used or discussed in this paper** — no LayerNorm on the generator, no code
normalization, nothing corresponding to HYLA's RMSHead or Schug 2024's unit-norm embedding. The entire
stability story here is initialisation plus learning-rate discipline.

### 2.8 Limitations, stated and unstated

**Stated (§6):** *"As an empirical study of meta-RL, we cannot guarantee that recurrent hypernetworks will
improve over every baseline nor on every environment."* Mitigated by breadth of baselines and ablations.

**Unstated but material:**
- **Three seeds** at the selected learning rate, and per-method learning-rate selection over five values on
  the same three seeds — i.e. the reported curve is a max over five configurations, which biases every arm
  upward but not necessarily equally.
- **All results are curves; no numeric table** outside ML10. Any number the project quotes from this paper
  other than the ML10 figures would be read off a plot.
- **The one benchmark with printed numbers (ML10) is the one where the authors decline to claim a win.**
- The task-inference baselines are the authors' own reimplementations and ablations, which is standard but
  means the comparison is not against published numbers.

### 2.9 Relevance and cautions for this project

**Useful.**
- **The RNN+S control is the single most transferable idea here.** If a modulator changes both *what the
  policy sees* and *how it computes*, the honest baseline is one with matched inputs. A project comparison of
  a FiLM-modulated agent against a plain agent that does *not* receive the interoceptive signal directly would
  be measuring the union of two effects. This is a concrete, cheap pre-registration item.
- **Bias-HyperInit generalises directly to FiLM-style modulators**: initialise the modulator's final layer to
  emit a constant (`γ = 1, β = 0`) so the agent begins as an unmodulated agent, with modulation learned in.
  The older Beck paper shows exactly this applied to FiLM, moving Pick-Place from 5.5 to 34.2.
- The **combined-objective negative result** (§8.3) is a caution against bolting an auxiliary task-inference
  loss onto an end-to-end objective — it reduced return in every variant tested.
- The **latent-gradient-norm probe** is a cheap training-health diagnostic that requires no extra runs.

**Cautions.**
- **This paper contains no FiLM baseline.** For a hypernetwork-vs-FiLM number in RL, the citation must be the
  *older* CoRL 2022 paper — with the corrected values from the box above.
- Do not cite it as showing "initialisation, not architecture" — see §2.6.
- Numbers other than ML10 are figure-read.
- The setting is **on-policy PPO meta-RL over a task distribution**, with weights regenerated **every
  timestep** from a recurrent state. That is a different regime from a per-episode or per-task modulator, and
  the stability findings may not transfer directly.

---

## Appendix: Section-by-Section Backbone — Beck et al. 2023 (Recurrent)

**Abstract.** Deep RL is impractical due to sample inefficiency; meta-RL addresses this. Recent work suggests
end-to-end learning with an off-the-shelf sequential model is a strong baseline, but claims are controversial
given limited evidence and contrary prior work. Conducts an empirical investigation; finds recurrent networks
can be strong but that **hypernetworks are crucial to maximizing their potential**; combined, the recurrent
baselines — far simpler than existing specialized methods — achieve the strongest performance of all methods
evaluated.

**1. Introduction.** Meta-RL defined as using sample-inefficient RL to learn a sample-efficient RL algorithm.
Black-box/recurrent methods (Duan et al. 2016; Wang et al. 2016) vs task-inference methods (Humplik 2019;
Zintgraf 2020; Kamienny 2020; Liu 2021; Beck 2022). Detailed critique of Ni et al. 2022: only one specialized
baseline, extra tuning compute given to the RNN, and RNNs significantly outperformed on two of four
challenging domains. This paper: more extensive investigation, stronger baselines, equal sample budget for
tuning. Key insight — the hypernetwork architecture is crucial (Figure 1: RNNs fail on Walker and Cheetah-Dir
where recurrent hypernetworks succeed). Notes RNN+HN is not novel but has never been evaluated in meta-RL
beyond a single environment.

**2. Related Work.** *Recurrent meta-RL* — sequence-model black-box methods; three-part critique of Ni et al.
2022. *Task inference meta-RL* — the main alternative; policy-gradient methods excluded because policy-gradient
estimation needs more data than these benchmarks allow. Task-inference methods add an inference objective, may
add variational inference, or pre-training with privileged information; each component is ablated here.
*Hypernetworks* — Ha et al. 2017; used in SL, meta-SL and meta-RL; can fail out-of-the-box but simple
initialization suffices for stable learning (Beck 2022; Chang 2020). Only Beck et al. 2022 have trained a
hypernetwork end-to-end to arbitrarily modify policy weights in meta-RL, and there a task-inference method was
superior with RNN+HN evaluated on a single task with statistically insignificant results.

**3. Methods.**
- **3.1 Problem setting.** MDP tuple; discounted return; meta-RL inner loop `f(τ) → φ` over meta-episodes;
  Eq. 1 objective; inner vs outer loop.
- **3.2 Recurrent methods.** RNN (= RL²/L2RL), `π_θ(a|φ=f_θ(τ))` with `f` recurrent and `π` feed-forward
  using disjoint parameter subsets. RNN+HN: the recurrent network produces the weights and biases of the
  policy directly, `π_φ(a|s)`; state must be passed in again; Bias-HyperInit (zero weight matrix, non-zero
  bias in the hypernetwork's final linear layer) adopted from Beck et al. 2022.
- **3.3 Task-inference methods.** TI Naive (given task representation, information bottleneck, conditioning
  on `μ` and `σ` for uncertainty-aware exploration; `J_infer` and `J_prior` forming the VariBAD ELBO). TI
  (adds a pre-trained multi-task policy learning `g_θ(c_M)`; `J_multi` and revised `J_infer`; pre-training
  charged against the meta-RL budget). TI++HN (adds meta-policy initialization from the multi-task policy,
  inference training over multi-task trajectories, and a hypernetwork `φ = h(ReLU(P^{φ⊥}(μ,σ)))`). VI+HN
  (= VariBAD + hypernetwork; reconstructs full trajectories `τ_{0:T}`).

**4. Experiments.** Three navigation domains, four MuJoCo tasks, one MineCraft memory task; meta-episode
return optimised over five learning rates, averaged over three seeds (four in MineCraft), 68 % bootstrap CI.
- **4.1 Grid-worlds.** Grid-World, Grid-World Show (goal shown at first timestep — designed to favour task
  inference), Grid-World Dense (dense observed reward — designed to favour end-to-end). RNN+HN achieves the
  greatest asymptotic return **and** sample efficiency on all three, including fastest learning on Show.
  TI++HN dominates the other task-inference baselines.
- **4.2 MuJoCo.** Ant-Dir and Cheetah-Dir non-parametric; Cheetah-Vel and Walker parametric; Walker expected
  hardest for end-to-end with 65 dynamics parameters. RNN+HN wins by a wide margin on Cheetah-Dir and Ant-Dir,
  ties on Cheetah-Vel, and is slightly beaten on Walker by TI (efficiency) and TI Naive (asymptote) with small
  effect size — both of which are among the worst elsewhere.
- **4.3 MineCraft.** MC-LS, 16 rooms, diamond/iron column navigation, red/green long-term-memory signal,
  rewards 0.1 / +4 / −3, two-episode meta-episodes, four seeds, linear LR decay. RNN+HN significantly
  outperforms VI+HN; VI+HN navigates but fails the memory behaviour.

**5. Discussion.** Investigates *why*. **RNN+S** ablation `π_θ(a|s,φ)` isolates the double-state-conditioning
confound: RNN+S beats RNN but RNN+HN still matches or beats RNN+S everywhere, ties on Ant-Dir and Cheetah-Vel,
and wins elsewhere — so re-conditioning on state is not sufficient and the architecture remains critical.
**Latent gradients**: gradient norm of the hypernetwork's first hidden layer on Walker, under Bias-HyperInit
vs Kaiming. Confirms Bias-HyperInit is crucial; RNN and RNN+HN-Kaiming are worst and have the greatest norm;
RNN+HN and RNN+S start low and decrease, RNN increases. Hypothesis: low latent sensitivity is crucial for
stable training.

**6. Limitations.** Empirical study — no guarantee of improvement on every baseline or environment; mitigated
by breadth of baselines (VI+HN contemporary, TI++HN their own stronger design, TI and TI Naive standard) and
appendix ablations.

**7. Conclusion.** Establishes recurrent hypernetworks as a strong, simple, robust meta-RL method; stronger
empirical evidence than prior work with equal tuning compute; passing the state to the policy shown to be a
crucial component; preliminary gradient analysis suggesting low latent gradient norms matter. Future work:
interaction between state and latent variables; hypernetworks with other sequence models such as transformers.

**8. Appendix.**
- **8.1 Additional task-inference ablations.** Method selection on Grid-World and Walker (Figure 12) chose
  TI++HN, TI and TI Naive; VI+HN added as a prior strong method. Extra baselines VI, TI++, TI+HN, and the
  novel **BI++HN** (inference reconstructs base-network parameters `φ'`). BI++HN performs similarly to TI++HN
  on Grid-World but was not selected as it is less standard and much more expensive. **Table 1** component
  matrix.
- **8.2 Hyperparameter tuning.** Five policy learning rates `[3e-3 … 3e-5]`, three seeds each; task-inference
  LR fixed at 0.001; 68 % bootstrap CIs. Projection size 25 (10 on Ant-Dir); state embedding 256, MLP 256→128
  ("XL" from Beck et al. 2022); trajectory-encoder state embedding 32; single GRU layer of 256. Pre-training
  tuned once on Grid-World and transferred: **100 PPO updates optimal** (960 frames each) = 20 % of the frames
  needed to fully train the multi-task policy and only 2.4 % of meta-RL training frames; 563 updates used for
  MuJoCo (2.4 % on Walker/Ant-Dir, 4.8 % on the Cheetahs). All other hyperparameters default to Beck et al.
  2022. Figure 14 shows LR of the task-inference module has little effect.
- **8.3 End-to-end and task inference together.** Combining the objectives **decreased** return relative to
  end-to-end alone for every method tested, under both RNN+HN and RNN+S; combined performance lands between
  the two pure methods; relative weightings of 10 % and 50 % made little difference (Figure 15).
- **8.4 Meta-World experiments.** ML10 re-runs and own experiments, with the numeric returns reproduced in
  §2.5 above; conclusion is a **match**, not a win, with variance too large for firm conclusions. Records the
  numerical instability at LR 3e-3.
- **8.5 Gridworld details.** 5×5, 15 steps/episode, +1 at goal / −0.1 otherwise, 4 episodes per meta-episode;
  Show and Dense variants.
- **8.6 MuJoCo details.** Per-environment observation dimensions, joint counts, reward compositions
  (control cost 5 % of action magnitude on the Cheetahs and Ant, 0.1 % on Walker; Ant contact penalty 0.05 %
  of external forces plus survival bonus 1/timestep; termination conditions), and Walker's 65 physics
  coefficients.
- **8.7 Compute.** Four to eight machines × eight GPUs, GTX 1080Ti to RTX A5000; 4 h (grid-worlds) to 3 days
  (MuJoCo) per experiment; ~360 MuJoCo and ~270 grid-world experiments; roughly **5,400 GPU-hours**.

---
---
