---
title: "Hyper-GoalNet: Goal-Conditioned Manipulation Policy Learning with HyperNetworks"
slug: yao_2025_hyper_goalnet
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_apps.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 2. Yao et al. 2025 — Hyper-GoalNet

**Full title:** *Hyper-GoalNet: Goal-Conditioned Manipulation Policy Learning with HyperNetworks*
**Venue as printed in the PDF:** footnote on page 1 — "39th Conference on Neural Information Processing
Systems (**NeurIPS 2025**)". Sidebar stamp: **arXiv:2512.00085v1 [cs.RO] 26 Nov 2025**.
**Authors:** Pei Zhou, Wanting Yao (intern at HKU, U. Pennsylvania), Qian Luo, Xunzhe Zhou, Yanchao Yang
— InfoBodied AI Lab, HKU. (Same lab and same senior author as HyPoGen, §1 above.)
**PDF:** `docs/project/references/Hypernetwork/sources/Yao et al. 2025 - Hyper-GoalNet - Goal-conditioned manipulation policy learning with hypernetworks.pdf`
**Code:** https://github.com/wantingyao/hyper-goalnet

### Plain-language entry point

**The question.** In goal-conditioned robot manipulation you show the robot a photograph of the desired
end state ("the mug is in the drawer") and it must act to reach it. The standard recipe is to glue the
goal image onto the current camera image and feed the pair into one fixed network. This paper asks
whether that is the wrong division of labour.

**The architectural claim, stated crisply.** *The goal should determine the network's **weights**; the
current observation should be the **input** those weights act on.* The paper's own phrasing: conventional
conditioning "conflates *what* to process (current state) with *how* to process it (goal-dependent
strategy)". A hypernetwork reads the goal image and emits the weights of a small policy MLP; that policy
then maps observations to actions **without seeing the goal again**. That is the difference from
goal-concatenation, where the goal is one more slice of the input vector and every goal must be handled
by one shared weight matrix.

**One honest wrinkle you must carry.** The deployed main model does **not** condition on the goal alone —
at inference it feeds the concatenated latents `[z_g, z_t]` (goal *and* current observation) into the
hypernetwork and regenerates weights at every step. The pure form of the claim is realized by the variant
the paper calls **Hyper-GoalNet (G)**, which generates weights once at the start of a rollout from the
goal image only and freezes them. (G) scores an average success rate of **0.50** against the main model's
**0.52** across 16 tasks — i.e. the strong version of the architectural claim costs about two points and
runs 4× faster (1.46 ms vs 6.33 ms per action step). This is the most useful number in the paper for us,
and it is buried in an appendix efficiency table.

**Second contribution: two constraints on the latent space.** Before the hypernetwork sees anything, the
image encoder is shaped by two auxiliary losses — (1) a **forward dynamics model** that must predict the
next latent from the current latent and action, and (2) a **monotonic distance constraint** forcing the
latent distance to the goal to shrink at every step of a successful demonstration. Both together are
worth a lot: removing them drops the Coffee-task average success from **0.77 to 0.31**.

**Headline results.** On Robosuite/MimicGen manipulation with only two observation frames and a single
goal image: average success 0.52 vs 0.32 for the strongest fixed-parameter baseline (C-BeT), 0.12 for
MimicPlay, and **0.00 for both goal-concatenation baselines** (GCBC and Play-LMP score exactly zero on
every task). On a real 7-DoF arm: 58/60 trials succeed against C-BeT's 21/60 and GCBC's 2/60.

