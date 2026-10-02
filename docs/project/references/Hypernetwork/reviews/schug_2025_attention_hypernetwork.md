---
title: "Attention as a Hypernetwork"
slug: schug_2025_attention_hypernetwork
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_theory.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

# 1. Schug et al. 2025 — Attention as a Hypernetwork

**PDF:** `docs/project/references/Hypernetwork/sources/Schug et al. 2025 - Attention as a hypernetwork.pdf`
**Authors:** Simon Schug, Seijin Kobayashi, Yassir Akram (ETH Zürich); João Sacramento (Google, Paradigms of
Intelligence Team); Razvan Pascanu (Google DeepMind). Sacramento and Pascanu are marked shared senior authors.
**Venue as printed:** the running header on every page reads *"Published as a conference paper at ICLR 2025"*.
The stamp in the margin of page 1 reads `arXiv:2406.05816v4 [cs.LG] 17 Feb 2025`. **The PDF does not state
Oral status anywhere** — if "ICLR 2025 Oral" is needed for a bibliography it must be sourced from the ICLR
programme, not from this file.
**Code:** `https://github.com/smonsays/hypernetwork-attention`

---

## Phase 1 — Foundational overview

### Introduction

Transformers sometimes solve problems built from familiar pieces combined in an unfamiliar way — a capacity
called **compositional generalization**. Nobody has a clear mechanistic account of why. This paper offers
one, and it comes from an unexpected direction: it shows by direct algebra that **multi-head attention is
already a hypernetwork**, with no modification required.

The reframing is this. Ordinarily we read an attention layer as "each query looks across the keys and takes
a weighted average of values". This paper instead reads the *same numbers* along a different axis. Fix one
query and one key. Across the `H` attention heads there are `H` attention scores for that specific pair.
Collect them into a vector. That `H`-dimensional vector, the paper shows, is exactly the **latent code of a
hypernetwork**: it linearly mixes `H` fixed learned matrices into one matrix, and that matrix is the
operation applied to that key's token. Different query–key pairs get different codes, hence different
operations, all built from the same shared library of `H` matrices.

That last clause is why the paper thinks this explains compositionality. Because the library is *shared
across every query–key pair in the layer*, the layer is structurally pushed to learn a small set of reusable
operations and recombine them, rather than learning a bespoke operation per situation.

### Key findings

- **The identity.** Multi-head attention can be rewritten, exactly, as a *linear* hypernetwork configuring a
  *linear* value network, one value network per query–key pair. This is a rearrangement of terms, not an
  approximation and not a theorem with preconditions.
- **The code is meaningful in practice.** On two in-context-learning tasks, a logistic-regression probe
  trained on the latent codes of *seen* tasks correctly predicts which sub-operations the network is applying
  on *unseen* task combinations. The codes cluster by sub-operation, not merely by output value.
- **Strengthening the mechanism helps.** They add a nonlinearity inside the generated value network — using
  weights the layer already has, so no new parameters — plus a normalization across the head axis. This is
  **HYLA** (Hypernetwork Linear Attention). It improves out-of-distribution accuracy on both synthetic tasks
  and closes most of the gap between linear and softmax attention on language modelling.
- **Removing the mechanism hurts.** With a single head the hypernetwork degenerates to rescaling one fixed
  matrix by a scalar — there is nothing left to compose — and out-of-distribution accuracy drops.
- **A new benchmark.** SRAVEN, a symbolic version of Raven's Progressive Matrices with parametrically
  controllable difficulty and exact control over which rule-combinations appear in training.

### Initial takeaway

If this reading is right, hypernetwork-style modulation is not an exotic add-on the project would be bolting
onto an otherwise-normal network — it is the same mechanism that already runs inside every transformer, just
made explicit and given a wider code. **But be careful about how much this paper licenses.** The identity is
airtight; the claim that this identity *is why* transformers compose is a hypothesis, supported by suggestive
evidence on two synthetic tasks and one language-model run, and it is presented as such by the authors.

---

## Phase 2 — Graduate-level deep dive

