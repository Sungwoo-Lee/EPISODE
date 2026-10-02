---
title: "Gated-Attention Architectures for Task-Oriented Language Grounding"
authors: ["Devendra Singh Chaplot", "Kanthashree Mysore Sathyendra", "Rama Kumar Pasumarthi", "Dheeraj Rajagopal", "Ruslan Salakhutdinov"]
year: 2018
venue: "AAAI copyright block 2018 (arXiv:1706.07230v2 [cs.LG], 9 Jan 2018) — no proceedings header printed in the PDF"
slug: chaplot_2018_gated_attention
source_pdf: docs/project/references/FiLM/sources/Chaplot et al. 2018 - Gated-Attention architectures for task-oriented language grounding.pdf
topic: FiLM
---

# Gated-Attention Architectures for Task-Oriented Language Grounding

## Plain-English entry point

An agent is dropped into a 3-D Doom level and told, in plain English, *"Go to the short green torch."* It sees only raw pixels from a first-person camera. It has never been given a dictionary, an object detector, or any hand-written link between words and things. Can it learn — end to end, from reward alone — to find the right object, and then to follow **new** instructions it was never trained on ("tall blue torch" when it only ever saw tall blue *objects* and short blue *torches*)?

The paper's answer is yes, and the load-bearing ingredient is **how the sentence is fused into the vision stream**. The standard approach at the time was **concatenation**: flatten the image features, glue the sentence vector onto the end, feed the result to the policy. The authors instead propose **Gated-Attention (GA)**: the sentence embedding is squeezed through one linear layer with a **sigmoid** into a 64-dimensional vector — one number in $(0,1)$ per convolutional feature map — and each feature map of the image is **multiplied** by its number before the policy ever sees it. In the vocabulary of this corpus, that is **feature-wise linear modulation with the shift term removed and the gain squashed into $(0,1)$**: a per-channel, single-site, gain-only FiLM whose conditioner is the task instruction. It predates Perez et al. 2018 and is one of the mechanism's direct ancestors in reinforcement learning.

**Why this paper matters to the corpus more than its age suggests:** it runs the ablation that most FiLM-in-RL papers do not. Same CNN, same GRU, same policy network, same reinforcement-learning algorithm (A3C), *only the fusion operator changes* — multiplicative gating versus concatenation — across three difficulty levels and two generalization regimes. On the hard setting the gated agent reaches **83 %** success on held-out maps and **73 %** on held-out instructions, while the concatenation agent reaches **24 %** and **12 %** and, in the authors' words, "fails to show any considerable performance". It does this with *fewer* parameters (3.39 M vs. 3.44 M). This is, to date, the largest FiLM-family-versus-concatenation margin in the reinforcement-learning half of this library.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | The natural-language instruction $L$ for the episode, encoded by a GRU (hidden size 256) into $x_L$. Episode-constant; **not** the current observation, and not internal state. |
| **What is modulated** | The output feature maps of the **shared visual CNN** (3 conv layers, final one 64 filters), *before* the policy/value heads. Shared trunk, so actor and critic are modulated identically — there is no separate actor or critic modulator. |
| **Modulation operator** | **Gain-only, sigmoid-bounded, elementwise (Hadamard) product**: $\gamma_c \in (0,1)$, no additive shift. Equivalent to FiLM with $\beta \equiv 0$ and $\gamma$ passed through a sigmoid. |
| **Granularity** | **Per-channel** (one scalar per CNN feature map, $d = 64$), broadcast over the $H \times W$ spatial grid. |
| **Placement / number of sites** | **One site**, at the top of the conv stack only. No modulation inside the conv stack, none in the LSTM, none in the heads. |
| **What it is for** | Multi-task language grounding + **zero-shot compositional generalization** to unseen attribute-object pairs. |
| **RL algorithm** | **A3C** (Asynchronous Advantage Actor-Critic) with entropy regularisation and GAE; also Behavioral Cloning and DAgger for the imitation-learning arm. |
| **Ablated against concatenation?** | **Yes — this is the paper's central experiment.** Six-cell grid: {BC, DAgger, A3C} × {Concat, GA} on three difficulty modes × two generalization regimes. Numbers in §Phase 2.4. |
| **Reported instability / failure mode** | No gain blow-up or optimisation instability reported (the sigmoid bounds the gain by construction). The reported failures are of the *baseline*: concatenation collapses as the environment gets harder, and imitation learning collapses when exploration is required. |

