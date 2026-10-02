---
title: "Universal Morphology Control via Contextual Modulation (ModuMorph)"
slug: xiong_2023_modumorph
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_modern.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## P2. Xiong, Beck & Whiteson 2023 — *Universal Morphology Control via Contextual Modulation* (**ModuMorph**)

**PDF:** `docs/project/references/modulation_in_rl/sources/Xiong et al. 2023 - Universal morphology control via contextual modulation (ModuMorph).pdf`
**Code:** https://github.com/MasterXiong/ModuMorph (stated in the abstract)

### P2.0 Why this paper is decision-relevant

Beukman (§P1) compares conditioning mechanisms in small MLP policies with a 1-to-5
dimensional context. ModuMorph runs a comparison of the same *kind* — how should
context enter the network? — at the opposite end of the scale: **PPO, a transformer
policy, 100 training robots and 100 held-out robots, 100–200 M environment steps**.
Two things make it valuable here beyond its size.

**First, it makes the sharpest available statement of *why* concatenation is weak,
and it is an argument the project can reuse verbatim.** When the context `c_k` is
*constant for the whole episode*, concatenating it to the node input and passing the
result through a shared linear embedding layer

$$e^i_k = W\!\begin{bmatrix} s^i_{k,t} \\ c^i_k \end{bmatrix} + b = \underbrace{W_s\, s^i_{k,t}}_{\text{depends on time}} + \underbrace{\left(W_c\, c^i_k + b\right)}_{\text{constant for the whole episode}}$$

is **exactly equivalent to adding a context-conditioned bias term** to the
embedding. The paper states this three separate times (§1, §2.2.1, §6). In the
project's own vocabulary: **concatenating a slow context is FiLM with the gain
frozen at 1 — an offset `β(c)` and no gain `γ(c)`, applied at exactly one site.**
That is a genuinely useful reframing: it makes "concat vs. FiLM" not a comparison of
two different things but a comparison of a *degenerate* modulator against a full
one, and it explains why the concat baseline is not as weak as one might think
(it is a real, if minimal, modulator) while still being capacity-limited.

**Second, the ablation separates two operators that the folder normally lumps
together**, and they behave differently: modulating *how information is routed*
(the attention matrix) is robust and helps everywhere; *generating weights* is
higher-variance and helps only where the task is hard enough to need behaviour
diversity, and can hurt.

### P2.1 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | **ICML 2023**, printed verbatim in the p. 1 footer: *"Proceedings of the 40th International Conference on Machine Learning, Honolulu, Hawaii, USA. PMLR 202, 2023."* PDF also carries `arXiv:2203.01110v2 [cs.AI] 3 Aug 2023`. Authors: Zheng Xiong, Jacob Beck, Shimon Whiteson (Oxford). |
| **Conditioning signal** | **Given, not inferred.** Per-node **morphology context** `c^i_k` supplied by the UNIMAL benchmark — limb size, mass, and the limb's initial position relative to its parent node — plus an adjacency matrix defining the morphology tree. Explicitly **time-invariant**: "the morphology context does not change on a robot." Two *separate* MLP context encoders are trained, one for each modulation module (2-layer for the hypernetwork, 3-layer for fixed attention, 128 units each). Future work explicitly names "how to learn better context representation for modulation" as open. |
| **What is modulated** | The **base controller** (a MetaMorph-style transformer). Three sites: (1) the **per-node embedding layer** — weights *and* biases generated per node; (2) the **per-node decoder** (the action head) — weights and biases generated per node; (3) the **attention matrices of the transformer encoder** — the key and query inputs are replaced by context embeddings. The transformer encoder's own weight matrices are **not** generated: "there are too many weight matrices in a transformer layer to efficiently generate them via HN." **Critic: not described anywhere in the PDF.** The paper discusses a value-prediction error for the HN variant (§5.1), so a value function exists, but its architecture and whether it is modulated are never stated. Record as **actor stated, critic unstated**. |
| **The operator** | **Two distinct operators, ablated separately.** (a) **HN — full weight generation of linear layers:** `θ^i_k = HN_φ(c^i_k)`, so `e^i_k = W^i_k x^i_k + b^i_k` with `W^i_k = HN_W(c^i_k)`, `b^i_k = HN_b(c^i_k)` — replacing MetaMorph's single shared `(W, b)`. Rung 3. (b) **FA — fixed attention:** the node embedding supplies **only** the value input `V`; the key and query come from a context encoder, so the attention matrix is a function of morphology alone and is **constant across timesteps within a robot**. This is not an affine operator at all: it modulates the *routing weights between limbs*, not the magnitude of any feature. **Neither operator is FiLM.** The FiLM-shaped thing in this paper is the *baseline*. |
| **Capacity-spectrum position** | HN sits at **rung 3** (per-module full weight generation, restricted to the linear embedding/decoder layers). FA does not sit on the spectrum at all — it is orthogonal, a **routing** modulation, closest in spirit to attention-as-gating. The baseline MetaMorph sits at **rung 0/1-degenerate** (concatenation ≡ additive context bias). |
| **RL algorithm** | **PPO** (on-policy), following MetaMorph's setup exactly, including the same proprioceptive and context features, so the comparison isolates architecture. Note this is the **only on-policy result in the batch** — Beukman is SAC, Benad and DALI are off-policy/model-based. |
| **Benchmark** | **UNIMAL** (Gupta et al. 2021) — 100 training morphologies and 100 held-out test morphologies, in five environments: **FT** (flat terrain locomotion), **Incline** (10°), **Exploration** (distinct grid cells visited), **VT** (variable terrain, resampled per episode), **Obstacles**. The last two also give the agent an exteroceptive height map. Training budget 100 M steps (FT, Incline, Exploration) and 200 M steps (VT, Obstacles). |
| **Seeds** | **Three random seeds** per method per environment, mean ± standard deviation. Much weaker than Beukman's 16; the paper itself flags "the large variance in the return across different seeds." |
| **Ablation present?** | **Yes — the load-bearing one.** MetaMorph, MetaMorph* (their fixed re-implementation), FA alone, HN alone, FA+HN, plus two single-robot references. Also a proof-of-concept ablation motivating the whole design, and a diagnostic ablation of the baseline (§P2.5). |
| **Reported instability** | **Yes, several.** HN "is also known to be harder to optimize due to its more complicated hierarchical network architecture, and proper initialization of HN is critical to stabilize its training." A specific initialisation is required (**Bias-HyperInit**). A transformer context encoder "makes HN training unstable" — hence MLPs. HN **degrades** performance in Exploration, traced to a much higher value-prediction error. Conditioning attention on terrain rather than morphology gave "results even worse than the MetaMorph* baseline." |
| **Single- or multi-task** | **Multi-task by construction** — the task *is* the robot body. A Contextual MDP `(S_k, A_k, C_k, T_k, R_k)` per robot; unusually, the state and action spaces **differ across tasks** (different limb counts), which is why a transformer over limb-nodes is used at all. |