### 2.1 Setup and notation

Self-attention maps `X ∈ ℝ^{D×T}` to `Y ∈ ℝ^{D×T}`. For each head `h ∈ {1,…,H}`, with
`D_head = D/H`, keys and queries are formed with head-specific projections
`W_h^key, W_h^query, W_h^value ∈ ℝ^{D_head×D}`:

$$K_h = W_h^{\text{key}} X, \qquad Q_h = W_h^{\text{query}} X.$$

The stacked attention array `A = (a_{h,q,k}) ∈ ℝ^{H×T×T}` is

$$A = \sigma\Big(\big[\tilde{A}_1\ \tilde{A}_2\ \dots\ \tilde{A}_H\big]\Big), \qquad
\tilde{A}_h = \frac{Q_h^\top K_h}{\sqrt{D_{\text{head}}}} \tag{1}$$

where `σ(·) = Id` for linear attention and `σ(·) = Softmax(·)` (per head, per query, across keys) for standard
attention.

A **hypernetwork** is a map `h(z; θ) ↦ W` whose output parameterises a **value network** `f(x; W)`; `z` is a
typically low-dimensional **latent code** read as a specification of the computation to perform.

### 2.2 The central derivation (Eqs. 2–5) — worked step by step

Fix a query index `q`. Write `x_k ∈ ℝ^D` for the `k`-th column of `X`. Standard multi-head attention is
"attend per head, concatenate heads, apply one output projection":

$$\text{MHA}_q(X) := W^{\text{out}} \bigoplus_{h=1}^{H} \sum_{k=1}^{T} a_{h,q,k}\, W_h^{\text{value}} x_k \tag{2}$$

with `⊕` denoting concatenation over the head axis.

**Step 1 — split the output projection along the head axis.** Because `W^out ∈ ℝ^{D×D}` multiplies a vector
that is the concatenation of `H` blocks each of size `D_head`, we may partition its *columns* into `H` slices
`W_h^out ∈ ℝ^{D×D_head}` with `W^out = ⊕_h W_h^out`. Matrix–vector product against a concatenated vector is
then a sum of the per-slice products:

$$= \sum_{h=1}^{H} W_h^{\text{out}} \sum_{k=1}^{T} a_{h,q,k}\, W_h^{\text{value}} x_k \tag{3}$$

**Step 2 — exchange the two finite sums.** Both sums are finite, so `Σ_h Σ_k = Σ_k Σ_h`. Move the scalar
`a_{h,q,k}` out (it is a scalar, so it commutes with the matrices) and collect:

$$= \sum_{k=1}^{T} \Bigg( \underbrace{\sum_{h=1}^{H} \underbrace{a_{h,q,k}}_{\text{latent code}} \underbrace{W_h^{\text{out}} W_h^{\text{value}}}_{\text{hypernetwork}} }\Bigg) x_k \tag{4}$$

**Step 3 — name the bracket.** Define

$$W_{q,k} := \sum_{h=1}^{H} a_{h,q,k}\, W_h^{\text{out}} W_h^{\text{value}} \ \in \mathbb{R}^{D\times D},
\qquad \text{so} \qquad
\text{MHA}_q(X) = \sum_{k=1}^{T} \underbrace{W_{q,k}}_{\text{value network}} x_k. \tag{5}$$

**Read the result carefully.** Three objects have been identified:

- **Latent code:** `z_{q,k} := (a_{1,q,k}, a_{2,q,k}, …, a_{H,q,k}) ∈ ℝ^H`. This is the attention scores for a
  *fixed* query–key pair, read **across the head index**. The latent dimension of the hypernetwork is `H`,
  the number of heads.
- **Hypernetwork:** the map `z ↦ Σ_h z_h B_h` with fixed learned basis `B_h := W_h^out W_h^value ∈ ℝ^{D×D}`.
  It is **linear in the code**, and `θ = {W_h^out, W_h^value}_h` are its parameters.
- **Value network:** `f(x; W_{q,k}) = W_{q,k} x`, a **linear** network.

