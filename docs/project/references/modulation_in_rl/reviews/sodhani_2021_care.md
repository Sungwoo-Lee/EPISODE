---
title: "Multi-Task Reinforcement Learning with Context-based Representations (CARE)"
slug: sodhani_2021_care
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_classics.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 2. Sodhani et al. 2021 — *Multi-Task Reinforcement Learning with Context-based Representations* (CARE)

**PDF:** `docs/project/references/modulation_in_rl/sources/Sodhani et al. 2021 - Multi-task reinforcement learning with context-based representations (CARE).pdf`
**Venue as printed (PDF p. 1 footer):** *"Proceedings of the 38th International Conference on Machine Learning, PMLR 139, 2021. Copyright 2021 by the author(s)."* — ICML 2021.
**Authors:** Shagun Sodhani (Facebook AI Research), Amy Zhang (FAIR / Mila / McGill), Joelle Pineau (FAIR / Mila / McGill).

### 2.1 Plain-English entry point

Meta-World's 50 robot-manipulation tasks all use the same-sized sensor vector, but
the *meaning* of each number changes from task to task — dimension 7 might be a
drawer handle in one task and a goal marker in another. A single shared network
therefore has to guess what it is looking at. What the agent is not usually given, but
almost always *has*, is a plain-English description of the job: "Open a drawer",
"Push and close a window". CARE's claim is that this free-text description — the
paper calls it **metadata** — is the missing key, because English descriptions of
related tasks are *themselves* related, and that relatedness tells the network what to
share.

CARE turns the description into a vector with a frozen off-the-shelf language model
(RoBERTa), shrinks it with a small MLP, and then uses it in **two** places. First, it
**picks among a bank of parallel state-encoders**: `k` small networks all read the
same sensor vector, produce `k` competing summaries, and an attention score computed
against the description decides how much each summary contributes to the blend.
Second, the description vector is **concatenated onto the blended summary**, and the
pair is what the actor and critic actually see.