**Is it RL?** **No** — behavior cloning from demonstrations, explicitly reward-free. The paper says so
directly in Appendix D ("Reward-Free Learning: operating within a behavior cloning paradigm, we lack
access to explicit reward signals"), and in Related Work it notes that prior robotic hypernetwork work
sits in RL and that "their end-to-end algorithms are not directly adaptable", while conceding the
hypernetwork architectures themselves decouple from RL.

### Phase 1 — Foundational overview

**Setup.** A dataset `D = {τ_i}` of `M` demonstrations; each trajectory is a sequence of
observation-action pairs, where an observation bundles a 128×128 front-view RGB image and a 9-dimensional
proprioceptive vector. Context length is deliberately just **2 frames** — "the current frame and one
historical frame" — to keep the setting realistic.

**What generates what.**
- **Generator:** a hypernetwork `H` built from the **HyPoGen architecture** (their citation [40] is Ren
  et al. 2025, reviewed in §1 above) with **8 optimization blocks**.
- **Generated:** the full parameters of a **3-layer MLP target policy** (they note it "can be flexibly
  extended in depth and width").
- **Conditioning input:** the concatenated latents of the goal image and the current image,
  `α = φ(o_c, o_g)`, produced by an R3M pre-trained visual encoder that is fine-tuned after epoch 20.
  In the (G) variant, the goal latent alone.
- **Not generated:** the visual encoder, the proprioceptive encoder, and the forward dynamics model — all
  static and shared across goals. Only the small action-producing MLP is weight-generated.

**Key findings.**
1. **Goal-as-weights beats goal-as-input, by a lot.** Contact-rich tasks, 50 rollouts each, three
   difficulty levels of object-pose randomization (d0 easiest → d2 hardest): overall average success 0.52
   (ours) vs 0.32 (C-BeT) vs 0.12 (MimicPlay) vs 0.00 (GCBC) vs 0.00 (Play-LMP).
2. **The gap widens with environment variability.** On Coffee: d0 0.94 vs C-BeT 0.92 — a tie — but d1
   0.76 vs **0.00** and d2 0.62 vs 0.74. The paper's claim is about d1–d2, and it mostly holds, though
   C-BeT beats them on Coffee-d2.
3. **Long-horizon tasks.** Coffee-Preparation + Kitchen average 0.78 vs C-BeT 0.59, MimicPlay 0.35, and
   0.00 for both concatenation baselines. Kitchen-d0 reaches 1.00.
4. **Latent shaping is load-bearing** — 0.77 → 0.31 average on Coffee when removed, and the loss is
   concentrated at the hard difficulty levels (d2: 0.62 → 0.00).
5. **The shaped latent doubles as a task-completion detector.** Thresholding the latent distance to the
   goal agrees with the simulator's ground-truth success signal at 86.6 % accuracy and 94.3 % recall.
6. **Architecture beats initialization tricks.** Against HyperZero given *two different stabilizing
   initialization schemes*, Hyper-GoalNet with plain standard initialization scores 77 % vs 16 % and 16 %.

**Initial takeaway.** Two ideas compose: (a) route the goal to the weights rather than the input, and (b)
make sure the space the goal is read from is geometrically well-behaved. Neither alone is enough — the
paper shows the second is necessary for the first (0.31 without shaping) and the first is necessary
beyond the second (giving C-BeT the same shaping lifts it to 0.69, still below 0.77).

### Phase 2 — Graduate-level deep dive

#### 2.1 The formulation

The object learned is a conditional distribution over target-policy weights (their Eq. 1):

$$H(\theta\mid o_c,o_g)\;:=\;P_{\mathcal{D}}\!\left(\theta \mid o_c=I_t,\ o_g=I_{t'}\right),\qquad I_t,I_{t'}\in\tau_i\in\mathcal{D},\ t'>t .$$

Note the sampling scheme: **any later frame of the same demonstration is a valid goal for any earlier
frame** — this is hindsight relabeling at the level of image pairs, which is what makes the training set
large enough to fit a weight generator. The paper then drops the distributional treatment for a
deterministic map (their Eq. 2):

$$H:\ \mathcal{O}\times\mathcal{O}\ \longrightarrow\ \Theta .$$

**This is where the "goal determines weights" claim is formally weakened**: the domain is
$\mathcal{O}\times\mathcal{O}$, i.e. *both* observations, not $\mathcal{O}_{\text{goal}}$ alone.

#### 2.2 The generator: HyPoGen, reused

$$\theta^K = H(o_c,o_g),\qquad \theta^k=\theta^{k-1}+\lambda^k(\theta^{k-1},\alpha)\,\psi^k(\theta^{k-1},\alpha),\qquad \alpha=\phi(o_c,o_g),$$

with $K=8$ blocks. $\lambda^k$ and $\psi^k$ are described as "learned analogs to step sizes and gradients
in optimization". This is Eq. 6 of HyPoGen with the sign folded into $\psi$ and with the task
specification replaced by an image-pair embedding. **The methodological novelty here is therefore not the
hypernetwork architecture — it is the conditioning signal (visual goal) and the latent shaping.** Worth
knowing when citing: §1 and §2 of this review share an architecture, so their results are not independent
evidence for that architecture.

**Training objective (their Eq. 5).** Pure behavior cloning through the generated policy:

$$\mathcal{L}_{\text{policy}}=\sum_{i=1}^{M}\ \sum_{1\le t<t'\le N_i}\ \ell\!\left(a^i_t,\ \hat a^i_t\right),\qquad \hat a^i_t=\pi\!\left(o^i_{t-L:t};\ H(o^i_t,o^i_{t'})\right),$$

with $\ell$ the MSE. Gradients flow through the generated policy into the hypernetwork end-to-end; there
is no weight-space regression target. The policy consumes a length-$L$ observation window
($L=2$), an explicit non-Markovian choice, $\pi_\theta(a_t\mid o_{t-1},o_t)$ (their Eq. 12).

#### 2.3 The two latent-space constraints

The motivation is stated as a *precondition for weight generation*: the hypernetwork must read the goal
out of a space where "how far am I from the goal" and "where will I be next" are geometrically legible,
because those are exactly the quantities that should drive the emitted weights.

**Constraint 1 — forward dynamics / predictability.** Model the latent transition (their Eq. 6),

$$\hat z_{t+1}\sim p_\Phi(z_{t+1}\mid z_t,a_t),$$

approximated deterministically by $\Phi:\mathcal{Z}\times\mathcal{A}\to\mathcal{Z}$, trained with (Eq. 7)

$$\mathcal{L}_{\text{pred}}=\mathbb{E}_{\tau\sim\mathcal{D}}\big[\ \ell\big(\Phi(z_t,a_t),\,z_{t+1}\big)\ \big].$$

The gradient is backpropagated **into the encoder $E$**, which is the whole point — this is a
representation-shaping loss, not a world model used for planning. $\Phi$ is a small MLP operating in the
compressed latent space.

**Constraint 2 — monotonic progression / physical structure.** The requirement (their Eq. 8) is that
latent distance to the goal never increases along a successful trajectory:

$$d_E\!\left(o^i_j,\,o^i_{j'}\right)\ \ge\ d_E\!\left(o^i_{j+1},\,o^i_{j'}\right)\qquad \forall\, j<j',$$

enforced by a **hinge/margin loss** (their Eq. 9):

$$\mathcal{L}_{\text{dist}}=\mathbb{E}_{\tau\sim\mathcal{D}}\ \sum_j \max\!\Big(0,\ \beta+d(z_{j+1},z_g)-d(z_j,z_g)\Big),\qquad d(z_1,z_2)=\lVert z_1-z_2\rVert_2 .$$

Read the hinge: the penalty activates whenever the next state is not at least $\beta$ closer to the goal
than the current one. **Empirically $\beta=0$ suffices** — a strict-monotonicity margin is not needed,
only non-increase. The metric is Euclidean by choice; see the ablation below for why.

**Total objective (their Eq. 10):**

$$\mathcal{L}_{\text{Hyper-GoalNet}}=\mathcal{L}_{\text{policy}}+\lambda_{\text{pred}}\mathcal{L}_{\text{pred}}+\lambda_{\text{dist}}\mathcal{L}_{\text{dist}},$$

with all $\lambda_i=1$ (uniform, no tuning reported), trained end-to-end.

**Inference (their Algorithm 1).** At each step: generate $\theta\leftarrow H(E(I_t),E(I_g))$, act with
$\pi(o_{t-L:t};\theta)$, step the environment, and declare success when
$d(E(I_{t+1}),E(I_g))<\epsilon$ or the environment says done, else time out at $T$. In the reported
benchmark numbers the *environment's* terminal signal is used for fairness across methods; the latent
criterion is validated separately (Table 5).

#### 2.4 Are the two constraints ablated? — precise answer

**Jointly, yes; individually, no.** The component ablation (their Table 3, Coffee task, success rate):

| Variant | d0 | d1 | d2 | Avg |
|---|---|---|---|---|
| Ours (visual encoder unfrozen from epoch 0) | 0.92 | 0.00 | 0.62 | 0.51 |
| **Ours w/o shaping** (both $\mathcal{L}_{\text{pred}}$ and $\mathcal{L}_{\text{dist}}$ removed) | 0.92 | 0.00 | 0.00 | **0.31** |
| Ours, distance measured to the **start** image instead of the goal | 0.50 | 0.52 | 0.32 | 0.45 |
| Ours, **cosine** distance instead of Euclidean | 0.94 | 0.36 | 0.48 | 0.59 |
| **C-BeT + our shaping** (shaping transplanted onto a fixed-parameter baseline) | 0.80 | 0.64 | 0.64 | 0.69 |
| **Ours (full)** | 0.94 | 0.76 | 0.62 | **0.77** |

What this establishes:
- **Shaping matters** (0.77 → 0.31), and the damage is entirely at d1/d2 — d0 is unchanged at 0.92. So
  the constraints buy *robustness to environmental variability*, not raw competence.
- **The distance term's design matters**: anchoring it to the start image rather than the goal costs 0.32;
  swapping Euclidean for cosine costs 0.18.
- **The parameter-adaptive mechanism has value beyond the shaping**: C-BeT with the same shaping reaches
  0.69, still 0.08 below Hyper-GoalNet. This is the cleanest *mechanism-isolating* comparison in the
  paper and I would cite this row specifically — it is the one place where conditioning mechanism is
  varied with the representation held fixed.
- **What is missing:** there is **no row for "$\mathcal{L}_{\text{pred}}$ removed, $\mathcal{L}_{\text{dist}}$
  kept"** or vice versa. The forward dynamics model is never ablated in isolation. The distance term is
  probed only by *variants* (start-anchored, cosine), never by deletion alone. So the paper cannot say
  which of the two constraints is doing the work, and neither can we when citing it.

#### 2.5 Head-to-head numbers

**There is no FiLM baseline.** The comparison set is concatenation-conditioning and latent-plan /
transformer variants of it:

| Baseline | Mechanism |
|---|---|
| **GCBC** | goal-conditioned BC — concatenate current and goal observations, feed a fixed RNN policy, maximize action log-likelihood |
| **Play-LMP** | latent plan inferred from a goal, then a *fixed-parameter* policy conditioned on state + latent plan |
| **C-BeT** | conditional behavior transformer — self-attention over observation history combined with the goal state, fixed-parameter |
| **MimicPlay** | hierarchical: high-level end-effector trajectory planner + low-level fixed policy |

**Contact-rich tasks, success rate over 50 rollouts (their Table 1).** Context length 2, single goal image.

| Method | Coffee avg | Mug-cleanup avg | 3-piece assembly avg | Threading avg | Nut assembly d0 | **Overall avg** |
|---|---|---|---|---|---|---|
| GCBC (concat) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** |
| Play-LMP | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** |
| MimicPlay | 0.24 | 0.16 | 0.04 | 0.07 | 0.03 | **0.12** |
| C-BeT | 0.55 | 0.40 | 0.01 | 0.32 | 0.34 | **0.32** |
| **Hyper-GoalNet** | **0.77** | **0.62** | **0.25** | **0.46** | **0.55** | **0.52** |

Per-difficulty, Coffee: ours 0.94 / 0.76 / 0.62 vs C-BeT 0.92 / 0.00 / 0.74. The d1 column
(0.76 vs 0.00) is the paper's strongest single data point and also its oddest — C-BeT is *non-monotone*
across difficulty (0.92, 0.00, 0.74), which is hard to explain and should temper how much weight that
column carries.

**The zero rows deserve scrutiny.** GCBC and Play-LMP score **exactly 0.00 on all 16 tasks**, which is
the kind of result that usually signals a broken baseline. The paper pre-empts this in a dedicated
paragraph: it attributes the failure to the *likelihood-maximizing objective* (both baselines maximize
$\log p(a\mid \cdot)$), reports "a large gap between low training loss and high validation loss", says the
implementations came from "reputable third-party code", and cites C-BeT's own paper as corroborating that
likelihood-based models fail in this regime. **This is an argument, not a control.** A same-objective
concatenation baseline (MSE-trained GCBC) is not reported, so the paper cannot fully separate
"concatenation fails" from "log-likelihood training fails". **When citing this paper as evidence that
weight generation beats concatenation, cite the C-BeT rows (0.32 → 0.52, same MSE-style regime), not the
0.00 rows.**

**Augmented-baseline table (their Table 7)** — this is where (G) appears:

| Method | Coffee | Mug-cleanup | 3-piece | Threading | Nut d0 | Avg |
|---|---|---|---|---|---|---|
| MimicPlay-O (wrist camera + 10 frames + goal *sequence*) | 0.84 | 0.63 | 0.30 | 0.15 | 0.44* | 0.44 |
| MimicPlay-M (10 frames + goal sequence, no wrist cam) | 0.24 | 0.16 | 0.04 | 0.07 | 0.03 | 0.12 |
| C-BeT | 0.55 | 0.40 | 0.01 | 0.32 | 0.34 | 0.32 |
| **Hyper-GoalNet (G)** — weights from the **goal image alone**, generated once per rollout | 0.72 | 0.63 | 0.23 | 0.39 | 0.67 | **0.50** |
| **Hyper-GoalNet** — weights from (goal, current), regenerated every step | 0.77 | 0.62 | 0.25 | 0.46 | 0.55 | **0.52** |

(*column read from the Nut-assembly d0 entry.) Note MimicPlay-O gets a wrist camera, a 10-frame history
and a goal *sequence* and still averages 0.44 against Hyper-GoalNet's 0.52 from 2 frames and one image.

**Long-horizon (their Table 2), success rate:**

| Method | CoffeePrep d0 | d1 | avg | Kitchen d0 | d1 | avg | **Overall** |
|---|---|---|---|---|---|---|---|
| GCBC | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Play-LMP | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| MimicPlay | 0.34 | 0.00 | 0.17 | 0.86 | 0.18 | 0.52 | 0.35 |
| C-BeT | 0.82 | 0.04 | 0.43 | 0.78 | 0.70 | 0.74 | 0.59 |
| **Ours** | 0.80 | **0.50** | **0.65** | **1.00** | **0.80** | **0.90** | **0.78** |

**Real robot (their Table 6), successes / 15 trials**, RealMan RMC-DA 7-DoF arm, RealSense D435i overhead:

| Method | Pick&place | Pull | Stack | Sweep | Total |
|---|---|---|---|---|---|
| GCBC | 0/15 | 0/15 | 0/15 | 2/15 | 2/60 |
| Play-LMP | 0/15 | 0/15 | 0/15 | 5/15 | 5/60 |
| C-BeT | 2/15 | 6/15 | 5/15 | 8/15 | 21/60 |
| **Ours** | **14/15** | **15/15** | **14/15** | **15/15** | **58/60** |

**Goal-completion detection (their Table 5), Coffee:** latent-threshold success rate vs environment
ground truth — d0 0.96 vs 0.94 (94 % accuracy, 98 % recall); d1 0.78 vs 0.76 (90 %, 95 %); d2 0.74 vs
0.62 (76 %, 90 %); mean accuracy 86.6 %, recall 94.3 %. Note the d2 row: the detector *over-reports*
success (0.74 claimed vs 0.62 actual), so it is optimistic under high variability.

#### 2.6 Capacity spectrum, cost, and stability

**Where it sits.** **Full weight generation of a small policy head**, via the same iterative-latent-update
machinery as HyPoGen. Crucially, the *expensive* parts of the network are **not** generated — the R3M
visual encoder, the proprioceptive encoder and the dynamics model are static. So in practice this is
"static perception backbone + weight-generated action head", which is architecturally much closer to a
FiLM-style deployment (fixed trunk, modulated readout) than the phrase "hypernetwork policy" suggests.
The modulated object is just larger: a whole 3-layer MLP's weights instead of a per-channel
$(\gamma,\beta)$ pair.

**Cost.** The generated policy is *tiny*, which makes inference **cheaper** than the fixed-parameter
baselines, not more expensive (their Table 10, ms per action step, 40 000 steps on one RTX 3090):
GCBC 15.47, Play-LMP 22.78, C-BeT 13.61, **Hyper-GoalNet 6.33, Hyper-GoalNet (G) 1.46**. (G) is ~10×
faster than every fixed baseline because weight generation happens once per rollout and the resulting
policy is a small MLP. **This inverts the usual assumption that hypernetworks cost more at deployment.**

Training cost against HyperZero under identical hyperparameters on one RTX 4090 (their Table 11):
per-epoch time ~90 s → ~104 s (+16 %); memory with frozen encoder 3 038 MB → 4 916 MB (+62 %); with
unfrozen encoder 13 452 MB → 14 844 MB (+10 %).

**Training-stability issues and fixes — this paper is unusually explicit.**

1. **Output-range mismatch in one-shot hypernetworks.** Their diagnosis of HyperZero: "because this direct
   mapping can produce parameters with a numerical range misaligned with that of an optimally trained
   network, it often requires special initialization to stabilize training." They implemented **two**
   remedies for the baseline to be fair:
   - **Scalar-Init** — a learnable scalar controlling the initial scale of the hypernetwork's output.
   - **Bias-Init** (from Beck et al. 2023) — for high-dimensional conditioning, constrain the parameter
     range with learnable biases alongside **zero-initialized weights** (so the generated network starts
     at the bias, i.e. at a sensible default).

   Result (their Table 4, Coffee success %):

   | Method | d0 | d1 | d2 | Avg |
   |---|---|---|---|---|
   | HyperZero + Scalar-Init | 16 | 18 | 14 | 16 |
   | HyperZero + Bias-Init | 30 | 18 | 0 | 16 |
   | **Ours (standard init, no special scheme)** | **94** | **76** | **62** | **77** |

   The paper's reading — and I agree with it — is that the **iterative residual form removes the need for
   initialization surgery**, because $\theta^k=\theta^{k-1}+\lambda\psi$ starts from a learned $\theta^0$
   that is already in the right numeric range, whereas a one-shot linear map from an embedding to a weight
   vector has no such anchor. This is a general lesson for weight-generating architectures.
2. **Visual-encoder unfreezing schedule.** The R3M encoder is frozen for the first 20 epochs and only then
   fine-tuned. Unfreezing from epoch 0 collapses Coffee-d1 to 0.00 and the average from 0.77 to 0.51
   (Table 3 row 1). Reason given: a moving representation destabilizes parameter generation, since the
   hypernetwork's input distribution shifts under it. **This is a genuinely hypernetwork-specific
   pathology** — a concatenation policy would merely have a moving input, whereas here a moving input
   means a moving *weight-space target*.
3. **No regularization is used in the hypernetwork** — "500 epochs without weight decay or dropout
   regularization in the hypernetwork component" — which the authors implicitly present as evidence the
   architecture is well-conditioned. Take it as a reported fact, not a validated design principle.
4. **Reported failure mode (Limitations).** "Out-of-distribution goals can cause the hypernetwork to
   generate erratic policies", and as an offline method it "lacks explicit safety guarantees against
   unforeseen states". This is the honest counterpart of full weight generation: FiLM's $(\gamma,\beta)$
   is bounded in effect by the fixed backbone; a generated weight matrix is not.

**Training protocol.** 950 training / 50 validation demonstrations per task from MimicGen; Adam, initial
lr $5\times10^{-4}$, cosine annealing, batch 256, 500 epochs, all $\lambda_i=1$; RTX 3090 or 4090; all
compared methods trained under the identical configuration.

#### 2.7 Notes for this project

- **The (G) result is the transferable one.** Goal-only weight generation, computed *once*, gives 0.50 vs
  0.52 for per-step regeneration. If we ever consider a context-conditioned weight generator, this says the
  per-step regeneration cost is probably not worth paying — generate once per episode/context and freeze.
  It also makes the mechanism far more legible: one weight-set per context is inspectable, a weight-set
  per timestep is not.
- **The "C-BeT + our shaping" row** (0.69 vs 0.77) is the template for the experiment we would want in our
  own setting: hold the representation fixed, vary only the conditioning mechanism. Most papers in this
  batch do not run it.
- **Only the small head is generated.** If we adopt anything from this line, the pattern to copy is
  "static encoder trunk + generated readout", which bounds both the parameter count and the blast radius
  of a bad generated weight.
- **The initialization finding** (Table 4) is the concrete, citable form of "hypernetworks are hard to
  train": a competently implemented one-shot hypernetwork with *two* different stabilizing initializations
  still scored 16 % where the residual-iterative form scored 77 %.
- **Biological framing appears but is decorative.** The introduction says the design "better aligns with
  biological goal-directed behavior, where prefrontal regions interpret task goals and dynamically
  modulate processing in sensorimotor circuits" (citing Miller/Cohen-style prefrontal literature via refs
  [32, 51]), and Related Work invokes Botvinick/Daw/Dayan. **No neural data, no biological measurement,
  no model comparison against a biological benchmark.** Treat as motivation only — this is exactly the
  kind of citation `professor-neuromodulation` would want flagged before it is repeated as support for a
  biological-plausibility claim.