### P2.2 The mechanisms, precisely

#### Baseline — MetaMorph, and why the paper calls it a bias term

MetaMorph concatenates the time-variant proprioceptive observation `s^i_{k,t}` with
the time-invariant morphology context `c^i_k` as the node input, passes it through a
**shared** embedding layer to get `e_i`, updates all node embeddings with a
transformer encoder, optionally concatenates an MLP-encoded exteroceptive height
map, and decodes each node's action with a **shared** decoder. Key/query/value are
all derived from the node embedding: `k_i = W_k e_i`, `q_i = W_q e_i`,
`v_i = W_v e_i`. It additionally adds a learned positional encoding,
`e_i = Encoder(s^i_{k,t}, c^i_k) + PE_i`.

The paper's objection is capacity, not correctness: because `c^i_k` never changes
within a robot, concatenation "in effect [is] equivalent to just adding a
context-conditioned bias term to the node embedding layer", and "this may lack
sufficient model capacity to represent the diverse policies required to control
different morphologies", citing Galanti & Wolf's theory of hypernetwork modularity
plus empirical results from Ben-Iwhiwhu et al. and Beck et al.

#### Motivating experiment — behaviour diversity across limbs (§3.1.1)

Before proposing anything, they run a diagnostic on **single robots**: train
MetaMorph on one robot at a time (20 robots sampled from UNIMAL, 10 M steps each),
but replace the shared embedding layer with a **separate embedding per node**, and
separately with a **separate decoder per node**. Both variants beat the shared
version (Fig. 3). Conclusion: hard parameter sharing across limbs is a real
constraint, and letting limbs behave differently helps.

They then reject the naive fix for two named reasons — it cannot generalise to
unseen morphologies, and parameter count grows linearly with morphologies — which
is precisely the argument for generating those per-node parameters from context
instead. **This is the same argument Beukman gives for rejecting one-adapter-per-task
NLP-style adapters**, arrived at independently.

#### Module 1 — HN, context-conditioned parameter generation

$$\theta^i_k = \mathrm{HN}_\phi\!\left(c^i_k\right),$$

with a single shared `φ` across all nodes and all robots. Concretely, for the
embedding layer, MetaMorph's `e^i_k = W x^i_k + b` becomes

$$e^i_k = W^i_k\, x^i_k + b^i_k, \qquad W^i_k = \mathrm{HN}_W\!\left(c^i_k\right),\ \ b^i_k = \mathrm{HN}_b\!\left(c^i_k\right).$$

Only the **linear** layers of the base network are generated: the embedding layer
and the decoder. The rationale for sharing `φ` is generalisation *by similarity*:
"if two nodes play similar roles in two different morphologies (e.g., they are both
the left thigh in their robots), then we may expect them to also have similar
node-wise parameters" — the context vector is what makes that similarity available.

#### Module 2 — FA, morphology-conditioned fixed attention

Standard attention is

$$\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V .$$

In MetaMorph, `Q`, `K`, `V` all derive from the node embedding, which contains the
**time-varying** proprioceptive state; so the attention pattern changes at every
timestep. FA replaces `Q` and `K` with projections of the **context embedding**,
leaving `V` as the node embedding. Because the context is constant, the softmax
matrix is computed once per robot and reused — hence "fixed attention".

The stated inductive bias, in the authors' own analogy: "when you want to grasp an
object within your reach, you pay more attention to the state of your arm than your
leg… whether you are standing or sitting, which changes the proprioceptive
observations of body parts, has little influence on your attention strategy for
grasping." In other words: **which limbs should listen to which is a fact about the
body, not about the current pose.**

This is a structurally interesting design for the project, because it is a
modulation that *removes* a dependency rather than adding one — the operator is
"compute this routing from the slow signal only, and forbid the fast signal from
touching it." That is the opposite of the usual FiLM framing where the modulator
adds an extra input path.

### P2.3 Every head-to-head comparison, with numbers

Arms: **MetaMorph** (original code), **MetaMorph\*** (their corrected
re-implementation, and the honest comparison point since ModuMorph is built on it),
**FA**, **HN**, **FA+HN** (= ModuMorph), plus **SR-fair** (single-robot MLP at the
same per-robot budget) and **SR-10M** (single-robot MLP trained to convergence, used
as an upper bound). 3 seeds.

