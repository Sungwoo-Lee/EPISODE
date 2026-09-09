---
title: "Dynamics Generalisation in RL via Adaptive Context-Aware Policies (Decision Adapter)"
slug: beukman_2023_decision_adapter
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_modern.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## P1. Beukman et al. 2023 — *Dynamics Generalisation in Reinforcement Learning via Adaptive Context-Aware Policies* (the **Decision Adapter**)

**PDF:** `docs/project/references/modulation_in_rl/sources/Beukman et al. 2023 - Dynamics generalisation in RL via adaptive context-aware policies (Decision Adapter).pdf`
**Code:** https://github.com/Michael-Beukman/DecisionAdapter (stated in footnote 1, p. 2)

### P1.0 Why this paper is the most decision-relevant in the acquisition

This is the controlled comparison the folder has argued about for a year and never
held direct evidence for. One RL algorithm (Soft Actor-Critic), one set of
environments, **parameter counts deliberately equalised across architectures**, 16
seeds, and five ways of getting the same context vector into the same policy:
ignore it, concatenate it, multiply by it (FiLM-style), generate a per-task linear
head from it, or generate the weights of a spliced-in adapter module from it.

And the paper's central empirical finding is a **conditional** one, which is why it
is worth reading carefully rather than citing as "hypernetworks win":

> With clean, fully relevant context, concatenation is a perfectly reasonable
> approach and all context-aware methods tie. The architectures separate only once
> the context contains dimensions that carry no information about the dynamics —
> and then concatenation and FiLM-style modulation both fail while weight
> generation does not.

The authors state this themselves (§7.2): *"This demonstrates that, given only
useful context, concatenating state and context is a reasonable approach in some
environments. However, this is a strong assumption in many practical cases where we
may be uncertain about which context variables are necessary. In such cases, the
consequences of ignoring the conceptual differences between state and context are
catastrophic."*

### P1.1 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | **NeurIPS 2023**, printed verbatim on p. 1: *"37th Conference on Neural Information Processing Systems (NeurIPS 2023)."* PDF also carries the arXiv stamp `arXiv:2310.16661v1 [cs.AI] 25 Oct 2023`. Authors: Beukman, Jarvis, Klein, James, Rosman (Wits / Oxford / UCL). |
| **Conditioning signal** | **Ground-truth context `c ∈ C`, GIVEN — not inferred from transitions.** This is a deliberate methodological choice, stated as such: the ground truth is used "to isolate the effect of the network architecture on generalisation performance" (App. G.1). Context = physical dynamics parameters: ODE polynomial coefficients `[c_0 … c_{n-1}]`; CartPole `(gravity, cart mass, pole mass, pole length, force magnitude)` — 5 dims, of which only pole length actually varies; Ant `mass`. Contexts are **normalised per-dimension by the largest value seen in training**, so the largest training context maps to 1.0 and extrapolation contexts exceed 1.0 (App. D.1.1). Inferring context is explicitly listed as future work (§8: *"integrating the Decision Adapter into existing context inference methods is a promising avenue"*). |
| **What is modulated** | **Both the SAC actor and the SAC critic.** The actor is a trunk (one hidden layer → 256-d features) plus a one-layer action head with two outputs (mean action, log σ). Default placement: adapter **before the action head's layer** in the actor, and **before the last layer** in the critic (location "C" in the paper's Fig. 14 diagram). Not an encoder, not a dynamics model — there is no model. |
| **The operator** | **Hypernetwork-generated bottleneck adapter with a residual skip.** Rung 2 on the capacity spectrum. Formally: an adapter `A_i : R^{d_i} → R^{d_i}` with parameter vector `θ^i_A ∈ R^{P_i}` is inserted between layers `L_{i-1}` and `L_i`; a context-conditioned hypernetwork `H_i : C → R^{P_i}` emits `θ^i_A = H_i(c)`, which is reshaped into weight matrices; the forward pass is `x_i ← x_i + A_i(x_i \| θ^i_A)`. The adapter is a **bottleneck**: 256 → 32 → 256 (down-project, up-project), i.e. `O(p·d_i)` parameters instead of `O(d_i^2)` — a deliberate low-rank inductive bias. The hypernetwork itself uses **chunking**, generating the parameter vector in pieces from a shared small network: the actor's hypernetwork holds ≈ 16 k learnable parameters vs ≈ 1.7 M for the non-chunked `[100,100]` alternative. |
| **Capacity-spectrum position** | **Rung 2 — low-rank adapter with fully generated weights.** The paper's Appendix C proves this **strictly contains** rung 1 (FiLM/cGate): set the adapter to a single linear layer with no bias and no nonlinearity, and force `W = H(c) = diag(g(c))`; then `A(φ(s)\|c) = diag(g(c))φ(s) = g(c) ⊙ φ(s) = cGate(s,c)`. The authors' framing: cGate "restricted the context features' effect on the state-based features to be linear"; the adapter "is general enough to be able to recover this elementwise product, but is not constrained to do so." |
| **RL algorithm** | **Soft Actor-Critic** throughout, CleanRL implementation, PyTorch, default hyperparameters (γ = 0.99, τ = 0.005, batch 256, buffer 1 M, policy LR 3e-4, critic LR 1e-3, automatic entropy tuning). Chosen explicitly "to isolate and fairly compare the network architectures." The method is stated to be algorithm-agnostic. |
| **Benchmarks** | Three, deliberately spanning a difficulty range: (1) **ODE** — a 1-D/2-D dynamical system `x_{t+1} = x_t + ẋ dt` with `ẋ = c_0 a + c_1 a² + …`, complex-valued 2-D action, 200-step episodes, shaped reward for `\|x\|` near 0, max return ≈ 200; (2) **CartPole** with continuous force action, 500-step cap, only pole length varied; (3) **MuJoCo Ant** — 111-d observation, 8-d torque action, 1000-step episodes, **mass** as context, train on {5, 35, 75}, evaluate on 200 evenly spaced masses in [0.5, 100]. |
| **Metric** | **Average Evaluation Reward (AER)**: `AER = 1/(c_max − c_min) ∫ R(c) dc` over the full evaluation context range, `n = 5` episodes per context. Includes training contexts by default; App. F.4 shows the test-only version is essentially identical because training contexts are a tiny fraction of the range. |
| **Seeds** | **16 seeds** for every reported curve; mean ± standard deviation shaded. This is unusually strong for the corpus. |
| **Ablation present?** | **Extensive.** Five architecture ablations (App. E: adapter architecture, hypernetwork chunking, skip connection, adapter location, pre-adapter activation), two extra baselines isolating the hypernetwork itself (App. F.3), and a full limitations battery (App. G: noisy context, wrong normalisation, narrow training range). |
| **Reported instability** | **Yes, four distinct ones** — catalogued in §P1.5. Briefly: (i) the Adapter *overfits* on a narrow context range, and its generalisation **degrades with further training**; (ii) training under large context noise (σ = 0.5) makes Concat *more* robust but makes the Adapter *worse*, with large across-seed variance; (iii) badly-scaled context normalisation (orders of magnitude off) breaks it; (iv) longer wall-clock time than the baselines at matched parameter count and matched timesteps, attributed to the hypernetwork. |
| **Single-task or multi-task** | **Zero-shot dynamics generalisation** — one reward function, a family of transition functions. Formally a Contextual MDP `⟨C, S, A, M', γ⟩` with `R^c = R ∀c`. Not multi-task in the reward sense. |