## Section-ordered backbone

**1. Introduction.** Defines *task-oriented language grounding*: mapping a natural-language instruction to visual elements and actions so that the described task is executed. Lists the compounded challenges — object recognition from raw pixels, exploration when the target is occluded or out of the field of view, grounding each concept of the instruction, pragmatic reasoning for superlatives ("go to the largest object"), and navigation that avoids the distractors. Three stated contributions: (1) an end-to-end architecture from raw pixels with no prior linguistic or perceptual knowledge that generalises to unseen instructions *and* unseen maps; (2) the **Gated-Attention** multimodal fusion unit, shown to outperform concatenation "using various policy learning methods"; (3) a new ViZDoom-based environment for language grounding.

**2. Related Work.** Four strands. *Grounding language in robotics* (open-vocabulary grounding, human-robot interaction, haptic grounding). *Mapping instructions to action sequences* (semantic parsing; Mei et al. 2015's neural seq-to-seq with bag-of-visual-words) — these ground navigational verbs, whereas this paper grounds **visual attributes** (shape, size, colour). *Deep RL from visual data* in FPS games, where the prior norm is **one policy per task**, versus this paper's *single network for many instructions*. *Instruction-following agents* (Yu et al. 2017; Misra et al. 2017 in 2-D blocks; Oh et al. 2017 with discretised positions and prior linguistic knowledge baked into an analogy-making objective). The claimed delta: 3-D, raw pixels, continuous positions, partial observability, no prior knowledge.

**3. Problem Formulation.** Episodic environment $E$. At episode start the agent receives instruction $L$ describing the target object; at each step it receives a first-person RGB frame $I_t$ and emits $a_t$. State $s_t = \{I_t, L\}$; the episode ends when the agent reaches *any* object or exceeds the horizon. Objective: learn $\pi(a_t \mid s_t)$. Two learning regimes are considered: **imitation learning** with an oracle that returns the optimal action, and **reinforcement learning** with a positive reward for reaching the correct object and a negative reward for reaching any other object.

**4. Proposed Approach.** Two modules.

*State-processing module.* A CNN gives $x_I = f(I_t; \theta_{\text{conv}}) \in \mathbb{R}^{d \times H \times W}$; a GRU gives $x_L = f(L; \theta_{\text{gru}})$; a fusion unit $M(x_I, x_L)$ combines them. The **concatenation** baseline is $M_{\text{concat}}(x_I, x_L) = [\mathrm{vec}(x_I); \mathrm{vec}(x_L)]$, "used as a baseline for the proposed Gated-Attention unit as it is used by prior methods". The **Gated-Attention** unit passes $x_L$ through a fully-connected layer with **sigmoid** activation whose output dimension $d$ equals the number of CNN feature maps, producing the *attention vector* $a_L = h(x_L) \in \mathbb{R}^d$; each element is expanded to an $H \times W$ matrix to form $M(a_L) \in \mathbb{R}^{d \times H \times W}$ with $M_{a_L}[i,j,k] = a_L[i]$; the fused representation is the Hadamard product $M_{GA}(x_I, x_L) = M(h(x_L)) \odot x_I$. The unit is fully differentiable, so the architecture trains end to end. Stated inspiration: the Gated-Attention Reader for text comprehension (Dhingra et al. 2017), which multiplies a query embedding into the intermediate states of a document reader; here the multiplication is between the instruction representation and the *convolutional feature maps*. Stated intuition: the conv feature maps detect object attributes (colour, shape), and the instruction should determine **which feature maps to attend to** — "green", "pillar", or both.

*Policy-learning module.* For imitation learning, Behavioral Cloning and DAgger against an oracle that reorients toward the target and moves forward; the head is a single fully-connected layer. For reinforcement learning, **A3C** with entropy regularisation and the **Generalized Advantage Estimator**; the head is a linear layer of size 256 followed by an **LSTM** of size 256, then a value scalar and three action logits. The LSTM is explicitly justified by partial observability: the agent may be in a state where not all objects are visible and must remember what it has already seen.

**5. Environment.** Built on the ViZDoom API. Each scenario spawns the agent plus one correct and several incorrect objects (columns, torches, armors, keycards) with varying colour, shape and size. Actions: turn left, turn right, move forward. 70 hand-written instructions of the form "Go to the X". Crucially, the *same* instruction refers to *different* objects across episodes ("Go to the red object" may mean a red keycard or a red torch), which prevents instruction-to-object memorisation. Three difficulty modes: **Easy** (agent at a fixed spawn, five objects on a fixed horizontal line in view), **Medium** (objects at random locations but guaranteed in view; agent fixed), **Hard** (agent *and* objects at random locations, target may be outside the field of view, so exploration is required).

**6. Experimental Setup.** Five objects per episode (1 correct, 4 incorrect), horizon $T = 30$, metric = success rate of reaching the correct object, averaged over 100 episodes. **55 training instructions / 15 held-out test instructions** covering unseen attribute-object combinations. Two evaluation regimes: **Multitask Generalization (MT)** — training instructions, *unseen maps*; **Zero-Shot Task Generalization (ZSL)** — *unseen instructions* on unseen maps. Baselines: Misra et al. 2017 adapted (reduces to **A3C-Concat**; reward shaping deliberately dropped so the method does not depend on target distance) and Mei et al. 2015 adapted (reduces to **BC-Concat**). The authors state explicitly that the CNN, GRU and policy architectures are **identical** across baseline and proposed models "to ensure fairness in comparison" — the fusion operator is the only difference. Hyper-parameters: input $3 \times 300 \times 168$; conv stack 128 filters $8\times8$/stride 4, 64 filters $4\times4$/stride 2, 64 filters $4\times4$/stride 2; GRU size 256; A3C trained with SGD, learning rate 0.001, discount 0.99, 16 parallel threads; imitation learning uses RMSProp and Huber loss with a linearly decayed DAgger mixing coefficient.

**7. Results & Discussion.** Table 1 (the ablation, reproduced in §Phase 2.4) and Figure 6 (A3C learning curves in each mode). GA beats Concat in **every one of the twelve cells**. GA models also *learn faster* and converge higher. Hard mode is where the operator matters most: A3C-GA 0.83 MT / 0.73 ZSL versus A3C-Concat 0.24 / 0.12. Imitation learning degrades badly in medium and hard modes because those settings require exploration, which the RL agent gets for free. A qualitative policy trace (Figure 9) shows the agent making a ~300° turn to find objects that start outside its view, then walking past a *tall* green torch to reach the *short* green torch. Attention-map analysis (Figures 7, 8, 11, 12): individual dimensions of the 64-dim attention vector specialise — dimension 18 for "armor", 8 for "skullkey", 36 for "pillar" — and no dimension fires for all instructions containing the generic word "object", indicating the model has learned that "object" is not an object *type*. t-SNE of the attention vectors clusters by colour and by object type. The same specialisation appears for held-out test instructions, which is the mechanistic explanation for zero-shot transfer.

**8. Conclusion.** The multiplicative fusion unit outperforms concatenation for both multitask and zero-shot generalization, across three difficulty modes, under both RL and imitation learning; the attention weights show the agent learns object, colour and size attributes without supervision.

**Appendices A–C.** Object inventory; the full list of 70 instructions grouped into Size+Color, Color+Size, Color, Object Type, Superlative-Size+Color, Superlative-Size, Size; additional attention-vector heatmaps.

## Phase 1 — Undergraduate-level synthesis

**The problem.** You want one agent that can follow many different English commands in a 3-D game, using only camera pixels, and you want it to handle commands it has never heard. The naive design gives the network the picture and the sentence side by side and hopes it works out what to do. That is *concatenation*, and it is what everyone did.

**The idea.** A convolutional network's channels are feature detectors: one may respond to green things, another to tall thin things, another to key-shaped things. If you already know the sentence says "green pillar", you do not need the whole feature bank — you need the green detector and the pillar detector, turned up, and everything else turned down. So: read the sentence with a small recurrent network, project it to exactly as many numbers as there are channels, squash each number to lie between 0 and 1 with a sigmoid, and **multiply each channel by its number**. Channels the sentence does not care about get multiplied by something near 0 and effectively vanish; channels it cares about survive. The policy then acts on the filtered picture.

**Why multiplication rather than gluing.** Gluing the sentence onto the feature vector leaves the network to *discover* the interaction between word and pixel through its own weights, and to discover it separately for every combination of word and pixel pattern. Multiplication *builds the interaction in*. In particular it makes the composition "green" + "pillar" work by construction: the sentence encoder only has to learn which channels correspond to "green" and which to "pillar", and a sentence containing both keeps both sets of channels. That is precisely why the model transfers to attribute-object pairs it never saw in training.

**The headline result.** In the hardest setting — random spawns, target possibly behind you — the multiplicative agent reaches the right object 83 % of the time on new maps and 73 % of the time on *new sentences*. The gluing agent reaches 24 % and 12 %, which is barely better than picking one of the five objects at random (20 %). The multiplicative model is also very slightly *smaller*, because a $d$-dimensional gain vector costs fewer parameters than the wide first layer that concatenation forces.

**What the attention maps show.** The learned gains are not opaque. Specific dimensions light up for specific nouns and colours, and the same dimensions light up correctly for held-out sentences. The model has effectively induced an unsupervised attribute vocabulary in the channel index space of its own CNN.

## Phase 2 — Graduate-level deep dive

### 2.1 The two fusion operators, side by side

Let the visual stream produce $x_I = f(I_t; \theta_{\text{conv}}) \in \mathbb{R}^{d \times H \times W}$ with $d = 64$ feature maps, and let the language stream produce $x_L = f(L; \theta_{\text{gru}}) \in \mathbb{R}^{256}$.

**Concatenation baseline.**

$$
M_{\text{concat}}(x_I, x_L) \;=\; \bigl[\,\mathrm{vec}(x_I)\,;\ \mathrm{vec}(x_L)\,\bigr] \;\in\; \mathbb{R}^{dHW + 256}.
$$

**Gated-Attention.** First the *attention vector*, produced by one fully-connected layer with sigmoid nonlinearity $h$,

$$
a_L \;=\; h(x_L) \;=\; \sigma\!\bigl(W_a x_L + b_a\bigr) \;\in\; (0,1)^{d},
\qquad W_a \in \mathbb{R}^{d \times 256},
$$

then spatial broadcast to a rank-3 tensor $M(a_L) \in \mathbb{R}^{d \times H \times W}$ whose entries are

$$
M_{a_L}[i, j, k] \;=\; a_L[i] \qquad \forall\, j \in \{1..H\},\ k \in \{1..W\},
$$

and finally the Hadamard product

$$
M_{GA}(x_I, x_L) \;=\; M\bigl(h(x_L)\bigr) \odot x_I,
\qquad\text{i.e.}\qquad
\bigl[M_{GA}\bigr]_{i,j,k} \;=\; a_L[i]\; \cdot \; x_I[i,j,k].
$$

Note what is *absent*: no additive term, no spatial dependence in the modulator, no per-layer repetition.

### 2.2 Relation to FiLM (Perez et al. 2018)

FiLM computes, for layer $\ell$ and channel $c$, $\widetilde F^{(\ell)}_{c} = \gamma^{(\ell)}_c(z)\, F^{(\ell)}_{c} + \beta^{(\ell)}_c(z)$ with $\gamma, \beta$ unconstrained affine functions of a conditioner $z$, applied at **every** residual block. Gated-Attention is the special case

$$
\gamma^{(\ell)}_c(z) \;=\; \sigma\bigl(w_c^\top z + b_c\bigr) \in (0,1),
\qquad
\beta^{(\ell)}_c(z) \;\equiv\; 0,
\qquad
\ell \in \{L_{\text{top}}\}\ \text{only},
$$

i.e. **gain-only, bounded-gain, single-site FiLM**. Three consequences worth stating precisely, because the corpus argues about all three:

1. **No shift $\Rightarrow$ no ability to activate a dead channel.** If $x_I[i,j,k] = 0$, no value of $a_L[i]$ changes it. The instruction can *suppress* and *rescale* evidence but cannot *inject* evidence. In an instruction-following task this is exactly the right inductive bias (the instruction is a selector over pre-existing visual evidence), which is an argument that the ablation's margin is partly a *task-structure* effect and does not automatically transfer to settings where the conditioner carries information the main stream does not have.
2. **Sigmoid bound $\Rightarrow$ structural immunity to gain blow-up.** $\gamma_c \in (0,1)$ makes $\|M_{GA}\|_\infty \le \|x_I\|_\infty$, so the modulated activations cannot exceed the unmodulated ones and the Jacobian $\partial M_{GA}/\partial x_I$ has spectral norm $\le 1$. This is why the paper reports no instability: the failure mode that the corpus flags as unmeasured elsewhere is ruled out by construction here — at the cost of a one-sided operator (it can only attenuate) and of sigmoid saturation, where $|\partial \gamma_c / \partial x_L| \to 0$ once $|w_c^\top x_L + b_c|$ is large.
3. **Single site $\Rightarrow$ the modulation cannot change *what features are computed*, only which are read out.** Perez et al.'s argument for injecting throughout the depth is that conditioning should bias intermediate computation. Gated-Attention gets its result with the weaker, cheaper version, which is a useful data point: on this task, top-of-stack channel selection was sufficient.

### 2.3 Why multiplicative fusion should help compositional zero-shot generalization

Write the policy head applied to the fused representation as $\pi(a \mid M(x_I, x_L))$. Under concatenation, the first weight matrix $W_1$ of the head splits as $W_1 = [W_1^I \;|\; W_1^L]$, so the pre-activation is

$$
W_1^I \,\mathrm{vec}(x_I) \;+\; W_1^L x_L,
$$

which is **additive and separable**: the instruction contributes a bias that is *independent of the image*. Any image–instruction interaction must be manufactured by the subsequent nonlinearities, and there is no architectural pressure for the network to represent the interaction in a factorised way. Under Gated-Attention the pre-activation is

$$
\sum_{i,j,k} W_1[\cdot,\, i,j,k]\; a_L[i]\; x_I[i,j,k],
$$

a **bilinear form** in $(a_L, x_I)$ — the interaction is first-order in the architecture rather than emergent.

The compositional-generalization argument follows from this factorisation. Suppose channel subsets $C_{\text{green}}, C_{\text{pillar}} \subset \{1..d\}$ carry the two attributes, and suppose the sentence encoder has learned a roughly additive pre-sigmoid code, $w^\top x_L(\text{"green pillar"}) \approx w^\top x_L(\text{"green object"}) + w^\top x_L(\text{"pillar"}) - w^\top x_L(\text{"object"})$. Then the gains for an *unseen* combination are approximately the pointwise conjunction of the gains for its seen constituents, so $M_{GA}$ selects $C_{\text{green}} \cap C_{\text{pillar}}$ without the policy head being retrained. Concatenation offers no analogous mechanism: the unseen sentence produces an unseen bias vector, and the head has never been trained at that bias. The paper's Figure 7 heatmaps and Figure 8 t-SNE clusters are the empirical check on this account — dimensions specialise by attribute, and the specialisation holds on the held-out instructions (marked `*` in the figures).

### 2.4 The ablation, in full (Table 1)

All values are success rate averaged over 100 episodes. **MT** = multitask generalization (training instructions, unseen maps); **ZSL** = zero-shot task generalization (held-out instructions, unseen maps). Chance is 0.20 (one correct object among five).

| Learning rule | Fusion | Params | Easy MT | Easy ZSL | Medium MT | Medium ZSL | Hard MT | Hard ZSL |
|---|---|---|---|---|---|---|---|---|
| Behavioral Cloning | Concat | 5.21 M | 0.86 | 0.71 | 0.23 | 0.15 | 0.20 | 0.15 |
| Behavioral Cloning | **GA** | 5.09 M | **0.97** | **0.81** | **0.30** | **0.23** | **0.36** | **0.29** |
| DAgger | Concat | 5.21 M | 0.92 | 0.73 | 0.45 | 0.23 | 0.19 | 0.13 |
| DAgger | **GA** | 5.09 M | **0.94** | **0.85** | **0.55** | **0.40** | **0.29** | **0.30** |
| **A3C (RL)** | Concat | 3.44 M | 1.00 | 0.80 | 0.80 | 0.54 | 0.24 | 0.12 |
| **A3C (RL)** | **GA** | 3.39 M | 1.00 | **0.81** | **0.89** | **0.75** | **0.83** | **0.73** |

Readings that matter for the corpus:

- **Twelve out of twelve cells favour multiplicative gating** (Easy MT under A3C is a tie at ceiling, 1.00 vs. 1.00; Easy ZSL is within noise at 0.81 vs. 0.80). The margin is monotone in task difficulty.
- **The RL row is the extreme case.** Hard mode, $+0.59$ absolute on MT and $+0.61$ on ZSL. Concatenation at 0.24 MT / 0.12 ZSL is at or below chance — the operator is not "slightly worse", it is the difference between learning the task and not learning it.
- **Parameter count is controlled and favours GA slightly** (3.39 M vs. 3.44 M for A3C; 5.09 M vs. 5.21 M for imitation learning), so this is not a capacity result. Concatenation is *larger* because flattening $x_I$ and appending $x_L$ widens the first head layer.
- **The comparison is architecture-matched by explicit statement**: same CNN, same GRU, same policy/value head, same optimiser, same reward. Only $M(\cdot,\cdot)$ differs.
- **Reward shaping was deliberately removed** from the Misra et al. baseline, so A3C-Concat is running without the distance-based shaping its original paper used. This is a fairness choice in one direction (both arms are unshaped) and a severity choice in another (the hard mode is a genuinely sparse-reward exploration problem). A reader should note that the hard-mode collapse of Concat is partly an *exploration* failure: with no shaping and near-chance early performance, the concatenated agent gets little learning signal. GA's advantage compounds because faster early grounding produces denser effective reward.
- **Figure 6 reports learning curves, not just final numbers**: GA "learns faster than Concat and converges to higher levels of accuracy" in all three modes, so the effect is on sample efficiency as well as asymptote.

### 2.5 The A3C objective, for completeness

The RL arm optimises the standard asynchronous advantage actor-critic loss over the fused state $\hat s_t = M(x_{I_t}, x_L)$ passed through the LSTM to give $h_t$:

$$
\mathcal{L} \;=\; \underbrace{-\,\mathbb{E}\bigl[\log \pi_\theta(a_t \mid h_t)\, \hat A_t\bigr]}_{\text{policy gradient}}
\;+\; \underbrace{\tfrac{1}{2}\,\mathbb{E}\bigl[(V_\theta(h_t) - R_t)^2\bigr]}_{\text{value, mean-squared}}
\;-\; \underbrace{\lambda_H\,\mathbb{E}\bigl[\mathcal{H}(\pi_\theta(\cdot \mid h_t))\bigr]}_{\text{entropy regularisation}},
$$

with $R_t = \sum_{k\ge 0} \gamma^k r_{t+k}$, $\gamma = 0.99$, and the advantage estimated by GAE,

$$
\hat A_t^{\text{GAE}(\gamma, \lambda)} \;=\; \sum_{l \ge 0} (\gamma\lambda)^l\, \delta_{t+l},
\qquad
\delta_t \;=\; r_t + \gamma V_\theta(h_{t+1}) - V_\theta(h_t).
$$

All parameters — CNN, GRU, the gating projection $W_a$, LSTM, heads — are shared between policy and value except the final fully-connected layer. **The gains therefore receive gradient from both the policy and the value objective**, and the same gains modulate the input to both heads. There is no separate actor-side and critic-side modulator, and the paper reports no problem arising from that. Sixteen parallel threads, SGD at learning rate 0.001.

### 2.6 What the attention-map analysis establishes, and what it does not

The heatmaps (Figures 7, 11, 12) plot $a_L \in (0,1)^{64}$ across instructions grouped by target object type and colour. Three findings: (i) **sparse, interpretable specialisation** — dimension 18 for "armor", 8 for "skullkey", 36 for "pillar"; (ii) **abstraction over the generic word "object"** — no dimension is uniformly high across all "*coloured* object" instructions, meaning the model represents "object" as *not* a type constraint while still gating on the colour; (iii) **the same structure on held-out instructions**, which is the mechanistic evidence that ZSL transfer comes from compositional reuse of gains rather than from memorisation.

What this does *not* establish: that a channel is a *pure* attribute detector (the analysis is on the gains, not on the CNN filters), or that the gate values are calibrated in any probabilistic sense. And, importantly for this corpus, there is **no reported statistic on the gain distribution over training** — no saturation fraction, no dead-channel count — so the paper contributes no evidence on whether the sigmoid saturates, only the structural guarantee that it cannot diverge.

### 2.7 What this paper does and does not settle for our own modulator design

**Settles (with a controlled experiment):** *within an on-policy actor-critic agent (A3C), with a shared trunk feeding both heads, replacing concatenation of an episode-constant task vector by a per-channel multiplicative gate on the visual features improves multi-task and zero-shot performance dramatically on hard, partially-observed, sparse-reward navigation, at equal or lower parameter count.* That is the single most direct answer to the corpus's FiLM-vs-concatenation question inside RL that this library holds, and it is stronger evidence than the four ablations previously catalogued in [`film_in_rl_survey.md`](../film_in_rl_survey.md) §8 because the margin is enormous and the architectures are matched by explicit design.

**Does not settle:** (a) whether an *unbounded* gain, or a gain *plus shift*, would do better or worse — only $\sigma$-bounded gain-only is tested; (b) whether multiple injection sites help — only one site is tested; (c) whether a **non-stationary** conditioner behaves the same way — $x_L$ is constant within an episode, so the gate is a *fixed* re-parameterisation of the network for the whole trajectory, and the temporal-credit and value-bootstrapping problems that a step-varying gain would create simply do not arise here; (d) whether modulating the critic specifically is safe — the trunk is shared, so the question is not isolated.

Point (c) is the one to hold onto. The corpus's open question is whether a modulator reading the **current observation** can work. Chaplot's gate reads a signal that is *exogenous and frozen for the episode* — the most benign possible conditioner. Its success is evidence that the *operator* is good, not that a fast, endogenous, observation-driven conditioner is safe.

## Connections

- **[`perez_2018_film.md`](perez_2018_film.md) (canonical FiLM)** — Chaplot's Gated-Attention is a **predecessor and strict special case**: $\beta \equiv 0$, $\gamma \in (0,1)$ via sigmoid, one injection site instead of per-block. Reading the two together isolates which parts of FiLM are load-bearing: this paper shows that the *multiplicative, per-channel, conditioner-driven* part alone already buys most of the compositional-generalization benefit on an instruction-following task.
- **[`jang_2022_bcz.md`](jang_2022_bcz.md) (BC-Z)** — same conditioning *signal type* (a task command encoded into a vector) and same target (a visual policy trunk), but BC-Z uses full affine FiLM at four ResNet blocks and **does not ablate FiLM against concatenation**. Chaplot supplies the missing ablation that BC-Z's design choice implicitly relies on, four years earlier and in a smaller environment.
- **[`chevalier_boisvert_2019_babyai.md`](chevalier_boisvert_2019_babyai.md) (BabyAI)** — the gridworld successor to this experimental design: same "instruction + partial egocentric view + actor-critic" template, with FiLM (full affine) rather than gain-only gating in the reference agent.
- **[`nikulin_2023_anti_exploration_rnd.md`](nikulin_2023_anti_exploration_rnd.md)** — the corpus's other strong FiLM-vs-concatenation-vs-gating sweep in RL, but on an auxiliary RND prior in *offline* RL. Note the tension worth recording: Nikulin's sweep ranks FiLM (95–100 D4RL) > concat (89.6) > **gating (67.3)**, i.e. *gating loses badly there*, whereas gating wins overwhelmingly here. The two settings differ in conditioner (action vs. instruction), in what the gate multiplies, and in whether an additive path exists. Anyone citing "multiplicative beats additive in RL" must reconcile these two results rather than cite whichever is convenient.
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §8** — this paper should be added to the ablation-quality table as a **fifth** genuine mechanism ablation, and it is the strongest one in the on-policy, online, pixel-based regime. Suggested row: *"Gain-only multiplicative gating beats concatenation in an on-policy actor-critic — Yes, Table 1, 12 matched cells across 3 difficulties × 2 generalization regimes × 3 learning rules; A3C hard mode 0.83 vs. 0.24 MT and 0.73 vs. 0.12 ZSL — Strong."*
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §10.1 (the corpus's headline open question)** — this paper does **not** close it. Its conditioner is episode-constant and exogenous, the opposite end of the spectrum from an observation-driven modulator. It does, however, remove one competing explanation: if our modulated agent underperforms a concatenation baseline, the operator itself is not the obvious culprit, since the operator wins decisively when the conditioner is well-behaved.
- **Project-side relevance** — two transferable design notes. (1) **A bounded gain is a free stability guarantee.** $\gamma = \sigma(\cdot) \in (0,1)$ makes gain blow-up structurally impossible; the price is that the modulator can only attenuate. If our temperature/gain heads have been observed hitting a clip, the comparison to make is *clip on an unbounded gain* versus *squash into a bounded gain*, and this paper is the citation for the second option working in an on-policy agent. (2) **A single top-of-stack site sufficed here**, which is a cheap ablation arm worth keeping in any injection-depth sweep. Any implementation follow-up should be handed to `senior-developer` as an `issue_plan`; this review proposes no code changes.