So the precise statement is: **multi-head attention is a linear hypernetwork that emits the weights of a
linear value network, with one value network instantiated per query–key pair, whose outputs are then summed
over the key index.**

### 2.3 What is proved, what is hypothesised — the careful version

This matters enough to state as a table, because it is easy to overclaim.

| Claim | Status | Evidence |
|---|---|---|
| MHA `=` a linear hypernetwork over a linear value network, per query–key pair | **Exact algebraic identity.** Holds for *any* trained or untrained MHA layer, softmax or linear, self- or cross-attention (footnote 2 states the cross-attention case is identical). No assumptions, no approximation, no conditions | Eqs. 2–5, three elementary steps (column-slice, sum exchange, renaming) |
| The number of heads `H` is the latent dimension of that hypernetwork | Follows immediately from the identity | Eq. 4 |
| The same hypernetwork (same basis `{B_h}`) is reused for every query–key pair in a layer | Follows immediately; the basis carries no `q,k` index | Eq. 4 |
| Because the basis is shared, the layer is *incentivised* to learn reusable, recombinable operations | **Hypothesis.** The word used in the paper is "incentivizes" / "we hypothesize" | argued, not derived |
| Hypernetworks support compositional generalization | **Not proved here.** Explicitly cited to Schug et al. 2024 (paper #2 in this file) | citation |
| The latent codes trained networks actually learn are organised by sub-operation | **Empirical**, two synthetic tasks | probe F1, tSNE, cosine-similarity heatmap |
| This mechanism explains transformers' compositional generalization in general | **Not established.** Authors' own Limitations paragraph restricts all analysis to models trained from scratch on controlled data; whether pretrained large models form similar codes is named as future work | — |

**Two further honesty notes.**

*(a) The identity is a rewriting, and the authors say so.* Immediately after presenting it they write: "In order
to investigate whether this constitutes a faithful characterization of what transformers learn in practice, we
study in-context learning tasks…". The algebra alone constrains nothing about learned behaviour — the same
rewriting applies to a randomly initialised layer.

*(b) The relation to fast-weight programmers is a real distinction, not a restatement.* The paper explicitly
separates itself from Schlag et al. 2021: in the fast-weight view, weights are built as a sum of outer products
**over the key indices**; here the composition runs **over the head index**. Different axis, different object.
Conflating the two would be the most likely way to misuse this paper.

### 2.4 HYLA — the intervention, and why it costs no parameters

If the hypernetwork reading is the operative one, then making the *generated* network more expressive should
strengthen compositionality. Note from Eq. 4 that `W_h^out W_h^value` is already a **deep linear network** —
two matrices multiplied with nothing between them. A nonlinearity can therefore be inserted **into the gap
that already exists**, with no new parameters:

$$\text{HYLA}_q(X) = \sum_{k=1}^{T} \Bigg(\sum_{h=1}^{H} a_{h,q,k} W_h^{\text{out}}\Bigg)\, \phi\Bigg(\sum_{h=1}^{H} a_{h,q,k} W_h^{\text{value}} x_k\Bigg) \tag{6}$$

$$= \sum_{k=1}^{T} W'_{q,k}\, \phi\big(W_{q,k} x_k\big), \qquad \phi(x) = \max(0,x). \tag{7}$$

The generated object is now a **one-hidden-layer nonlinear** value network, with *both* its layers composed
from the same latent code. Note the structural change from Eq. 4: the attention-weighted mixing is now applied
to `W_h^out` and `W_h^value` **separately**, instead of to their product.

**The normalization change.** HYLA sets `σ(·) = RMSHead(·)`, i.e.
`RMSNorm(x) = x / sqrt((1/n) Σ_i x_i²)` applied **across the head index** for each `(q,k)` pair independently,
with no learnable scale. Two consequences the paper names:

1. **Stability.** Quoting directly: it "ensures that the parameters of the value network generated by the
   hypernetwork maintain the variance preserving properties of neural network initializations that have been
   found to be important for the stability of gradient-based training (Glorot & Bengio, 2010)." **This is the
   hypernetwork-specific training-stability fix in this paper** — see §2.7.
2. **Locality.** Normalizing across heads rather than across keys means the operation needs no communication
   between key positions, unlike softmax attention.

An appendix variant **HYLA+** adds a second generated layer (Eq. 10), which *does* add parameters
(`W_h^{value′} ∈ ℝ^{D_key×D_key}`).

### 2.5 Where this sits on the capacity spectrum

**Rung 3 — parameter composition over a fixed learned basis.** Precisely:

- The emitted code is `H`-dimensional (`H = 8` for fuzzy logic and language modelling, `H = 16` for SRAVEN).
  That is *smaller* than a FiLM code for the same layer, which would be `2D` numbers with `D = 128` or `512`.
- But the code indexes a basis of **full `D×D` matrices**, each `B_h = W_h^out W_h^value` of rank at most
  `D_head = D/H`. The induced weight `W_{q,k}` is a full matrix of rank up to `D`, not a diagonal rescaling.

So relative to FiLM this is **a smaller code driving a larger-effect operator**. That is the load-bearing
observation for the project: code dimensionality and modulation capacity are independent axes, and the
Schug pair is arguing that the second axis is what matters for composition.

It is emphatically **not** rung 4 (full weight generation): no free `D²` parameters are ever emitted, and the
achievable set of `W_{q,k}` is confined to the `H`-dimensional linear span of `{B_h}`.

**The degenerate case is illuminating and worth stating exactly.** At `H = 1`, Eq. 4 collapses to
`W_{q,k} = a_{1,q,k} B_1` — a **single scalar gain on one fixed matrix**. That is a degenerate FiLM: one
scalar, not even per-channel. The paper's own words: "in the case of a single head the mechanism degenerates,
only allowing the network to rescale the weights of the sole remaining value projection but no longer allowing
it to compose multiple value projections." Figure 5C reports "a noticeable decrease in OOD performance" for
`H = 1`. **Caveat: this is reported as a figure trend, not a table; no numeric value for the single-head case
appears in the text.** And reducing head count changes more than the hypernetwork mechanism, so the ablation
is suggestive rather than clean.

### 2.6 Experimental results — the actual numbers

**There is no RL in this paper and no FiLM baseline.** The baselines are softmax attention and linear
attention. Everything below is from Table A1 (page 19), standard error over **3 seeds**.

Left column: out-of-distribution `R²` on the fuzzy-logic task, sequence length 32, **70 %** of task
combinations held out. Right column: out-of-distribution accuracy on SRAVEN, 4-layer transformer, 20 M
training problem instances.

| Model | Fuzzy logic OOD `R²` | SRAVEN OOD accuracy |
|---|---|---|
| Softmax attention | 63.28 ± 2.31 | 56.56 ± 1.05 |
| Linear attention | 59.89 ± 5.22 | 56.30 ± 1.11 |
| **HYLA** | **81.13 ± 7.77** | **69.13 ± 1.90** |
| Linear attention + RMSHead | 68.93 ± 5.10 | 59.01 ± 2.50 |
| Linear attention + RMSHead + nonlinear value | 56.91 ± 4.25 | 55.38 ± 0.32 |
| HYLA − RMSHead | 81.27 ± 7.88 | 62.53 ± 5.73 |
| HYLA − nonlinearity | 84.54 ± 5.32 | 56.54 ± 0.21 |
| HYLA − nonlinearity − RMSHead | 79.42 ± 7.43 | 56.33 ± 1.41 |
| HYLA − RMSHead + softmax | 70.98 ± 7.08 | 38.21 ± 2.98 |
| HYLA + deep value network (extra params) | 87.65 ± 4.54 | 66.59 ± 0.08 |
| Softmax attention + MoE | 63.83 ± 6.07 | 57.68 ± 1.31 |
| Linear attention + MoE | 60.09 ± 6.16 | 64.34 ± 4.3 |
| HYLA + MoE | 82.37 ± 6.55 | 66.94 ± 3.94 |

**Headline gaps.** HYLA over the better standard baseline: **+17.9 `R²` points** on fuzzy logic
(81.13 vs 63.28 softmax) and **+12.6 accuracy points** on SRAVEN (69.13 vs 56.56 softmax).

**Three caveats a careful reader must carry:**

1. **The paper's ablation claim is supported on SRAVEN but not on fuzzy logic.** §3.1 states that "both
   components in combination are required to obtain the observed performance improvements". On SRAVEN this
   holds cleanly: dropping the nonlinearity collapses HYLA to 56.54 (baseline level) and dropping RMSHead
   costs ~7 points and triples the seed variance. On fuzzy logic it does **not**: `HYLA − nonlinearity` scores
   **84.54**, *higher* than full HYLA's 81.13, and `HYLA − RMSHead` scores 81.27, also higher. With ±7.8
   standard errors over 3 seeds these differences are not resolvable — which is the honest reading, but it
   means the fuzzy-logic column does not evidence the necessity claim.
2. **The MoE control partially undercuts the specificity claim.** Linear attention + Mixture-of-Experts
   reaches **64.34** on SRAVEN, most of the way from 56.30 to HYLA's 69.13, using a completely different
   mechanism (sparse expert routing in the feedforward layer). The authors' own framing is that MoE gains
   "seem to be similar to other increases of model capacity such as increasing the width/depth". That is a
   fair reading, but it means SRAVEN OOD accuracy is not a clean assay for *the hypernetwork mechanism
   specifically*.
3. **Three seeds.** Every number above.

**Scaling (Figure 4, values read from axes — no table).** On SRAVEN, sweeping training instances from 10 M to
40 M at widths 1×/2×/4× and depths 4/8/16, all three model classes eventually reach roughly **80 %** OOD
accuracy given enough data and size. HYLA's advantage is concentrated at **small data and small model size** —
i.e. it is an inductive-bias effect that scale eventually washes out. Figure A5 sweeps the held-out fraction
from 0.1 to 0.9.

**Latent-code analyses (all supporting, all correlational).**
- Fuzzy logic: logistic-regression probes trained per layer and per term recover the constituent terms of
  *unseen* tasks from the `H`-vector of the response token attending to itself (Figure 2B, F1 score).
- tSNE of those codes clusters by **constituent term**, and only partially by output value (Figure 2D).
- SRAVEN: final-layer codes cluster by **ground-truth rule**; magnitude-of-target explains clusters better in
  *early* layers (Figures 5A/5B, A6, A7).
- Cosine-similarity heatmap (Figure 5E): semantically related rules share codes — rule F (addition) and rule
  G (difference) are "implemented with a very similar latent code, indicating that the same code might be
  reused by flipping the sign of the operands."

**A negative result worth recording.** Held-out combinations of **known** terms generalize; held-out
combinations of **unknown** terms do not. "testing on functions obtained as novel combinations of `K` unknown
terms, we find that none of the models considered here is able to solve such a task (see Figure A3C)." The
compositional generalization demonstrated is strictly *recombination of a learned library*, never extrapolation
to new primitives.

**Language modelling (§5, Figure 6).** Decoder-only transformers, **50 M parameters**, **130 B tokens** of C4,
trained on 16 Cloud TPU v5e (72–100 h per run). Result stated qualitatively only, no table: HYLA "improves
performance over linear attention and performs closely to softmax attention despite being a linear attention
variant itself." No perplexity numbers appear in the text.

### 2.7 Training-stability issues and reported fixes

Hypernetwork-specific instability appears here in exactly one place, and the fix is architectural rather than
an initialisation scheme:

- **The problem.** The generated weights `W_{q,k} = Σ_h a_{h,q,k} B_h` inherit their scale from the attention
  scores. Unnormalized (linear attention, `σ = Id`), the code magnitude is uncontrolled, so the *effective
  initialisation variance of the generated value network* drifts with the data. This is the same failure mode
  that Beck (paper #3) attacks with an explicit initialisation correction.
- **The fix.** RMSHead — RMS-normalize the code across the head axis, no learnable gain, so the generated
  weights preserve the variance properties that standard initialisation schemes are designed to give (Glorot &
  Bengio 2010).
- **Evidence it matters.** `HYLA − RMSHead` on SRAVEN: **62.53 ± 5.73** vs HYLA's **69.13 ± 1.90** — ~7 points
  worse and **three times the seed variance**, the variance increase being the more diagnostic signal.
- **Evidence the *axis* matters, not just normalization.** `HYLA − RMSHead + softmax` (normalize across keys
  as usual, instead of across heads) scores **38.21 ± 2.98** on SRAVEN — **18 points below plain linear
  attention**. Normalizing the wrong axis is far worse than not normalizing at all, because softmax-across-keys
  does not constrain the code magnitude that sets the generated weight scale.

No other stability treatment is reported. Optimisation is AdamW with linear warmup from 0 and cosine decay to
0.1× base; grid search over learning rate, weight decay and warmup steps (Table A3); biases and LayerNorm
parameters exempt from weight decay.

### 2.8 Relevance and cautions for this project

**Useful.**
- It supplies the *formal* statement that the project's "conditional-architecture ladder" needs: the rungs are
  not a taxonomy someone invented, they are readings of one algebraic form at different code dimensions. The
  `H = 1` degenerate case landing exactly on scalar gain is the cleanest possible demonstration that FiLM and
  hypernetworks are one family.
- The module-collapse connection (§6) is directly transferable. Prior work found most attention heads can be
  pruned post-training with small loss (Voita et al. 2019; Michel et al. 2019); this paper reinterprets that as
  **module collapse** — the pathology where a modular system learns to use only one module. Any project
  modulator with `K` slots should be checked for the same pathology, and this gives a principled reason to
  expect it.
- The latent-code probe is a cheap, directly reusable diagnostic: train a classifier on the modulator's output
  code to predict a known task variable, evaluate on held-out conditions. If it decodes, the code is carrying
  task structure rather than nuisance.

**Cautions.**
- **No RL, no FiLM baseline, no comparison to concatenation.** Citing this paper for any *performance* claim
  about hypernetworks-vs-FiLM in RL would be a misuse. It supports the *conceptual* unification only.
- The compositional-generalization causal claim is a hypothesis with correlational support on two synthetic
  tasks. State it as "consistent with", never "shows that".
- The MoE control (64.34 on SRAVEN) means the benchmark does not isolate the mechanism.
- Generalization is recombination of learned primitives only; novel primitives fail completely.

---

## Appendix: Section-by-Section Backbone — Schug et al. 2025

Preserving the paper's original section order.

**Abstract.** Reformulates multi-head attention as a hypernetwork, revealing a composable low-dimensional
latent code specifying key-query specific operations. Claims: the code is predictive of subtasks on unseen
compositions; making the generated value network nonlinear improves compositional generalization; introduces
SRAVEN; shows scaling model and data enables compositional generalization and a functionally structured latent
space.

**1. Introduction.** Frames abstract reasoning and the long connectionist-vs-symbolic debate. Reviews the
in-context-learning literature: transformers performing gradient-based optimisation in-sequence (Dai 2023;
Akyürek 2023; von Oswald 2023), linear attention as fast-weight programmer (Schmidhuber 1992; Schlag 2021),
task vectors in hidden activations (Hendel 2023; Todd 2024). States the key finding — multi-head attention is
mathematically equivalent to a hypernetwork — and the hypothesis that sharing one hypernetwork per layer
encourages reuse and recombination. Four listed contributions: the reformulation; the scaling result; the HYLA
modification; the SRAVEN benchmark.

**2. Attention as a Hypernetwork.** Notation: bold lower-case vectors, bold upper-case matrices, bold italic
upper-case learnable parameters.
- **2.1 Multi-head attention.** Defines hypernetwork `h(z;θ) → W` parameterising value network `f(x;W)`.
  Defines self-attention, per-head projections, Eq. 1 for the stacked attention array with normalization `σ`.
  Derives Eqs. 2–5 identifying latent code, hypernetwork and value network. Explicitly distinguishes this from
  the fast-weight-programmer view (composition over head index, not key index). States that the same
  hypernetwork is reused for every key-query index, which "incentivizes reuse of latent codes".
- **2.2 Hypernetwork Linear Attention (HYLA).** Motivates modifying attention to reinforce the mechanism:
  make hypernetwork and value network nonlinear; use `σ` to encode inductive biases such as competition or
  sparsity. Defines HYLA (Eqs. 6–7) with ReLU `φ` and RMSHead normalization across the head index. Notes it
  adds no parameters, is a drop-in replacement, and requires no cross-key communication.

**3. Compositional Generalization on Fuzzy Logic Functions.** Task built from Zadeh operators (Eq. 8):
`x_i ∧ x_j = min`, `x_i ∨ x_j = max`, `x̄_i = 1 − x_i`. Each task is a disjunctive-normal-form function of `K`
terms over `L` variables (Eq. 9 shows `L = 4`, `K = 2`). All `2^L` terms indexed; combinations split into
train and OOD sets so constituent terms are always seen. `N` in-context examples, token dimension `L+1`,
target masked on final token, mean-squared-error loss.
- **3.1 Compositional generalization.** Sweeps in-context examples and held-out fraction. All models solve the
  task with enough examples; OOD performance declines as held-out fraction rises; HYLA declines least
  (Figure 2C). In-distribution differences are small (Figure A3B/D). Appendix A.1 separates RMSHead and
  nonlinearity contributions. Negative result: novel combinations of **unknown** terms are unsolvable by all
  models (Figure A3C).
- **3.2 Latent code structure.** Collects attention scores of the response token attending to itself, one
  `H`-vector per layer and task, on held-out tasks. tSNE clusters (Figure 2D) match the constituent **terms**
  more than the output value; logistic-regression probes decode the terms on held-out tasks (Figure 2B).

**4. SRAVEN: Symbolic Raven.**
- **4.1 Abstract reasoning based on symbolic Raven's Progressive Matrices.** Motivates a symbolic,
  compositional benchmark that also models the "finding correspondences" difficulty of Carpenter et al. 1990.
- **4.2 Task description.** 8 context panels + 1 response panel. Each panel a tuple of `K` integers (`K = 4`
  default) drawn from `{0,…,F−1}` with `F = 8`; arithmetic rules use modular arithmetic mod `F`. `K` of `R = 8`
  possible rules sampled per task; each rule generates three length-3 sequences → nine panels. Model predicts
  each feature independently; a prediction counts as correct only if **all** subpredictions are correct.
  Direct symbol prediction avoids the multiple-choice shortcut found in prior Raven datasets (Zhang 2019;
  Hu 2021). **25 %** of rule combinations held out by default; permutations (AB vs BA) treated as identical
  and never split.
- **4.3 Finding correspondences.** Explains the Carpenter difficulty via the shape-vs-orientation grouping
  example (Figure 3B). Implemented by sampling a **column-specific permutation** of features, consistent across
  rows, so the task cannot decompose into `K` independent single-feature tasks. Fewer than half a percent of
  instances are ambiguous (Appendix B.2).
- **4.4 Results.** (i) Scaling model size and data enables compositional generalization — all classes reach
  ~80 % OOD given enough data/size; HYLA best at small data and small models (Figure 4). (ii) Disrupting the
  hypernetwork mechanism hurts — single-head models show noticeably lower OOD accuracy (Figure 5C).
  (iii) Latent code structured by rule — final-layer clusters match ground-truth rules; target magnitude
  explains early layers better (Figures 5A/B, A6, A7). (iv) Semantically related rules (addition/difference)
  share codes (Figure 5E). (v) Logistic-regression rule decoding from codes succeeds on OOD tasks, best in
  later layers (Figure 5F). Figure 5D shows difficulty scaling with `K`.

**5. Language modeling.** 50 M-parameter decoder-only transformers, 130 B tokens of C4 (Raffel 2020). HYLA
improves over linear attention and performs closely to softmax attention, notable given softmax's hypothesised
role in binding and associative recall (Arora 2023; Olsson 2022; Schlag 2021). Suggests practical relevance of
the mechanism at scale.

**6. Related work.** *Role of multiple heads*: prior work prunes almost all but one head with small loss
(Voita 2019; Michel 2019), leading to speculation that heads mainly aid training stability (Liu 2021); this
paper offers the alternative account, and connects singular-head dominance to **module collapse** (Shazeer
2017; Kirsch 2018; Rosenbaum 2018; Mittal 2022). *Compositional generalization*: scaling improves it (Hosseini
2022; Furrer 2021); extent beyond training distribution remains debated (Srivastava 2023; Press 2023; Dziri
2023). *Raven-based tasks*: prior variants render images; SRAVEN is symbolic, parametrically controllable, and
adds the correspondence difficulty.

**7. Discussion.** Restates the decomposition and the empirical findings. Generalises the perspective:
multi-head attention is *one choice of granularity* — value networks are key-query specific with a sum-pooling
step over keys; alternatives include a query-specific value network subsuming the key aggregation, or
parameterising the full sequence operation. Draws a connection to attention-based graph neural networks
(Veličković 2018; Shirzad 2023): under this reading the **message function is a hypernetwork subsuming the
attention weights** and aggregation becomes a plain sum, raising the question of alternative pooling
operators (Rosenbluth 2023; Dudzik 2023). **Limitations:** analysis restricted to models trained from scratch
for control over training data; whether pretrained large-scale models form similarly structured codes is
future work.

**Appendix A — Additional results.** A.1 Model ablations (Table A1, reproduced in §2.6 above), plus HYLA+ with
a deeper value network (Eq. 10), the softmax-instead-of-RMSHead ablation, and the mixture-of-experts
replacement of the feedforward layer. Figures A2–A8: tSNE of fuzzy-logic codes by label/function/term;
fuzzy-logic performance metrics including training `R²` and the unknown-term failure; SRAVEN training loss;
held-out-fraction sweep (A5); SRAVEN latent codes at depth 4 and 16 (A6, A7); detailed attention-score /
latent-code samples and cosine similarities (A8).

**Appendix B — SRAVEN.** B.1 number of possible tasks and instances; B.2 ambiguity handling; B.3 rule
definitions.

**Appendix C — Experimental details.** Standard pre-LayerNorm decoder-only block
(`Z = MHA(LN(X)) + X`, `Y = FF(LN(Z)) + Z`); T5-style relative positional embeddings for the synthetic tasks,
rotary embeddings for language modelling; GeLU feedforward. Tokenization: raw concatenated examples (fuzzy
logic), one-hot integers (SRAVEN), SentencePiece 32 000 vocabulary with tied transposed embedding (language).
AdamW, linear warmup from 0, cosine decay to 0.1× base, biases and LayerNorm exempt from weight decay.
Table A3 hyperparameters — fuzzy logic: 2 layers, width 1×, `emb_dim` 128, `kqv_dim` 16, `mlp_dim` 256,
**8 heads**, batch 128; SRAVEN: 4/8/16 layers, width 1×/2×/4×, `emb_dim` 128, `kqv_dim` 64, `mlp_dim` 256,
**16 heads**; language modelling: 6 layers, `emb_dim` 512, `kqv_dim` 64, `mlp_dim` 2048, **8 heads**,
batch 256.

**Appendix D — Additional details.** D.1 Compute: two RTX 3090s for development, a 4×RTX 3090 server and an
RTX 4090 Slurm cluster for experiments; fuzzy logic 2–3 min/run, SRAVEN 20–200 min/run, language modelling
16 Cloud TPU v5e at 72–100 h/run; totals ≈24 GPU-hours (fuzzy), ≈10 GPU-days (SRAVEN), ≈163 TPU-days (C4).
D.2 Software: JAX, Flax, NanoDo, DeepMind JAX ecosystem, WandB, Plotly.

---
---
