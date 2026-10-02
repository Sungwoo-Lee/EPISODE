---
title: "Don't Flatten, Tokenize! Unlocking the Key to SoftMoE's Efficacy in Deep RL"
authors: ["Ghada Sokar", "Johan Obando-Ceron", "Aaron Courville", "Hugo Larochelle", "Pablo Samuel Castro"]
year: 2025
venue: "\"Published as a conference paper at ICLR 2025\" — running header on every page of the held PDF. Verified."
slug: sokar_2025_dont_flatten_tokenize
source_pdf: docs/project/references/modulation_in_rl/sources/Sokar et al. 2025 - Don't flatten, tokenize - Unlocking the key to SoftMoE's efficacy in deep RL.pdf
topic: modulation_in_rl
---

# Don't Flatten, Tokenize! Unlocking the Key to SoftMoE's Efficacy in Deep RL

## Plain-English entry point

Reinforcement-learning agents that see the world through a camera usually process pixels with a
convolutional encoder. That encoder outputs a small three-dimensional block of numbers — height ×
width × channels — and essentially every agent since DQN then **flattens** it into one long vector
before the final layers compute action values. Flattening is so standard that nobody argues about
it.

Separately, a line of recent work found that replacing those final layers with a **mixture of
experts** — several parallel sub-networks, with a learned router deciding which of them each piece
of input goes to — lets deep RL agents get *bigger* without getting *worse*, which is otherwise a
chronic problem. The natural explanation was that the experts specialise: different sub-networks
learn different things, and that structured sparsity is what buys the improvement.

**This paper takes that explanation apart and finds it is wrong.** The authors strip a soft
mixture-of-experts down component by component and show that the gain does not come from having
several experts, from the experts specialising, from the extra layer the design adds, or from the
extra width. It comes from the step nobody was looking at: to feed a mixture of experts you must
first cut the encoder output into **tokens** instead of flattening it, and *that* is what helps. A
mixture with a **single** expert, scaled up, keeps essentially all of the benefit.

**Why this matters for a review of conditional modulation in reinforcement learning.** Routing is
one of the mechanisms this corpus counts as a rival to affine modulation, and this paper is the
strongest evidence in the corpus that a headline routing result can be produced by something that
is not routing at all. It is a caution about attribution: the corpus contains several papers that
add a conditional-computation module, observe an improvement, and credit the conditioning. Here the
same experiment was run properly and the credit went elsewhere.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | The encoder's own output tokens. Routing is input-dependent, so there is no external conditioner — no task label, no language, no context vector. |
| **What is modulated** | The penultimate layers of the value network (the layers between the convolutional encoder and the action-value head). The encoder itself is untouched. |
| **Mechanism** | **Routing / conditional computation**, not affine modulation. Soft mixture-of-experts: a learnable tensor Φ produces dispatch weights `Φ_D` and combine weights `Φ_C`, so each expert slot receives a *weighted average of all tokens* rather than a hard assignment. Compared against top-k and expert-choice routing. |
| **Granularity** | Per-token, per-slot. `p` slots per expert, default `p = #tokens / #experts`. |
| **RL algorithm** | **Rainbow** (value-based, DQN lineage) with the Impala ResNet encoder for the main study; also DER, the standard Mnih CNN encoder, and Procgen. |
| **Benchmark** | Arcade Learning Environment: 20 games for the main analysis, extended to all 60; 200M environment steps; **5 independent runs per configuration**; scores reported as interquartile mean (IQM) with stratified bootstrap intervals. |
| **Headline result** | The efficacy of soft mixture-of-experts in deep RL is driven by **tokenizing the encoder output**, not by the experts. A single scaled expert (`SoftMoE-1`) matches `SoftMoE-4`. |
| **Claim strength** | **Ablated, thoroughly** — five components isolated individually, on a benchmark with a defensible seed count and an appropriate aggregate statistic. Among the most carefully controlled papers in this corpus. |

## Section-ordered backbone