### Appendix: Section-by-Section Backbone

- **Abstract.** Hyper-GoalNet generates task-specific policy parameters from goal specifications via
  hypernetworks. "Unlike conventional methods that simply condition fixed networks on goal-state pairs,
  our approach separates goal interpretation from state processing — the former determines network
  parameters while the latter applies these parameters to current observations." Two complementary latent
  constraints: a forward dynamics model for state-transition predictability, and a distance-based
  constraint ensuring monotonic progression toward goals. Evaluated on manipulation with varying
  environmental randomization; strongest gains in high-variability conditions; real-robot validation.
- **§1 Introduction.** The conflation argument: a fixed-parameter network "must process all possible
  goal–current state combinations using the same fixed weights, conflating *what* to process with *how* to
  process it". Reframing: goals as specifications, not input features. Hypernetworks disentangle
  task-dependent processing from state-dependent processing. Biological analogy to prefrontal modulation
  of sensorimotor circuits. Claimed advantage: the goal-aware design also enables **autonomous task
  completion detection**. Two contributions: (i) adapt optimization-inspired hypernetwork architectures to
  goal-conditioned parameter generation; (ii) latent-space shaping imposing predictability + monotonic
  distance decrease.
- **§2 Related work.** *Goal-conditioned policy* — state augmentation with goals, HER; the criticism that
  these need extensive tuning. *Imitation learning for goal-conditioned policies* — C-BeT, MimicPlay;
  their requirement for **sequences** of achievable goal images, and their weakness on contact-rich tasks;
  Hyper-GoalNet needs only a single goal image. *Hypernetworks and cognitive science* — explicitly notes
  that prior robotic hypernetwork work is "primarily within reward-driven reinforcement learning (RL)
  settings", that "this fundamental difference in training paradigms, RL versus our reward-free behavior
  cloning (BC), means their end-to-end algorithms are not directly adaptable", but that "their core
  hypernetwork architectures can be decoupled from the RL framework".
