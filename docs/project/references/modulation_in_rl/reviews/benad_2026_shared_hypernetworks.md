---
title: "Dynamics-Aligned Shared Hypernetworks for Contextual RL under Discontinuous Shifts"
slug: benad_2026_shared_hypernetworks
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_modern.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## P3. Benad, Banerjee, Röder, Ay, Butz & Eppe 2026 — *Dynamics-Aligned Shared Hypernetworks for Contextual RL under Discontinuous Shifts* (**DMA\*-SH**)

**PDF:** `docs/project/references/modulation_in_rl/sources/Benad et al. 2026 - Dynamics-aligned shared hypernetworks for contextual RL.pdf`
**Code:** https://github.com/dma-sh/dmash (stated in §1)

### ⚠ P3.0 Venue correction — read before citing

**The PDF does not say ICLR 2026 anywhere.** Page 1 carries a single italic line,
**"Preprint."**, and the arXiv stamp `arXiv:2602.06550v2 [cs.LG] 11 May 2026`; the
embedded PDF metadata gives `DOI: 10.48550/arXiv.2602.06550`, i.e. the arXiv DOI,
not a proceedings DOI. There is no acceptance note, no camera-ready banner, no
"Published as a conference paper at ICLR 2026" header, and the paper is not in the
ICLR two-column-with-banner style.

The acquisition brief described it as ICLR 2026. That may well be true from an
external source (OpenReview, an author page), but it is **not verifiable from inside
this file**, which is the standard this folder applies. **Cite as a 2026 preprint
(arXiv:2602.06550v2) unless someone confirms acceptance from a venue-side record.**
Flagged here rather than silently propagated.

### P3.1 Plain-English entry point

Imagine borrowing a colleague's laptop and finding the trackpad scrolls backwards.
Every practised swipe now does the opposite of what you intend, and no amount of
trying harder helps — you have to switch to a different control law, not adjust the
one you have. That is this paper's central problem, which it calls **actuator
inversion**: a hidden property of the world flips the sign of what your actions do.

Why that is hard for the usual approaches: most ways of telling an agent about its
situation assume the required change is *smooth*. Glue a context number onto the
observation, or learn a Gaussian latent code, and the network naturally interpolates
between neighbouring contexts. But there is no meaningful halfway point between
"push left to go left" and "push left to go right" — an averaged behaviour is simply
incoherent.

The paper's answer has three ingredients:

1. **Infer the context rather than being told it.** A recurrent encoder watches the
   last few transitions — state, action, and how much the state changed — and
   compresses them into an 8-number code. Nothing tells it what the context *is*;
   it has to work it out from how the world responded.
2. **Train that code only on a prediction task, never on reward.** The code is
   trained to make a forward-dynamics model predict the next state change
   accurately. Reward gradients are explicitly blocked from touching it.
3. **Let one small side-network turn that code into weights, and share those weights
   across all three of the dynamics model, the policy, and the value function.**
   Not three separate modulators — one, whose output all three modules use.

The result: on a purpose-built benchmark of sign-flip and channel-swap tasks, this
beats plain domain randomisation by **58 %** on held-out contexts, the standard
concatenate-the-context baseline by **11.5 %**, and the Decision Adapter of §P1 —
which is the same idea with *given* context and *separate* policy/value
hypernetworks — by **4.6 %**.

The two ablations the project specifically asked about both exist and both are
decisive. Separate hypernetworks per module (**DMA\*-H**) are worse than one shared
one. And letting reward gradients flow into the shared modulator does not merely
degrade performance — **it collapses learning to near-zero return.**