**§1–2, Introduction and background.** Sets up the scaling problem: deep RL degrades as networks
grow. Prior work (Obando Ceron et al. 2024; Willi et al. 2024) showed soft mixtures-of-experts
mitigate this and hypothesised structured sparsity as the cause. The authors flag the anomaly that
motivates the whole paper — gains were observed **even with a single expert**, which structured
sparsity cannot explain.

**§3, Mixtures of experts.** Distinguishes *token choice* routing (each token picks k experts;
tokens can be dropped and experts can starve), *expert choice* routing (each expert picks p tokens;
better load balance), and *soft* mixtures (each slot gets a learned weighted combination of all
tokens, so nothing is dropped). Also defines the two tokenization schemes inherited from prior
work: **PerConv** makes `h·w` tokens of dimension `d`; **PerFeat** makes `d` tokens of dimension
`h·w`.

**§4.2, the component ablation — the core of the paper.** Five components isolated:

| Component tested | How | Result |
|---|---|---|
| Combined tokens (the "soft" part) | Compare against expert-choice routing, which does not combine | Combining helps, but expert choice **also** gains substantially over baseline — so combining is not the explanation |
| Expert specialisation | Raise slots per expert to the token count, granting unlimited capacity | **Little change** for both soft and expert-choice routing — specialisation is not a major factor |
| Expert width | Scale up each expert's dimensionality | Does **not** degrade, unlike naïvely scaling the baseline's penultimate layer |
| Network depth | Add an equivalent extra layer to the baseline | Does **not** improve the baseline — the extra projection layer is not the cause |
| Number of experts | Sweep 1, 2, 4, 8 | Gains **plateau after about four**; cannot account for the advantage |

**§5, tokenization.** Having eliminated the others, the authors test tokenization directly by
applying it to the baseline agent with no mixture at all — tokenize the encoder output, then sum or
average over the tokens. This recovers the gains. Figure 1 shows `SoftMoE-1`, a single scaled
expert, tracking `SoftMoE-4`.

**§5.1, additional analyses.** Four tokenization schemes compared: **PerConv best**, PerPatch
close behind, PerFeat worse, and **Shuffled worst** — where Shuffled is PerConv after a fixed
permutation of the encoder output. That ordering is the mechanism argument: shuffling destroys the
*spatial* structure the convolutional encoder produced, and destroys the benefit with it. Also:
`SoftMoE-1` with **10% of the default slots, and even with a single slot**, performs comparably,
which matters because soft-mixture time complexity scales with slot count.

**§8, conclusions and the honest caveats.** Two are stated by the authors and both are load-bearing:

- Tokenization is only meaningful where the encoder is convolutional, i.e. **pixel-based**
  environments. That plausibly explains why mixtures-of-experts gave no gains in PPO and SAC in
  prior work — those were evaluated on non-pixel environments, where there is no spatial structure
  to preserve. Initial experiments on continuous control suggest the findings do carry over.
- "It is somewhat surprising that our results **do not seem to carry over to DQN**." The effect is
  not universal even within the value-based family.

## Phase 1 — Undergraduate-level synthesis

The paper's logic is elimination, and it is worth appreciating as a piece of experimental design.
The claim under test — "mixtures of experts help deep RL because the experts specialise" — is not
attacked directly. Instead each component that could plausibly carry the effect is removed or
neutralised in turn, and the effect is watched. Four components turn out not to matter. The one
remaining candidate is then tested *positively*, by applying it in isolation to an agent with no
mixture at all, where it reproduces the gain.

That last step is what makes the paper convincing rather than merely suggestive. Showing that
removing X does not hurt is weaker than showing that adding X alone helps; this paper does both.

The intuition for why tokenization helps is geometric. A convolutional encoder produces a feature
map whose two spatial axes still mean something — this feature, at this place in the image.
Flattening throws that away: the dense layer that follows sees one long vector in which spatially
adjacent positions have no special relationship. Tokenizing keeps each spatial position as its own
token, so the downstream computation is applied to structured units rather than to an arbitrary
ordering. The **Shuffled** control is the proof: same tokens, same count, same dimensionality, only
the spatial arrangement scrambled — and it is the worst of the four schemes.

## Phase 2 — Graduate-level deep dive

### 2.1 Why this is the corpus's most important attribution warning

