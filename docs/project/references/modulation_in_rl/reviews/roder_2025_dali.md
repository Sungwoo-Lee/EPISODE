---
title: "Dynamics-Aligned Latent Imagination in Contextual World Models (DALI)"
slug: roder_2025_dali
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_modern.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## P4. Röder, Benad, Eppe & Banerjee 2025 — *Dynamics-Aligned Latent Imagination in Contextual World Models for Zero-Shot Generalization* (**DALI**)

**PDF:** `docs/project/references/modulation_in_rl/sources/Roeder et al. 2025 - DALI - Dynamics-aligned latent imagination in contextual world models.pdf`
**Code:** https://github.com/frankroeder/DALI (stated in §6)

### P4.0 Note on operator class — set expectations before reading

The folder acquired this paper because it is the **first precedent for conditioning
inside a world model's latent dynamics**, which is genuinely new territory here. It
delivers on that. But it should be catalogued accurately on the operator axis:

> **DALI conditions by concatenation.** The learned 8-dimensional context code is
> appended as an extra input to whichever modules are conditioned. There is **no
> FiLM, no gain-and-offset, no adapter, no hypernetwork, no weight generation
> anywhere in this paper.**

So DALI is not a data point in the concat-vs-FiLM-vs-hypernet comparison that §P1
and §P2 supply. Its contributions are on two other axes the project cares about:
**where** the conditioning signal is injected (the RSSM's recurrent state, the
predictors, the decoder, the actor, the critic — enumerated exactly, which is rare),
and **what trains the conditioning signal** (a self-supervised forward-dynamics
objective plus a cross-modal alignment term, with reward gradients structurally
excluded). It shares its last two authors with §P3 and is the direct predecessor of
that work — §P3's Related Work cites DALI as prior art, and §P3 is essentially
"DALI's conditioning signal, but delivered through a shared hypernetwork instead of
by concatenation." Reading them as a pair is the right way to use them.

### P4.1 Plain-English entry point

A **world model** is an agent's learned simulator: it compresses what it sees into a
small internal state, predicts how that state will evolve, and lets the agent
practise entirely inside its own imagination rather than in the real environment.
The Dreamer family is the standard version of this idea.

The problem: a Dreamer agent trained across many worlds — different gravities,
different string lengths, different motor strengths — has to squeeze all of that
into one recurrent memory. That memory is simultaneously tracking *where the ball is
right now* and *what kind of world this is*, and these compete for the same limited
capacity. Working out "this world has high gravity" from scratch can take most of an
episode.

DALI's fix is a division of labour. A **separate small encoder** watches the last
few dozen (observation, action) pairs and produces an 8-number summary of *what kind
of world this is*. It is trained on one job only: predict the next observation. It
never sees reward. Its output is then handed to the world model, freeing the
recurrent memory to concentrate on moment-to-moment dynamics.

Two ways of handing it over are defined, and the difference is precisely the thing
the project asked about:

- **Shallow** — the code goes into the world model's **observation encoder only**.
  The policy and value function never see it directly; it reaches them only because
  it has already coloured the latent state they read.
- **Deep** — the code goes into the world model's **recurrent transition function**,
  its reward predictor, its continue predictor, its decoder, **and** explicitly into
  the actor and the critic.

Results, on DeepMind Control tasks where gravity, string length or motor strength
are pushed outside the training range: Shallow integration beats a Dreamer agent
that just trains on randomised worlds by **+4 % to +96 %**, and — the striking part
— often beats agents that are **handed the true gravity and friction values**, by up
to +64 %. The authors' reading is that the ground-truth numbers invite overfitting
to the training range, while an inferred code that has to explain observed dynamics
generalises further.

Finally, the paper shows the code is not an arbitrary embedding: **nudging one
particular dimension of it makes the imagined ball swing faster and hang higher** —
exactly what higher gravity and a shorter string would do. That is a mechanistic
check on the representation that the rest of this batch does not attempt.

