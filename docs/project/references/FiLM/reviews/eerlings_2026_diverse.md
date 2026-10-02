---
title: "DIVERSE: Disagreement-Inducing Vector Evolution for Rashomon Set Exploration"
authors: ["Gilles Eerlings", "Brent Zoomers", "Jori Liesenborgs", "Gustavo Rovelo Ruiz", "Kris Luyten"]
year: 2026
venue: "\"Preprint\" — running header on every page of the held PDF; stamped arXiv:2601.20627v1 [cs.LG], 28 Jan 2026. The 'ICLR 2026 Poster' attribution recorded in the corpus is NOT verifiable from this file."
slug: eerlings_2026_diverse
source_pdf: docs/project/references/FiLM/sources/Eerlings et al. 2026 - DIVERSE - Disagreement-inducing vector evolution for Rashomon set exploration (preprint).pdf
topic: FiLM
---

# DIVERSE: Disagreement-Inducing Vector Evolution for Rashomon Set Exploration

## Plain-English entry point

Train the same network twice on the same data and you get two models that score the same but
disagree about individual examples. Statisticians call this the **Rashomon effect** — after the film
in which four witnesses give four irreconcilable accounts of one event — and the collection of
equally-accurate-but-behaviourally-different models is a **Rashomon set**. It matters practically: if
two models are equally accurate and one denies your loan while the other approves it, the outcome
depended on which model happened to be trained, not on you.

The obvious way to map that set is to retrain many times, which is expensive. This paper proposes a
cheaper route, and the route is what makes it relevant here. Take one trained model, **freeze its
weights**, and bolt FiLM layers onto it — the same gain-and-offset operator this corpus is about.
Now a single latent vector `z` controls all of those FiLM layers at once, so varying `z` sweeps out
a family of behaviourally different models without touching a single weight. Then search over `z`
with an evolution strategy, looking for vectors that make the model *disagree* with its own
unmodulated self while staying within an accuracy margin.

**The reason this paper belongs in a review of conditional modulation is that it inverts the
operator's purpose.** Everywhere else in this corpus, `(γ, β)` is a *control input*: something tells
the network which task it is doing, and the network re-tunes. Here the modulation parameters are a
**search space** — a low-dimensional, well-behaved handle on the function the network computes, used
to explore the neighbourhood of a trained model. The conditioner is not a signal at all. Nothing is
learned; the projections are frozen random matrices.

This is **not reinforcement learning** — the experiments are supervised image classification on
MNIST, PneumoniaMNIST and CIFAR-10 — so it contributes to the mechanism lineage, not to the
evidence base on whether modulation helps an RL agent.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | A latent vector `z ∈ R^d`, **not derived from any input**. It is the free variable of an outer search, initialised at `z = 0`, which recovers the unmodified reference model exactly. |
| **What is modulated** | The **pre-activations** of a frozen pretrained classifier. Three placements depending on architecture: after dense layers; after convolutional blocks (after batch normalisation where present); and optionally on residual skip connections. |
| **Modulation operator** | Full affine FiLM with a **bounded** gain: `FiLM(h; z) = γ(z) ⊙ h + β(z)`, with `γ(z) = 1 + tanh(z W_γ)` and `β(z) = tanh(z W_β)`. |
| **Granularity** | Per-channel. For convolutional outputs `γ, β ∈ R^{B×C}` are reshaped to `(B,1,1,C)` and broadcast across space — per-channel, shared across spatial positions. |
| **Placement / number of sites** | **All inserted FiLM layers share one latent vector `z`**, so a single `d`-dimensional code modulates the whole network in a coordinated, network-wide fashion. |
| **What is learned** | **Nothing.** `W_γ` and `W_β` are frozen random projections drawn from `N(0, 0.5²)`. The base model's weights are frozen. Only `z` moves, and it moves by CMA-ES, not by gradient descent. |
| **RL algorithm** | **Not RL.** Supervised classification; MNIST, PneumoniaMNIST, CIFAR-10. |
| **Claim strength** | **Ablated** for the method's own question (compared against retraining, dropout sampling and adversarial weight perturbation), but the modulation operator itself is not compared against an alternative conditioning mechanism — there is no concatenation or hypernetwork arm, because that is not the paper's question. |