### P1.2 Every head-to-head comparison, with numbers

Five arms, all SAC, all with **matched learnable-parameter counts** (hidden widths
adjusted to equalise), 16 seeds each:

| Arm | Rung | Mechanism, as implemented here |
|---|---|---|
| **Unaware** | — | Ignores `c` entirely; policy is `π(s)`. |
| **Concat** | 0 | Augmented state space `S' = S × C`; policy is `π([s; c])`. Named as "the current standard approach" with six citations. |
| **cGate** | 1 | Benjamins et al.'s FiLM-analogue: separate state encoder `φ(s)` and context encoder `g(c)`, action `a = f(φ(s) ⊙ g(c))`. **This is the FiLM arm** — elementwise multiplicative gating, one gate per feature, at one site. (Note: gain only, no additive offset — it is FiLM with β ≡ 0.) |
| **FLAP** | 3, per-task | Shared feature extractor `φ(s)`, then a **task-specific linear head** `W_i φ(s) + b_i`; a supervised model maps transition tuples to those weights at test time. |
| **Adapter (theirs)** | 2 | Hypernetwork-generated bottleneck adapter, described above. |

#### (a) ODE, 1-D context — context is *necessary*

Train contexts `{−5, −1, 1, 5}`; evaluate on 201 points in `[−10, 10]`; 300 k steps.
Results are reported as learning curves (Fig. 3, left) rather than a table, so exact
endpoint values are not printed. The paper's verbatim ordering:

> "the Unaware model fails to generalise well … Concat, cGate and FLAP perform
> reasonably well, but our Decision Adapter outperforms all methods and converges
> rapidly."

Decomposed by context region (App. F.1, Fig. 17): on **training** contexts every
method except Unaware performs well; the Adapter's margin comes from
**extrapolation** (contexts in `[−10,−5) ∪ (5,10]`), where "the Adapter outperforms
all methods."

#### (b) ODE, 2-D context — the one place exact numbers are printed