### P4.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | **NeurIPS 2025**, printed verbatim at the foot of p. 1: *"39th Conference on Neural Information Processing Systems (NeurIPS 2025)."* PDF also carries `arXiv:2508.29294v3 [cs.LG] 15 Jan 2026`. Authors: Röder\*, Benad, Eppe, Banerjee\* (\*equal contribution), TU Hamburg. Acknowledgements thank "the anonymous reviewers" and DFG project MoReSpace (402776968). |
| **Conditioning signal** | **INFERRED from interaction history.** `z^ctx_t = g_φ(o_{t−K:t}, a_{t−K:t−1})` — a window of past observations **and actions** (note: not state *differences*, unlike §P3), encoded by a **transformer block** into `z^ctx_t ∈ R^8`. Trained by a forward-dynamics loss plus an optional cross-modal alignment loss (§P4.4). Ground-truth context is **never given to DALI**; it *is* given to the cRSSM-S/D baselines. |
| **What is modulated** | **Depends on the integration strategy, and this is enumerated exactly (Appendix A.1) — see §P4.3.** Shallow: the world model's **posterior encoder only**. Deep: the RSSM **sequence model**, the **reward predictor**, the **continue predictor**, the **decoder**, **and** the actor and critic. |
| **The operator** | **Concatenation.** `z^ctx_t` is appended as an additional conditioning argument to the relevant distributions/functions. No affine modulation, no generated weights. |
| **Capacity-spectrum position** | **Rung 0** on the operator axis. The paper's novelty is on the *signal* and *placement* axes, not the operator axis. |
| **RL algorithm** | **DreamerV3 (small variant)**, model-based, actor-critic in latent imagination, hyperparameters from Hafner et al. 2025 following Prasanna et al. 2024's setup for comparability with their cRSSM baselines. |
| **Benchmark** | **CARL-contextualised DeepMind Control**: **Ball-in-Cup** (context = gravity, string length; 200 k steps) and **Walker Walk** (context = gravity, actuator strength; 500 k steps), each in **Featurized** and **Pixel** modality. Plus **Quadruped Walk** (56-D observations, 12-D actions; 600 k steps) as a scaling check in the appendix. Three generalisation regimes: Interpolation (within training range), Extrapolation (out of distribution), Mixed (one dimension OOD, one within). |
| **Seeds and statistics** | **10 seeds.** IQM and probability-of-improvement from `rliable`, with stratified bootstrap 95 % CIs over seeds and aggregated contexts. Total experimental cost 600 training runs, ≈ 24 000 A100-GPU-hours sequential (Table 2). |
| **Ablation present?** | **Partially — see §P4.6.** Two conditioning-depth arms (Shallow vs. Deep) and two loss arms (forward-dynamics only vs. + cross-modal), which is a 2×2 design in principle. But the main results report **Shallow only**, and the Shallow/Deep contrast changes world-model *and* policy conditioning simultaneously, so **world-model conditioning is not ablated independently of policy conditioning**. |
| **Reported instability** | **Named but not measured.** The Discussion lists "training instability, sensitivity to hyperparameters, and the risk of overfitting in high-dimensional observation spaces" as practical challenges beyond the theory's scope. No instability curves, no divergence report, no seed-failure analysis. One design element is *described* as an implicit stabiliser: the bidirectional cross-modal constraint "prevent[s] degenerate solutions (e.g., `z^ctx_t` collapsing to a constant) by enforcing invertibility." |
| **Cost** | **≈ +4 % parameters**: Dreamer-DR 15.73 M vs. DALI-S 16.45 M. (Compare §P3's Remark A.7: DMA\*-SH is +9.5 % over its no-hypernetwork baseline.) |
| **Single- or multi-task** | cMDP with **dynamics-only variation**, reward fixed across contexts, context latent and fixed within an episode. Partially observable: the agent observes neither the state nor the context. |

### P4.3 The injection point in the RSSM, written out exactly

This is the part of the paper the project should read most carefully, because
Appendix A.1 enumerates every conditioned distribution for all five arms. Reproduced
in full, with the paper's own notation.

**Notation warning.** The paper overloads the symbol `z_t` for two different objects:
the **context representation** produced by the context encoder, and the **stochastic
latent state** of the RSSM. Below they are disambiguated as `z^ctx_t` (context,
8-dimensional) and `z^rssm_t` (RSSM stochastic state, 32-dimensional per the
cross-modal projection shapes). The paper's own `L_cross` equation is genuinely hard
to read because of this.

#### Baseline — DreamerV3 with domain randomisation

$$
\begin{aligned}
\text{Sequence model:}&\quad h_t = f_\theta(h_{t-1},\, z^{rssm}_{t-1},\, a_{t-1})\\
\text{Encoder (posterior):}&\quad z^{rssm}_t \sim q_\theta(z^{rssm}_t \mid h_t, o_t)\\
\text{Dynamics predictor (prior):}&\quad \hat z_t \sim p_\theta(\hat z_t \mid h_t)\\
\text{Reward predictor:}&\quad \hat r_t \sim p_\theta(\hat r_t \mid h_t, z^{rssm}_t)\\
\text{Continue predictor:}&\quad \hat n_t \sim p_\theta(\hat n_t \mid h_t, z^{rssm}_t)\\
\text{Decoder:}&\quad \hat o_t \sim p_\theta(\hat o_t \mid h_t, z^{rssm}_t)
\end{aligned}
$$

Actor `a_τ ∼ π_ϕ(a_τ | s_τ)`, critic `v_ψ(s_t)`, where `s_t = {h_t, z^rssm_t}`.

#### DALI-S — Shallow Integration

**Exactly one change to the world model:**

$$z^{rssm}_t \sim q_\theta\!\left(z^{rssm}_t \mid h_t,\, o_t,\, \boxed{z^{ctx}_t}\right)$$

Everything else is byte-identical to the baseline — sequence model, prior, reward
predictor, continue predictor, decoder. **Actor and critic are unchanged**:
`a_τ ∼ π_ϕ(a_τ | s_τ)`, `v_ψ(s_t)`. The context reaches the policy **only**
because it has already shaped `z^rssm_t`, which is half of `s_t`, and because `h_t`
absorbs `z^rssm_{t-1}` through recurrence.

#### DALI-D — Deep Integration

**Five changes:**

$$
\begin{aligned}
\text{Sequence model:}&\quad h_t = f_\theta\!\left(h_{t-1}, z^{rssm}_{t-1}, a_{t-1},\, \boxed{z^{ctx}_t}\right)\\
\text{Encoder:}&\quad z^{rssm}_t \sim q_\theta(z^{rssm}_t \mid h_t, o_t) \quad \text{(unchanged — accesses } z^{ctx} \text{ only through } h_t)\\
\text{Dynamics predictor:}&\quad \hat z_t \sim p_\theta(\hat z_t \mid h_t) \quad \text{(unchanged — same indirect access)}\\
\text{Reward predictor:}&\quad \hat r_t \sim p_\theta\!\left(\hat r_t \mid h_t, z^{rssm}_t,\, \boxed{z^{ctx}_t}\right)\\
\text{Continue predictor:}&\quad \hat n_t \sim p_\theta\!\left(\hat n_t \mid h_t, z^{rssm}_t,\, \boxed{z^{ctx}_t}\right)\\
\text{Decoder:}&\quad \hat o_t \sim p_\theta\!\left(\hat o_t \mid h_t, z^{rssm}_t,\, \boxed{z^{ctx}_t}\right)
\end{aligned}
$$

**and the policy is conditioned explicitly:**

$$a_\tau \sim \pi_\phi\!\left(a_\tau \mid s_\tau,\, \boxed{z^{ctx}_t}\right), \qquad v_\psi\!\left(s_t,\, \boxed{z^{ctx}_t}\right) \approx \mathbb{E}_{\pi(\cdot \mid s_\tau, z^{ctx}_t)}\!\left[\sum_{\tau=t}^{t+H} \gamma^{\tau - t} r_\tau\right].$$

**Note the asymmetry that matters most.** In Deep Integration the context enters the
**transition function** — it changes how the imagined state evolves. In Shallow it
does not: the transition function never sees it, and the only route into imagination
is via whatever `z^rssm` carried into `h`. For a project interested in "modulation
inside a world model's latent dynamics", **Deep Integration is the arm that actually
does that**, and Shallow is a much weaker form of it.

#### The ground-truth-context baselines, for comparison

**cRSSM-S** (called "concat-context" in Prasanna et al.): `z^rssm_t ∼ q_θ(z^rssm_t |
h_t, o_t, c)` — the same single injection point as DALI-S but with the true context
`c` instead of the inferred code. **cRSSM-D** (called "cRSSM"): `h_t = f_θ(h_{t-1},
z^rssm_{t-1}, a_{t-1}, c)`, plus `c` into reward, continue and decoder, plus
`π_ϕ(a_τ|s_τ, c)` and `v_ψ(s_t, c)`. So the baseline pair is **exactly** DALI-S/D
with `z^ctx` replaced by ground-truth `c` — a genuinely clean
inferred-vs-given comparison at matched architecture. That is a nice piece of
experimental design and worth noting.

#### Gradient routing (§4.3, "Training") — the reward-exclusion rule again

Both strategies unroll the world model over the `K`-length window, initialising
`h_{t−K} = 0` or a learned initial state, and generating `z^ctx_τ` for
`τ = t−K … t`. The gradient rules:

- Gradients through `h_τ` and `z^rssm_τ` are **stopped in the recurrent dynamics**,
  and through `h_τ` in the world model's encoder — "preventing updates to `θ`."
- **Shallow:** `z^ctx_τ` gradients are preserved in the world model's encoder *and*
  in `L_FD` and `L_cross`, "allowing updates to `φ`, `W_z`, and `W_z̄`."
- **Deep:** `z^ctx_τ` gradients are **stopped in the recurrent dynamics** and
  preserved only in `L_FD` and `L_cross`.

Appendix Remark 4 makes the isolation explicit: "The world model parameters (`θ`)
are frozen during context learning (inputs to `f_θ` and `q_θ` are detached), so
gradient stopping isolates `φ`."

**The context encoder is therefore never trained by reward, and (in Deep) never
trained by the world model's own objective either.** This is the same structural
choice §P3 later makes with a stop-gradient on the hypernetwork output, and §P3's
ablation is the one that shows *why* it matters (letting actor gradients in gives
near-zero returns). DALI adopts the rule; DMA\*-SH tests it. Reading the pair
together is what makes the rule credible.

### P4.4 The two training objectives

#### Forward-dynamics alignment (Eq. 1)

$$\mathcal{L}_{FD}(\phi) = \mathbb{E}\left\| o_{t+1} - f^{w}_{\phi}\!\left(o_t, a_t, z^{ctx}_t\right) \right\|_2^2,$$

where `f^w_φ` is a two-layer, 128-unit, SiLU MLP predicting the next **observation**
(not the state difference — a small but real difference from §P3, which predicts
`δs_{t+1}`). `g_φ` and `f^w_φ` are trained jointly. The logic: `z^ctx_t` is
*useful* to the extent that supplying it improves next-observation prediction, so it
must carry whatever about the world governs how actions turn into consequences.

#### Cross-modal regularisation (Eq. 2)

$$\mathcal{L}_{\text{cross}}(\phi) = \mathbb{E}\left\| z^{ctx}_t - W_z\, z^{rssm}_t \right\|_2^2 \;+\; \mathbb{E}\left\| z^{rssm}_t - W_{\bar z}\, z^{ctx}_t \right\|_2^2,$$

with `W_z ∈ R^{8×32}` and `W_z̄ ∈ R^{32×8}` learnable linear maps. Three design
notes, all of which the project should register:

1. **It aligns to `z^rssm_t`, not to the full latent state `s_t = {h_t, z^rssm_t}`.**
   Stated reason: "By aligning with `z^rssm_t` instead of the full latent state
   `s_t`, `z^ctx_t` avoids encoding redundant trajectory-specific information from
   the deterministic `h_t`, which could impair generalization." That is a
   deliberate choice to align with the *observation-informed, instantaneous* part of
   the state and not the *history-accumulating* part.
2. **It is bidirectional on purpose.** "The bidirectional constraints prevent
   degenerate solutions (e.g., `z^ctx_t` collapsing to a constant) by enforcing
   invertibility." A one-way alignment could be satisfied by a constant; requiring
   both directions cannot.
3. **Total loss:** `L_total(φ) = L_FD(φ) + λ_cross · L_cross(φ)` with
   **`λ_cross ∈ {0, 1}`** — i.e. it is a *binary switch*, not a tuned weight. The
   "-χ" suffix in method names means `λ_cross = 1`.

### P4.5 Every head-to-head comparison, with numbers

Five arms:

| Arm | Context | Where it enters |
|---|---|---|
| **Dreamer-DR** | none (domain randomisation) | — |
| **cRSSM-S** | **ground truth `c`** | posterior encoder only |
| **cRSSM-D** | **ground truth `c`** | sequence model, reward, continue, decoder, actor, critic |
| **DALI-S / DALI-S-χ** | **inferred `z^ctx`** | posterior encoder only (χ = with cross-modal loss) |
| **DALI-D / DALI-D-χ** | **inferred `z^ctx`** | sequence model, reward, continue, decoder, actor, critic |

All results are IQM of min–max normalised score, 10 seeds, bootstrap CIs.

#### Ball-in-Cup (gravity + string length; 200 k steps)

| Regime / modality | Dreamer-DR | cRSSM-S (given `c`) | cRSSM-D (given `c`) | **DALI-S-χ (inferred)** |
|---|---|---|---|---|
| Interpolation, Featurized | 0.92–0.95 band | 0.92–0.95 band | 0.92–0.95 band | 0.9490 |
| Interpolation, Pixel | 0.92–0.95 band | 0.92–0.95 band | 0.92–0.95 band | 0.9440 |
| **Extrapolation, Featurized** | (−87.9 % rel.) | 0.2270 | 0.2780 | **0.3720** |
| **Extrapolation, Pixel** | (−96.4 % rel.) | 0.1870 | 0.2420 | **0.2730** |
| Mixed, Featurized | (−51.1 % rel.) | (−20.3 % rel.) | (−1.9 % rel.) | **0.6830** |
| Mixed, Pixel | — | — | **0.6250** | 0.6030 |

Relative gains as printed: Extrapolation Featurized **+87.9 % over Dreamer-DR,
+63.9 % over cRSSM-S, +33.8 % over cRSSM-D**; Extrapolation Pixel **+96.4 %,
+45.9 %, +12.8 %**.

**Two things worth pulling out.** First, **interpolation is a tie** — every arm lands
in the 0.92–0.95 band, including the context-unaware one. The entire effect is at
extrapolation. That is the *third* independent instance of this batch's recurring
shape: architecture and conditioning barely matter in the benign regime and matter a
great deal in the stressed one (cf. §P1's distractors, §P3's overlap/non-overlap
split). Second, **the inferred code beats the ground-truth code**, and the authors'
explanation is worth quoting: "This suggests ground-truth context may overfit,
limiting OOD adaptability." That is a genuinely counter-intuitive result and the most
interesting single finding in the paper.

Sanity caveat the authors supply themselves: the absolute extrapolation IQMs
(0.14–0.37) "reflect the extreme OOD context ranges, such as gravity values of 0.98
or 19.6, far from the training range of [4.9, 14.7]." All arms are performing poorly;
DALI is performing least poorly. A 96 % relative gain over a score of 0.14 is a
smaller absolute effect than the percentage suggests.

#### Walker Walk (gravity + actuator strength; 500 k steps)

| Regime / modality | Winner | DALI-S | DALI-S-χ | cRSSM-S | cRSSM-D |
|---|---|---|---|---|---|
| Interpolation, Featurized | **DALI-S 0.9710** | 0.9710 | — | — | — |
| **Extrapolation, Featurized** | **DALI-S 0.7810** | 0.7810 | 0.7770 | 0.7020 | 0.7490 |
| **Extrapolation, Pixel** | **cRSSM-S 0.7770** | 0.7580 | 0.7330 | **0.7770** | — |
| Mixed, Featurized | **cRSSM-D 0.8720** | +1.1–1.8 % over Dreamer-DR | | | **0.8720** |
| Mixed, Pixel | **cRSSM-S 0.8610** | +1.1–5.5 % over Dreamer-DR | | | |

Walker Featurized Extrapolation gains: **+4.0 % over Dreamer-DR, +11.3 % over
cRSSM-S, +4.3 % over cRSSM-D**. The paper explains the much smaller margins honestly:
"Higher IQM scores (0.7–0.78) across methods reflect less extreme OOD actuator
strength ([0.1, 2.0] vs. [0.5, 1.5]), reducing generalization demands."

**In three of the eight Walker/Ball-in-Cup cells the ground-truth-context baselines
win**, all of them in the Pixel modality or the Mixed regime. The paper reports these
losses plainly.

#### The cross-modal loss is task-dependent, in both directions

- **Ball-in-Cup:** DALI-S-χ > DALI-S "across all regimes and modalities." Stated
  reason: aligning with the world model's posterior "enhances context inference for
  nonlinear dynamics" — pendulum dynamics where gravity and string length interact
  nonlinearly.
- **Walker:** DALI-S > DALI-S-χ "across most regimes and modalities." Stated reason:
  the forward-dynamics loss alone suffices "for contexts where actuator strength
  linearly scales joint torques", and in Pixel "visual noise may amplify `L_cross`'s
  complexity."
- Authors' conclusion: "This underscores the need for **task-specific
  regularization**."

**This is an honest and useful negative-ish result.** The regulariser that helps most
on the nonlinear task hurts on the near-linear one, and the split is by dynamics
type, not by benchmark difficulty. A project adding an auxiliary alignment term
should not assume it transfers.

#### Quadruped Walk (Appendix C.5) — the only place Deep Integration is scored

56-D observations, 12-D actions, 600 k steps, gravity + actuator strength, Featurized
Extrapolation IQM:

| Arm | Context | IQM |
|---|---|---|
| Dreamer-DR | none | 0.220 ± 0.023 |
| cRSSM-D | ground truth | 0.258 ± 0.028 |
| cRSSM-S | ground truth | 0.317 ± 0.031 |
| **DALI-S** | inferred, shallow | 0.326 ± 0.043 |
| **DALI-D-χ** | inferred, **deep** | **0.389 ± 0.027** |

Reported as "up to **+76.8 %** improvement over the context-unaware baseline and up
to **+50.8 %** over the context-aware baselines."

**This is the single most project-relevant number in the paper**, and it is buried in
an appendix: on the largest environment tested, **Deep Integration beats Shallow by
19 % relative (0.389 vs 0.326)** — reversing the paper's own main-text finding that
Shallow is preferable. The authors do not comment on the reversal. Read together
with §6.2's "Shallow Context Propagation as Regularization" argument, the natural
hypothesis is that Shallow's advantage is a *regularisation* effect that matters
when the context code is noisy and the task is small, and that the extra
conditioning of Deep pays off once the task is large enough to need it. **That
hypothesis is not tested.**

### P4.6 Ask — is the world-model conditioning ablated separately from the policy conditioning?

**Short answer: no, not cleanly, and the paper's main results do not report Deep
Integration at all.** Precisely:

| Configuration | World model conditioned? | Policy / critic conditioned? | Reported where |
|---|---|---|---|
| Dreamer-DR | no | no | main results |
| **DALI-S** | **yes — posterior encoder only** | **no (only implicitly, via `s_t`)** | main results |
| **DALI-D** | **yes — transition function + all predictors + decoder** | **yes, explicitly** | learning curves (Fig. 4) and Quadruped only |
| cRSSM-S | yes, posterior encoder only, **ground truth** | no | main results |
| cRSSM-D | yes, deep, **ground truth** | yes, **ground truth** | main results |

So:

- **A world-model-only conditioning arm exists** — DALI-S is exactly that, and it is
  the paper's headline method. That is a real and useful data point: *conditioning
  only the world model's observation encoder, with the policy receiving nothing
  explicit, is sufficient for large OOD gains.*
- **A policy-only conditioning arm does not exist.** There is no variant where the
  actor and critic read `z^ctx` while the world model does not. So the paper cannot
  say whether the gains come from better imagination or from a better-conditioned
  policy.
- **Shallow vs. Deep changes both factors simultaneously** — depth of world-model
  conditioning *and* presence of explicit policy conditioning move together. The
  contrast is therefore confounded with respect to the project's question.
- **The main experiments report Shallow only.** §6.2: "Shallow Integration… consistently
  performs well, leading to its **exclusive use in the results reported here**."
  Deep appears only in the appendix learning curves and the Quadruped experiment,
  where it wins.

**What the paper does argue about the difference**, in the "Shallow Context
Propagation as Regularization" paragraph: Shallow "allow[s] context information to
propagate indirectly to the recurrent state `h_t = f_θ(h_{t−1}, z^rssm_{t−1},
a_{t−1})` through recurrence. This design regularizes the world model, potentially
mitigating overfitting to noisy `z^ctx_t` estimates, which can be particularly
beneficial in OOD settings." Hedged throughout ("potentially", "suggests"), and
listed in the Outlook as future work: "Future work could investigate the
regularization effects of Shallow Integration, explore hybrid strategies
interpolating between Shallow and Deep."

**For the project's records: DALI establishes that a world model can be conditioned
on an inferred code and that this helps at extrapolation. It does not establish
where inside the world model the conditioning should go, nor whether the policy needs
it at all.** The one piece of evidence on that question (Quadruped) points toward
Deep and is a single environment.

### P4.7 Phase 2 — the theory

The theoretical claim is **information-theoretic, about the context encoder, not
about the policy**. Assumptions: continuous context `c ∈ R^d` drawn i.i.d. per
episode with finite differential entropy `h(c)`; noisy observations
`o_t = s_t + η_t`, `η_t ∼ N(0, σ²I)`; **Lipschitz-continuous dynamics** (small
context changes give smoothly varying behaviour); and a **β-mixing**
observation-action process (distant observations become nearly independent, at rate
`λ`).

**Theorem 1 (informal, main text).** In a cMDP with β-mixing and Lipschitz dynamics,
DALI's context encoder captures near-optimal context information

$$I\!\left(c;\, z^{ctx}_t\right) \ \ge\ (1-\delta)\, h(c), \qquad \delta \in (0,1),$$

using `N = O(1/δ²)` windows of `K = Ω(log(1/δ)/λ)` transitions. Moreover DALI's
recurrent state retains more context information than DreamerV3's,

$$I\!\left(c;\, h^{DALI}_t\right) \ \ge\ I\!\left(c;\, h^{RSSM}_t\right) - \epsilon(K), \qquad \epsilon(K) = O\!\left(e^{-\lambda K/2}\right),$$

and against DreamerV3 processing full episodes of `T ≫ K` transitions, DALI achieves
a **sample-complexity gain of `O(T/K)`**.

**The argument, in words.** DreamerV3's `h^RSSM_t` is a fixed-size GRU state that
must compress *everything* about the episode — context, dynamic state, and
observation noise. Those compete for capacity, so "essential cues about the
underlying context (e.g., gravity) may be lost or delayed," and identifying `c` may
require accumulating evidence across an entire episode of length `T` because early
actions may not excite the dynamics enough to reveal contextual differences. DALI
**decouples context inference from dynamics modelling**: a specialised module learns
`z^ctx_t` from short local histories, freeing `h^DALI_t` to focus on dynamics.
β-mixing is what makes `K ≪ T` sufficient — the dependence on distant past decays at
rate `λ`, so `K = Ω(log(1/δ)/λ)` transitions carry almost all the recoverable
context information.

**The worked numerical illustration the paper gives:** at `δ = 0.01` with a typical
DMC mixing rate `λ ≈ 0.1`, a window of `K ≈ 64` steps yields a conditional-entropy
error bounded by roughly `δ' ≈ 0.1`. DALI needs `N = O(1/δ²)` such windows, total
`O(K/δ²)` transitions; DreamerV3 needs `O(T/δ²)` with `T = 1000`. Hence the `O(T/K)`
ratio.

**Remark 4** notes the sample-complexity result carries from Deep to Shallow because
"the context encoder `z^ctx_t` is trained identically on `K`-length windows in both
configurations", and that `L_cross` "does not affect sample complexity, as it
operates on the same `K`-length windows." **Theorem 5** proves the sequence model's
information-bottleneck reduction.

**What the theory does *not* claim, stated by the authors.** From the Limitations:
"As an information-theoretic result, it does not address the downstream impact of
`z^ctx_t` on policy performance, which depends on joint optimization of the context
encoder, world model, and actor-critic components." Also: reliance on an exploratory
policy "may falter in sparse-reward or high-dimensional settings, producing noisy
estimates"; and β-mixing "may not hold in environments with slow-mixing dynamics,
such as highly correlated trajectories or restricted exploration."

**Project reading.** The β-mixing assumption is the load-bearing one and it is
falsifiable per-environment: it says the informative signal about "what world is
this" is recoverable from a short window. In an environment where the relevant
distinction only manifests after a long, specific sequence of actions — or where the
agent's own policy avoids the states that would reveal it — the whole
`O(T/K)` argument fails, and the paper says so.

### P4.8 The counterfactual-consistency analysis (§6.3, Appendix D) — a method worth copying

The paper's third contribution is a **mechanistic check on the learned code**, and
it is methodologically the most transferable thing in the paper.

**Protocol.** With `z^ctx ∈ R^8` and a frozen world model and policy:
1. Sample a fixed observation `o_t` from a test episode; infer
   `z = g_φ(o_{t−K:t}, a_{t−K:t−1})` with `K = 50`.
2. For each dimension `j = 1 … 8`, form the perturbed code
   `z' = z + Δ · e_j`, where `Δ = σ(z_j)` is the standard deviation of that
   dimension across the dataset — i.e. a **one-standard-deviation nudge in one
   coordinate**.
3. Roll out `H = 50` steps in imagination under both `z` and `z'`, decoding the
   predicted observation sequences: baseline `T^(0)` and counterfactual `T'^(j)`.
4. Repeat `N = 2500` times per dimension, giving 5000 trajectories per dimension.
5. **Train a binary classifier to tell perturbed from unperturbed trajectories.**
   An ensemble (SVM + MLP + AdaBoost), stratified 5-fold cross-validation, AUC
   aggregated across folds, 95 % bootstrap CIs over 500 resamples, and permutation
   tests (1000 iterations) for significance between top-ranked dimensions.
6. Rank the eight dimensions by AUC; take the top one for physical analysis.

**Result — Ball-in-Cup, dimension `z₆`.** Rolling out with **zero actions** to expose
passive dynamics only:

- *Pixel:* the counterfactual ball "hovers higher than the original in frame 40,
  indicating a shorter string," and "overtakes the original in frame 15 and 45,
  demonstrating faster swing cycles due to increased gravitational pull."
- *Featurized:* reduced oscillation amplitude (lower peak Z-position) and a velocity
  profile that "peaks earlier and higher."
- Interpretation: `z₆` encodes a **coupled** gravity–string-length factor — shorter
  string raises oscillation frequency, higher gravity amplifies acceleration, and
  both move together under a single-coordinate perturbation. Both effects are
  Newtonian-consistent.

**Result — Walker Walk, dimension `z₃`** (Appendix D.2). Here the original policy
actions are *retained* rather than zeroed, to see how the factor affects control.
Both the original and perturbed agents fall in frames 0–20; the perturbed one then
"exhibits enhanced actuator strength, enabling the Walker to stand from a challenging
pose… and locomote forward (frames 50–64)", while "the original trajectory fails to
recover, collapsing after the fall." Featurized: sustained torso elevation after
timestep 20 in the counterfactual only.

**Why the project should note this.** It is a genuine test of whether a learned
conditioning code is *mechanistically* aligned rather than merely predictive, and it
requires nothing but a frozen model and a classifier. The AUC-ranking step is what
makes it rigorous — rather than eyeballing a dimension, it identifies which
dimensions produce *statistically distinguishable* imagined dynamics, with
confidence intervals and permutation tests. Any project that learns a low-dimensional
conditioning code inside a world model could run exactly this.

**Its limits.** It shows a perturbation produces physically plausible change; it does
**not** show the code is disentangled (`z₆` conflates gravity and string length, as
the authors say), nor that the mapping from code to physics is monotone or
calibrated, nor that any *other* dimension is meaningless. And it is qualitative at
the physics level — no quantitative comparison against the true simulator under the
corresponding parameter change.

### P4.9 Phase 1 — Foundational overview

**The setting.** An agent that learns a simulator of its world and practises inside
it (DreamerV3). The world varies between episodes — different gravity, different
string length, different motor strength — and the agent is never told which.

**The bottleneck being attacked.** DreamerV3's memory is a single recurrent state
that has to hold everything: where things are now, what kind of world this is, and
the noise in between. The paper's argument is that these compete, so the "what kind
of world" information gets lost or arrives late.

**The fix.** A dedicated 8-number summary produced by a small transformer that reads
only the last few dozen observation-action pairs, and that is trained on exactly one
job — predict the next observation — with reward gradients structurally excluded.
Optionally, a second term ties this summary to the world model's own instantaneous
latent state, in both directions, which stops it collapsing to a constant.

**Two ways to deliver it, and the paper only fully tests one.** *Shallow* puts the
summary into the world model's observation encoder and nowhere else — the policy
never sees it directly. *Deep* puts it into the transition function, all the
predictors, the decoder, and explicitly into the policy and value function. The main
results use Shallow throughout.

**Findings.**
- Within the training range, everything ties, including the agent that just trains on
  randomised worlds.
- Outside it, the gains are large: +88 % (state inputs) to +96 % (pixel inputs) over
  the randomisation baseline on the swing-the-ball-into-a-cup task; +4 % on the
  easier walking task, where the out-of-range conditions are much milder.
- **The inferred summary often beats being handed the true gravity and string
  length** — by up to +64 %. The authors read this as the true numbers inviting
  overfitting to the training range.
- The optional alignment term helps on the nonlinear pendulum task and hurts on the
  near-linear walking task — so it is task-specific, not a free improvement.
- On the largest environment tested (a 56-dimensional quadruped, appendix only),
  **Deep beats Shallow**, reversing the main-text preference.
- Nudging one dimension of the summary by one standard deviation makes the imagined
  ball swing faster and hang higher, exactly as more gravity and a shorter string
  would. A trained classifier confirms the effect is statistically real, not
  eyeballed.

**Initial takeaway.** Giving a world model an explicitly-inferred description of
"what kind of world this is" — kept separate from its moment-to-moment state, and
trained on prediction rather than reward — helps most exactly where it is hardest, at
conditions outside the training range, and can beat being told the truth. What
remains open is *where* inside the world model that description should be delivered.

### P4.10 What the paper does **not** establish

1. **No operator comparison.** Concatenation only. No FiLM, adapter or hypernetwork
   arm anywhere. DALI cannot be cited on the operator question.
2. **World-model and policy conditioning are not separately ablated** (§P4.6); and
   the main results use Shallow only, so the Deep arm — the one that actually
   conditions the latent *dynamics* — is scored in exactly one appendix experiment.
3. **The Quadruped reversal is unexplained.** Deep wins there and loses (or is
   simply unreported) elsewhere; the paper does not address the inconsistency.
4. **Two environments in the main results**, both DeepMind Control, both with
   two continuous context dimensions of the same physical kind. No discrete or
   discontinuous contexts (that gap is what §P3's benchmark exists to fill).
5. **`λ_cross ∈ {0,1}` is a switch, not a sweep** — the strength of the alignment
   term is never tuned, so "cross-modal helps here and hurts there" may partly be a
   weighting artefact.
6. **No instability measurement.** Training instability and hyperparameter
   sensitivity are named in the Discussion and never quantified.
7. **The theory is about the encoder, not the agent** — explicitly disclaimed: it
   "does not address the downstream impact of `z^ctx_t` on policy performance."
8. **β-mixing and Lipschitz dynamics are assumptions**, acknowledged as possibly
   failing under slow mixing, high trajectory correlation, or restricted
   exploration.
9. **Window size `K` is not swept.** `K = 50` is stated for the counterfactual
   analysis; there is no `K` sensitivity study of the kind §P3 runs (its Fig. 14).
10. **Relative gains sit on small absolute numbers** at extrapolation (IQM
    0.14–0.37). The percentages are correct and the authors flag the reason, but they
    should not be read as "the agent solved the OOD task."

### P4.11 Relevance to this project

- **This is the folder's first precedent for conditioning inside a world model, and
  Appendix A.1 is the reusable artefact.** It enumerates, for five arms, exactly
  which RSSM components receive the conditioning signal. If the project ever
  conditions a Dreamer-style model, that table is the design menu — and the
  cRSSM-S/D pair shows what the "given ground truth" control arm looks like at
  matched architecture.
- **The strongest transferable design principle is the separation of concerns:**
  keep the slow "what kind of situation is this" signal in a *separate* module,
  computed from a short window, trained on prediction, and structurally forbidden
  from receiving reward gradients — so that the fast recurrent state is not
  simultaneously responsible for both. §P3 then shows what happens when that rule is
  violated (collapse). The two papers together make the rule, not either alone.
- **"Inferred beats given" is the result most worth carrying, and also the one most
  worth being careful about.** It is measured on two environments with strong OOD
  ranges, at a single architecture family, with a stated mechanism (ground-truth
  context overfits the training range) that is asserted rather than demonstrated. It
  is suggestive rather than established. Note also that §P3, by the same group,
  reports the *same* qualitative finding against the same baseline family — which is
  corroboration, but from a partially overlapping author set.
- **Interpolation is a tie. Again.** All four papers in this batch find that
  conditioning architecture is nearly irrelevant in the benign regime and decisive
  in the stressed one. If the project runs a conditioning comparison, it must
  construct the stressed regime deliberately — irrelevant/shifting context
  dimensions (§P1), discontinuous action effects (§P3), or out-of-range parameters
  (§P4) — because an in-distribution comparison will report a null and the null will
  be uninformative.
- **Copy the counterfactual protocol.** Perturb one code dimension by one standard
  deviation, roll out imagination, train a classifier to detect the perturbation,
  rank dimensions by AUC with bootstrap CIs and permutation tests, then inspect the
  top one. It is cheap, it needs only a frozen model, and it is the only method in
  this batch that asks whether a learned conditioning signal means anything
  mechanistically rather than merely correlating with performance.
- **The auxiliary-loss warning.** The cross-modal term helps on nonlinear dynamics
  and hurts on near-linear dynamics, in the same paper, at the same weight. An
  auxiliary alignment objective is a task-specific bet.
- **Handoff note.** Conditioning a Dreamer-style world model in this project touches
  the RSSM, the predictors, the actor-critic, and the loss — and the project's
  Dreamer stack has its own status constraints. That scoping belongs to
  `senior-developer` / `experiment-designer`, not to this review.

### P4.12 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Real-world RL needs adaptation without retraining; cMDPs model this but existing methods often require **explicit** context variables, limiting use when context is latent. Introduces **DALI**, integrated within the Dreamer architecture, inferring latent context from agent-environment interactions via a **self-supervised encoder trained to predict forward dynamics**, whose representations condition **the world model and policy**. Claims theoretical proof that the encoder is essential; **counterfactual consistency** (perturbing a gravity-encoding dimension alters imagined rollouts physically plausibly); significant gains over context-unaware baselines and frequent superiority over context-aware ones in extrapolation. |
| 1 | **Introduction** | Legged-robot-on-tiles/gravel/ice motivation; ground-truth friction coefficients are "often unavailable or prohibitively expensive to obtain", so the agent must infer variation "by observing how its actions influence the environment". DreamerV3 "struggles to generalize across diverse latent contexts due to its limited ability to retain critical environmental information" (citing Prasanna et al.). Three contributions: theoretical foundations (near-optimal sample complexity from short windows, information-bottleneck mitigation), zero-shot gains "up to +96.4 % over context-unaware baselines", and physically consistent counterfactuals. |
| 2 | **Related Work** | Contextual RL for zero-shot generalisation (cMDPs, domain randomisation, meta-RL; Kirk et al.'s survey on clear train/eval context sets). Splits prior work into context-as-privileged-information and context-must-be-inferred; DALI is the latter, "focusing on self-supervised context inference through forward dynamics alignment". Model-based RL: Dreamer family, TD-MPC. Meta-RL: most methods "require fine-tuning on new tasks", whereas DALI targets zero-shot. |
| 3 | **Preliminaries** | cMDP `(S, A, O, C, R, P, E, μ, p_C)` with observation function `E`, initial-state distribution `μ(s₀|c)`, and **partial observability** — the agent observes neither `s_t` nor `c`. Objective `E[Σ_t r_t]` for `π(a_t | o_{1:t}, a_{1:t−1})`. Context varies dynamics, reward fixed. Train and eval context distributions `p_train`, `p_eval`. |
| 4 | **DALI** | **4.1 DreamerV3 background** — RSSM latent `s_t = {h_t, z_t}` with deterministic recurrent `h_t = f_θ(h_{t−1}, z_{t−1}, a_{t−1})` and stochastic `z_t`; two modes, posterior inference during training and prior prediction during imagination; components: posterior encoder, prior, reward predictor, continue predictor, decoder; actor-critic optimised entirely in latent space. **4.2.1 Forward dynamics alignment** — `z^ctx_t = g_φ(o_{t−K:t}, a_{t−K:t−1})`, loss `L_FD = E‖o_{t+1} − f^w_φ(o_t, a_t, z^ctx_t)‖²`, `g_φ` and `f^w_φ` trained jointly. **4.2.2 Cross-modal regularisation** — bidirectional `L_cross = E‖z^ctx − W_z z^rssm‖² + E‖z^rssm − W_z̄ z^ctx‖²`; aligns to `z^rssm` rather than to full `s_t` to avoid "redundant trajectory-specific information from the deterministic `h_t`"; bidirectionality prevents collapse to a constant by enforcing invertibility; `L_total = L_FD + λ_cross L_cross`, `λ_cross ∈ {0,1}`. **4.3 Integration** — **Shallow** modifies only the posterior encoder `z^rssm_t ∼ q_θ(z^rssm_t | h_t, o_t, z^ctx_t)`, leaving sequence model, all predictors and actor-critic unchanged; **Deep** adds `z^ctx_t` to the sequence model, reward/continue/decoder predictors, and conditions actor and critic explicitly. **Training** — both unroll over a `K`-length window from `h_{t−K} = 0` or a learned init; gradients through `h_τ` and `z^rssm_τ` are stopped in the recurrent dynamics and through `h_τ` in the encoder, preventing updates to `θ`; Shallow preserves `z^ctx` gradients in the encoder and both losses, Deep only in the losses. |
| 5 | **Theoretical Insights** | Assumptions: continuous i.i.d. per-episode context, Gaussian observation noise, Lipschitz dynamics, β-mixing observation-action process, exploratory policy. Argument: domain-randomised DreamerV3's `h^RSSM_t` compresses context, state and noise into a fixed-size GRU — an information bottleneck — and may need a full episode of length `T` to disambiguate `c`. DALI decouples context inference from dynamics modelling. **Theorem 1**: `I(c; z^ctx_t) ≥ (1−δ)h(c)` with `N = O(1/δ²)` windows of `K = Ω(log(1/δ)/λ)`; `I(c; h^DALI_t) ≥ I(c; h^RSSM_t) − ε(K)` with `ε(K) = O(e^{−λK/2})`; sample-complexity gain `O(T/K)`. Numerical illustration at `δ = 0.01`, `λ ≈ 0.1`, `K ≈ 64`, `T = 1000`. |
| 6 | **Experiments and Analysis** | **6.1** — CARL-contextualised DMC Ball-in-Cup and Walker Walk; methods DALI-S/D with or without χ; baselines Dreamer-DR (context-unaware) and cRSSM-S/D (ground-truth context-aware, from Prasanna et al.); DreamerV3-small, **transformer** context encoder, 200 k (Ball-in-Cup) / 500 k (Walker) steps, **10 seeds**; two modalities (Featurized, Pixel); three regimes (Interpolation, Extrapolation, Mixed); context ranges tabulated (Ball-in-Cup gravity train [4.9, 14.7] eval [0.98, 4.9) ∪ (14.7, 19.6], string length train [0.15, 0.45] eval [0.03, 0.15) ∪ (0.45, 0.6]; Walker same gravity, actuator strength train [0.5, 1.5] eval [0.1, 0.5) ∪ (1.5, 2.0]); metrics IQM and PoI with stratified bootstrap CIs. **Results** as tabulated in §P4.5. **6.2** — modality-specific effects; cross-modal regularisation helps Ball-in-Cup's nonlinear pendulum dynamics and hurts Walker's near-linear torque scaling ("underscores the need for task-specific regularization"); Ball-in-Cup drops more from Featurized to Pixel, reflecting higher partial observability; comparison with context-aware baselines including the losses; **"Shallow Context Propagation as Regularization"** — Shallow used exclusively in the reported results, its indirect propagation through recurrence framed as regularisation against noisy `z^ctx` estimates. **6.3** — counterfactual protocol (`z ∈ R^8`, `K = 50`, one-σ single-coordinate perturbation, `H = 50` imagination, `N = 2500` pairs per dimension, binary classifier, AUC ranking with bootstrap CIs). **6.3.1** — Ball-in-Cup dimension `z₆` under zero-action rollouts: shorter string (ball hovers higher, frame 40) and higher gravity (counterfactual overtakes at frames 15 and 45); Featurized confirms via reduced Z-amplitude and earlier/higher velocity peak; `z₆` encodes a **coupled** gravity-string factor. |
| 7 | **Discussion and Outlook** | Restates the +4.0 % to +96.4 % range over Dreamer-DR and the +12.8 % to +63.9 % over ground-truth-context baselines in Ball-in-Cup. **Limitations:** the theory is information-theoretic and "does not address the downstream impact of `z^ctx_t` on policy performance"; reliance on an exploratory policy may falter in sparse-reward or high-dimensional settings; β-mixing may fail under slow-mixing or restricted-exploration dynamics; training instability, hyperparameter sensitivity and overfitting in high-dimensional observation spaces are "beyond its scope". **Outlook:** investigate Shallow Integration's regularisation effect, explore **hybrid strategies interpolating between Shallow and Deep**, and build theory connecting context inference to policy performance. |
| A | **Formal Results and Proofs** | **Theorem 2** (necessity and efficiency of the context encoder, stated for Deep Integration) and **Theorem 5** (sequence-model information-bottleneck reduction), with **Lemma 6** supplying the β-mixing bound `h(c | τ_{t−K:t}) ≤ C' e^{−λK} h(c)`. **Remark 4** extends the `O(T/K)` gain to Shallow, since the encoder is trained identically on `K`-windows and `L_cross` operates on the same windows; world-model parameters are frozen during context learning. **A.1** — the full component-by-component specification of Dreamer-DR, DALI-S, DALI-D, cRSSM-S and cRSSM-D world models (A.1.1) and actor-critic models (A.1.2), reproduced in §P4.3; notes that cRSSM-S/D correspond to "concat-context" and "cRSSM" in Prasanna et al. |
| B | **Algorithms** | Algorithms 1–2 (DALI-S with forward-dynamics loss, and DALI-S-χ with cross-modal regularisation) and 3–4 (the Deep Integration counterparts). |
| C | **Experimental Setup** | **C.1** — CARL defaults; **single context variation** (100 uniform values in one dimension's training range, other fixed at default) and **dual context variation** (100 pairs from the Cartesian product); the three regimes. **C.2** — environment descriptions and Table 1 of context ranges; Ball-in-Cup's gravity-string interaction "amplifies nonlinear effects", Walker's actuator strength has "predictable" torque effects and a milder OOD range. **C.3** — architecture: context encoder is a standard **transformer encoder block** (dense 256 → LayerNorm → single-head self-attention with skip → LayerNorm → 2-layer 256-unit MLP with residual → dense to `R^8`), SiLU throughout, **no attention masking**; forward model a 2-layer 128-unit SiLU MLP; `W_z ∈ R^{32×8}`, `W_z̄ ∈ R^{8×32}`; DreamerV3-small following Prasanna et al. **"DALI adds only about 4 % parameter overhead (e.g., Dreamer-DR: 15.73 M vs. DALI-S: 16.45 M)."** **C.4** — NVIDIA A100 80 GB, Intel Xeon Platinum 8352V; 600 runs (10 seeds × 5 variants × 2 environments × 2 modalities × 3 context settings); ≈ 24 000 GPU-hours sequential, ≈ 1 051 (4 GPUs) to 2 101 (2 GPUs) wall-clock GPU-hours. **C.5** — learning curves (Fig. 4, which does include the DALI-D and DALI-D-χ arms), and the **Quadruped Walk** scaling experiment (56-D observations, 12-D actions, 600 k steps): DALI-S 0.326 ± 0.043, **DALI-D-χ 0.389 ± 0.027**, Dreamer-DR 0.220 ± 0.023, cRSSM-D 0.258 ± 0.028, cRSSM-S 0.317 ± 0.031 — "up to 76.8 % improvement over the context-unaware baseline" and "up to 50.8 % improvement over the context-aware baselines". |
| D | **Supplementary Counterfactual Experiments** | **D.1** — the AUC-ranking machinery: ensemble classifier (SVM + MLP + AdaBoost), stratified 5-fold CV, 95 % bootstrap CIs from 500 resamples, permutation tests with 1000 iterations comparing top-ranked dimensions against a shuffled null; Figure 5 gives AUC ± CI for all eight Ball-in-Cup dimensions. **D.2** — Walker Walk, top-ranked dimension `z₃` in DALI-S, with the **original policy actions retained** (unlike Ball-in-Cup's zero-action rollouts): both agents fall in frames 0–20, but the perturbed trajectory recovers from a challenging pose (frames 30–45) and locomotes forward (frames 50–64) while the original "fails to recover, collapsing after the fall"; Featurized torso-height traces confirm sustained elevation after timestep 20. Conclusion: `z₃` encodes actuator-strength/torque dynamics critical for stability. |

---

## P5. Cross-paper notes for the merge

Not a paper section — four observations that only become visible with all four
reviews side by side, offered to whoever merges this into the master review.

### P5.1 The batch establishes a nesting chain, with a citable argument for each link

$$\text{concatenation} \ \subset\ \text{FiLM (affine)} \ \subset\ \text{generated low-rank adapter} \ \subset\ \text{generated full layer}$$

- **concat ⊂ FiLM** — Xiong §2.2.1/§6: concatenating a *time-invariant* context and
  passing through a linear layer is exactly an additive bias `β(c)` with the gain
  frozen at 1. Derivation written out in §P2.8.2, with the one-layer caveat.
- **FiLM ⊂ generated adapter** — Beukman Appendix C: constrain the adapter to a
  single linear layer, no bias, no nonlinearity, `W = diag(g(c))`, and it *is*
  cGate. Derivation in §P1.7.4.
- **generated adapter ⊄ concatenation** — Benad Theorems A.1 / A.5: a
  hypernetwork-conditioned adapter can represent `f(s,z) = sz` exactly, and no ReLU
  MLP on `[s;z]` can (its mixed partial is 1 everywhere; CPWL functions have
  vanishing Hessian a.e.). Proof in §P3.6.1.
- **generated adapter ⊂ generated full layer** — Xiong's HN generates whole `W^i_k`
  for the embedding and decoder layers, unconstrained by a bottleneck.

**Consequence for the folder's framing:** the concat baseline is not "no
modulation"; it is the weakest member of the modulation family. Comparisons should
be labelled accordingly.

### P5.2 All four papers report the same conditional shape

| Paper | Benign regime — architectures tie | Stressed regime — architectures separate |
|---|---|---|
| **Beukman** | CartPole with clean context: Adapter ≈ Concat ≈ cGate ≈ optimal | Add 20–100 irrelevant context dimensions whose values shift train→test: Concat and cGate collapse, Adapter does not |
| **Xiong** | (not tested — no benign arm) | Weight generation helps only in the two hardest environments; hurts in the one where value prediction is intrinsically hard |
| **Benad** | Overlapping contexts: +1.2–7 % over every baseline; domain randomisation competitive | Non-overlapping (sign-flip / permutation) contexts: +5.8 % over DA, +14 % over Concat, **+97 % over domain randomisation** |
| **Röder (DALI)** | Interpolation: every arm 0.92–0.95, including context-unaware | Extrapolation: +88–96 % over domain randomisation, and beats *ground-truth* context by up to +64 % |

**This is the batch's single most actionable finding for experiment design.** An
architecture comparison run in-distribution will report a null, and the null will
carry no information. The stressor has to be constructed deliberately, and the three
constructions available are: irrelevant/shifting conditioning dimensions (Beukman),
discontinuous context-to-behaviour maps (Benad), and out-of-range context values
(Röder).

### P5.3 "Start the conditioner at zero influence" is independently required by two different operators

- **Xiong** (weight generation): **Bias-HyperInit** — hypernetwork output weights
  set to 0, biases drawn from the modulated layer's own init distribution, so every
  node starts with identical weights and diversity grows from zero. Described as
  "critical to stabilize its training."
- **The folder's existing FiLM corpus** (affine): identity-init / AdaLN-Zero —
  `γ = 1, β = 0` at step 0, so the modulated block is the identity.
- **Beukman** reaches something similar structurally without naming it: with the
  residual skip, the diagonal case reads `x ← diag(1 + g(c))x`, a gate around 1.
- **Benad** does not use zero-init but achieves the analogous effect by a different
  route — the stop-gradient means the modulator's map is shaped only by dynamics
  prediction and can never be dragged by reward.

Two operator families, three papers, one principle. Worth recording as a cross-paper
finding rather than a per-paper detail.

### P5.4 One place the batch contradicts itself — flag on merge

**Question: is a weight-generating modulator more or less robust than concatenation
when its conditioning signal is noisy?**

- **Benad, Remark A.6 (argued, not measured):** concatenation implements mode
  switching as a learned decision boundary in `z`-space, so "small perturbations in
  `z` near a decision boundary cause large policy changes"; multiplicative modulation
  is smoother and should degrade more gracefully.
- **Beukman, Appendix G.1 (measured, 16 seeds):** at moderate evaluation noise the
  adapter *is* more robust than concat, as Benad predicts. But when *trained* under
  large context noise (σ = 0.5), **the ranking inverts** — "the Concat model becomes
  more robust to noisy contexts, but the Adapter performs worse", with large
  across-seed variance indicating some seeds fail outright.

The two papers are not in direct conflict (different noise regimes, different
training conditions), but a citation of the form "hypernetworks are robust to noisy
context" is supported only in the low-noise regime and is contradicted in the
high-noise one. **Cite Beukman's measurement, not Benad's argument.** And note the
project-relevant gap: nobody in this batch measures noise robustness for an
*inferred* code, which is the regime a project-side inferred conditioner would live
in.

### P5.5 Provenance note

Benad et al. 2026 (§P3) and Röder et al. 2025 (§P4) share two authors (Benad,
Banerjee) and an institution (TU Hamburg), and §P3 explicitly builds on §P4 — DALI is
cited in §P3's Related Work and appears as the `DMA` baseline family there. Their
agreeing finding that an *inferred* context can beat a *given* one is therefore
corroboration from a partially overlapping group, not from independent replication.
Beukman (§P1) and Xiong (§P2) are independent of both and of each other (though
Xiong shares an institution with Beukman's current affiliation, Oxford, and Jacob
Beck's Bias-HyperInit is cited by both Xiong and Benad).