## Section-ordered backbone

**§1, Introduction.** Frames the Rashomon effect and predictive multiplicity, and the practical
tension: multiplicity is useful for uncertainty estimation, fairness auditing and interpretability,
and is simultaneously a threat to trust when equally accurate models assign different outcomes.
Positions three prior approaches — retraining (costly), adversarial weight perturbation (scales
poorly), dropout sampling (limited control over diversity) — and proposes a fourth that is
gradient-free and gives explicit diversity control.

**§2, Background.** Standard empirical-risk setup; a reference model `f_ref` obtained by ordinary
training; the Rashomon set defined as models within a performance margin of it.

**§3, Modulating activations for Rashomon set generation.** Three steps: train a reference model;
wrap it in frozen FiLM layers to define a modulated model space; search that space with CMA-ES under
the Rashomon accuracy constraint. This is where the operator is defined (equation 7 above) and where
the design choices worth extracting live.

**§4–5, Experimental setup and results.** MNIST, PneumoniaMNIST, CIFAR-10. DIVERSE discovers
accurate and functionally distinct model sets, beating retraining on efficiency and beating dropout
on diversity most of the time. The authors are careful in the abstract: *"retraining remains the
baseline for generating Rashomon sets; DIVERSE achieves comparable diversity at reduced
computational cost"* — a parity-plus-efficiency claim, not a superiority claim.

## Phase 1 — Undergraduate-level synthesis

The construction is elegant and easy to state. A trained network is a point in a very
high-dimensional weight space. Exploring its neighbourhood directly is hopeless — the space is far
too big, and most directions either do nothing or break the model. DIVERSE replaces that space with
a much smaller one: a `d`-dimensional latent vector, mapped through fixed random matrices into
per-channel gains and offsets across the whole network.

Three properties make this a *good* search space, and each is a deliberate design decision:

1. **It contains the original model, at a known point.** `z = 0` gives `γ = 1, β = 0`, which is the
   identity, so the reference model is the origin and the search starts somewhere sane.
2. **It is bounded.** The `tanh` confines `γ ∈ [0, 2]` and `β ∈ [−1, 1]`. The authors state the
   reason directly: preventing "destabilizing amplification or large DC shifts during search."
3. **It is reproducible and hyperparameter-free.** Because the projections are frozen and random,
   the modulation space is fixed once the seed is fixed; there is nothing to tune.

The search itself is CMA-ES — an evolution strategy that maintains a Gaussian over candidate
vectors and adapts its covariance as it learns which directions are productive. It needs only
function evaluations, so it works on a model whose gradients are unavailable.

## Phase 2 — Graduate-level deep dive

### 2.1 The bounded gain, and why it does not contradict Perez et al.

This corpus records, as one of its firmest facts, that **bounding the gain hurts**: Perez et al.
2018 tried sigmoid, `tanh` and exponential constraints on `γ` and all three degraded accuracy, which
is why implementations since use an unrestricted signed gain. DIVERSE bounds the gain with `tanh`
and reports no such problem.

These do not conflict, and the reason is instructive about what the operator is *for* in each case.
Perez's `γ` is **learned by gradient descent to fit a task**, so any constraint on its range is a
constraint on the hypothesis class, and clipping the range costs expressiveness the task needed.
DIVERSE's `γ` is **searched by an evolution strategy to stay near a reference model**, so the bound
is not a restriction on what can be fit — it is a leash keeping the search inside the region where
the frozen weights still compute something sensible. A bound that is a cost when you are fitting is
a feature when you are exploring.

The general lesson for the review: "bounding the gain hurts" is a claim about *learned* modulation
under a task loss, and it should be quoted with that qualifier.