- **§3 Method.** Dataset/observation definitions; the key insight that the goal image specifies *how* the
  current image should be processed.
  - *§3.1 Goal-conditioned hypernetworks.* Reframing from "what action given current and goal" to "what
    processing parameters given the goal". Conditional weight distribution (Eq. 1) with hindsight pairing
    $t'>t$; deterministic map (Eq. 2); optimization-inspired architecture following [40] = HyPoGen
    (Eqs. 3–4) with $\lambda^k,\psi^k$ as learned step size and gradient. *Hypernetwork training*: BC loss
    through the generated policy (Eq. 5), MSE, length-$L$ observation window, non-Markovian assumption,
    end-to-end backprop through policy and hypernetwork; goals restricted to **images** because
    proprioceptive goal states are often unavailable.
  - *§3.2 Latent space shaping.* Motivation — parameter-adaptive policies depend on representation
    quality. Predictability via a latent forward dynamics model (Eqs. 6–7), with the encoder fine-tuned
    through $\Phi$. Physical structure via monotonic distance decrease (Eq. 8) and a margin hinge loss
    (Eq. 9); $\beta=0$ suffices empirically.
  - *§3.3 Hyper-GoalNet for manipulation.* Combined objective (Eq. 10) with $\lambda_{\text{pred}}$,
    $\lambda_{\text{dist}}$; inference by feeding $[z_g,z_t]$ to $H$; two claimed advantages —
    parameter-adaptive generation, and natural goal-completion detection via $d_E(o_t,o_g)$. Algorithm 1
    (test-time loop with threshold $\epsilon$ and horizon $T$).