### P3.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | **Preprint, 2026.** Printed on p. 1: "Preprint." Stamp: `arXiv:2602.06550v2 [cs.LG] 11 May 2026`. See §P3.0 — the ICLR 2026 attribution is **not** confirmable from the PDF. Authors: Benad, Banerjee (equal contribution), Röder, Ay, Butz, Eppe — TU Hamburg / Santa Fe Institute / Tübingen. |
| **Conditioning signal** | **INFERRED from transitions — the first paper in this batch to do so.** A sliding window `τ^c_t` of the past `K` transitions, each a tuple `(s_t, a_t, δs_{t+1})` with `δs_{t+1} = s_{t+1} − s_t` the **state difference**. Encoded by `g_φ` into `z_t ∈ R^8`. Pipeline: random masking → linear projection → **AvgL1Norm** → LSTM → projection → **SimNorm** (two 4-dimensional simplices via group-wise softmax). `K = 24` for the toy environments, `K = 128` for DeepMind Control / Gymnasium; only a **random 20 % subsample** of the window is fed to the LSTM in random order (a permutation-invariance heuristic borrowed from PEARL — so on DMC it sees ≈ 25 transitions). Context is fixed within an episode. **Ground-truth context is never given to the method** (though the Concat and Decision-Adapter baselines *are* given it — see §P3.5). |
| **What is modulated** | **All three of: the forward-dynamics model `f_{θ,ω}`, the policy `π_{ξ,ω}`, and the action-value function `Q_{ζ,ω}`** — with **the same generated weights `ω`**. One bottleneck adapter per network, inserted **after the feature trunk and before the output head**, with a residual skip. Trunk width 256, bottleneck 32, no activation before the adapter, ReLU after — placement choices explicitly copied from the Decision Adapter, "where the placement of activation functions is likewise crucial." |
| **The operator** | **Hypernetwork-generated bottleneck adapter**, rung 2, essentially the Decision Adapter's operator: `x̃ = x + g_adapter(x; ω)` with `g_adapter(x;ω) = W_up(ω)·ReLU(W_down(ω)·x)`, `W_down : R^256 → R^32`, `W_up : R^32 → R^256`, both emitted by `h_η(z_t)` (von Oswald et al. hypernetwork framework). The novelty is **not** the operator; it is (a) the conditioning signal is inferred, (b) `ω` is **shared** across dynamics/actor/critic, and (c) `ω` is **trained only by dynamics prediction**, with a stop-gradient blocking RL losses. |
| **Capacity-spectrum position** | **Rung 2**, identical in form to Beukman. The paper's own theory (§P3.6) argues that the essential property is *multiplicativity* — `W(z)x` produces genuine bilinear coupling between feature and context coordinates — which a concatenation ReLU MLP cannot represent exactly on any set with non-empty interior. |
| **RL algorithm** | **SAC**, CleanRL defaults, deliberately untuned, for every method except the recurrent Amago baseline. Critic LR 1e-3, actor LR 3e-4, hidden dims (256, 256), ReLU, γ = 0.99, batch 256, buffer 100 k per context. Trained in parallel across the `n_c = 20` training contexts. |
| **Benchmark** | **The Actuator Inversion Benchmark (AIB)**, introduced here: 14 environments, each with two context dimensions (except ODE-*k*), classified as **overlapping** (a single context-unaware policy can do well — mass, gravity, friction, actuator strength) or **non-overlapping** (every memoryless context-unaware policy incurs nontrivial regret in at least one context — a binary actuator inversion factor `c ∈ {±1}` that flips action effects, or an actuator permutation `q ∈ {0,1}` that swaps action dimensions). Sources: custom (DI, DI-Friction, DI-Perm, ODE, ODE-*k*), DeepMind Control (Cartpole, Cheetah, Reacher E/H, Reacher-Perm, BallInCup, Walker), Gymnasium (WalkerGym, HopperGym). |
| **Seeds and statistics** | **10 seeds**, 20 contexts per split, 10 rollouts per context, three disjoint context sets (train / eval-in interpolation / eval-out extrapolation), reported as **interquartile mean with 95 % bootstrap CIs** after min–max scaling (Agarwal et al.'s `rliable` protocol). This is the most statistically careful reporting in the batch. |
| **Ablation present?** | **Yes, unusually thorough** — see §P3.5. Component ablations (masking, input norm, output norm, and all combinations, by probability-of-improvement), hyperparameter sweeps (masking ratio 0–100 %, four input norms, three output norms, six window sizes), and — critically — **architecture ablations that isolate exactly the two questions asked**: shared vs. separate hypernetworks, dynamics-aligned vs. RL-only hypernetworks, and detach vs. non-detach of the RL gradient. |
| **Reported instability** | **Yes, and one of them is catastrophic.** Letting actor gradients into the shared hypernetwork gives **near-zero returns**. Also: "Hypernetworks can amplify small perturbations in `z_t` into large changes in `ω`" (the stated reason for input masking); output normalisation of `z_t` is "critical for stable online training"; hypernetwork capacity is "a practical bottleneck: too little limits expressiveness, while too much can overfit and reduce stability"; dynamics-model errors can propagate into the representation under misspecification. |
| **Single- or multi-task** | Contextual MDP with **dynamics-only variation**, reward fixed: `r^c = r ∀c`. Same formalism as Beukman. |

### P3.3 Ask (a) — what does sharing the modulator across dynamics, policy and value buy?

The paper answers this **three ways**: architecturally, empirically, and
diagnostically.

#### The architecture, stated precisely

Training interleaves two update streams (Appendix A.5, Algorithm 2):

$$\textbf{RL updates:}\quad \xi \leftarrow \xi - \alpha_1 \sum_c \nabla_\xi L^c_\xi, \qquad \zeta \leftarrow \zeta - \alpha_2 \sum_c \nabla_\zeta L^c_\zeta,$$

$$\textbf{Dynamics updates:}\quad \phi \leftarrow \phi - \alpha_3 \sum_c \nabla_\phi L^c_{\phi,\theta,\eta},\quad \theta \leftarrow \theta - \alpha_3 \sum_c \nabla_\theta L^c_{\phi,\theta,\eta},\quad \eta \leftarrow \eta - \alpha_3 \sum_c \nabla_\eta L^c_{\phi,\theta,\eta},$$

where `L_{φ,θ,η} = ‖δŝ_{t+1} − δs_{t+1}‖²₂` is the forward-dynamics reconstruction
loss, and `ω = h_η(z_t)` is treated as a **constant** (stop-gradient) inside the
actor and critic losses. So the parameter sets partition cleanly:

- `η` (hypernetwork) and `φ` (context encoder) are updated **only** by dynamics
  prediction;
- `ξ` (actor base) and `ζ` (critic base) are updated **only** by RL;
- `θ` (dynamics base) only by dynamics prediction.

The three modules remain coupled through the single shared pathway

$$\tau^c_t \xrightarrow{\ g_\phi\ } z_t \xrightarrow{\ h_\eta\ } \omega \xrightarrow{\ \text{shared adapters}\ } \{ f_{\theta,\omega},\ \pi_{\xi,\omega},\ Q_{\zeta,\omega}\}.$$

The paper's own framing: this "acts as a **structural prior**, requiring the actor
and critic to process context through adapters shaped by the dynamics", and it
"separates mode identification from mode-conditioned control, unlike recurrent or
Transformer agents that entangle both in an RL-trained hidden state."

#### The comparison arm: DMA\*-H (separate hypernetworks)

DMA\*-H gives each module its own hypernetwork `η^f, η^π, η^Q` producing separate
`ω^f, ω^π, ω^Q`. The forward-dynamics loss updates `η^f`; **the actor and critic
losses update `η^π` and `η^Q` directly**. The stated concern: this "decouples
dynamics-driven and reward-driven adaptation, which can introduce objective mismatch
when reward-driven adapters move in directions not supported by the
dynamics-trained pathway."

**Result (Figure 15):** the shared design outperforms DMA\*-H across all three
context splits. Reported as IQM bars with CIs; the paper's summary is that
"hypernetwork sharing" is one of four ablated components that "are all beneficial."

#### The diagnostic: shadow gradients (§6.5)

This is the paper's most original piece of evidence and worth understanding. Because
`ω` is detached in the RL losses, the *actual* gradient of the actor loss with
respect to `z` is identically zero: `∇_z L_π = 0` by construction. So they define a
**shadow gradient** — temporarily remove the stop-gradient, compute
`E‖∇_z L_π‖`, and **throw it away without ever applying it**. It measures: *how much
would the policy objective like to change the context code, if it were allowed to?*

Interpretation of the result:

- **DMA\*-SH shows persistently non-negligible shadow norms** — the policy objective
  remains strongly sensitive to the context signal throughout training. The context
  pathway stays *live*.
- **DMA\*-H shows substantially smaller shadow norms** — "consistent with weaker
  effective context dependence along the corresponding adapter pathway."
- This separation "co-occurs with faster learning and higher returns for DMA\*-SH."

The claim, then, is counter-intuitive and precise: **the design that forbids the
policy from shaping the context code is the one where the policy ends up depending
on it more.** The paper's proposed explanation is an *implicit gradient
regularisation* story — when the actor and critic are allowed to bend their own
modulators toward reward, they bend them toward degenerate, mode-blurring solutions,
and the context pathway atrophies; when they cannot, they must actually use the
dynamics-grounded structure.

**A caveat the project should register.** The shadow gradient is a *diagnostic
signature*, not a measurement of the trained system: it computes a quantity along a
pathway that does not exist during training. Its interpretation ("sustained
hypothetical sensitivity") is reasonable, but nothing in the paper establishes that
a larger shadow norm *causes* better returns; the two are shown to co-occur across
four environments. Treat it as suggestive evidence, not a demonstrated mechanism.

#### Efficiency: sharing is also cheaper (Remark A.7)

Measured under matched hardware, batch size, precision, and update schedule, against
the Decision Adapter — which is precisely "the same operator with separate
policy/value hypernetworks and given context":

| Comparison | Parameters | Training speed | Peak memory |
|---|---|---|---|
| DMA\*-SH **vs. DA** (Decision Adapter) | **+4.1 %** | **43.5 % faster** | **24.4 % less** |
| DMA\*-SH **vs. DMA** (no hypernetwork at all) | +9.5 % | **79.2 % slower** | +21.7 % more |

The first row is the interesting one and directly addresses ask (a): **one shared
context-to-adapter map across three modules costs essentially the same parameters as
separate maps but trains substantially faster and uses less memory.** The second row
is the honest cost of the whole approach against plain concatenation of an inferred
code — a hypernetwork roughly doubles wall-clock, matching Beukman's §8 complaint.

The paper also notes the adapter's asymptotic cost: `O(dk)` per adapted module for
trunk width `d` and bottleneck `k`, "rather than the `O(d²)` cost of a full
context-conditioned layer" — the same low-rank argument as Beukman's App. D.3.

### P3.4 Ask (b) — is *dynamics-grounding rather than reward* the thing that makes it work? Yes, and it is ablated three ways

This is the paper's strongest experimental contribution and the answer is
unambiguous. Figure 15 contains **seven arms**; five of them are variations on
exactly this question:

| Arm | What it changes | Result |
|---|---|---|
| **DMA\*-SH** | Reference: shared hypernetwork, dynamics-trained only, RL gradients detached | Best across all three splits |
| **DMA-SH** | Shared hypernetwork but **without** normalisation and masking | Worse — the stabilisers are load-bearing |
| **DMA\*-H** | **Separate** hypernetworks for dynamics, actor, critic; actor/critic hypernetworks trained by their own RL objectives | Worse than shared |
| **DMA\*-H (RL only)** | Hypernetwork on the actor and critic **but not on the dynamics model** — so the RL adapter weights are **not dynamics-aligned at all**. The paper notes this "closely mirrors R2PGO (Li et al. 2024b) in an online RL setting", modulo a KL term and a contrastive term | Worse — this is the cleanest isolation of "does the dynamics grounding matter?" |
| **DMA\*-SH (critic non-detached)** | Allow critic gradients into the shared hypernetwork | Degraded |
| **DMA\*-SH (actor non-detached)** | Allow actor gradients into the shared hypernetwork | **"leads to near-zero returns"** |
| **DMA\*-SH (actor-critic non-detached)** | Allow both | Degraded / collapsed |

The verbatim conclusion (Appendix F, p. 48):

> "Allowing actor gradients to propagate directly through the shared hypernetwork
> leads to near-zero returns (DMA\*-SH, actor non-detached). This shows that letting
> RL rewrite the shared `ω` is harmful, and that gradient detachment is necessary."

**So the answer to ask (b) is: yes, decisively, and the failure mode is total rather
than gradual.** Note carefully what is and is not established:

- **Established:** with a *shared* hypernetwork, reward gradients must be blocked, or
  training collapses. And a hypernetwork trained on RL objectives without any
  dynamics alignment (DMA\*-H RL-only) underperforms one that is dynamics-aligned.
- **Not established:** that dynamics prediction is the *uniquely* right grounding
  signal. No other self-supervised auxiliary objective (reward prediction, inverse
  dynamics, contrastive/temporal-consistency losses, next-observation
  reconstruction) is tested as the modulator's training signal. The comparison is
  *dynamics-prediction vs. reward*, not *dynamics-prediction vs. other
  self-supervision*. A project citing this should say "grounding the modulator in a
  transition-prediction objective rather than in reward", not "dynamics prediction
  is the right objective."
- **Partially confounded:** the collapse under non-detachment is measured only in the
  *shared* configuration. DMA\*-H, by design, lets RL gradients train `η^π` and
  `η^Q` and does **not** collapse — it merely underperforms. So "reward gradients
  destroy the modulator" is specific to the case where **one modulator serves all
  three modules**: there, an actor gradient rewrites the dynamics model's adapter
  too, which is a much more destructive edit than rewriting a private one. That is a
  coherent story and the paper gestures at it, but it does not run the decomposition
  that would prove it.

#### A neat corroborating result: smooth-prior methods fail on discontinuous shifts

Appendix F reports that both **VariBAD** and **DMA-Pearl** — which regularise the
latent context toward a Gaussian prior — do fine on the *overlapping* DI-Friction
but "struggle considerably with the non-overlapping contextualizations in DI and
ODE". The stated reason: their objectives "explicitly encourage latent embeddings to
vary continuously with respect to context trajectories… where the correct
representation requires a sign flip rather than a smooth interpolation." VariBAD is
excluded as a baseline for this reason (Fig. 18). DMA-Pearl is retained and does
indeed score best-in-class on several overlapping environments while losing on
non-overlapping ones (Table 2: BallInCup 903, Walker 804, WalkerGym 3162 — all
strong; DI 68, DI-Perm 70 — weak).

**Project reading:** if a conditioning code is trained with a smoothness-inducing
regulariser (a KL to a Gaussian prior, a contrastive loss with a smooth metric),
that regulariser is an assumption that neighbouring contexts require neighbouring
behaviours. Where that assumption is false, the regulariser is actively harmful.

### P3.5 Every head-to-head comparison, with numbers

Eight arms, grouped by what they know about context:

| Group | Arm | What it gets |
|---|---|---|
| Context-**aware** (given ground truth) | **Concat** | `[s; c]` and `[s; a; c]` into policy and Q |
| | **DA** (Decision Adapter, Beukman §P1) | Hypernetwork-generated adapters in policy and Q, conditioned on **given** `c`, **separate** per module. Reimplemented and verified against the original |
| Context-**unaware** | **DR** (domain randomisation) | Ignores context |
| | **Amago** (Amago-2, GRU trajectory encoder) | In-context meta-RL; recurrent; "substantially higher parameter count than the other SAC-based approaches" |
| Context-**inferred** | **DMA** | Vanilla dynamics-model-aligned encoder, `z_t` **concatenated** into policy and Q |
| | **DMA-Pearl** | PEARL's probabilistic encoder + KL to `N(0,I)` (β = 0.4), coupled to a dynamics model |
| | **DMA\*** | DMA + masking + AvgL1Norm + SimNorm; still **concatenation** |
| | **DMA\*-SH** | DMA\* + shared, dynamics-trained hypernetwork adapters |

Note the arm structure carefully: **DMA\* vs. DMA\*-SH is a clean
concatenation-vs-weight-generation comparison holding the conditioning signal
fixed**, and **DA vs. DMA\*-SH is a given-context-with-separate-hypernets vs.
inferred-context-with-shared-hypernet comparison holding the operator roughly
fixed**. Both are directly relevant to the folder's standing question.

#### Aggregate relative gains — Table 9, verbatim

Relative gain computed as `(DMA*-SH − baseline)/baseline × 100`, on min–max-scaled
AER aggregated by environment type:

| Regime | Type | vs. DR | vs. Concat | vs. DA |
|---|---|---|---|---|
| **Train** | All | 50.0 % | 6.3 % | 3.7 % |
| | Overlap | 6.3 % | 6.3 % | 1.2 % |
| | Non-overlap | 90.9 % | 6.3 % | 5.0 % |
| **Eval-out** (extrapolation) | All | **58.1 %** | **11.5 %** | **4.6 %** |
| | Overlap | 7.3 % | 5.4 % | 1.7 % |
| | Non-overlap | **97.3 %** | **14.1 %** | **5.8 %** |
| **Aggregated** (all three splits) | All | 51.9 % | 8.2 % | 3.9 % |
| | Overlap | 7.0 % | 7.0 % | 1.3 % |
| | Non-overlap | 95.1 % | 8.1 % | 3.9 % |

**The structure of this table is the finding, and it echoes Beukman's exactly.**
Read the Overlap rows against the Non-overlap rows:

- On **overlapping** contexts — smooth physical parameters, the ordinary case — the
  gain over concatenation is 5–7 %, and over the Decision Adapter 1.2–1.7 %. Small.
  Domain randomisation is only 6–7 % behind. **The architecture barely matters.**
- On **non-overlapping** contexts — where an averaged behaviour is incoherent — the
  gain over concatenation is 8–14 %, over the Decision Adapter 3.9–5.8 %, and over
  domain randomisation **91–97 %**. **The architecture is the difference between
  working and not.**

This is the same conditional shape as Beukman's distractor result: *all
architectures tie in the benign regime; they separate only in the regime the paper
was built to expose.* Two independent groups, different stressors (irrelevant
context dimensions vs. discontinuous context-to-dynamics maps), same conclusion —
which makes the pattern much more citable than either result alone.

#### Aggregate normalised scores (Tables 2, 6, 8), `All / Overlap / Non-overlap`

Higher is better; min–max scaled; 95 % CIs; 10 seeds:

| Split | Row | Concat | DA | DR | Amago | DMA | DMA-Pearl | DMA\* | **DMA\*-SH** |
|---|---|---|---|---|---|---|---|---|---|
| **Train** | All | 0.79 | 0.81 | 0.56 | 0.79 | 0.78 | 0.80 | 0.80 | **0.84** |
| | Overlap | 0.79 | 0.83 | 0.79 | 0.81 | 0.79 | 0.83 | 0.80 | **0.84** |
| | Non-overlap | 0.79 | 0.80 | 0.44 | 0.78 | 0.78 | 0.78 | 0.79 | **0.84** |
| **Aggregated** | All | 0.73 | 0.76 | 0.52 | 0.73 | 0.72 | 0.74 | 0.75 | **0.79** |
| | Overlap | 0.71 | 0.75 | 0.71 | 0.73 | 0.71 | **0.76** | 0.73 | **0.76** |
| | Non-overlap | 0.74 | 0.77 | 0.41 | 0.73 | 0.72 | 0.73 | 0.75 | **0.80** |
| **Eval-out** | All | 0.61 | 0.65 | 0.43 | 0.61 | 0.59 | 0.63 | 0.64 | **0.68** |
| | Overlap | 0.56 | 0.58 | 0.55 | 0.56 | 0.55 | **0.60** | 0.58 | 0.59 |
| | Non-overlap | 0.64 | 0.69 | 0.37 | 0.63 | 0.61 | 0.65 | 0.68 | **0.73** |

Three observations the prose does not emphasise:

1. **On overlapping contexts at eval-out, DMA\*-SH is not the best arm** — DMA-Pearl
   is (0.60 vs 0.59), and domain randomisation (0.55) is within striking distance of
   everything. The method's advantage is entirely concentrated in the
   non-overlapping regime.
2. **The DMA\* → DMA\*-SH step is the operator step**, holding the inferred code
   fixed: 0.64 → 0.68 all, 0.68 → 0.73 non-overlap, 0.58 → 0.59 overlap. So
   swapping concatenation for a generated adapter buys ≈ 5 points where it matters
   and ≈ 1 point where it does not.
3. **Amago is a serious baseline and the paper says so.** A recurrent in-context
   agent with no dynamics grounding "performs competitively, especially in the
   training and eval-in regime, in most environments including non-overlapping
   settings such as DI" — with the disclosure that it "uses a substantially higher
   parameter count." On the two hardest DMC tasks it *wins*: Reacher(H) 853 vs 805,
   WalkerGym 3924 vs 3258 (Table 2). The paper's advantage is at extrapolation, not
   uniformly.

#### Per-environment highlights (Table 2, aggregated over splits)

Largest DMA\*-SH wins: **Cartpole** 967 [954, 978] vs. Concat 863 and DA 892;
**Reacher(H)-Perm** 840 [800, 873] vs. Concat 712 and DA 749; **Reacher(H)** 805 vs.
683/713. Losses: **BallInCup** 890 vs. Concat 924; **WalkerGym** 3258 vs. Amago 3924;
**HopperGym** 2563 vs. DMA-Pearl 2646; **Cheetah** 408 vs. Amago 414. The paper
notes explicitly that "In Walker, simple domain randomization suffices, suggesting
that explicit or inferred context can sometimes hinder performance."

### P3.6 Phase 2 — the theory, worked through

#### P3.6.1 Why concatenation cannot express a sign flip (Theorem A.1)

The setup: `H_concat` is the class of functions `f : R^{d_s} × R^{d_z} → R`
realised by finite ReLU MLPs on the concatenated input `[s; z]`. `H_hyper` is the
class

$$f(s,z) = w^{\top}\!\left(x(s) + g_{\text{adapter}}\!\left(x(s);\ \omega = h_\eta(z)\right)\right) + b,$$

with `x` a finite ReLU trunk, `h_η` a finite ReLU network with linear output, and
`g_adapter(·; ω) : x ↦ W(ω)x` linear in `x` for each `ω`. **Claim:**
`H_hyper ⊄ H_concat`.

**Proof, in full.** Take the witness `f*(s,z) = s·z` with `d_s = d_z = 1`.

*Membership in `H_hyper`.* Set `n = 2` and

$$x(s) = \big[\mathrm{ReLU}(s),\ \mathrm{ReLU}(-s)\big]^{\top}, \qquad h_\eta(z) = \big[z-1,\ -(z+1)\big]^{\top}, \qquad W(\omega) = \mathrm{diag}(\omega),$$

with `w = [1,1]^T`, `b = 0`. The trunk is a valid ReLU network; `h_η` is affine in
`z` hence realisable with a linear output layer. With the skip connection,

$$\tilde x = x + W(\omega)x = \big[(1+\omega_1)x_1,\ (1+\omega_2)x_2\big]^{\top}.$$

Substituting `ω₁ = z − 1` and `ω₂ = −(z+1)` gives `1 + ω₁ = z` and
`1 + ω₂ = −z`, so

$$\tilde x = \big[z\,\mathrm{ReLU}(s),\ -z\,\mathrm{ReLU}(-s)\big]^{\top},$$

and therefore

$$f(s,z) = w^{\top}\tilde x = z\,\mathrm{ReLU}(s) - z\,\mathrm{ReLU}(-s) = z\big(\mathrm{ReLU}(s) - \mathrm{ReLU}(-s)\big) = z\cdot s,$$

using the identity `ReLU(s) − ReLU(−s) = s`.

*Non-membership in `H_concat`.* Every finite ReLU MLP realises a **continuous
piecewise-linear** function, which is affine on each cell of a polyhedral partition,
so its Hessian vanishes almost everywhere. But

$$\frac{\partial^2 f^{\star}}{\partial s\, \partial z} = \frac{\partial^2 (sz)}{\partial s\, \partial z} = 1 \neq 0 \quad \text{everywhere.}$$

No CPWL function can equal `sz` on a domain with non-empty interior. ∎

**What this does and does not prove.** It is an *exact-representation* separation,
not an approximation separation: a ReLU MLP can approximate `sz` arbitrarily well
with enough linear regions. The paper is explicit about this (Remark A.6): the
concatenation network "can approximate mode-switching behavior via CPWL
partitioning… However, this indirect representation is more sensitive to encoder
noise (small perturbations in `z` near a decision boundary cause large policy
changes) and less parameter-efficient." **The noise-sensitivity argument is the one
that actually bears on the empirics**, and it is the one that has practical teeth
for this project: when the conditioning signal is *inferred and therefore noisy*,
an architecture that implements mode switching as a learned decision boundary in
`z`-space will flip modes on small inference errors, while one that implements it as
a smooth multiplicative map degrades gracefully. That argument is stated but not
directly measured.

Theorem A.2 generalises to arbitrary operator families: if the hypernetwork/adapter
can realise `W(h_η(z)) = T(z) − I_n`, then `f_T(s,z) = w^T T(z) x(s) + b ∈ H_hyper`.
For actuator inversion with `c ∈ {±1}`, `T(c) ∈ {I_n, −I_n}` and hence
`W ∈ {0_{n×n}, −2 I_n}` — a two-valued map on a two-point domain, trivially
realisable. Theorem A.5 extends the separation to the **bottleneck** adapter
actually used (`k ≥ 2`), which matters because the bottleneck is a rank constraint
and could in principle have destroyed the construction; it does not.

#### P3.6.2 The variance story (Theorems A.15, A.17, Proposition A.18)

Three diagnostics are defined on the learned embeddings, for each split
`M ∈ {train, eval-in, eval-out}`:

- **Informativeness** `I(z_t; c)` — mutual information between embedding and true
  context, estimated with the Kraskov k-NN estimator (`k = 3`, `L₂`).
- **Variability** `Variability(M) = (1/d_z)·tr(Cov(Z))` — the dataset-level spread of
  embeddings.
- **Representation-Overlap (RO)** — average pairwise cosine similarity between
  per-context mean embeddings.

**Theorem A.15** decomposes Variability, for a context `C = (S, U)` with `S` binary
(the inversion mode) and `U` continuous, into three additive parts: **within-context
noise** + **within-mode spread** along the continuous dimensions + **between-mode
separation** induced by the sign flip. **Theorem A.17** bounds policy-gradient
variance in terms of Variability — lower Variability, tighter bound.

Empirically (Figure 3), Variability falls monotonically along
`DMA → DMA* → DMA*-SH`, and RO rises. But so does something awkward: **DMA\*-SH has
*lower* `I(z_t; c)` yet better returns.** The paper names this the
**Informativeness–Variability paradox** and resolves it with **Proposition A.18**:
within-mode compression reduces policy-gradient variance *even as total information
about the context decreases*. Framed through an approximate **structural information
bottleneck** (Definition A.20, Appendix A.3.4): keep the information that identifies
the *mode*, discard the information that merely locates you within a mode.

The direct evidence is Figure 4, the cosine-similarity matrices on DI over six
contexts `(inversion ∈ {±1}) × (mass ∈ {0.8, 1.0, 1.3})`:

| Method | Within-mode similarity (same inversion, different mass) | Cross-mode similarity (opposite inversion) |
|---|---|---|
| **DMA** | 0.84 – 0.98 | **−0.97 to −0.40** (strongly anti-aligned, but mass-dependent) |
| **DMA\*** | 0.75 – 0.95 | 0.01 – 0.03 (near-orthogonal) |
| **DMA\*-SH** | **1.00** across the board | **0.14 – 0.23** |

DMA\*-SH collapses the three mass values to *identical* directions within a mode
while keeping the two modes clearly separated. The authors note the apparent
oddity — "Mass clusters overlap more for DMA\*-SH, yet returns are higher" — and
give the right reading: mass has *largely overlapping policy effects*, so
information about it is nuisance for control and discarding it is a gain.

**A project-relevant reading, and a caution.** The useful lesson is that a
conditioning code should be evaluated by *whether it separates the things that
require different behaviour*, not by how much it knows about the underlying
parameters — a high-mutual-information context code can be a worse code. The caution
is that the theory here is a chain of "consistent with" links: Theorem A.15 is a
statistical identity, Theorem A.17 is a bound (not a tightness result), and the
empirical correlation between low Variability and high return is across four
environments. The paper is careful in its own wording ("correlates with", "consistent
with", "suggesting"); a citation should preserve that hedging.

### P3.7 Phase 1 — Foundational overview

**Problem.** An agent should cope zero-shot with worlds it has not trained on, where
what differs is *how actions affect the world*. The hard case is when that difference
is **discontinuous** — a control that reverses, two control channels that swap.
There is no sensible average between the two behaviours, so any method whose
inductive bias is smoothness will blur them together and be mediocre at both.

**Three design decisions.**
1. *Where does the context come from?* Not from a label — from watching. An LSTM
   reads the last few (state, action, state-change) triples and compresses them to
   eight numbers.
2. *What trains that code?* Only a next-state-change prediction task. Reward is not
   allowed to touch it.
3. *How does the code reach the agent?* Not by being appended to the input. A small
   network converts it into the weights of a bottleneck module that is spliced into
   the policy, the value function, **and** the dynamics model — the *same* weights
   in all three.

**Plus stabilisers that turn out to be load-bearing.** Random masking of 40 % of the
encoder's inputs (because a hypernetwork amplifies small changes in its input into
large changes in the weights it emits); a scale-free per-sample input normalisation;
and an output normalisation that projects the eight numbers onto two four-way
probability simplices, bounding their scale and encouraging sparsity.

**Findings.**
- Against domain randomisation, +58 % on held-out contexts overall and +97 % on the
  discontinuous ones.
- Against the standard "paste the context onto the observation" baseline (which is
  *given* the true context, an advantage), +11.5 % overall and +14 % on
  discontinuous contexts.
- Against the Decision Adapter (§P1) — the same weight-generating operator, but with
  the true context given and separate generators for policy and value — +4.6 %
  overall, +5.8 % on discontinuous contexts, while using +4 % parameters, training
  43 % faster, and using 24 % less memory.
- On *smooth* context variation, everything ties and domain randomisation is fine.
- **Sharing one generator across the three modules beats giving each its own.**
- **Letting reward gradients into the shared generator collapses training to
  near-zero return.**

**Initial takeaway.** Two claims worth carrying forward. First, the useful thing to
ask of a conditioning code is not "how much does it know" but "does it separate the
situations that need different behaviour, and collapse the ones that don't" — this
paper measures a code with *less* information about the context that produces
*better* control. Second, a modulator that several parts of the agent share must be
trained by something other than reward; here, blocking the reward gradient is not a
refinement but a prerequisite.

### P3.8 What the paper does **not** establish

1. **Venue.** See §P3.0. Preprint as far as the PDF is concerned.
2. **Dynamics prediction is not compared against other self-supervised objectives** —
   only against reward-driven adaptation and against no grounding. See §P3.4.
3. **The collapse under non-detachment is only measured in the shared
   configuration.** Whether reward gradients are equally destructive to a *private*
   modulator is not isolated (DMA\*-H allows exactly that and merely underperforms).
4. **The shadow gradient is a diagnostic along a non-existent pathway**, and its
   correlation with returns is shown, not causally established.
5. **No noise-robustness experiment on the inferred code.** The Remark A.6 argument
   that concatenation is more brittle to encoder noise near a decision boundary is
   the mechanistic heart of the paper's case, and it is never measured. Beukman's
   App. G.1 is the closest thing in the batch — and it points the *other* way for
   heavy noise (see §P3.9).
6. **Reward-varying contexts are out of scope** and named as a limitation:
   "Multiplicative modulation is natural for discontinuous action-effect shifts, but
   may be less effective when context modifies rewards."
7. **Model error propagates.** Named limitation: "model errors can propagate into the
   representation and impair adaptation under misspecification or rapidly shifting
   dynamics."
8. **Hypernetwork capacity is unresolved** — "too little limits expressiveness, while
   too much can overfit and reduce stability" — with no sweep over hypernetwork size
   (only over masking ratio, normalisation type and window size).
9. **Baselines get an advantage the method does not, and this is not neutral.**
   Concat and DA receive the **ground-truth context**; DMA\*-SH must infer it. That
   makes the +11.5 % and +4.6 % *stronger* than they look. But it also means the
   comparison is not architecture-controlled — DA-with-inferred-context and
   Concat-with-inferred-context (i.e. DMA and DMA\*) are separate arms, so the
   cleanest architecture-only comparison in the paper is **DMA\* vs. DMA\*-SH**
   (concatenation vs. generated adapter, inferred code held fixed): 0.75 → 0.79
   aggregated, 0.68 → 0.73 non-overlap eval-out.

### P3.9 Relevance to this project

- **This is the batch's only inferred-context paper, and the folder's first.** Every
  other conditioning study in the corpus hands the modulator a clean, given signal.
  A project modulator reading an *interoceptive* signal computed by the agent's own
  machinery is in the inferred regime, and this paper is the closest available
  precedent.
- **The architecture question is answered conditionally, and the condition is
  legible.** Where different contexts require *compatible* behaviours ("overlapping"
  in this paper's terms), the mechanism barely matters — 1–7 % spreads, and plain
  domain randomisation is competitive. Where they require *incompatible* behaviours,
  the mechanism is decisive. Before running an architecture comparison, a project
  should first establish which regime its environment is in; the paper gives a
  formal criterion (Definition A.8: normalised worst-case regret of the best
  memoryless context-unaware policy) and an operational one (does a context-unaware
  agent already do fine?).
- **The single most transferable design rule:** if one modulator serves several
  consumers, do not train it on reward. Here that is not a tuning preference — the
  non-detached variant collapses.
- **A caution for the project's own instincts about noisy conditioners.** This paper
  argues (Remark A.6) that generated-weight modulation degrades more gracefully than
  concatenation under a noisy inferred code, but never measures it. Beukman *does*
  measure it (§P1.5.1) and finds the opposite at high noise: trained under σ = 0.5
  context noise, the Concat model becomes *more* robust while the adapter gets worse
  with large seed variance. **These two papers make opposite predictions about the
  same question and only one of them ran the experiment.** Anyone citing "hypernets
  are robust to noisy context" should cite Beukman's actual measurement, not
  Benad's argument.
- **Metric hygiene worth copying.** 10 seeds, three disjoint context sets, IQM with
  bootstrap CIs, probability-of-improvement for ablations, and per-environment tables
  in the appendix. Also the diagnostic triple (Informativeness / Variability /
  Representation-Overlap) — a project that learns a conditioning code could compute
  all three cheaply, and the cosine-similarity matrix over context pairs (Figure 4)
  is a particularly readable one-figure summary of whether a code is separating the
  right things.
- **The stabiliser list is a checklist.** Input masking at 40 %, scale-free input
  normalisation, simplex output normalisation, no activation before the adapter,
  residual skip, bottleneck 32 on trunk 256. Ablations show each contributes.
- **Handoff note.** Implementing an inferred-context modulator in this project would
  be a substantial change touching the encoder, the auxiliary loss, and the
  actor/critic architecture. That is an `experiment-designer` / `senior-developer`
  scoping question, not a literature one.

### P3.10 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Zero-shot generalisation in contextual RL, especially when context is **latent and must be inferred**. Canonical failure: latent context discontinuously changes how actions affect the environment, requiring incompatible control responses. Proposes **DMA\*-SH** — a single hypernetwork, trained **solely via dynamics prediction**, generating a small set of adapter weights **shared across the dynamics model, policy, and action-value function**; input/output normalisation and random input masking stabilise context inference. Contributes expressivity-separation theory and a variance decomposition with policy-gradient variance bounds. Introduces the **Actuator Inversion Benchmark (AIB)**. Headline: on held-out tasks, beats domain randomisation by 58.1 % and a standard context-aware baseline by 11.5 %. |
| 1 | **Introduction** | The reversed-trackpad anecdote as a minimal instance of **actuator inversion**; the same problem appears in swapped control channels, coordinate remappings, gain changes, sim-to-real actuator mismatch. "There may be no valid interpolation between incompatible control laws; an 'averaged' behavior can be incoherent." Smooth inductive biases — context concatenation, Gaussian latent structure — blur modes; domain randomisation compromises across regimes. The required primitive is **multiplicative context-dependent modulation of network parameters**. Four contributions: AIB, the DMA\*-SH architecture, theory, and empirics (+58.1 % over DR, +11.5 % over Concat, +4.6 % over DA). |
| 2 | **Background** | CMDP `(C, S, A, {P^c}, {r^c}, γ)`; context fixed within an episode; **dynamics-only variation**, `r^c = r ∀c`, following Beukman, Benjamins, Prasanna, Röder. Three context sets for zero-shot evaluation: `C_train`, `C_eval-in` (interpolation), `C_eval-out` (extrapolation), pairwise disjoint; no gradient updates at evaluation. |
| 3 | **Related Work** | Prior work either assumes observable context or infers it from interaction history; this paper does the latter, learning context representations by **self-supervised alignment with a dynamics model**. Recurrent agents can acquire latent context but their representations "are typically not grounded in environment dynamics." Positions against **Beukman et al. 2023**: they condition hypernetworks on *explicitly provided* context; here a **single dynamics-aligned hypernetwork shared across policy and value** with inferred context. |
| 4 | **Context Encoding and Utilization** | **4.1 DMA / DMA\*** — sliding window `τ^c_t` of `K` past `(s_t, a_t, δs_{t+1})` triples → encoder `g_φ` → `z_t ∈ R^{d_z}`, trained jointly with a forward-dynamics model by `L = ‖δŝ_{t+1} − δs_{t+1}‖²₂` (Eq. 1). Two additions define DMA\*: **random input masking** (independent per timestep, zeroing state/action/state-difference vectors; used purely as input corruption, not as a masked-prediction objective; "reduces reliance on brittle feature co-adaptations") and **input/output normalisation** — AvgL1Norm `x / (Σ|x_i|/N)` per sample after a linear layer (statistic-free, unlike BatchNorm, so suited to small-batch online RL), then an LSTM whose final hidden state is projected to `z_t ∈ R^8` and normalised by **SimNorm** into `L = 2` simplices of dimension `V = 4` via group-wise softmax (bounds scale, promotes sparsity, prevents representation collapse). **4.2 DMA\*-SH** — hypernetwork `h_η(z_t) → ω` generates adapter weights used by the dynamics model; `φ, θ, η` are trained jointly by the reconstruction loss (Eq. 2); the **same `ω` is reused** by policy and Q-function; `ω` is **detached** in the actor and critic losses so RL gradients never modify `η` or reshape `z_t` through this pathway. "This constraint acts as a structural prior… separates mode identification from mode-conditioned control." **4.3 Expressive advantage** — in vanilla DMA context enters additively through the input channel and any context-dependent feature transformation must be synthesised implicitly; DMA\*-SH inserts one bottleneck adapter with a residual skip after the trunk and before the output head of each network, `x̃_t = x_t + g_adapter(x_t; ω)` (Eq. 3), producing terms `W(z_t)x_t` that are explicitly multiplicative. Theorems A.1, A.2, A.5 formalise the separation from concatenation-based ReLU policies. |
| 5 | **The Actuator Inversion Benchmark (AIB)** | Diagnostic suite for discontinuous context-to-dynamics interactions: actuator **inversion** (`c ∈ {±1}` flips action effects), actuator **permutation** (`q ∈ {0,1}` swaps action dimensions), and **weakly non-overlapping** continuous systems (ODE / ODE-*k*, where the required action direction changes across regions of continuous context space), plus standard physical-parameter variations. Every environment has two context dimensions (except ODE-*k*) and is classified **Overlapping** (a single context-unaware policy can do well) or **Non-overlapping** (every memoryless context-unaware policy incurs nontrivial regret somewhere). Table 1 lists 14 environments from custom, DMC and Gymnasium sources. Distinguished from CARL (continuous/categorical variation only) and Meta-World (varies goals and tasks, not action effects). |
| 6 | **Results** | **6.1 Metrics** — 20 contexts per set, 10 rollouts per context, AER per set, IQM with empirical CIs after min–max scaling, **10 seeds**. **6.2 Baselines** — Concat and DA (context-aware, given ground truth); DR and Amago-2/GRU (context-unaware); DMA and DMA-Pearl (context-inferred); SAC everywhere except Amago, untuned CleanRL hyperparameters, trained in parallel over the 20 training contexts. **6.3 Zero-shot generalisation** — DMA\* and DMA\*-SH generalise strongly, especially out-of-distribution; DMA\*-SH beats Concat and DA in all three regimes (Fig. 2, Table 2). Honest caveats: in Walker domain randomisation suffices; Amago is competitive despite no dynamics grounding, with a much larger parameter count; DMA-Pearl is strong on overlapping contexts but its smooth KL prior makes it uncompetitive on non-overlapping ones. **6.4 Embedding diagnostics** — Informativeness `I(z_t;c)` (Kraskov k-NN), Variability `tr(Cov(Z))/d_z`, Representation-Overlap (mean pairwise cosine similarity of per-context means). Variability falls along DMA → DMA\* → DMA\*-SH; RO rises; DMA\*-SH has **lower** Informativeness yet better returns, resolved by Proposition A.18 (within-mode compression lowers policy-gradient variance even as total information falls) and interpreted as an approximate structural information bottleneck. Figure 4's cosine matrices on DI: DMA\*-SH gives within-mode similarity 1.00 across masses while keeping modes separated at 0.14–0.23. **6.5 Implicit gradient regularisation** — the shadow-gradient diagnostic `E‖∇_z L_π‖`, computed by temporarily removing the stop-gradient and never applied; DMA\*-SH sustains non-negligible shadow norms while DMA\*-H's are substantially smaller, co-occurring with faster learning and higher returns. |
| 7 | **Conclusions + Limitations** | Restates AIB, DMA\*-SH, the expressivity separation, the geometry findings, and the variance chain. "Notably, these effects emerge without auxiliary objectives" — i.e. no explicit contrastive or bottleneck loss. **Limitations:** dynamics-model errors propagate into the representation under misspecification or rapid shifts; multiplicative modulation may be less effective when context modifies **rewards** or induces non-factorisable policy changes; hypernetwork capacity is a practical bottleneck at both ends. **Future work:** ensembles / Bayesian hypernetworks for model uncertainty; dual hypernetworks or multi-view encoders for reward-modifying contexts; explicit compression/separation objectives; real-robot deployment with actuator degradation and swapped channels. |
| A | **Theory and supplementary analyses** | **A.1** — concatenation ReLU MLPs are CPWL with almost-everywhere-vanishing Hessian, so cannot represent bilinear coupling exactly; **Theorem A.1** proves `H_hyper ⊄ H_concat` with witness `f*(s,z) = sz`; **Theorem A.2** generalises to operator families `W(h_η(z)) = T(z) − I_n`, covering sign inversion (`T ∈ {I, −I}`), permutation and gain modulation; **Corollary A.3** gives a continuous affine-operator separation; **Remark A.4** specifies the SAC implementation (trunk 256, bottleneck 32, `g_adapter(x;ω) = W_up(ω)·ReLU(W_down(ω)x)`, skip connection, no trunk activation, shared `η` across actor, critic and dynamics); **Theorem A.5** extends the separation to the bottleneck adapter with `k ≥ 2`; **Remark A.6** applies it to actuator inversion and argues concatenation's CPWL work-around is more **noise-sensitive** near decision boundaries and less parameter-efficient; **Remark A.7** gives the overhead numbers (vs. DA: +4.1 % parameters, 43.5 % faster, 24.4 % less peak memory; vs. DMA: +9.5 % parameters, 79.2 % slower, +21.7 % memory; adapter cost `O(dk)` vs `O(d²)`). **A.2** — Definition A.8 formalises overlapping vs. non-overlapping by normalised worst-case regret; Definition A.10 defines actuator inversion; sub-parts analyse the context-aware, context-unaware (Remark A.12: context-unaware policies as epistemic-POMDP solvers) and context-inferred cases; Remark A.13 explains why variational latent priors impose a continuity bias mismatched to sign flips. **A.3** — Definition A.14 (Variability), **Theorem A.15** (decomposition into within-context noise, within-mode spread, between-mode separation), **Theorem A.17** (policy-gradient variance bound controlled by Variability), **Proposition A.18** (the Informativeness–Variability paradox), A.3.4 the structural-information-bottleneck view (Definition A.20), A.3.5 regime shifts on `C_eval-out`. **A.4** — scale control and directional geometry; Definition A.21 (Representation-Overlap); t-SNE and cosine analyses. **A.5** — the two update streams written out; the shared pathway `τ → z → ω → {f, π, Q}`; DMA\*-H's separate pathways and the objective-mismatch argument; the shadow-gradient definition in η-space and z-space. **A.6** — comparison to history-based recurrent and Transformer agents. |
| B–E | **Extended related work; Algorithms; Hyperparameters; AIB details** | **C** gives Algorithms 1–2. **D** gives the full hyperparameter table (SAC untuned from CleanRL; context encoder LR 3e-4, model dim 32, context dim 8, `K` = 24 or 128, window fraction 0.2, LSTM, AvgL1Norm in, SimNorm out, masking 0.2 for DMA\* and 0.4 for DMA\*-SH; dynamics model 256×256; hypernetwork 64×64; adapter bottleneck 32, skip on, **no pre-adapter activation**, ReLU post-adapter) and notes the hypernetwork framework of von Oswald et al. and that "the design choices regarding the hypernetworks and adapters match those in DA [Beukman et al., 2023]", with DA reimplemented and verified against the original. **E** describes each AIB environment, the overlap classification rationale, context supports and return bounds (Table 5), and contrasts AIB with CARL and Meta-World. |
| F | **Ablations and Design Rationale** | Rationales: **masking** — "Hypernetworks can amplify small perturbations in `z_t` into large changes in `ω`"; masking encourages a redundant distributed code; 40 % best for DMA\*-SH, 20 % for DMA\*, robust across a wide range (Fig. 11). **AvgL1Norm** best among LayerNorm / AvgL1Norm / SimNorm / WindowNorm for the input (Fig. 12). **SimNorm** best among LayerNorm / AvgL1Norm / SimNorm for the output; output normalisation "is critical for stable online training" (Fig. 13). **Window size** `K = 24` (DI/ODE) and `128` (DMC/Gym), impact modest above a minimum (Fig. 14). **Figure 10** gives probability-of-improvement for every combination of dropping masking, input norm and output norm. **Figure 15 — the architecture ablation**: DMA\*-SH vs. DMA-SH (no norm/mask), DMA\*-H (separate hypernetworks), **DMA\*-H (RL only)** (hypernetwork on the RL modules but **not** the dynamics model, so RL adapters are not dynamics-aligned; close to R2PGO in an online setting), and the three non-detached variants. Verbatim: "Allowing actor gradients to propagate directly through the shared hypernetwork leads to near-zero returns… This shows that letting RL rewrite the shared `ω` is harmful, and that gradient detachment is necessary." Conclusion: "normalization, masking, hypernetwork sharing, and dynamics-model alignment are all beneficial." Also: Amago's GRU encoder beats its Transformer (Fig. 16); PEARL vs. DMA-Pearl and the β sweep (Fig. 17); VariBAD tested at two β and excluded because it "struggles considerably with the non-overlapping contextualizations in DI and ODE" (Fig. 18). |
| G | **Detailed Results** | **G.1** — per-split AER tables (Tables 6–8 for `C_train`, `C_eval-in`, `C_eval-out`) and **Table 9**, the relative-gain table reproduced in §P3.5. Learning curves for six environments per split; 100 k–500 k gradient steps, `n_c = 20` contexts, i.e. 2 M–10 M total environment steps. **G.2** — context-instance generalisation analysis. **G.3** — scalability in the explicit context dimension. |

---