#### (a) Training performance — final return vs. MetaMorph* (§5.1)

Reported as percentage improvements in the prose (curves in Fig. 5; no numeric
table):

| Environment | ModuMorph (FA+HN) vs. MetaMorph* |
|---|---|
| Flat terrain (FT) | **+19 %** |
| Incline | **+53 %** |
| Exploration | **+48 %** |
| Variable terrain (VT) | **+31 %** |
| Obstacles | **+29 %** |

Context for those numbers: all multi-robot methods beat SR-fair (the sample-
efficiency argument for multi-task learning), but a gap to SR-10M remains;
ModuMorph "significantly reduces this gap (even outperforms SR-10M in
Exploration)." Where MetaMorph beats MetaMorph* (VT, Obstacles), ModuMorph still
beats **MetaMorph**.

#### (b) Zero-shot generalisation to kinematics/dynamics variations (§5.2, Fig. 6)

New robots with the **same topology** but perturbed parameters — six parameter
families tested (armature, damping, gear, density, limb params, joint angle), four
variants of each training robot per parameter, 64 rollouts each:

| Environment | ModuMorph vs. MetaMorph* |
|---|---|
| FT | **+26 %** |
| Incline | **+50 %** |
| Exploration | **+43 %** |
| VT | **+28 %** |
| Obstacles | **+30 %** |

Caveat the authors themselves raise: generalisation to **joint-angle** variation is
"much harder" for every method, because joint angles change the feasible action set
and the required gait.

#### (c) Zero-shot generalisation to unseen **topologies** — Table 1, verbatim