- **§4 Experiments.** Three questions: effectiveness of parameter adaptation; contribution of latent
  shaping; comparison to conventional goal conditioning and alternative representation learning.
  - *§4.1 Setup.* Robosuite + MimicGen; contact-rich tasks (coffee, threading, mug cleanup, nut assembly,
    three-piece assembly) and long-horizon tasks (coffee preparation, kitchen); difficulty levels d0–d2
    scaling object-pose randomization. 950 demonstrations/task; 128×128 front-view RGB; 9-d proprioception;
    Adam, lr $5\times10^{-4}$, cosine schedule, all $\lambda_i=1$, 500 epochs, batch 256.
  - *§4.2 Main results.* Baselines GCBC, Play-LMP, C-BeT, MimicPlay, all adapted to a single goal image;
    50 rollouts per task; horizons $T=600/800$ (contact-rich) and $T=1600$ (long-horizon); environment
    terminal signals used for standardized evaluation. Tables 1–2. *Analysis of likelihood-based
    baselines* — GCBC/Play-LMP failure attributed to log-likelihood maximization causing severe
    overfitting (large train/validation loss gap), not to implementation.
  - *§4.3 Ablations.* Hypernetwork architecture vs HyperZero + Scalar-Init / Bias-Init (Table 4). Latent
    shaping ablations (Table 3) including the C-BeT + shaping transplant. Visualization of monotonic
    distance-to-goal (Figs. 3, 5, 6) vs unshaped R3M. Goal-completion detection validation (Table 5).
  - *§4.4 Real robot.* RealMan platform, 7-DoF arm, four tasks × 15 trials (Table 6); MimicPlay excluded
    because it needs end-effector pose the hardware does not expose.