**Headline result.** On Meta-World MT10 after 2 M steps, CARE reaches **0.84 ± 0.051**
mean success against **0.75 ± 0.037** for a FiLM-conditioned SAC, **0.73 ± 0.043** for
Soft Modularization (paper #1 of this file), and **0.49 ± 0.073** for plain multi-task
SAC — with a per-task-specialist ceiling of **0.90 ± 0.032**. On MT50 after 2 M steps,
**0.54 ± 0.031** vs 0.40 for FiLM and 0.50 for Soft Modularization.

**Why the project cares.** CARE is the paper that put **FiLM and routing and
concatenation on the same benchmark with the same 10 seeds** — it is the only
head-to-head in the historical corpus, and it is therefore the reference point any
"per-task modulation helps" claim gets measured against. It also, quietly, does *not*
statistically beat Soft Modularization at the two larger sample budgets, which is a
result the downstream literature routinely omits.

### 2.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | ICML 2021 — *Proceedings of the 38th International Conference on Machine Learning, PMLR 139, 2021* (p. 1 footer). |
| **RL algorithm** | **SAC**. Explicitly stated to be swappable: *"CARE can be paired with any policy optimization method."* CARE is a **representation-learning** module, not an RL algorithm. |
| **Conditioning signal** | **Natural-language task metadata** — a free-text description such as *"Open a door with a revolving joint"*. Embedded by a **frozen RoBERTa** into 768 dimensions, then projected by a 2-layer feedforward "context encoder" (hidden/output dims = 50) to `z_context`. The paper stresses the metadata may be *"high-level, under-specified, and unstructured"* and *"does not have to explain how to perform the task"*. Metadata is contrasted explicitly with the standard *"simplistic context in the form of an ordinal task id"*. |
| **What is modulated** | The **state encoder**, and only the state encoder. There is no per-layer conditioning of the policy or critic MLPs. Actor and critic are ordinary 3-layer, 400-unit MLPs that consume the conditioned representation `z_s`. Because encoder + representation are **shared between actor and critic**, the conditioning reaches both — but indirectly, through a single shared input, not through separate modulators (contrast paper #1, where actor and critic each carry their own router). |
| **The operator** | **Two operators, stacked, neither of them affine modulation.** (i) **Soft attention / mixture over encoders** — a convex combination of `k` parallel encoder outputs, weights from a dot product against the context: `α_j = softmax_j(z^j_enc · stopgrad(z_context))`, `z_enc = MLP(Σ_j α_j z^j_enc)`. (ii) **Concatenation** — `z_s = z_context :: z_enc`. So the context both *routes* and *is appended*. **No gain, no offset, no generated weights.** |
| **Granularity** | **Per-encoder** — `k` scalars per forward pass (`k = 6` for MT10, `k = 10` for MT50). One weight per whole encoder output vector; no per-unit or per-channel resolution anywhere. |
| **Placement** | **One site**, at the encoder output, before the policy/critic trunk. Compare paper #1's `L−1` inter-layer sites and FiLM's per-block sites. CARE is the shallowest conditioning in this file. |
| **Ablated against concatenation?** | **Yes, thoroughly, and against FiLM as well.** The ladder is: `Multi-task SAC` (task-ID conditioning at all only via per-task temperature) → `Multi-task SAC + Task Encoder` (learned task embedding, concatenated) → `Multi-headed SAC` → `PCGrad` → `Soft Modularization` (routing) → `SAC + FiLM` (affine modulation of the encoder on the same context) → `CARE`. Plus a factorial ablation isolating the two ingredients (`SAC + ME` = mixture without metadata, `SAC + Metadata` = metadata without mixture). 10 seeds throughout, with Welch's t-test at p = 0.05. |
| **Reported instability** | **None about the mechanism.** The paper's stability discussion is entirely about **evaluation protocol**, and it is unusually candid: evaluation frequency acts as *"an implicit hyperparameter"* (Table 19), and seed count changes results drastically — the authors get 0.61 for multi-headed SAC on MT10 with 10 seeds where Yu et al. report 0.88 with 1 seed, *"leading to a 44 % change in performance"*. |
| **Single-task or multi-task** | **Multi-task only** (MT10, MT50), plus a small zero-shot held-out-task experiment. |
| **Claim strength** | **Ablated**, with statistical testing — and the testing partially *undercuts* the headline (see §2.6). |

### 2.3 Phase 1 — Foundational overview

**The problem, formalised.** The authors formalise multi-task RL as a **Block
Contextual MDP (BC-MDP)**: a tuple `⟨C, S, A, M′⟩` where a context `c` selects not only
the reward and transition functions but also *the observation space*
`M′(c) = {R^c, T^c, S^c}`. This extends Hallak et al.'s Contextual MDP, which assumed a
shared state space across contexts. Meta-World is offered as a natural instance: all
tasks share the ambient dimensionality but *"those dimensions have different semantics
across tasks"*. Crucially the authors argue this is **not** partial observability,
*"because we have access to a task id or description that uniquely identifies the
task, and therefore what objects are referred to by the task-specific state space"*.

**The inductive bias.** Tasks share **objects** (drawer, door, window, puck) and
**skills** (open, close, push). So learn a small bank of encoders that specialise to
objects and skills, and let the task's description say which ones matter. The paper is
explicit that this is a *softer* bias than object-oriented learning: no privileged
object labels, no explicit modelling of interactions between encoders (contrast Goyal
et al.'s RIMs, Kipf et al.'s graph nets).

**The mechanism in one line.** Frozen language model → small MLP → `z_context`;
`k` parallel encoders → `k` summaries; dot-product attention picks the blend;
concatenate the context back on; hand to SAC.

**Initial takeaway.** Conditioning on *what the task is about* — carried by language,
which already encodes the compositional structure — beats conditioning on *which task
this is* (a one-hot or a learned embedding). And the useful operator, on this
benchmark, is a **mixture over specialised sub-encoders**, not a rescaling of one
general encoder.

### 2.4 Phase 2 — Graduate-level deep dive

#### 2.4.1 The BC-MDP, stated precisely

**Definition (Contextual MDP, Hallak et al. 2015).** `⟨C, S, A, M⟩` with `M(c) = {R^c, T^c}`.

**Definition (Block Contextual MDP, this paper).** `⟨C, S, A, M′⟩` with

$$
M'(c) \;=\; \{\,R^{c},\; T^{c},\; \mathcal{S}^{c}\,\},\qquad \mathcal{S}^{c}\subseteq \mathcal{S},
$$

so the observation space itself is context-dependent. In this work `S^c` is *"a strict
subset of the dimensions in `S`"* — the low-dimensional setting. The footnote matters:
*"the dynamics `T^c` for each MDP are still different because the state spaces are
different"*, while the underlying **object-specific dynamics are assumed consistent
across tasks**. That assumption is what licenses encoder reuse at all.

#### 2.4.2 The context encoder

$$
z_{\text{context}} \;=\; C\big(\text{metadata}\big) \;=\; \mathrm{MLP}_{\omega}\big(\mathrm{RoBERTa}(\text{description})\big)\in\mathbb{R}^{50},
$$

with RoBERTa producing 768 dimensions and **frozen** (*"the language model is not
updated during training"*), and `MLP_ω` a two-layer feedforward network with
hidden/output dims 50, trained by the RL losses.

#### 2.4.3 The attention, derived

Given `k` encoders `E_1, …, E_k` and a state `s^i_n` from task `T_i`:

$$
z^{j}_{\text{enc}} \;=\; E_{j}\big(s^{i}_{n}\big), \qquad j = 1,\dots,k .
$$

The context is **detached from the computation graph** before the score is computed:

$$
\bar z^{\,i}_{\text{context}} \;=\; \mathrm{stopgrad}\big(z^{i}_{\text{context}}\big).
$$

Scores are raw inner products, normalised over the encoder index:

$$
\alpha_{j} \;=\; \frac{\exp\big(\langle z^{j}_{\text{enc}},\, \bar z^{\,i}_{\text{context}}\rangle\big)}{\sum_{j'=1}^{k}\exp\big(\langle z^{j'}_{\text{enc}},\, \bar z^{\,i}_{\text{context}}\rangle\big)},
\qquad \sum_{j}\alpha_j = 1,\ \ \alpha_j \ge 0 .
$$

Then the pooled representation and the final state encoding:

$$
z^{i}_{\text{enc}} \;=\; \mathrm{MLP}\Big(\textstyle\sum_{j=1}^{k}\alpha_{j}\, z^{j}_{\text{enc}}\Big),
\qquad
z^{i}_{s} \;=\; z^{i}_{\text{context}} \,\Vert\, z^{i}_{\text{enc}} .
$$

**Three consequences worth spelling out.**

1. **The attention is dot-product, not learned-projection.** There is no query/key
   matrix — the encoder output *is* the key and the context vector *is* the query. So
   `z^j_enc` and `z_context` must share a dimensionality, and, more subtly, the
   encoders are pushed to align their output geometry with the frozen language
   model's projected geometry. The specialisation the paper observes (Fig. 4c) is a
   consequence of this coupling.
2. **The stop-gradient is asymmetric, and its purpose is stated.** `z_context` is
   detached *inside the attention* but not inside the concatenation: *"`z_context` is
   updated using the policy loss directly, as it is a part of the state encoding."*
   The effect is that the RL loss cannot shape the context vector *in order to game
   the attention weights*; it can only shape it as a feature. Without this, the
   context encoder and the mixture weights would co-adapt and the interpretability
   result in §4.3 would be unavailable. This is a design detail the downstream
   literature almost never reproduces when it cites CARE.
3. **A prose/pseudocode discrepancy.** §3.2 states `z_enc = Σ_i α_i z^i_enc`, with no
   MLP; Algorithm 1 line 7 states `z^i_enc = MLP(Σ_j z^j_enc × α_j)`. Take the
   pseudocode as authoritative but record the ambiguity — it changes whether the
   mixture is a pure convex combination or a convex combination followed by a
   nonlinear map.

**Why this is a mixture and not modulation.** Write the pre-MLP pooled vector as
`Σ_j α_j z^j_enc` with `α` on the simplex. Every output coordinate is a *weighted
average of the same coordinate across encoders* — the operation cannot change a
coordinate's scale beyond the range spanned by the encoders, and it applies the same
scalar to all coordinates of a given encoder. FiLM's `γ ⊙ z + β` does the opposite: one
encoder, per-coordinate scale and shift, unbounded. The two are not variants of one
another and CARE's Table 1/3 is the empirical statement of the difference.

#### 2.4.4 Training

All components are trained by the **RL losses only** — no auxiliary reconstruction, no
contrastive term. Appendix Algorithms 3 and 4 make this explicit: the context encoder's
objective is `J_C(ω) = J_V + J_Q + J_π` and each encoder's is
`J_{E_k}(ζ_k) = J_V + J_Q + J_π`, the standard SAC value, Q and policy losses. The SAC
machinery is textbook (soft value regression, twin Q, KL-form policy improvement) and
the paper reproduces Haarnoja's equations verbatim in Appendix A.2.

The tasks are processed **concurrently**: *"steps 3 to 11 can be run concurrently for
multiple tasks (as is done in our implementation)"*, with batch size
`128 × number of tasks`, and temperature *"learned and disentangled with tasks"* —
i.e. one `α` per task, as in Yang et al.

### 2.5 Results, as printed

Meta-World mean success rate, **10 seeds**, evaluated every 10 K env steps per task,
reported as `mean ± stderr`. `*` marks baselines over which CARE's improvement is
**statistically significant** by a two-tailed Welch's t-test at p = 0.05.

| Agent | MT10 @100 K | MT10 @500 K | MT10 @2 M | MT50 @100 K | MT50 @500 K | MT50 @2 M |
|---|---|---|---|---|---|---|
| Multi-task SAC | 0.13 ± 0.022 * | 0.38 ± 0.041 * | 0.49 ± 0.073 * | 0.13 ± 0.0061 * | 0.28 ± 0.017 * | 0.36 ± 0.013 * |
| **Multi-task SAC + Task Encoder** (learned embedding, concatenated) | 0.14 ± 0.012 * | 0.42 ± 0.031 * | 0.54 ± 0.047 * | 0.28 ± 0.015 * | 0.37 ± 0.016 * | 0.40 ± 0.024 * |
| Multi-headed SAC | 0.17 ± 0.033 * | 0.44 ± 0.045 * | 0.61 ± 0.036 * | 0.19 ± 0.0071 * | 0.45 ± 0.064 | 0.45 ± 0.064 |
| PCGrad | 0.20 ± 0.032 * | 0.53 ± 0.030 * | 0.72 ± 0.022 * | 0.21 ± 0.0068 * | 0.47 ± 0.016 | 0.5 ± 0.017 |
| **Soft Modularization** (routing; paper #1) | 0.33 ± 0.036 | 0.64 ± 0.052 | 0.73 ± 0.043 | 0.20 ± 0.023 * | 0.47 ± 0.012 | 0.5 ± 0.035 |
| **SAC + FiLM** (affine modulation of the encoder, same context) | 0.27 ± 0.037 * | 0.57 ± 0.035 * | 0.75 ± 0.037 | 0.16 ± 0.006 * | 0.30 ± 0.012 * | 0.40 ± 0.012 * |
| **CARE** (SAC + Metadata + Mixture of Encoders) | **0.36 ± 0.035** | **0.66 ± 0.028** | **0.84 ± 0.051** | **0.40 ± 0.015** | **0.51 ± 0.036** | **0.54 ± 0.031** |
| One SAC agent per task (upper bound) | — | — | 0.90 ± 0.032 | — | — | 0.74 ± 0.041 |

**Additional headline the abstract does not mention:** CARE composed with a
multi-headed policy reaches **0.61 ± 0.0287** on MT50 — the paper's best number —
because *"CARE focuses on learning representations, it can benefit from the
improvements in policy optimisation"*.

**Component ablation (Tables 5 and 6, 2 M steps).**

| Configuration | MT10 | MT50 |
|---|---|---|
| SAC + Mixture of Encoders (no metadata) | 0.74 ± 0.043 | 0.44 ± 0.012 * |
| SAC + Metadata (single encoder) | 0.79 ± 0.041 | 0.48 ± 0.025 |
| **CARE** (both) | **0.84 ± 0.051** | **0.54 ± 0.031** |

The authors' reading: *"removing the metadata (first row) hurts the models more than
removing the mixture of encoders (second row)"*. Numerically, on MT10, metadata alone
buys +0.05 over the mixture alone; the two together buy +0.10 over the mixture alone.
**The conditioning signal contributes more than the operator.**

**Encoder-count and hard-attention ablation (Table 18, MT10 @2 M).**

| Variant | Success |
|---|---|
| CARE with 2 encoders | 0.76 ± 0.043 |
| **CARE with 6 encoders (the reported model)** | **0.84 ± 0.051** |
| CARE with 10 encoders * | 0.71 ± 0.029 |
| CARE, 10 encoders, top-2 active * | 0.55 ± 0.051 |
| CARE, 10 encoders, top-4 active * | 0.69 ± 0.040 |
| CARE, 10 encoders, top-6 active * | 0.71 ± 0.051 |
| CARE, 10 encoders, top-8 active * | 0.67 ± 0.043 |
| Hand-coded task→encoder mapping | 0.80 ± 0.037 |

Three findings: **more encoders is not better** (10 < 6 < ... ; *"having too many
encoders can hurt the performance when shared information is no longer leveraged"*);
**hard top-`k` attention is consistently worse than soft** (best hard variant 0.71 vs
soft 0.84) — the same soft-beats-hard pattern paper #1 reports for routing; and a
**hand-written** mapping of tasks to object/skill encoders reaches 0.80, close to
learned 0.84, which is the paper's evidence that the learned mixture is discovering
object/skill structure rather than arbitrary partitions. The hand-coded mapping itself
is printed in Table 20 (encoders for skills `close`/`open`/`push`, objects
`drawer`/`goal`/`puck`/`window`, plus two catch-alls).

**Zero-shot generalisation (Table 7).** Train on 8 of the MT10 tasks, evaluate on the
held-out `drawer-open-v1` and `window-open-v1`, which are compositionally reachable
from `drawer-close-v1`, `window-close-v1`, `door-open-v1`.

| Agent | Held-out success |
|---|---|
| PCGrad * | 0.05 ± 0.076 |
| Soft Modularization | 0.1 ± 0.089 |
| SAC + FiLM | 0.2 ± 0.073 |
| **CARE** | **0.3 ± 0.077** |

The authors flag their own caveat: *"the comparison is unfair to PCGrad and Soft
Modularization as they do not have any means for generalizing to the unseen task"* —
neither has a route from a novel task to a conditioning vector. Only FiLM and CARE
read language, so **only the FiLM vs CARE column is a like-for-like comparison**, and
it is 0.2 vs 0.3 with standard errors of ~0.075 and no significance star.

### 2.6 The finding the citing literature usually drops

Read the asterisks column by column and the honest summary is narrower than the
abstract's *"state-of-the-art results"*:

- **CARE's advantage over Soft Modularization is statistically significant at exactly
  one of six (benchmark × budget) cells** — MT50 @100 K (0.40 vs 0.20). At MT10 @100 K,
  MT10 @500 K, MT10 @2 M, MT50 @500 K and MT50 @2 M it is **not** significant.
- **CARE's advantage over FiLM is significant in five of six cells**, the exception
  being MT10 @2 M (0.84 vs 0.75) — the single cell most often quoted.
- **Zero-shot CARE vs FiLM (0.3 vs 0.2) carries no significance star.**

So the defensible claims are: *language-metadata conditioning beats task-ID
conditioning decisively and significantly*; *a context-driven mixture-of-encoders
beats context-driven FiLM on the encoder, significantly, in the low-sample and
50-task regimes*; and *the mixture is roughly on par with soft routing*. Any report
sentence stronger than that outruns the statistics as printed in this PDF.

Two further protocol facts should travel with any cross-paper number:

- **Evaluation frequency is an implicit hyperparameter** (Table 19). Evaluating every
  1 K instead of 10 K steps changes PCGrad 0.72 → 0.75, Soft Modularization 0.73 →
  0.78, CARE 0.84 → 0.87 — because the reported score is the max over the evaluation
  time series.
- **Numbers are not comparable to paper #1's.** CARE runs 10 seeds and gets 0.61 for
  multi-headed SAC on MT10; Yang et al. run 3 seeds and get 0.85 on MT10-Fixed; Yu et
  al. report 0.88 at 1 seed. Same nominal baseline, three very different numbers. When
  the merged review tabulates Meta-World results, **the seed count and the
  fixed-vs-conditioned goal setting must be carried alongside every figure.**

### 2.7 Relevance to this project

- **This is the one paper in the corpus that benchmarks FiLM against its
  alternatives under a controlled protocol.** If the report needs a single citation
  for "affine modulation is not automatically the best conditioning operator in RL",
  it is Tables 1, 3 and 16–17 here.
- **The conditioning *signal* mattered more than the *operator*.** `SAC + Metadata`
  with one encoder (0.79 MT10) already beats FiLM-on-context (0.75) and Soft
  Modularization (0.73). That ordering is directly relevant to any project decision
  that phrases itself as "which modulation mechanism" when the live question is
  "which conditioning variable".
- **Soft beats hard, again.** Top-`k` hard attention loses 0.13–0.29 to soft
  attention, mirroring paper #1's hard-routing collapse. Two independent papers, two
  operators, same direction.
- **Stop-gradient placement is a transferable implementation detail.** Detaching the
  conditioner where it computes mixing weights, while leaving it attached where it is
  a feature, is a cheap way to stop a modulator from co-adapting with the pathway it
  steers. Worth noting if the project's modulator ever both gates and feeds.
- **Precedent for "the conditioner is also a direct input".** `z_s = z_context ∥ z_enc`
  means the conditioning vector reaches the policy twice — once by steering the
  encoder mixture, once as a plain concatenated input. The project's own corpus has
  flagged this pattern elsewhere (PAPL); CARE is the 2021 precedent.
- **A caution for construct claims.** The specialisation result (Fig. 4b/c/d cosine
  similarity matrices) shows only that context representations of semantically similar
  tasks are similar — which is largely inherited from RoBERTa (Fig. 4b is the *frozen*
  embedding and already shows the structure). The "encoders specialise to objects and
  skills" claim rests on the hand-coded-mapping experiment (0.80), not on the
  visualisation.

### 2.8 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Multi-task benefit depends on capturing task structure. **Metadata** — extra information about a task, useless in a single-task setup but informative about task relations — can help but is hard to incorporate. Posits knowledge transfer via *"multiple context-dependent, composable representations shared across a family of tasks"*, with metadata providing both interpretability and the signal for **which** representations to compose and **how**. State-of-the-art on Meta-World's 50 tasks. |
| 1 | **Introduction** | RL's successes are single-task; humans compose skills. Existing MTRL cannot use side information such as a task description. Natural-language descriptions exist in real tasks but are normally consumed only by humans. |
| 2 | **Preliminaries** | MDP `⟨S,A,R,T,γ⟩`, value function, optimal value function. **Contextual MDP** (Hallak et al. 2015): `⟨C,S,A,M⟩`, `M(c) = {R^c, T^c}`. Observes that in multi-task settings the agent sees only a **partial** state space `S^c ⊂ S`. **Definition 2, Block Contextual MDP**: `⟨C,S,A,M′⟩` with `M′(c) = {R^c, T^c, S^c}`. Footnote 2 argues this is not partial observability because a task id/description uniquely identifies the task. Meta-World presented as the instantiation: 50 tasks, same state dimensionality, **different semantics per dimension**; broad task distribution unlike prior narrow ones. |
| 3 | **A Method for Learning Contextual Attention-based Representations** | Overview. Factorise the state representation into sub-components common across the BC-MDP family (objects: drawer, door; skills: open, close). Train **one universal policy** that uses task metadata to choose a functional representation. Compositionality introduced by a **mixture of encoders**. CARE is a representation method; must be paired with a policy-optimisation algorithm — SAC here. |
| 3.1 | **Incorporating Information from Metadata** | Goal: reconstruct the universal `S` from context-dependent `S^c`. Knowing which objects matter would need object-level supervision, which is unavailable — sidestepped by conditioning the **attention** on task context. Metadata may be high-level, under-specified, unstructured; it need not say how to do the task; it can be constructed from descriptive names (*"HalfCheetah Run"*). Context obtained from **RoBERTa** (768-dim, frozen), projected by feedforward layers to `z_context`. |
| 3.2 | **Contextual Attention based Representations** | `k` encoders (`k ≪ N` tasks) produce `z^i_enc`; soft-attention weights `α_i` from the context; pooled `z_enc = Σ_i α_i z^i_enc`; concatenate with `z_context` to form `z_s`, the policy input; trained end-to-end. **Language model frozen; `z_context` detached before computing attention weights but updated by the policy loss as part of `z_s`.** Positions the bias as softer than object-oriented learning: no privileged object info, no explicit inter-encoder interaction modelling (contrast RIMs, graph nets, slot attention). Figure 3 = architecture; Algorithm 1 = the loop, with line 6 `α_j = softmax(z^j_enc · z̄^i_context)` and line 7 the MLP-wrapped pooling. |
| 3.3 | Downstream Evaluation | SAC used for downstream evaluation; steps 3–11 of Algorithm 1 run concurrently across tasks. Pointers to Appendix Algorithms 2–4. |
| 4 | **Experiments** | Four questions: (i) is contextual attention effective vs methods without context, (ii) is metadata useful only with compositional representations, (iii) does metadata give factored/specialised representations, (iv) does metadata help zero-shot generalisation. |
| 4.1 | How CARE compares to existing MTRL baselines | Baseline taxonomy: task-specific-parameter extensions of single-task RL vs specialised MTRL algorithms. Compares against PCGrad (SOTA on Meta-World, beating GradNorm and CosReg), **Soft Modularization**, and **FiLM** — *"a popular and general-purpose conditioning method"*, applied as *"FiLM layers to condition the encoder on the context (generated using a context encoder, just like in CARE)"*, motivated by its use in language-conditioned RL (BabyAI, RTFM). Evaluation protocol spelled out: 5 evaluation episodes per env, mean across envs, 10 seeds, best mean over the time series. Two candid protocol critiques: **evaluation frequency is an implicit hyperparameter**, and **seed count changes results by up to 44 %**. Tables 1–4 (MT10/MT50 at 2 M and 100 K), plus the note that CARE + multi-headed SAC reaches 0.61 on MT50. Forward-references the appendix ablations. |
| 4.2 | Is the metadata useful only when learning compositional representations? | Tables 5–6. Removing metadata hurts more than removing the mixture; metadata with a single encoder is already competitive with the baselines. |
| 4.3 | Interpreting the specialized representations | Figure 4. (b) cosine similarity of **frozen RoBERTa** task embeddings; (c) of CARE's learned context representations with `k = 6`; (d) of context representations **without** metadata. (b) and (c) show clear task structure — tasks 2/3 share an object, tasks 4/5/6 share skill "open" and object "drawer" — (d) does not. |
| 4.4 | Zero-shot generalization to unseen environments | Train on 8 MT10 envs, test on `drawer-open-v1` and `window-open-v1`. Table 7. Explicit caveat that PCGrad and Soft Modularization *"do not have any means for generalizing to the unseen task"*. Notes CARE generalises better than FiLM, which also uses metadata. |
| 5 | **Related Work** | MTRL assumes shared low-dimensional structure; prior work uses *"only ... a simplistic context in the form of an ordinal task id"*. Negative interference (PCGrad `O(n²)` in task count; gradient-dropping slows learning) — CARE instead uses context to decide **what to share**. Contextual MDPs (Hallak; Modi's smoothness + PAC; Klink's controllable context/curriculum). Metadata in supervised task-relation discovery. Language-conditioned RL: there language is **part of the problem specification**, here it is **auxiliary side information**; and prior work assumes structured templates (*"a two-word tuple ... skill and item"*) whereas CARE's metadata may be unstructured. Compositional MTL: Liu et al.'s task-specific soft-attention modules, Devin et al.'s task/robot decomposition, Yang et al.'s routing — none conditions the decomposition on metadata. |
| 6 | **Discussion** | Contributions restated: metadata within the MDP framework; the BC-MDP definition; mixture of encoders with a single policy. Two extensions: other context types (people, places — personalised medicine, recommender systems, household layouts) and the **rich-observation / pixel** version of the BC-MDP, which approaches but is more tractable than full POMDP. |
| A | **Additional Implementation Details** | A.1 libraries (PyTorch, Hydra, MetaWorld at a pinned commit, MTEnv, MTRL). A.2 SAC equations reproduced verbatim (Eq. 1–6: soft value residual, its gradient, soft Bellman residual, target, Q gradient, KL-form policy objective). A.3 CARE components: context encoder and `k` encoders both trained **by the policy loss only**, `J = J_V + J_Q + J_π`; restates the stop-gradient. |
| B | **Hyperparameter Details** | Common: batch `128 × #tasks`; actor/critic = 3 FC layers × 400 units; ReLU; 1500 uniform-exploration steps; 1 env step per train step; lr 3e-4 both; Adam (0.9, 0.999); `γ = .99`; horizon 150; reward scale 1.0. Per method (Tables 9–15): task encoder = 2-layer FF, dims 50 (for Task-Encoder SAC it is embedding + 2 FC, dims 50); PCGrad uses **5** layers × 400; Soft Modularization uses 4 layers × 4 modules; **FiLM's only listed hyperparameters are the task encoder size and the temperature — its layer placement is not specified**; CARE uses `k = 6` (MT10) / `k = 10` (MT50). Temperature *"learned and disentangled with tasks"* everywhere. |
| C | **Additional Results** | C.1 ablations (Table 18: encoder count, top-`k` hard attention with the renormalised formula, hand-coded mapping; Table 20 gives the mapping). C.2 evaluation frequency (Table 19: 1 K vs 10 K). Tables 16–17: 500 K-step results. |
| D | **Testing for statistical significance** | Two-tailed Welch's t-test (equal sample sizes, unequal variance), null = equal mean performance, `p = 0.05`. |

---