The field review this corpus supports asks, of every paper, whether the conditioning mechanism is
*isolated*. Most papers that add a conditional-computation module report improvement and attribute
it to conditioning. This paper is the control experiment for that entire genre, and it returns a
negative: the improvement in the best-known case is produced by a **data-layout change** that the
conditioning machinery merely required as a precondition.

The general form of the error is worth naming, because it is not specific to mixtures of experts.
Adding a conditional module often forces an incidental change elsewhere in the network — an input
reshaping, an extra normalisation, a different initialisation, an extra projection. If the
incidental change is never applied to the baseline on its own, its contribution is silently
credited to the conditioning. A paper's ablation of "with module vs. without module" cannot detect
this; only an ablation of the *incidental change alone* can.

This bears directly on two entries elsewhere in the corpus. FLOWER's shared-generator result is
recorded as **ablated but confounded**, because the per-layer LoRA adapters added to compensate for
coarsening are never themselves ablated — structurally the same error. And HyperMARL's
self-conditioning ablation moves regeneration frequency at the same time as it moves the
conditioner. In both cases the missing arm is the incidental change on its own.

### 2.2 The soft-mixture operator, and why the slot result matters

In a soft mixture with `n` experts and `p` slots each, the input tokens `X ∈ R^{t×d}` are combined
into slot inputs by dispatch weights derived from a learnable `Φ`, so slot `j` receives a convex
combination of *all* `t` tokens rather than a subset. Outputs are recombined by combine weights.
Nothing is dropped and no expert starves, which is the design's advantage over top-k routing.

The cost is that the dispatch and combine operations scale with the number of slots. The finding
that `SoftMoE-1` retains performance at **10% of the default slots, and even at a single slot**, is
therefore an efficiency result of some practical size: the expensive part of the mechanism can be
cut by an order of magnitude without losing the benefit, because the benefit was never coming from
that part.

Note the one component that did *not* vanish: `ExpertChoice-1` underperforms `SoftMoE-1`, so the
soft weighted combination does contribute something beyond tokenization. The paper's claim is that
tokenization is the *primary* driver, not the only one, and the review should quote it that way.

### 2.3 What the paper does not establish

- **It is not a modulation paper.** There is no external conditioning signal, no `(γ, β)`, and no
  claim about affine modulation. It belongs in this corpus as evidence about *routing* and about
  attribution discipline, not as a data point on FiLM.
- **The DQN non-transfer is unexplained.** The authors report it plainly and do not account for it.
  Any claim that tokenization is a general property of pixel-based value-based agents is weakened by
  this.
- **The actor-critic extension is preliminary.** The conclusion cites "initial experiments"
  (Figure 22) suggesting the findings carry to continuous control. That is a promissory note, not a
  result, and should not be cited as one.
- **Spatial structure is the proposed mechanism, not a proven one.** The Shuffled control is strong
  evidence that spatial arrangement matters, but the paper does not isolate *what* the downstream
  layers do with that structure.

### 2.4 Bearing on the field review's open questions

Two of the review's open items move slightly:

1. **"Conditional computation, not gain, is what collapses."** The review records that the
   2024–2026 instabilities cluster on mixtures-of-experts rather than on affine modulation. This
   paper adds a different criticism of the same family: not that it is unstable, but that in its
   best-documented success the credit belongs elsewhere.
2. **"Does modulator capacity matter at all?"** The review's only direct capacity measurement (an
   adapter rank sweep, flat over a 32-fold range) now has a companion: expert count plateaus after
   four, and slot count can be cut by 90%. Two independent capacity sweeps in different mechanism
   families both find the capacity axis nearly flat.

## Connections

- Same corpus, contrasting result: `modulation_in_rl` §17 records MENTOR as evidence that
  conditional capacity helps in single-task visual RL. That entry is context-only and extracts no
  numbers; this paper is the one to cite for what mixtures of experts do and do not buy.
- The attribution failure described in §2.1 is the same shape as the FLOWER confound recorded in
  the `modulation_in_rl` master review §7.3.
- Shazeer et al. 2017 (`FiLM/sources/`) is the sparsely-gated mixture-of-experts original this
  lineage descends from.