- **§5 Discussion.** Conclusion — "how" observations should be processed is inherently goal-dependent;
  latent shaping is critical. *Limitations* — reliance on a well-structured latent space, hard to form for
  highly complex tasks; requires demonstration data with clear goal progression; **out-of-distribution
  goals can cause erratic generated policies**; no safety guarantees as an offline method.
- **Appendix A.** Task descriptions (Coffee, Mug cleanup, Three-piece assembly, Threading, Nut assembly,
  Coffee preparation, Kitchen); data processing; observation space (context length 2, 128×128 RGB,
  9-d proprioception); the partial-observability rationale.
- **Appendix B.** Baseline reimplementation details; augmented baselines MimicPlay-O (wrist camera,
  10 frames, goal sequence) and MimicPlay-M; Tables 7–8; **efficiency analysis, Table 10** (inference
  latency, where Hyper-GoalNet (G) is introduced as generating weights once per rollout from the goal).
- **Appendix C.** Comparison with other hypernetworks; C.1 training time and memory vs HyperZero
  (Table 11).
- **Appendix D.** MDP formalism; three stated divergences — **reward-free learning**, goal-specific policy
  generation, non-Markovian extension (Eqs. 11–12). Model architecture: R3M visual encoder with a
  two-phase freeze/fine-tune schedule (frozen for 20 epochs); **hypernetwork = HyPoGen architecture [40]
  with 8 optimization blocks generating a 3-layer MLP target policy**; predictive model as a latent-space
  MLP; proprioceptive encoder MLP; feature integration by concatenation; lightweight MLP target policy.
  Training details (950/50 split, batch 256, Adam $5\times10^{-4}$, cosine, 500 epochs, no weight decay or
  dropout in the hypernetwork, RTX 3090/4090, identical configuration for all methods).
- **Appendix E.** Enumeration of the ablation variants (unfreeze at epoch 0; w/o shaping; distance to
  start image; cosine distance; C-BeT with shaping).
- **Appendix F.** Real-robot platform (RealMan RMC-DA dual-arm, 7-DoF, parallel-jaw gripper,
  1.25 m × 0.75 m tabletop, Intel RealSense D435i overhead, distractor objects) and per-task protocols.

---