Held-out morphologies with different topology graphs; best per row bold in the
original; underline in the original marks methods not statistically distinguishable
from the best (Welch's t-test, α = 0.05). Reproduced exactly as printed (p. 8):

| Environment | MetaMorph | MetaMorph* | FA | HN | FA+HN |
|---|---|---|---|---|---|
| FT | 1384 ± 62 | 1266 ± 105 | 1439 ± 27 | 1259 ± 112 | **1490 ± 59** |
| Incline | 27 ± 32 | 312 ± 136 | **468 ± 58** | 312 ± 97 | 403 ± 66 |
| Exploration | 19 ± 1 | 19 ± 1 | 22 ± 2 | 16 ± 3 | **23 ± 3** |
| VT | 752 ± 62 | 767 ± 23 | 860 ± 112 | 900 ± 24 | **971 ± 122** |
| Obstacles | 866 ± 30 | 829 ± 50 | 937 ± 46 | 969 ± 47 | **1133 ± 12** |

Headline in the prose: ModuMorph beats MetaMorph* by **18 %, 29 %, 24 %, 27 % and
37 %** respectively.

**Read the columns, not just the last one.** This table is the batch's most
instructive ablation because the two operators dissociate:

- **FA (routing modulation) improves over MetaMorph\* in all five environments** —
  1439 vs 1266, 468 vs 312, 22 vs 19, 860 vs 767, 937 vs 829. Never harmful.
- **HN (weight generation) helps in only two of the five** (VT 900 vs 767;
  Obstacles 969 vs 829), is **neutral in two** (FT 1259 vs 1266; Incline 312 vs 312
  — identical to three significant figures), and is **actively harmful in one**
  (Exploration 16 ± 3 vs 19 ± 1).
- **FA+HN is not always the best arm.** On **Incline**, FA alone (468 ± 58) beats
  FA+HN (403 ± 66) by 16 %; adding weight generation *costs* performance there.
- The largest combined win (Obstacles, 1133 ± 12) is **super-additive**: FA gives
  +108 over MetaMorph*, HN gives +140, and together they give +304. So the two
  operators are not redundant.

#### (d) The paper's own diagnosis of when weight generation helps

§5.1, verbatim: HN "contributes more in the two environments with changing terrains
(VT and Obstacles)… This may imply that behavior diversity across nodes is more
important in environments that require complex locomotion skills, while in easier
terrains, the benefits of HN may be outweighed by its optimization challenges."

And for the failure: "adding HN harms learning performance in the Exploration
environment. The training statistics show that the HN variant has a **much higher
error in value prediction** compared to the other methods in Exploration… Value
prediction is particularly hard in Exploration, as the value depends on not only the
robot's status, but also the robot's visitation history in the arena, which is not
accessible to the robot. We hypothesize that this problem is more severe when using
the more complex HN architecture."

**This is the single most transferable warning in the paper for this project:** the
extra capacity of a weight-generating conditioner is spent on the *value* estimate
as much as on the policy, and in a task where the value function is intrinsically
hard to fit (partial observability — history not in the observation), the added
capacity makes value prediction *worse*, not better. A project agent in a
partially-observed environment is in exactly that regime.

#### (e) The negative result on conditioning attention on the fast signal

§5.1, Fixed Attention paragraph. They tried adding the terrain height map as an
additional input to the attention computation, so that routing could vary with
terrain, and "got results even worse than the MetaMorph* baseline." Their reading:
the height map already reaches the decoder, so attention only needs to model
*intra-morphology* interactions, and adding the fast signal to the attention
computation "may introduce further optimization challenges."

**Project reading:** giving a modulator a *fast* input in addition to its slow one
made things worse here, even though the fast information was genuinely relevant and
was already being used elsewhere in the network. This is one of the few direct data
points in the folder on the question "should a modulator read the fast signal too?"
and the answer here is no.

### P2.4 Stability apparatus — what had to be done to make weight generation train

Appendix A.1, and worth reading as a checklist rather than a footnote:

1. **Bias-HyperInit** (from Beck et al. 2022). The hypernetwork's output layer is a
   linear map from context encoding to base-network parameters, with one independent
   output head per modulated layer. It is initialised with **weights set to 0** and
   **biases sampled from the distribution that would have initialised the modulated
   layer directly**. Consequence, in the authors' words: "all the nodes share the
   same control parameters just like MetaMorph at the beginning, and gradually
   develop node-wise diversity while the HN weights are updated."
   **This is the same idea as FiLM's identity-initialisation / AdaLN-Zero** that the
   folder's existing corpus documents repeatedly: *start the modulator at "do
   nothing", let it earn its influence.* Here it is applied to weight generation
   rather than to a gain, and the paper calls proper initialisation "critical to
   stabilize its training."
2. **Small, simple context encoders.** MLPs, not transformers or GNNs, for two
   stated reasons: (i) the effective sample size for the context encoder is the
   *number of robots*, not the number of timesteps, because context is constant per
   robot — so high capacity risks overfitting; (ii) "using transformers as the
   context encoder makes HN training unstable." **Point (i) is a general and easily
   overlooked observation:** a modulator conditioned on a slow signal sees far fewer
   effective training examples than the policy it modulates, and should be sized
   accordingly.
3. **Separate encoders per module.** The HN and FA context encoders are independent
   (the figure shows one only for clarity).
4. **PPO early-stopping threshold tuned per method per environment** over
   `{0.03, 0.05}` (Table 2). Necessary because they removed the baseline's dropout
   (see §P2.5), but it is a per-arm hyperparameter and therefore a mild confound in
   the comparison — the ranking is not established at a single shared setting.

**Compute:** HN increases training cost but has **no deployment cost** — since
context is fixed per robot, all node-wise parameters can be generated once, offline.
FA adds essentially no training cost (it only changes what feeds `Q` and `K`) and
*reduces* evaluation cost, since the attention matrix is computed once per robot.
This mirrors Beukman's unexploited caching observation; ModuMorph actually exploits
it.

### P2.5 The baseline audit (Appendix C) — a methodological contribution in its own right

The authors could not reproduce MetaMorph's reported benefit from positional
encoding, and dug in. Two findings:

1. **The reported PE gain is actually a dropout gain.** MetaMorph's code implements
   `e'_i = dropout(e_i + PE_i)`. Testing `dropout(e_i)` and `e_i + PE_i`
   separately, "the dropout operation is the main contributor here, while PE alone
   makes little difference in training performance" (Fig. 10). **Why PE fails
   multi-robot:** a morphology is a *tree*, so MetaMorph flattens it by depth-first
   search and indexes nodes by sequence position — but (a) nodes at the same index
   play different physical roles in different robots, and (b) there is no intrinsic
   order among a node's children, so two identical morphologies can receive
   completely different PE (Fig. 11). Confirmed by a clean control: **in single-task
   training, where no inconsistency is possible, PE does help** (Fig. 12). PE is
   therefore dropped from MetaMorph*.
2. **The dropout that helps is a *bug*.** MetaMorph resamples a fresh dropout mask
   when a state is reused for the policy update, so the PPO importance ratio is
   `r' = π_θ(a|s;m') / π_{θ_k}(a|s;m)` with `m' ≠ m` — meaning `r ≠ 1` even before
   any policy update, which "does not make sense intuitively." Empirically the
   inconsistent mask **keeps the ratio distribution stable across epochs**
   (Fig. 13), i.e. it accidentally implements a trust region. MetaMorph's own early
   stopping was set to a threshold of 0.2, too large to ever trigger. MetaMorph*
   removes the buggy dropout and sets the early-stopping threshold to 0.03–0.05,
   recovering the same performance principledly.

For the project this is a worked example of a general hazard: **a reported
architectural gain that is really a regularisation artefact of an implementation
bug.** It also explains why MetaMorph* is sometimes *worse* than MetaMorph (VT,
Obstacles) — the bug was doing useful work — and why the authors honestly report
both baselines.

### P2.6 Qualitative and mechanistic evidence (§5.4)

Beyond returns, they show *what changes*:

- **Behaviour.** On one example morphology in FT, MetaMorph* moves by kicking with a
  front limb that never fully extends, falls twice in 1000 steps, and reaches a best
  return of **1375**. ModuMorph fully extends the front limb, coordinates front and
  back, never fails during evaluation, and reaches **4612**.
- **Limb coordination, quantified.** They compute the correlation matrix between
  action dimensions as a proxy for behavioural synergy. On the example robot,
  ModuMorph's joint 2 (front limb) is far better synchronised with joints 3 and 4
  (back limbs). Aggregated across all training morphologies in VT, mean action
  correlation is **0.24 for MetaMorph\* vs 0.29 for ModuMorph**.

This is a modest but real attempt to show a *mechanism* rather than only a score,
and it is more than Beukman offers for its distractor result.

### P2.7 Phase 1 — Foundational overview

**The problem.** Train one controller that can drive many differently-shaped robots
— different numbers of legs, different limb lengths and masses — and have it work
on body plans it has never seen. Because limb counts differ, the observation and
action vectors have different sizes across robots, so the standard trick is to treat
each limb as a token and run a transformer over the limbs.

**What everyone was doing.** Prior work concentrated on the *architecture* for
handling variable numbers of limbs (graph networks, then transformers) and treated
the body description itself casually: paste the body numbers onto each limb's input
and let the network sort it out.

**The paper's objection.** Because the body description never changes during an
episode, pasting it onto the input does exactly one thing — it shifts each limb's
embedding by a fixed amount. A shift cannot make one robot's controller
*qualitatively* different from another's; it can only offset it. Different bodies
plausibly need different control *strategies*, not offsets of a common one.

**The two proposals.**
1. **Write the weights instead of shifting the inputs.** A small side-network reads
   a limb's description (its size, mass, and where it attaches) and outputs the
   actual weights of that limb's input layer and output layer. Every limb of every
   robot gets its own personal input and output layer, but they are all produced by
   one shared generator, so the system can still handle a limb it has never seen —
   it just feeds that limb's description in. The biological analogy the authors
   offer: different muscles are driven by different classes of motor neuron
   according to their identity.
2. **Decide who listens to whom from the body alone.** In a transformer, the
   attention pattern says which limbs each limb should take into account. Normally
   it is recomputed every timestep from the current sensor readings. The paper
   argues this is wrong: which limbs matter to which is a fact about anatomy, not
   about the current pose. So compute the attention pattern from the body
   description only, once per robot, and freeze it for the episode.

**Findings.** On a benchmark of 100 training and 100 held-out robot bodies across
five locomotion tasks, the combination raises final training return by 19–53 % and
zero-shot return on unseen bodies by 18–37 % against the same backbone. The two
ideas contribute differently: **freezing attention on anatomy helps in all five
tasks and never hurts; generating weights helps in the two hardest tasks, does
nothing in two, and hurts in one.** In the task where it hurts, the diagnosis is
that the *value estimate* — the agent's prediction of how much reward is still
coming — becomes much less accurate, because that task is partially observed and the
richer architecture makes an already hard prediction harder.

**Initial takeaway.** Two things, one encouraging and one cautionary. Encouraging:
a slow, structural conditioning signal really can be worth more than an extra input
coordinate, and the gain survives to unseen conditions. Cautionary: the more powerful
the modulator, the more it can damage the value function, and it needs to be
initialised so that it starts out doing nothing at all.

### P2.8 Phase 2 — Graduate-level deep dive

#### P2.8.1 The problem formulation

A set of `K` robots, each a Contextual MDP `(S_k, A_k, C_k, T_k, R_k)`. All robots
are drawn from a **modular design space**: robot `k` is a tree over `N_k` nodes
(limbs), and every node shares a common node-level state and action space, so

$$S_k = \{S^i_k \mid i = 1,\dots,N_k\}, \qquad A_k = \{A^i_k \mid i = 1,\dots,N_k\}.$$

The context comprises node-wise features `{C^i_k}` plus the adjacency matrix. The
objective is the average return across training robots,

$$\max_{\theta}\ \left[\frac{1}{K}\sum_{k=1}^{K}\sum_{t=0}^{H} r_{k,t}\right],$$

for a single universal policy `π_θ(a_{k,t} | s_{k,t}, c_k)`, with the additional
requirement of zero-shot transfer to unseen morphologies.

#### P2.8.2 Derivation: concatenation of a slow context is an additive bias

This is asserted in the paper without derivation; it is worth writing out because
the project will want to cite it. Take MetaMorph's shared embedding layer applied to
the concatenated node input:

$$x^i_{k,t} = \begin{bmatrix} s^i_{k,t} \\ c^i_k \end{bmatrix} \in \mathbb{R}^{d_s + d_c}, \qquad e^i_k = W x^i_{k,t} + b, \quad W \in \mathbb{R}^{d_e \times (d_s + d_c)}.$$

Split `W` column-wise into the block acting on the state and the block acting on the
context, `W = [\,W_s \ \ W_c\,]`. Then

$$e^i_{k,t} = W_s\, s^i_{k,t} + W_c\, c^i_k + b .$$

Since `c^i_k` is constant for the whole episode (indeed for the whole robot), the
term `W_c c^i_k + b` is a constant vector `β^i_k` that does not depend on `t`:

$$e^i_{k,t} = W_s\, s^i_{k,t} + \beta^i_k, \qquad \beta^i_k \equiv W_c\, c^i_k + b .$$

So the entire effect of the context, *at this layer*, is an additive per-node offset.
Comparing with the general FiLM form `γ(c) ⊙ h + β(c)`:

$$\underbrace{e^i_{k,t} = \mathbf{1} \odot \left(W_s s^i_{k,t}\right) + \beta^i_k}_{\text{concatenation}} \quad\text{vs.}\quad \underbrace{\gamma(c) \odot \left(W_s s^i_{k,t}\right) + \beta(c)}_{\text{FiLM}} \quad\text{vs.}\quad \underbrace{W(c)\, s^i_{k,t} + b(c)}_{\text{ModuMorph's HN}} .$$

The three are nested: concatenation is FiLM with `γ ≡ 1`; FiLM is weight generation
restricted to `W(c) = diag(γ(c)) W_s` — i.e. a **diagonal** rescaling of a fixed
weight matrix, expressed in the fixed basis that `W_s` happens to define. ModuMorph's
HN lifts that restriction entirely: `W(c)` is unconstrained, so it can rotate as
well as rescale.

Two consequences worth stating explicitly, since they connect this paper to §P1:

- **The concat baseline is not "no modulation".** It is the `γ ≡ 1` corner of the
  modulation family. Any project comparison that frames concat as the unmodulated
  control is mislabelling the arm — concat *is* a modulator, of the weakest kind.
- **This nesting is the same nesting Beukman proves** in his Appendix C, approached
  from the other side. Beukman shows FiLM ⊂ generated-adapter; Xiong shows
  concat ⊂ FiLM. Together the batch establishes the full chain
  **concat ⊂ FiLM ⊂ generated low-rank adapter ⊂ generated full layer**, with
  citable arguments for each inclusion.

  **Caveat on the derivation's scope.** The equivalence holds for *this* architecture
  — a single linear embedding layer applied to the concatenated vector. The moment
  the concatenated vector passes through a *nonlinearity* before the split matters,
  or through more than one layer, `W_c c + b` no longer factors out and the
  equivalence is only approximate. The paper's claim is exact for MetaMorph's
  one-layer node embedding and should be quoted with that qualifier.

#### P2.8.3 Fixed attention, written out

Standard scaled dot-product attention over the `N_k` limb tokens, with all three
projections derived from the node embedding `e_i` (which contains the fast
proprioceptive state):

$$q_i = W_q e_i,\quad k_i = W_k e_i,\quad v_i = W_v e_i,\qquad \mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^{\top}}{\sqrt{d_k}}\right) V .$$

ModuMorph introduces a context encoder `g_{FA}` (3-layer MLP, 128 units) and sets

$$q_i = W_q\, g_{FA}\!\left(c^i_k\right), \qquad k_i = W_k\, g_{FA}\!\left(c^i_k\right), \qquad v_i = W_v\, e_i,$$

so that

$$A_k = \mathrm{softmax}\!\left(\frac{ g_{FA}(C_k) W_q^{\top} W_k\, g_{FA}(C_k)^{\top}}{\sqrt{d_k}}\right)$$

is a function of the morphology alone: `A_k` has **no `t` index**. The layer output
is `A_k V_t`, a fixed mixing matrix applied to time-varying values.

Three observations the paper does not make but which matter for reading it as a
modulation paper:

1. **This is a linear, input-independent mixing of features across tokens** — much
   closer to a *learned, context-selected graph convolution* than to attention. The
   paper's own framing ("a structure-aware inductive bias") is accurate; calling it
   attention is a statement about where it sits in the code, not about what it
   computes.
2. **It removes a pathway rather than adding one.** The fast signal loses its route
   into the routing decision. That is a *restriction* of the hypothesis class, and
   the empirical result (helps in all five environments, never hurts) is therefore a
   result about a **beneficial inductive bias**, not about added capacity. It is the
   mirror image of the HN result, which adds capacity and helps unevenly.
3. **Its robustness relative to HN is consistent with (2).** Restrictions that
   encode a true structural fact are cheap — they cost no parameters and cannot
   destabilise optimisation. Added capacity has to be paid for in optimisation
   difficulty, which is exactly the trade-off the Exploration failure exposes.

#### P2.8.4 Bias-HyperInit, and its relationship to identity-initialised FiLM

The HN output layer maps context encoding `z = g_{HN}(c)` to base parameters through
a per-layer linear head:

$$\theta = W_{out}\, z + b_{out}.$$

Bias-HyperInit sets

$$W_{out} \leftarrow \mathbf{0}, \qquad b_{out} \sim \mathcal{D}_{\text{init}},$$

where `D_init` is the initialisation distribution the modulated layer would have used
if it were a normal layer. At initialisation, therefore,

$$\theta^i_k = \mathbf{0}\cdot z^i_k + b_{out} = b_{out} \quad \forall i, k,$$

i.e. **every node of every robot receives the same weights**, exactly reproducing
MetaMorph's shared layer, and with the correct variance scaling for that layer's
fan-in. Context-dependence then grows from zero as `W_out` receives gradient.

The parallel to the folder's FiLM corpus is exact in structure. AdaLN-Zero
initialises the modulation head so that `γ = 1, β = 0`, making the modulated block
the identity at step 0; Bias-HyperInit initialises the generation head so that
`∂θ/∂c = 0`, making the generated layer *context-independent* at step 0. Both
implement the same principle — **the conditioner starts with zero influence and must
earn it** — and both are reported as necessary rather than optional. That the same
device is independently required for an affine modulator and for a weight generator
is a strong signal that it is a property of *conditional architectures in general*,
not of FiLM specifically. Worth recording as a cross-paper finding.

### P2.9 What the paper does **not** establish

1. **No FiLM arm.** Despite the title's "contextual modulation", there is no
   scale-and-shift baseline. The comparison is concat-as-bias vs. attention-routing
   vs. weight-generation. FiLM appears only as a citation in §6 ("feature-wise
   multiplication", citing Ben-Iwhiwhu et al. and Benjamins et al.).
2. **Three seeds.** With Table 1 standard deviations as large as ±136 (Incline,
   MetaMorph*) and ±122 (VT, FA+HN), several of the pairwise orderings are not
   resolvable. The paper's own Welch's t-test underlining acknowledges this, and it
   itself notes "the large variance in the return across different seeds."
3. **Per-arm hyperparameter tuning.** The PPO early-stopping threshold is tuned per
   method per environment. Small, and disclosed, but the arms are not compared at a
   single shared setting.
4. **Critic architecture unstated.** Whether the value function shares the modulated
   architecture is never described, which is unfortunate given that the paper's own
   diagnosis of its worst result is a value-prediction failure.
5. **Context is hand-designed and given.** "we directly used the original node
   context features provided in the benchmark… as the modulator input, and a simple
   MLP as the context encoder"; learning better context representations is named as
   the first item of future work. No inference from transitions anywhere.
6. **The transformer encoder is never weight-generated** — only the embedding and
   decoder. So "weight generation" here means the *boundary* layers, not the trunk.
7. **The modular design-space assumption** (every robot is a tree of interchangeable
   limbs sharing a node-level state/action space) is acknowledged as possibly false
   for real robots.

### P2.10 Relevance to this project

- **Cite this for the concat-is-a-bias-term argument**, with the derivation in
  §P2.8.2 and the one-layer caveat attached. It is the cleanest available statement
  of why concatenating a slow signal is a weak form of conditioning, and it makes
  the project's "concat vs. FiLM" framing precise rather than rhetorical.
- **The dissociation is the finding.** Routing modulation (FA) is cheap, safe and
  universally helpful; capacity modulation (HN) is expensive, unstable and helpful
  only when the task is hard enough to need it. A project design that wants a low-risk
  first step should look at conditioning *where information flows* before conditioning
  *how much of it there is*.
- **The value-function warning is the most portable result.** Weight generation made
  value prediction *worse* in the one environment where value prediction was
  intrinsically hard because relevant history was not in the observation. Any
  project agent operating under partial observability should expect this and should
  log a value-loss / explained-variance metric alongside return when a modulator is
  added — a return curve alone would have shown only "HN is worse", not why.
- **Initialisation is a hard requirement, not a nicety.** Bias-HyperInit here and
  identity-init/AdaLN-Zero in the folder's FiLM corpus are the same principle.
  Any project conditional module should start at zero influence.
- **Size the conditioner by the number of distinct context values, not the number of
  timesteps.** The observation that the context encoder's effective sample size is
  the *number of robots* is directly transferable: if a project modulator reads a
  signal that takes few distinct values, a large modulator will overfit those values
  regardless of how many environment steps are collected.
- **A modulator given the fast signal in addition to the slow one did worse.** The
  height-map-into-attention experiment is a genuine negative result on
  self-conditioning-style designs, in a setting where the fast information was
  relevant and already available elsewhere in the network.
- **Contrast with Beukman on the on/off-policy axis.** This is the batch's only
  on-policy (PPO) result, and it is the one where the weight-generating module is
  unstable. Beukman's off-policy SAC result shows no comparable optimisation
  difficulty. That is a confound worth holding in mind before generalising either
  paper's verdict on hypernetworks.

### P2.11 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Universal policies across morphologies improve efficiency and generalisation but pose a hard multi-task RL problem because the optimal policy depends critically on morphology. Prior GNN/transformer work handles heterogeneous state/action spaces but pays little attention to that dependency. Proposes a **hierarchical architecture** with two submodules: hypernetwork-generated morphology-dependent control parameters instead of hard parameter sharing, and a **fixed attention** mechanism depending solely on morphology. Improves both training performance and zero-shot generalisation. Code released. |
| 1 | **Introduction** | Per-morphology training does not scale. Multi-task RL treats each robot as a task; morphology is the task context — an injured leg needs a different gait, a tail changes locomotion. Prior work concentrates on architecture (GNNs, transformers) rather than on context use. Feeding context as an extra input or as morphology-aware positional encoding "in effect… [is] equivalent to just adding a context-conditioned bias term to the node embedding layer", which may lack capacity, citing theory (Galanti & Wolf) and empirics (Ben-Iwhiwhu, Beck). Proposes **ModuMorph** = base controller + context modulator. Modules in principle transferable to any transformer or GNN backbone; here built on **MetaMorph** and evaluated on **UNIMAL**. |
| 2 | **Background** | **2.1 Problem formulation** — `K` robots, each a CMDP `(S_k, A_k, C_k, T_k, R_k)`; modular design space so each robot is a tree of nodes sharing node-level state/action spaces; context = node-wise features (limb size, mass, initial position relative to parent) + adjacency matrix; objective is the average return over training robots plus zero-shot transfer. **2.2 Transformers for universal control** — attention over limb tokens handles variable limb counts; standard `softmax(QKᵀ/√d_k)V`; multiple heads; feedforward, normalisation, skip connections; stackable. **2.2.1 MetaMorph** — concatenate proprioception with context per node → shared embedding → transformer encoder → optional exteroceptive height map concatenated → shared decoder → per-node actions; `k_i = W_k e_i`, `q_i = W_q e_i`, `v_i = W_v e_i`. Objection stated: context is constant, so it acts as a bias; insufficient expressive power. MetaMorph also adds learned PE, `e_i = Encoder(s,c) + PE_i`, which the authors find provides little help (analysis in App. C) and omit. **2.3 Hypernetworks** — `θ = HN_φ(c)`; better parameter complexity than concatenation (Galanti & Wolf) and lower gradient variance (Sarafian); but harder to optimise, and **proper initialisation is critical**. |
| 3 | **Method** | **3.1 Context conditioning via hypernetworks** — hard parameter sharing across nodes limits behaviour diversity and capacity; neuroscience analogy (motor-neuron classes by muscle identity). **3.1.1 Proof-of-concept** — single-robot MetaMorph with per-node embeddings, and separately per-node decoders, both beat the shared version on 20 robots at 10 M steps each (Fig. 3); but per-node parameters do not generalise and scale linearly. **3.1.2 HN** — `θ^i_k = HN_φ(c^i_k)` with shared `φ`; embedding example `e^i_k = W^i_k x^i_k + b^i_k`; only linear layers (embedding, decoder) are generated because a transformer layer has too many matrices. **3.2 Fixed attention** — the attention matrix should reflect anatomy, not pose (arm-vs-leg grasping analogy); node embedding supplies only `V`, context embedding supplies `Q` and `K`, so the attention matrix is fixed per robot. **3.3 Computational cost** — HN costs training time but nothing at deployment (parameters precomputed per robot); FA costs nothing extra in training and *saves* compute at evaluation. |
| 4 | **Experimental Setup** | **Environments** — UNIMAL, 100 train + 100 test morphologies, five tasks: FT, Incline (10°), Exploration, VT (variable terrain resampled per episode), Obstacles; the last two add an exteroceptive height map. **Baselines** — multi-robot: MetaMorph and **MetaMorph\*** (their corrected version, on which ModuMorph is built; both reported for fairness); single-robot: SR-fair (same per-robot budget, for sample-efficiency comparison) and SR-10M (10 M steps, as an upper bound), each a 3×256 MLP chosen by grid search. **Ablations** — FA only, HN only, FA+HN. **Training setup** — 100 M steps (FT/Incline/Exploration), 200 M (VT/Obstacles), **3 seeds**, PPO, early-stopping threshold tuned over `{0.03, 0.05}` per method per environment, all other hyperparameters as in MetaMorph. **Evaluation** — two zero-shot regimes of increasing difficulty: same topology with perturbed kinematics/dynamics parameters (4 variants per training robot per parameter), and unseen topology graphs; 64 rollouts per robot; mean episodic return. |
| 5 | **Results** | **5.1 Training** — all multi-robot methods beat SR-fair; a gap to SR-10M remains; ModuMorph narrows it and beats SR-10M in Exploration; +19 %, +53 %, +48 %, +31 %, +29 % over MetaMorph* in FT/Incline/Exploration/VT/Obstacles, and beats MetaMorph even where MetaMorph beats MetaMorph*. Ablation: **FA improves in all five**, more so on unchanged terrain; **HN helps in three of five**, more so on changing terrain, and **harms Exploration**, traced to much higher value-prediction error under partial observability. Negative result: conditioning attention on the terrain height map was worse than the baseline. **5.2 Kinematics/dynamics generalisation** — +26 %, +50 %, +43 %, +28 %, +30 %; joint-angle variation remains much harder for all methods. **5.3 Unseen topologies** — Table 1; +18 %, +29 %, +24 %, +27 %, +37 % over MetaMorph*; ordering tracks training performance, so the gains are not overfitting to training morphologies; large across-seed variance acknowledged. **5.4 Qualitative** — locomotion visualisation (MetaMorph* best trial 1375 with two falls; ModuMorph 4612 with none) and action-correlation analysis (VT mean correlation 0.24 → 0.29). |
| 6 | **Related Work** | *Universal morphology control* — same-morphology parameter variation (MLP-based, cannot handle heterogeneous spaces); GNNs; transformers (Kurin et al.: GNNs struggle with distant nodes); recent work adding morphology info by concatenation or positional encoding, which "in effect just add a context-conditioned bias term"; node-wise or morphology-wise parameters improve learning but do not generalise or scale. *Contextual modulation in RL* — architecture choice reflects inductive bias; alternatives to concatenation include **feature-wise multiplication** (Ben-Iwhiwhu; Benjamins — i.e. the FiLM/cGate line), **routing networks** (Yang et al. soft modularization; Sodhani et al. CARE; Ponti et al.), and **hypernetworks** (Yu; Peng; Sarafian; Beck; Rezaei-Shoshtari). This paper targets the harder morphology-control domain where tasks do not share state/action spaces. |
| 7 | **Conclusion** | Restates the two modules and the results. Future work: learn better context representations (they used the benchmark's raw node features and a simple MLP encoder); improve zero-shot generalisation, still far from directly-trained performance; relax the modular design-space assumption; extend to joint morphology-and-control optimisation. |
| A | **Implementation Details** | **A.1** — GNN/transformer context encoders were tried; MLPs performed similarly or better, hypothesised because the context encoder's effective sample size is the *number of robots*, so high capacity overfits; also, transformer context encoders "make HN training unstable". Two separate context encoders: 2-layer MLP for HN, 3-layer for FA, 128 units each. HN output layer = linear map with one head per modulated layer, initialised by **Bias-HyperInit** (weights 0, biases drawn from the modulated layer's own init distribution) so all nodes start identical to MetaMorph and diversify as HN weights update. **A.2** — proprioceptive and context features identical to MetaMorph's. |
| B | **PPO and Early Stopping** | PPO clipped objective written out; one iteration = `T` epochs × `B` minibatches; the clipping objective alone does not enforce the trust region, so early stopping on approximate KL with threshold `δ` is used. `δ` tuned over `{0.03, 0.05}`; Table 2 gives the chosen value per method per environment. Smaller values stop too early; larger values allow too big a trust region. |
| C | **Analysis on MetaMorph** | Motivates MetaMorph*. The reported PE benefit is really a **dropout** benefit: the code computes `dropout(e_i + PE_i)`; separating the two shows PE alone makes little difference (Fig. 10). **C.1 Why PE does not help** — the morphology is a tree flattened by DFS, so the same index means different roles across robots, and sibling order is arbitrary, so identical morphologies can get completely different PE (Fig. 11); confirmed by the control that PE *does* help in single-task training (Fig. 12). **C.2 Why dropout helps** — the code resamples the dropout mask at update time, so the PPO ratio `r' = π_θ(a\|s;m')/π_{θ_k}(a\|s;m)` is noisy and `≠ 1` even before any update; empirically this keeps the ratio distribution stable across epochs (Fig. 13), accidentally acting as a trust region. MetaMorph's own early-stopping threshold of 0.2 rarely triggers; setting it to 0.03–0.05 recovers the same performance without the inconsistent dropout. |

---