Train on `({1,0,−1}² ∪ {5,0,−5}²) \ {(0,0)}`; evaluate on the 21 × 21 grid of
evenly spaced points in `[−10,10]²`; 16 seeds. The heatmaps in App. F.2 (Fig. 18)
carry a printed grand-average cell. **These are the batch's cleanest head-to-head
numbers** (higher is better; the environment's ceiling is ≈ 200):

| Arm | Rung | 2-D ODE AER (mean over 441 eval contexts × 16 seeds) | vs. Concat |
|---|---|---|---|
| **Adapter** (hypernet-generated adapter) | 2 | **159.0** | **+50.0 (+45.9 %)** |
| Concat | 0 | 109.0 | — |
| cGate (FiLM-style gating) | 1 | 85.0 | −24.0 (−22.0 %) |
| FLAP | 3, per-task | 60.0 | −49.0 (−45.0 %) |

Two things worth flagging for the project. First, **the FiLM-style arm loses to
plain concatenation here** — modulation is not automatically better than
concatenation; the *capacity* of the modulation matters. Second, the ordering is
Adapter > Concat > cGate > FLAP, i.e. it is not monotone in the capacity spectrum:
FLAP generates a full linear head but is the worst arm, because its per-task head
gives no route to generalise to unseen continuous contexts.

#### (c) CartPole with distractor context dimensions — **the key robustness result**

Setup (§6.3.2): only pole length actually varies. During training, `k` **additional
context dimensions with the constant value 1** are appended; during evaluation those
same dimensions are set to **0**. So the context is `5 + k` dimensional, of which
one dimension is informative and `k` are pure noise whose value shifts between
training and test. `k ∈ {0, 1, 20, 100}`; 16 seeds; up to 900 k steps; optimal
return = 500.

Reported as three panels of learning curves (Fig. 4). Verbatim findings:

- **`k = 0`:** "the Adapter, Concat and cGate models perform comparably. In this
  case, each architecture achieves near the maximum possible reward for the domain."
- **`k = 1`:** "little effect."
- **`k = 20` and `k = 100`:** "the Concat and cGate models' performances drop
  significantly, whereas the Adapter's performance remains relatively stable."
- The strongest single sentence in the paper: *"Strikingly, the Adapter architecture
  trained with 100 distractor context variables is still able to perform well on
  this domain and significantly outperforms the Concat model with significantly
  fewer (just 20) distractor variables."*

**Note the FiLM arm's position.** cGate degrades *with* Concat, not with the
Adapter. Elementwise multiplicative gating does **not** confer distractor
robustness; generating a nonlinear adapter's weights does.

#### (d) Same experiment, distractors drawn from a Gaussian rather than fixed

App. F.6 / Fig. 5. Distractors resampled each episode from `N(1, 0.2²)` in training
and `N(0, 0.2²)` at evaluation. Same conclusion: "the Adapter is still more robust
to changing distractor variables compared to either Concat or cGate", in both
CartPole and ODE.

**The crucial control (App. F.6.2 / F.6.3):** when the distractor distribution is
held *identical* between training and test, the effect largely disappears — "the
difference is much less pronounced." So the mechanism being measured is
**overfitting to nuisance context that shifts**, not distractor count per se. In the
ODE, cGate with 20 same-distribution distractors is *slightly better* than with 0,
which the authors read as the noise "effectively act[ing] as an additional, noisy,
bias term." That is a small but genuinely interesting data point: uninformative
input to a modulator is not always harmful — it is harmful when its distribution
moves.

#### (e) MuJoCo Ant — the same result at 111 observation dimensions

§7.3, Fig. 6, `k ∈ {0, 1, 20, 100}`, 1 M steps, 16 seeds. "We observe a similar
result to that of CartPole — the Concat and cGate models are significantly less
robust to having irrelevant distractor variables. By contrast, the Adapter
consistently performs well regardless of how many distractor dimensions are added."

Separately, App. B.3 (Fig. 9) shows the no-distractor Ant case: the Unaware model is
beaten by both context-aware models, because it "cannot simultaneously perform well
on light and heavy masses."

#### (f) The two ablation baselines that isolate the hypernetwork itself

App. F.3 — this is the ablation that answers "is it the adapter or the
hypernetwork?":

| Extra baseline | What it removes | Result |
|---|---|---|
| **AdapterNoHnet** | Same adapter architecture and location, but **no hypernetwork** — the adapter is one MLP taking the concatenation of state features and raw context. | "performs **much worse** than our hypernetwork-based adapter" (1-D and 2-D ODE). |
| **cGateEveryLayer** | cGate's elementwise product applied at **every** hidden layer instead of one. | "does **not** outperform cGate." |

Two lessons the project should note. (1) The gain is attributable to **weight
generation**, not to the adapter's placement or its residual form — remove the
hypernetwork and the same adapter loses. (2) **More modulation sites do not help**
a low-capacity operator: applying FiLM-style gating at every layer buys nothing over
applying it once.

#### (g) CartPole with a *clean* context — the honest negative

App. B.2, Fig. 8. Pole length varied over train `{1, 4, 6}`, eval 301 points in
`[0.1, 10]`, no distractors. The Unaware model **eventually reaches** comparable
generalisation (AER > 400) but needs > 600 k steps, while cGate, Concat and the
Adapter all cross that threshold **before 100 k steps**. So on a clean, benign
context, the benefit of *any* conditioning is sample efficiency rather than
asymptote — and all three conditioning mechanisms are indistinguishable.

### P1.3 The architecture ablations (App. E), compactly

All on the 1-D ODE, 16 seeds. The authors' own bolded conclusions, with the
project-relevant reading:

| Ablation | Options tried | Finding | Reading |
|---|---|---|---|
| **Adapter architecture** | `[]` (no hidden layer), `[8]`, `[16]`, `[32]` (default), `[64]`, `[256]`, `[32,32]` | Most perform comparably; `[8]` and `[]` slightly worse; `[256]` no better than `[32]`; multiple layers no benefit. | A **bottleneck of 32 on 256-d features is sufficient**; capacity beyond that is wasted. The low-rank constraint is not a cost. |
| **Hypernetwork chunking** | chunked (default, ≈16 k params) vs. `[]`, `[100,100]` (≈1.7 M params), `[100,100,100]`, larger chunks `[66,66]` | Both chunked configurations are **best**; non-chunked slightly worse, worst with no hidden layer. | The hypernetwork can be **two orders of magnitude smaller** than the naive full-vector generator *and* perform better. Directly relevant to any project-side concern about hypernetwork parameter blow-up. |
| **Skip connection** | `x ← A(x) + x` vs. `x ← A(x)` | "performs similarly to the alternative." | The residual is not load-bearing here (unlike FiLM-family papers where zero-init/identity-init is load-bearing). |
| **Adapter location** | A = network start, B = inside trunk, C = before action head (default), D = on the output action | "the base model performs the best… performance is quite poor if we put the adapter modules at the start… when adapting only the final action, the performance is also poor." Three adapters (A+B+C) ≈ one adapter at C. | **Placement matters and the failures are at the extremes.** Modulating the raw input or the emitted action both fail; the useful region is the middle of the network. Adding more sites does not help. |
| **Pre-adapter activation** | no activation after trunk (default) / with / only on the log-σ head / no activation in critic | "Not having an activation function outperforms having one." | Minor, but note the actor's adapter operates on **pre-activation** features by default. |

### P1.4 Theoretical component

§4 plus Appendix A. The paper proves a two-sided existence result for a
goal-reaching CMDP where the context names the goal circle:

- **(i)** For some context sets — goals that do not overlap — a context-unaware
  policy performs **arbitrarily poorly on average**, because it is forced to take
  the same action in the same state and must therefore visit each goal in sequence.
- **(ii)** For other context sets — goals that overlap — an unaware policy can go
  straight to the joint intersection and its value is within a factor `γ^τ` of the
  optimal context-aware policy: `V̄^π_{C_close}(s) / V̄^*_{C_close}(s) ≥ γ^τ`.

Appendix B then does something the corpus rarely sees: it **maps the theory onto the
empirics**, showing that the ODE with both positive and negative contexts is a
case-(i) environment (Unaware "fails completely") while the ODE with only positive
contexts, and CartPole, are case-(ii) environments (Unaware performs nearly as
well). App. B also shows a coordinate transform proving that the
context-dependent-reward formalisation in the proof and the
context-dependent-dynamics setting studied empirically are equivalent for that
environment.

### P1.5 Reported instabilities and limitations — full catalogue

The paper's §8 plus App. G. This is the honest half and it is directly relevant to
any project design that would feed a *learned* or *noisy* context to a modulator.

1. **Noisy context at evaluation (App. G.1)** — the closest analogue to "the
   modulator reads a signal that is partly wrong." Gaussian noise with
   `σ ∈ {0, 0.05, 0.1, 0.2, 0.5, 1}` added to the *normalised* context (so σ = 1 is
   very large) at evaluation, on CartPole checkpoints at 600 k steps.
   - Models trained **without** noise: "the Concat model is more susceptible to
     noisy contexts than our Adapter." But **both degrade**, unlike the Unaware
     model which is flat by construction. The Adapter beats Unaware only until
     about **σ = 0.5** — which the authors contextualise as a pole length of 3 m
     against a default of 0.5 m and a maximum training length of 6 m.
   - Models trained **with** σ = 0.1: both behave like the no-noise case.
   - Models trained **with** σ = 0.5: **the result inverts.** "the Concat model
     becomes more robust to noisy contexts, but the Adapter performs worse. In
     particular, the Adapter model exhibits a large amount of variation across
     seeds, indicating that some seeds performed badly." On average the Adapter
     drops to roughly Unaware-level.
   - **Project reading:** weight generation is more robust than concatenation to
     *irrelevant-but-clean* context and to *moderately* noisy context, but it is
     **less** able to be *trained* into robustness against heavy context noise —
     and it fails with high seed variance rather than gracefully. If a project-side
     modulator reads an inferred or noisy interoceptive signal, this is the failure
     mode to expect and to check for across seeds.

2. **Overfitting on a narrow context range (App. G.3.1)** — the sharpest number in
   the limitations. Training on the 2-D ODE with the narrow context set
   `{(±1,±1),(±1,0),(0,±1)}`, the Adapter's AER **rises then falls with continued
   training**: printed heatmap grand averages of **123.0 at 50 k steps** and
   **65.0 at 300 k steps**. "our model exhibits worse extrapolation performance due
   to overfitting on the narrow training contexts." **This is a
   train-longer-generalise-worse instability**, invisible to any training-return
   curve, and it is exactly the shape of failure that a project running a fixed
   step budget would miss.

3. **Sensitivity to context normalisation (§8, App. G.2)** — normalisation is by the
   largest training value per dimension. "our Adapter performs well when the context
   normalisation is incorrect by a factor of 2 or 3, [but] its performance does
   suffer when the normalisation value is orders of magnitude too small, leading to
   very large contexts being input into the model."

4. **Narrow or badly-chosen training context sets (App. G.3, Fig. 28)** — eight
   different training sets on the 1-D ODE. Poor generalisation when the set is tiny
   (`{±0.1}`), when it lacks variation (`{±0.1,±1.0}`), when it is one-signed
   (`{1,5}`), and — notably — also when it is spread **too** far (`{±0.1, ±7.5}`).

5. **Wall-clock cost (§8)** — "A final limitation of our Adapter is its longer
   wall-clock training time compared to other methods (given the same training
   timesteps and a similar number of parameters). This is likely caused by the
   hypernetwork." Mitigations named but not implemented: caching generated weights
   per context (valid because context is episode-constant), better batching.

6. **Assumes ground-truth context (§8)** — acknowledged as a limitation; integration
   with context-inference methods is future work. **No experiment in this paper uses
   an inferred context.**

### P1.6 Phase 1 — Foundational overview

**The problem.** A robot trained on tiled floor slips on asphalt; a robot that
trained empty struggles under load. These are changes in *dynamics* — how the world
responds to the agent's actions — not changes in the goal. One fix is to train on
lots of variation and hope one behaviour covers everything ("robustness"); the
paper shows this provably fails whenever succeeding in one setting means moving
away from success in another. The other fix is to *tell* the agent which setting it
is in. That description is the **context**, and it differs from ordinary observation
in that it changes on a much slower timescale — mass and friction hold still for a
whole episode while joint angles change every step.

**The neglected question.** Whether to use context is settled; **how to plug it in**
is not. The overwhelmingly common answer is to glue the context numbers onto the
observation vector, which throws away the conceptual difference between the two and,
the authors argue, invites the network to confuse them.

**The proposal.** Borrow **adapters** from natural-language processing — small
modules inserted between the layers of a frozen backbone. In NLP one adapter is
trained per task, which is useless for zero-shot generalisation to a *continuous*
context you have never seen. So instead of learning one adapter per context, learn a
**hypernetwork** that *writes* an adapter's weights on the fly from the context
vector. The main network extracts state features; the generated adapter decides how
those features should be transformed for this particular world. Training is
completely standard RL — no pre-training phase, no fine-tuning phase, no change to
the loss, just a different architecture.

**Main findings, in order of importance.**

1. When the context is clean and every dimension matters, **concatenation is fine** —
   all context-aware architectures reach near-optimal performance on CartPole.
2. When some context dimensions are **irrelevant and their values shift between
   training and deployment**, concatenation and elementwise gating collapse while
   the Decision Adapter does not — an adapter agent with **100** junk dimensions
   beats a concatenation agent with only **20**.
3. On a task where context is genuinely necessary (the ODE), the Adapter wins
   outright, and its margin lies in **extrapolating** beyond the training contexts:
   2-D average return 159 vs. 109 for concatenation, 85 for elementwise gating,
   60 for per-task heads.
4. Removing the hypernetwork while keeping the adapter destroys the benefit — so
   the credit belongs to **generating weights from context**, not to the adapter
   module's shape.
5. The elementwise-gating method (cGate) is a **special case** of the Decision
   Adapter, proved constructively.

**Initial takeaway.** "Concatenate the context" is a defensible default only under
the assumption that you know which variables matter. The moment that assumption is
wrong — which the authors argue is the normal real-world case — the architecture
choice becomes the difference between working and not working, and the deciding
property is whether the conditioner has enough capacity to *ignore* the parts of its
input that carry no signal.

### P1.7 Phase 2 — Graduate-level deep dive

#### P1.7.1 Setting: the Contextual MDP

A standard MDP is `⟨S, A, T, R, γ⟩` with transition kernel

$$T(s' \mid s, a) : S \times A \times S \to [0,1],$$

reward `R : S × A × S → R`, and the objective of maximising the return

$$G_t = \sum_{k=0}^{\infty} \gamma^{k} R_{t+k+1}.$$

A **Contextual MDP** (Hallak et al.) is `⟨C, S, A, M', γ⟩` where `M'` maps a context
`c ∈ C` to an MDP `M = ⟨S, A, T^c, R^c, γ⟩`. All members share `S` and `A`; only the
transition and reward functions vary. This paper fixes the reward,

$$R^{c} = R \quad \forall c \in C,$$

so the family varies **only in dynamics**, and the goal is to train on
`C_train ⊂ C` and generalise zero-shot to `C_eval ⊃ C_train`.

The evaluation functional is the **Average Evaluation Reward**

$$\mathrm{AER} = \frac{1}{c_{\max} - c_{\min}} \int_{c_{\min}}^{c_{\max}} R(c)\, dc,$$

approximated by a uniform grid over the evaluation range, with `R(c)` itself the
mean episode return over `n = 5` episodes.

#### P1.7.2 The Decision Adapter forward pass, written out

Let the primary network be `n` fully-connected layers,

$$x_{i+1} = L_i(x_i) = \sigma_i\!\left(W_i x_i + b_i\right), \qquad x_1 = s, \quad x_{n+1} = a.$$

Insert an adapter `A_i : R^{d_i} → R^{d_i}` between `L_{i-1}` and `L_i`, where
`d_i` is the output dimension of `L_{i-1}`. The adapter is parameterised by
`θ^i_A ∈ R^{P_i}`, and those parameters are **not learned directly** — they are the
output of a context-conditioned hypernetwork

$$H_i : C \to \mathbb{R}^{P_i}, \qquad \theta^i_A = H_i(c),$$

reshaped into the adapter's weight matrices and bias vectors. The modified forward
pass (Algorithm 1, changes in blue in the original) is:

$$
\begin{aligned}
\theta^i_A &= H_i(c) &&\text{(generate weights)}\\
x'_i &= A_i\!\left(x_i \mid \theta^i_A\right) &&\text{(adapter forward pass)}\\
x_i &\leftarrow x_i + x'_i &&\text{(residual skip)}\\
x_{i+1} &= L_i(x_i) &&\text{(continue as normal)}
\end{aligned}
$$

The whole system — primary network parameters `{W_i, b_i}` and hypernetwork
parameters — is trained end-to-end by ordinary SAC. Note the two-timescale structure
this induces implicitly: `θ^i_A` is constant within an episode because `c` is, so
the adapter is effectively a *fixed* module for the duration of an episode whose
identity is selected by the context. (This is precisely why the authors note that
caching `H_i(c)` per episode would recover most of the wall-clock cost.)

#### P1.7.3 The bottleneck, and why it is a low-rank prior

The adapter is `d_i → p → d_i` with `p < d_i` (default `d_i = 256`, `p = 32`).
Parameter count:

$$P_i = \underbrace{d_i p}_{\text{down}} + \underbrace{p\, d_i}_{\text{up}} + \underbrace{p + d_i}_{\text{biases}} = O(p\, d_i),$$

against `O(d_i^2)` for a single full-width layer. At `d_i = 256, p = 32` that is a
**4×** reduction. Two justifications are given, and the second is the interesting
one:

1. Fewer parameters for the hypernetwork to emit, "which, in turn, makes it easier
   for the adapter hypernetwork to generate useful weights."
2. **A low-rank inductive bias that may prevent overfitting**, connected explicitly
   to the literature showing that *reducing* an RL agent's network capacity can
   *improve* generalisation. The skip connection is the safety valve: whatever the
   bottleneck destroys, the identity path preserves.

Composing (i) the residual and (ii) the bottleneck, the adapter computes a
**low-rank perturbation of the identity**,

$$x_i \;\longmapsto\; x_i + U(c)\,\rho\!\left(D(c)\, x_i + b_D(c)\right) + b_U(c),$$

with `D(c) ∈ R^{p×d_i}`, `U(c) ∈ R^{d_i×p}`, `ρ` the nonlinearity — a
context-generated LoRA-shaped update, three years before that framing became
standard in RL.

#### P1.7.4 Derivation: cGate is a strict special case (Appendix C, expanded)

cGate computes, with state encoder `φ` and context encoder `g` both mapping to
`R^d`:

$$h = \mathrm{cGate}(s,c) = \varphi(s) \odot g(c), \qquad a = f(h).$$

Identify the pieces with the adapter architecture. Let the primary network's layers
`L_1 … L_{i-1}` be the state encoder and `L_i … L_n` be the policy head:

$$\varphi(s) = L_{i-1}(x_{i-1}), \qquad f(h) = L_n(x_n).$$

Now constrain the adapter to be a **single linear layer with no bias and no
nonlinearity**, and constrain the hypernetwork's output, after reshaping, to be a
diagonal matrix whose diagonal is `g(c)`:

$$W = H(c) = \operatorname{diag}\!\left(g(c)\right) \in \mathbb{R}^{d \times d}.$$

Then

$$A\!\left(\varphi(s) \mid c\right) = W\varphi(s) = \operatorname{diag}\!\left(g(c)\right)\varphi(s).$$

Using the identity `diag(u) v = u ⊙ v` for `u, v ∈ R^d`:

$$\operatorname{diag}\!\left(g(c)\right)\varphi(s) = g(c) \odot \varphi(s) = \varphi(s) \odot g(c) = \mathrm{cGate}(s,c),$$

which is then passed to `f`. Hence every function cGate can express, the Decision
Adapter can express. The containment is **strict**: `H(c)` is not constrained to be
diagonal (off-diagonal entries mix features, which no elementwise gate can do), the
adapter may have a bias (an additive offset — the `β` that cGate lacks), and the
adapter may be nonlinear and multi-layer.

Three remarks the paper does not spell out but which matter for this project:

- **cGate is FiLM with `β ≡ 0`.** Full FiLM, `γ(c) ⊙ x + β(c)`, corresponds to
  `W = diag(γ(c))` *plus* the adapter bias `b = β(c)` — still inside the adapter's
  hypothesis class, still a diagonal special case.
- **With the residual skip on, the diagonal case reads
  `x ← x + diag(g(c))x = diag(1 + g(c))x`,** i.e. the skip converts a plain gate into
  a *gate around 1* — the identity-initialised form that the FiLM literature
  independently converged on.
- **The capacity that buys distractor robustness is the off-diagonal / nonlinear
  part.** An elementwise gate must transform *every* feature by *something*
  determined by *all* context dimensions passing through `g`; there is no
  architectural route for it to route around a nuisance dimension other than
  learning `∂g/∂c_junk ≈ 0` in the encoder — the same thing Concat must learn in its
  first layer. The adapter can additionally learn to place the nuisance dimensions'
  influence in directions that the bottleneck's low-rank projection discards. This is
  the most plausible mechanistic explanation of §7.2's result, and the paper does
  **not** offer one — flagged below as an open question.

#### P1.7.5 Derivation sketch: when context is provably necessary

Appendix A's setting: the agent starts at the origin; the context `c` names a goal
circle of radius `τ̄`; reward 1 on entry, 0 otherwise; discount `γ`. Because an
unaware policy `π(s)` must emit the same action in the same state regardless of `c`,
its trajectory is a *single* path that must intersect every goal circle in the
context set.

- **Non-overlapping goals.** With `m` mutually distant goals, the single path must
  visit them in sequence; the `k`-th goal visited is reached after at least
  `(k−1)·(distance between goals)` steps, so its discounted value decays
  geometrically. As `m` grows or the goals separate, the ratio to the optimal
  context-aware value tends to 0 — "arbitrarily poorly."
- **Overlapping goals.** If all circles share a common intersection point at
  distance at most `τ` from the origin's optimal path, the unaware policy heads
  there and reaches every goal within `τ` extra steps, giving

$$V^{\pi}_c(s) \ \ge\ \gamma^{\tau} V^{*}_c(s) \quad \forall c \in C_{\text{close}}$$

  and, taking expectations over `c ∼ C_close` and pulling the constant out,

$$\bar V^{\pi}_{C_{\text{close}}}(s) = \mathbb{E}_{c}\!\left[V^{\pi}_c(s)\right] \ \ge\ \mathbb{E}_{c}\!\left[\gamma^{\tau} V^{*}_c(s)\right] = \gamma^{\tau}\,\bar V^{*}_{C_{\text{close}}}(s),$$

  hence the printed bound

$$\frac{\bar V^{\pi}_{C_{\text{close}}}(s)}{\bar V^{*}_{C_{\text{close}}}(s)} \ \ge\ \gamma^{\tau}.$$

Appendix B closes the loop between the proof's context-dependent-*reward*
formulation and the paper's context-dependent-*dynamics* setting. Take dynamics
`s' = s + C_i a` with `C_i` a context-selected rotation matrix, fixed goal `g`,
`s_0 = 0`. Left-multiplying by `C_i^{-1}`:

$$C_i^{-1} s' = C_i^{-1} s + a,$$

so in the transformed coordinates the action's effect is context-*independent*
while the goal becomes `g_{c_i} = C_i^{-1} g`, context-*dependent*. The two
formulations are the same problem in different frames.

### P1.8 What the paper does **not** establish (for citation hygiene)

Recording these so the project does not over-cite:

1. **No mechanism for the distractor result.** The paper demonstrates the
   robustness but never analyses *why* — no probe of what the hypernetwork learns
   about junk dimensions, no gradient or sensitivity analysis, no measurement of
   `∂θ_A/∂c_junk`. The explanation in §P1.7.4 above is this reviewer's, not the
   authors'.
2. **Context is always ground truth.** Every experiment. The one experiment
   involving imperfect context (App. G.1) *perturbs* the ground truth rather than
   inferring a context, and there the Adapter's advantage is bounded and can invert.
3. **Vector observations only.** No images, no recurrence, no partial observability
   in the state (the CMDP is fully observed given `c`). Extending to image
   observations is named as future work.
4. **Off-policy, single algorithm.** SAC only. The claim of algorithm-agnosticism
   is asserted, not demonstrated. **No PPO / on-policy result exists in this paper.**
5. **Exact endpoint numbers are largely unprinted.** All main-text results are
   learning curves; the only printed numeric summaries are the 2-D ODE heatmap
   grand averages (§P1.2b) and the overfitting heatmaps (§P1.5.2). Quote those two;
   describe the rest qualitatively.
6. **`n = 5` evaluation episodes per context.** Cheap per context, compensated by
   dense context grids and 16 seeds — but individual context cells are noisy.

### P1.9 Relevance to this project

- **Direct answer to the standing "concat vs. FiLM vs. hypernet" question.** The
  honest summary for the project's own design docs is *neither* "hypernetworks win"
  *nor* "concat is fine", but: **all three tie when the conditioning signal is clean
  and fully relevant; only weight generation survives a conditioning signal that is
  partly nuisance and whose nuisance part shifts between training and test.**
- **The FiLM arm loses to concatenation on the ODE (85 vs. 109).** Any project
  claim of the form "modulation beats concatenation" needs a qualifier: it depends
  on the *capacity* of the modulator, and a bare elementwise gate is not
  automatically an improvement over an extra input coordinate.
- **"More sites" is not a lever.** cGateEveryLayer ≈ cGate. If a project-side FiLM
  design underperforms, adding injection sites is not the fix this paper supports;
  raising per-site capacity is.
- **Placement.** Failure at the very first layer and at the output; success in the
  middle. A project modulator applied to raw observations or directly to emitted
  actions is in the regime this paper found poor.
- **Two failure modes to instrument for.** (i) *Train-longer-generalise-worse*
  overfitting when the training context distribution is narrow (AER 123 → 65). Any
  project run that reports only end-of-training numbers cannot see this; an
  evaluation curve over training is required. (ii) *High across-seed variance under
  a noisy conditioner* — with a noisy context the Adapter's mean falls to
  Unaware-level because some seeds fail entirely, which a mean-only report hides.
  16 seeds is the paper's answer; project runs at 3–5 seeds would not resolve it.
- **Cost is real but small if exploited.** The hypernetwork slows wall-clock at
  matched parameters; the paper names the obvious mitigation (cache the generated
  weights while the context is constant) and does not implement it. If a project
  conditioner is constant over an episode or a phase, this caching is free
  performance.
- **Handoff note.** If the project wants to run this comparison in its own
  environment, the arms and the distractor protocol are fully specified here and the
  code is public; that is an `experiment-designer` / `senior-developer` task, not a
  literature-review one.

### P1.10 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Problem: generalising to new *transition dynamics*. Claim: how context is incorporated architecturally has received less attention than whether to use it. Introduces the **Decision Adapter**, which generates the weights of an adapter module from context. Two claims: superior generalisation vs. prior approaches, and **greater robustness to irrelevant distractor variables**. |
| 1 | **Introduction** | Legged-robot motivating example (tiles vs. asphalt; empty vs. loaded). Robustness-style single-policy training fails when variation is large. Context differs from state by **timescale** — friction and mass hold for a long time, joint angles change every step. The prevalent approach is concatenation, which ignores that difference and may confound the two, and is worsened when the relevant context variables are unknown, adding irrelevant dimensions. Lists the four comparisons made: no context, concatenation, competitive baselines, distractor robustness. Code released. |
| 2 | **Background** | MDP `⟨S,A,T,R,γ⟩`, return `G_t = Σ γ^k R_{t+k+1}`. **Contextual MDP** `⟨C,S,A,M',γ⟩`: a family of MDPs sharing `S`, `A`, differing in `T^c`, `R^c`. This paper fixes `R^c = R ∀c` — dynamics generalisation only. |
| 3 | **Related Work** | Four strands. (a) *Robustness* — one policy trained to tolerate perturbation; limited because it must act identically in identical states. (b) *Context-adaptive* — CMDP-style; context obtained as ground truth, by supervised prediction, or by unsupervised inference from observation sequences. Notes that **how** to incorporate it is under-studied: concatenation dominates (6 citations); Biedenkapp et al. learn separate representations and concatenate late; **FLAP** learns a shared representation plus a per-task linear head generated from transition tuples, which scales poorly in task count; **FiLM** modulates features of one modality by another, and **cGate** (Benjamins et al.) is its RL instantiation, restricted to a *linear* elementwise effect. (c) *Foundation models for control* — MetaMorph-style morphology transformers, learned dynamics + MPC, pre-trained observation/action models. (d) *Meta-RL* — including Beck et al. (recurrent task encoder generates the **whole policy's** weights) and Sarafian et al. (generate weights from **state**, then process encoded context through the generated network); MAML. Meta-RL usually needs multiple target-domain episodes, so it fits the zero-shot setting poorly. |
| 4 | **Theoretical Intuitions** | Unifies "only context-conditioned policies are guaranteed optimal" with "unaware policies often generalise fine empirically". Two cases, illustrated in Fig. 1: **(i) non-overlapping goals** — unaware policy must visit each in sequence, arbitrarily poor; **(ii) overlapping goals** — unaware policy heads to the intersection and is within `γ^τ` of optimal. Formal statement and proof deferred to App. A; App. B links theory to the ODE and CartPole results. |
| 5 | **The Decision Adapter** | Adapters defined (same in/out dimension, inserted between layers of a primary network; one-per-task in NLP with a frozen base). Three departures from the NLP recipe: (1) one adapter per context is useless for zero-shot generalisation over a **continuous** context and scales badly, so a **hypernetwork generates the adapter weights from context**, giving parameter sharing and cross-context transfer; (2) **no separate pre-train/adapt phases** — the architecture changes, training does not, so it drops into standard RL libraries; (3) algorithm-agnostic. Algorithm 1 + Fig. 2 give the forward pass: `θ_A = H_i(c)`, `x'_i = A_i(x_i\|θ_A)`, `x_i ← x_i + x'_i`, `x_{i+1} = L_i(x_i)`. Multiple adapters allowed, at most one between consecutive layers. Closes by asserting cGate is a special case (proof in App. C). |
| 6 | **Experimental Setup** | **6.1 Metrics** — AER as an integral over the evaluation context range, `n = 5` episodes per context; includes training contexts, with App. F.4 showing the test-only variant is near-identical. **6.2 Baselines** — SAC for all methods with **equalised learnable-parameter counts**; Unaware, Concat, cGate, FLAP, Adapter. **6.3 Environments** — ODE (`ẋ = c_0 a + c_1 a² + …`, complex action to keep the system solvable, state clipped to [−20,20], 200 steps, graded reward on `\|x\|`); CartPole (continuous force, 500-step cap, 5-dim context of which only pole length varies, `k` distractor dims equal to 1 in training and 0 at test); MuJoCo Ant (111-d obs, 8-d torque, 1000 steps, mass context, train {5,35,75}, eval 200 points in [0.5,100]). |
| 7 | **Results** | **7.1 Generalisation** — 1-D ODE: Unaware fails; Concat/cGate/FLAP reasonable; Adapter best and fastest; margin is in extrapolation. 2-D ODE: Adapter best, Concat second, FLAP and Unaware struggle. **7.2 Robustness to distractors** — narrows to Concat and cGate as baselines and gives three reasons why. CartPole: no separation at `k = 0` or `k = 1`; Concat and cGate collapse at `k = 20, 100`; Adapter stable; Adapter at `k = 100` beats Concat at `k = 20`. Also Gaussian-distributed distractors with a train/test mean shift, same conclusion. **7.3 High-dimensional control** — Ant reproduces the CartPole distractor pattern. |
| 8 | **Limitations** | Five, expanded in App. G: noisy context degrades the Adapter (though it stays comparable to Concat); context normalisation must be roughly right (factor 2–3 fine, orders of magnitude not); narrow training context ranges cause overfitting *and* poor generalisation; ground-truth context is assumed and may not be available; wall-clock cost from the hypernetwork, with caching and batching named as unexploited mitigations. Future work: image observations and language contexts; few-shot fine-tuning in the NLP adapter style. |
| 9 | **Conclusion** | Restates: context is sometimes provably necessary; the Decision Adapter beats all baselines including Concat when context is necessary; when irrelevant context variables shift between train and test, Concat and cGate fail and the Adapter does not, including on Ant; the Adapter is theoretically more powerful and empirically more effective than cGate. |
| A | **Proofs** | Formal statement and proof of the two-case theorem; ends with the bound `V̄^π/V̄^* ≥ γ^τ` for the overlapping case. |
| B | **Linking Theory and Practice** | Coordinate-transform argument showing context-dependent-reward and context-dependent-dynamics formulations coincide for the studied environment. **B.1 ODE** — training on `{1,5}` (positive only) makes Unaware nearly competitive (case ii); training on `{−5,−1,1,5}` makes it fail completely (case i). **B.2 CartPole** — Unaware eventually reaches AER > 400 but needs > 600 k steps vs. < 100 k for Adapter/Concat/cGate; context buys sample efficiency here, not asymptote; FLAP converges slower but catches up. **B.3 Ant** — Unaware underperforms because it cannot handle light and heavy masses at once. |
| C | **cGate as a Special Case** | Constructive proof: one adapter, single linear layer, no bias, no nonlinearity, `W = H(c) = diag(g(c))` recovers `φ(s) ⊙ g(c)` exactly, via `diag(a)b = a ⊙ b`. Adapter strictly more powerful since it may be a full nonlinear network. |
| D | **Experimental Details** | D.1 environments — **context normalisation** `c_norm,i = c_i / max_i` by the largest *training* value, so evaluation contexts outside the convex hull exceed 1.0; ODE initial-state cycling; CartPole's five context variables and defaults (g 9.80, cart mass 1.00, pole mass 0.10, pole length 0.50, force 10.00). D.2 hyperparameters — ReLU everywhere, CleanRL SAC, PyTorch, defaults tabulated. D.3 **bottleneck justification** — 256→32→256, `O(p d_i)` vs. `O(d_i²)`, 4× fewer parameters at `p = 32`; low-rank inductive bias against overfitting, connected to work showing reduced capacity aids RL generalisation; skip connection preserves whatever the bottleneck discards. Fig. 10 draws all four baseline architectures. D.4 compute — internal cluster, RTX 3090 nodes, 1–3 days per method per experiment for all seeds. |
| E | **Adapter Ablations** | All on the 1-D ODE. **E.1 architecture** — `[]`/`[8]` slightly worse, `[16]`–`[256]` and `[32,32]` comparable, no benefit from depth or width beyond the bottleneck. **E.2 chunking** — chunked best; non-chunked slightly worse and far larger (≈16 k vs ≈1.7 M actor-hypernetwork parameters). **E.3 skip connection** — no significant difference. **E.4 location** — positions A (input), B (in trunk), C (before action head, default), D (on the action); base (C) best, B slightly worse, A and D poor, three adapters ≈ one. **E.5 pre-adapter activation** — no activation before the actor's adapter is best; the critic is insensitive. |
| F | **Additional Results** | F.1 the 1-D ODE split into Train / Interpolation / Extrapolation. F.2 the 2-D heatmaps with printed grand averages **Concat 109.0, Adapter 159.0, cGate 85.0, FLAP 60.0**. F.3 **extra baselines**: AdapterNoHnet (adapter without hypernetwork, taking concatenated features and raw context) "performs much worse"; cGateEveryLayer does not beat cGate. F.4 AER over all contexts vs. test-only contexts — near-identical. F.5 ODE distractor results mirror CartPole. F.6 Gaussian distractors: F.6.1 shifted means (train `N(1,0.2)`, test `N(0,0.2)`) reproduce the effect; F.6.2 matched means largely remove it, and cGate with 20 matched distractors is slightly *better* than with 0, read as a noisy bias term; F.6.3 summary — the phenomenon is overfitting to nuisance context that shifts, not distractor count. |
| G | **Limitations (expanded)** | **G.1 noisy contexts** — CartPole checkpoints at 600 k steps, evaluation noise `σ ∈ {0,…,1}` on normalised context. Trained clean: Concat degrades more than Adapter, both degrade, Unaware flat, Adapter beats Unaware only up to about σ = 0.5. Trained with σ = 0.1: unchanged. Trained with σ = 0.5: **inverts** — Concat becomes more robust, Adapter becomes worse with large across-seed variance. **G.2 suboptimal normalisation** — robust to a factor of 2–3, breaks when orders of magnitude too small. **G.3 narrow context range** — eight training sets on the 1-D ODE; failure when tiny, when insufficiently varied, when one-signed, and when spread too far. **G.3.1 overfitting** — narrow 2-D training set; Adapter AER **123.0 at 50 k steps falling to 65.0 at 300 k steps**, i.e. generalisation degrades with continued training. |

---