### 2.2 One shared latent for the whole network — the grouped-modulation question

The corpus has an open question about whether **grouped** modulation — one gain shared across a
block of units rather than one per channel — is attested anywhere, and the answer so far is
essentially "once, and forced by a symmetry constraint rather than chosen" (EquAct's iFiLM, where
Schur's lemma requires one scalar per irreducible block).

DIVERSE is a second, different instance of coarsening, and it is worth recording precisely because
it is *not* the same thing. The FiLM layers are still per-channel; what is shared is the **latent
code upstream of them**. One `d`-dimensional `z` is projected into every site's `(γ, β)` through
per-site frozen matrices. So the modulation is fine-grained at the point of application but
low-dimensional at the point of control.

That is structurally the same idea as FLOWER's Global-AdaLN-Zero — one generator weight set feeding
all layers — arrived at from a completely different motivation. FLOWER shares to save parameters;
DIVERSE shares to make the search space small enough for an evolution strategy. Two papers, two
purposes, one architectural conclusion: **the control space for modulation can be far smaller than
the modulation itself, apparently without penalty.** That is now three independent observations
pointing the same way, counting the flat rank sweep recorded elsewhere in the corpus.

### 2.3 The modulation latent as an object of study

The sharpest contribution for this review is conceptual. In every other corpus paper the pair
`(γ, β)` is a *means*: the interesting object is the task, and the modulation is how the network
adapts to it. Here `(γ, β)` — or rather the `z` that generates them — is the *object*: a coordinate
system on a neighbourhood of function space, in which one can measure distances, run an optimiser,
and characterise a set of models.

That reframing has a use the paper does not pursue but which is directly relevant to reinforcement
learning. If a modulator's latent is a well-behaved coordinate system on functional variation, then
a trained modulator's occupied region is measurable: how much of the space does a policy's modulator
actually use, and is the used region low-dimensional? That is a diagnostic for whether a modulator
is doing anything, and it is close in spirit to CASH's SND metric (total-variation distance between
action distributions with the observation held fixed and only the context varied), which the corpus
already records as a portable "does the modulator actually modulate?" test.

### 2.4 What this paper does not establish

- **No RL evidence whatsoever.** Supervised classification on three small image datasets. It cannot
  speak to whether modulation helps a policy.
- **No comparison against other conditioning mechanisms.** There is no concatenation arm and no
  hypernetwork arm, because the paper is not asking which conditioner is better. Do not cite it in
  the head-to-head table.
- **Local, not global, Rashomon exploration.** The authors say so: this explores a *local* Rashomon
  set around one reference model. It does not characterise the whole set, and models reachable only
  by retraining into a different basin are out of reach by construction.
- **Venue is unverified.** The held PDF prints "Preprint" and nothing else. The corpus's recorded
  "ICLR 2026 Poster" attribution comes from elsewhere and is not supported by the document.
- **Scale.** MNIST, PneumoniaMNIST and CIFAR-10 are small. Whether a frozen random projection into a
  `d`-dimensional latent stays expressive enough on a large model is untested.

## Connections

- [`perez_2018_film`](perez_2018_film.md) — the operator, and the source of the "bounding the gain
  hurts" finding this paper appears to contradict and (§2.1) does not.
- [`turkoglu_2022_film_ensemble`](turkoglu_2022_film_ensemble.md) — the other corpus paper that uses
  the modulation parameters for something other than task conditioning, there to generate ensemble
  members from one backbone. DIVERSE and FiLM-Ensemble are the two "modulation as a family of
  models" papers in the library.
- [`yan_guo_2025_context_aware_dg`](yan_guo_2025_context_aware_dg.md) — the other FiLM-corpus paper
  whose conditioner is not an external signal.
- `modulation_in_rl/field_review/` — the shared-control-space observation in §2.2 bears on that
  review's open question about whether modulator capacity matters.
