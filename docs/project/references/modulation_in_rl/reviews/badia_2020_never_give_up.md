---
title: "Never Give Up: Learning Directed Exploration Strategies"
slug: badia_2020_never_give_up
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_classics.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 4. Badia et al. 2020a — *Never Give Up: Learning Directed Exploration Strategies* (NGU)

**PDF:** `docs/project/references/modulation_in_rl/sources/Badia et al. 2020 - Never Give Up - Learning directed exploration strategies.pdf`
**Venue as printed (running header on every page):** *"Published as a conference paper at ICLR 2020"*. arXiv stamp: `arXiv:2002.06038v1 [cs.LG] 14 Feb 2020`.
**Authors:** Adrià Puigdomènech Badia\*, Pablo Sprechmann\*, Alex Vitvitskyi, Daniel Guo, Bilal Piot, Steven Kapturowski, Olivier Tieleman, Martín Arjovsky, Alexander Pritzel, Andrew Bolt, Charles Blundell — all DeepMind (\* equal contribution).

### 4.1 Plain-English entry point

Atari games like *Montezuma's Revenge* and *Pitfall!* give almost no reward until the
agent has done a long, specific sequence of things. The standard fix is a **curiosity
bonus**: pay the agent a little for seeing something new. The standard problem with
that fix is that the bonus **runs out** — once a place stops being novel, the agent
stops going there, even if going there was the only route to the reward. And an agent
trained on reward-plus-bonus can never fully switch the bonus off, so it stays
distracted forever.

NGU fixes both. It builds a novelty bonus that **never vanishes**, by measuring
novelty *within the current episode* against an episodic memory that is wiped at every
episode start — so every episode the agent is paid to tour the whole level again. And
it fixes the "can't switch it off" problem by training **many policies at once inside
one network**: policy 0 ignores the bonus entirely and is pure task-solving; policy 31
weights the bonus most heavily and is pure exploration; policies in between interpolate.

**The conditioning mechanism, which is what this project cares about.** The single
network is a **Universal Value Function Approximator** `Q(x, a, β_i)` — the index `i`
of which policy is running is fed **into** the network as a **one-hot vector over the
32 possible indices**, concatenated alongside the previous action and the previous
extrinsic and intrinsic rewards, and consumed by the recurrent core. Not an embedding
lookup. Not separate output heads. **A one-hot concatenation.** Each index also carries
a paired discount factor `γ_i`, but that one enters the *learning target*, not the
network's input.

**Headline result.** Doubles the base agent's score on every hard-exploration game in
Atari-57, reaching a median human-normalised score of **1344 %** (the abstract's
figure; §4.2 prints **1354.4 %**), and is *"the first algorithm to achieve non-zero
rewards (with a mean score of 8,400) in the game of Pitfall! without using
demonstrations or hand-crafted features."*

**Why the project cares.** This is the canonical **hyperparameter-conditioned policy**:
one network parameterising a family indexed by an exploration weight. The paper also
runs the cleanest available test of whether the conditioning *does anything* — compare
`NGU(N=1)` (one policy, no conditioning index) against `NGU(N=32)`. On *Pong*, the
single-policy version scores **−9.4** (human: 14.6) while the conditioned family scores
**19.6**. Conditioning is not decoration here; it is what makes the agent work at all.

### 4.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | ICLR 2020 — *"Published as a conference paper at ICLR 2020"*, page header throughout. |
| **RL algorithm** | **R2D2** (Recurrent Replay Distributed DQN) with the **n-step objective replaced by transformed Retrace double Q-learning**. Distributed: 256 actors, one GPU learner, prioritised replay, 35 B frames, 3 seeds. |
| **Conditioning signal** | A **discrete hyperparameter index** `i ∈ {0, …, N−1}` naming which member of a policy family is being run. Each index carries a **pair**: an intrinsic-reward weight `β_i` (with `β_0 = 0`, `β_{N−1} = β = 0.3`) and a discount factor `γ_i` (with `γ_0 = γ_max = 0.997`, `γ_{N−1} = γ_min = 0.99`). Note the anti-correlation: **the exploitative policy is far-sighted, the exploratory policy is short-sighted.** `N = 32` by default. **The index is not learned, not inferred, and not observed from the environment — it is assigned.** |
| **What is modulated** | The **Q-network** — which in a value-based agent *is* both the policy and the value function; there is no separate actor. The network is R2D2's dueling architecture: CNN torso → FC 512 → LSTM(512) → dueling head (a 512→1 value branch and a 512→18 advantage branch, combined by subtracting the advantage mean). The intrinsic-reward machinery (embedding network, RND) is **not** conditioned on `β_i`. |
| **The operator** | **Concatenation of a one-hot vector.** Verbatim: *"We concatenate to the output of the network a one-hot vector encoding the value of `β_i`, the previous action `a_{t−1}`, the previous intrinsic reward `r^i_t` and the previous extrinsic reward `r^e_t`."* **No embedding table, no affine modulation, no gating, no separate heads, no generated weights.** The one-hot is `N`-dimensional (32 bits for the default agent). |
| **Granularity and placement** | **One site, whole-vector.** The one-hot joins the recurrent core's input alongside the standard R2D2 auxiliary inputs (previous action, previous reward), which is the R2D2 convention for exactly those companions — so the concatenation sits **between the convolutional torso and the LSTM**. **Caveat: the phrase "to the output of the network" is loose in the PDF and App. H.3 contains only a figure**; record the placement as *at the recurrent core's input, inferred from the companion inputs*, not as a verbatim claim. Nothing is per-layer or per-unit. |
| **`γ_i` does NOT enter the network** | Worth stating separately because it is easy to get wrong. Only `β_i`'s one-hot is an input. `γ_i` enters through the **Retrace bootstrap target and the discounts stored in replay** — it is a property of the learning target, not of the forward pass. So "the network is conditioned on a `(β, γ)` pair" is **half right**: it is *indexed* by the pair, but it *reads* only `β`'s index. |
| **Ablated against no-conditioning?** | **Yes, and this is the paper's strongest conditioning evidence.** `NGU(N=1)` — a single policy with `β = 0.3` and no index input — is run everywhere alongside `NGU(N=32)`. Plus a sweep over `N ∈ {2, 8, 16, 32}`, a **Cross Mixture Ratio** ablation separating *weight* sharing from *data* sharing, a `β ∈ {0.2, 0.3, 0.5}` sweep, RND on/off, and extrinsic-reward on/off. **Not** ablated: the choice of one-hot concatenation versus any other injection mechanism. |
| **Reported instability** | **Yes, three distinct items.** (i) `NGU(N=1)` *"catastrophically fails to learn"* on Pong (**−9.4 ± 2.6**, human 14.6); the conditioned family fixes it (19.6). (ii) **Representation interference between family members**: `NGU(N=32)` does not match R2D2 on Breakout (532.8 vs 837.7) or Beam Rider (68.7 k vs 188.2 k) — *"the representations learned by using the intrinsic signal still slightly interfere with the learning process of the exploitative mixture. We hypothesize that alleviating this further by having non-shared representations between mixtures should help."* (iii) **Aggregate cost**: NGU's Atari-57 median (1354.4 %) is **below** its own base agent R2D2 (1920.6 %). |
| **Single-task or multi-task** | **Single-task, per game.** The "family" is a family of *objectives on the same task*, not a family of tasks. This is the key structural difference from papers #1–#3 and it is exactly why the mechanism is interesting for a project that wants to condition a policy on an internal setting rather than on an external task label. |
| **Claim strength** | For the **conditioning signal + family size**: **ablated** with numbers on 8 Atari games. For the **injection operator**: **asserted**, never varied. |

### 4.3 Phase 1 — Foundational overview

**The intrinsic reward, in three requirements.** The paper states them up front: the
bonus must (i) *rapidly* discourage revisiting a state **within** an episode,
(ii) *slowly* discourage states visited many times **across** episodes, and (iii) ignore
parts of the environment the agent cannot influence. These map onto three components:

- **Episodic novelty**: a memory `M`, emptied at every episode start, holding the
  embeddings of every observation seen this episode. The bonus is an inverse
  square-root pseudo-count computed from a `k`-nearest-neighbour kernel over `M`.
  Because `M` is wiped each episode, the bonus **never permanently decays** — a state
  visited a thousand times across a thousand episodes is as rewarding on its first
  visit this episode as a genuinely new one.
- **Life-long novelty**: a Random Network Distillation error, slowly decaying, used as a
  *multiplicative* modulator on the episodic bonus, clipped to `[1, L]` with `L = 5`.
- **Controllable states**: the embedding `f` used for the memory lookup is trained by an
  **inverse dynamics** objective — predict the action that took you from `x_t` to
  `x_{t+1}`. Anything in the observation the agent cannot affect (falling leaves,
  flashing wall colours) is useless for that prediction and is therefore discarded.

**The conditioned family.** Feeding a bonus into the reward changes the MDP — the paper
notes the augmented reward, if unpredictable from state and action, makes the process a
POMDP. Two mitigations: **feed the intrinsic reward to the agent as an input**, and use
a **recurrent** agent that summarises the whole episode's inputs. Then, rather than
committing to a single mixing weight, train `N` policies at once via UVFA:
`Q(x, a, β_i)` targets `r^{β_i}_t = r^e_t + β_i r^i_t`. Acting greedily w.r.t.
`Q(x, a, 0)` gives a **purely exploitative** policy — the bonus can be switched off at
evaluation without ever having trained a separate network.

Why many values rather than just two (`β = 0` and `β > 0`)? *"exploitative and
exploratory policies could be quite different from a behaviour standpoint. Having a
larger number of policies that change smoothly allows for more efficient training."*
The family is a smooth interpolation, and smoothness is the training argument.

**Initial takeaway.** A single network can host a **continuum of behavioural regimes**
indexed by a scalar knob, learn all of them simultaneously from shared experience, and
let the useful one be selected at evaluation by setting the knob. The knob costs 32 input
bits. The mechanism is embarrassingly simple; the value comes from the family, not from
the operator.

### 4.4 Phase 2 — Graduate-level deep dive

#### 4.4.1 The intrinsic reward, derived

*Combination.* Episodic bonus times clipped life-long modulator:

$$
r^{i}_{t} \;=\; r^{\text{episodic}}_{t}\cdot \min\big\{\max\{\alpha_t, 1\},\, L\big\},\qquad L = 5 .
$$

Note the **asymmetric clip**: `α_t` is floored at 1 and ceilinged at `L`, so the
life-long term can only ever *amplify* the episodic bonus, never suppress it — and by
at most 5×. As RND's prediction error decays, `α_t → 1` and *"this modulation will
vanish over time, reducing our method to using the non-modulated reward"*. The
never-give-up property therefore lives entirely in the **episodic** term.

*Episodic bonus as a pseudo-count.* Following count-based exploration theory
(`1/√n(s)` bonuses):

$$
r^{\text{episodic}}_{t} \;=\; \frac{1}{\sqrt{n\big(f(x_t)\big)}} \;\approx\; \frac{1}{\sqrt{\displaystyle\sum_{f_i \in N_k} K\big(f(x_t), f_i\big) \;+\; c}},\qquad c = 0.001 ,
$$

where the "count" is replaced by a sum of kernel similarities to the `k = 10` nearest
neighbours in the episodic memory. **Why a kernel and not exact matching:** *"when `K`
is a Dirac delta function, the approximation becomes exact but consequently provides no
generalisation of exploration required for very large state spaces."* The constant `c`
floors the count so the bonus cannot diverge.

*The kernel.* An inverse kernel, normalised by a running distance scale:

$$
K(x,y) \;=\; \frac{\epsilon}{\dfrac{d^{2}(x,y)}{d^{2}_{m}} + \epsilon},\qquad \epsilon = 10^{-3},
$$

with `d` Euclidean and `d²_m` a running average of the squared distance to the `k`-th
nearest neighbour. That normalisation is what makes the bonus comparable across games:
*"different tasks may have different typical distances between learnt embeddings."*

*Controllable-state embedding.* Given `(x_t, a_t, x_{t+1})`, parameterise
`p(a | x_t, x_{t+1}) = h(f(x_t), f(x_{t+1}))` with `h` a one-hidden-layer MLP plus
softmax, and train `f` and `h` jointly by maximum likelihood — a Siamese inverse
dynamics model. *"all the variability in the environment that is not affected by the
action taken by the agent would not be useful to make this prediction."* Architecture
(App. H.1): the standard DQN conv stack (32@8×8/4, 64@4×4/2, 64@3×3/1) → FC 32 per
branch → concatenate → FC 128 → FC 18 → softmax. The controllable state is therefore
**32-dimensional**.

*Life-long modulator.* RND: a frozen random network `g`, a trained predictor `ĝ`,
`err(x_t) = ‖ĝ(x_t;θ) − g(x_t)‖²`, normalised:

$$
\alpha_t \;=\; 1 + \frac{\mathrm{err}(x_t) - \mu_e}{\sigma_e},
$$

with running mean and standard deviation.

#### 4.4.2 The conditioning schedules

*The `β` ladder.* Not linear — deliberately sigmoid-shaped to over-sample the endpoints:

$$
\beta_i =
\begin{cases}
0 & i = 0,\\[2pt]
\beta & i = N-1,\\[4pt]
\beta \cdot \sigma\!\left(10\,\dfrac{2i - (N-2)}{N-2}\right) & \text{otherwise},
\end{cases}
$$

`σ` the logistic sigmoid, `β = 0.3`. The argument runs from `−10` at `i = 1` to `+10` at
`i = N−2`, so the middle indices saturate near `0` and near `β`; the paper's stated
intent is that this *"allows to focus more on the two extreme cases which are the fully
exploitative policy and very exploratory policy."* In effect the family is closer to a
soft two-mode mixture with a few intermediates than to a uniform sweep.

*The `γ` ladder.* Evenly spaced in log-space **in `1−γ`**, i.e. in effective horizon:

$$
\gamma_i \;=\; 1 - \exp\!\left(\frac{(N-1-i)\log(1-\gamma_{\max}) + i\,\log(1-\gamma_{\min})}{N-1}\right),
$$

with `γ_max = 0.997` (index 0, exploitative) and `γ_min = 0.99` (index `N−1`,
exploratory). Verify the endpoints: at `i = 0` the exponent is `log(1−γ_max)`, giving
`γ_0 = γ_max`; at `i = N−1` it is `log(1−γ_min)`, giving `γ_{N−1} = γ_min`. Between
them, `1 − γ_i` is a geometric interpolation, so **effective horizon `1/(1−γ)` is
geometrically spaced** from 333 steps down to 100 steps.

*Why the anti-correlation is deliberate.* *"We can use smaller discount factors for the
exploratory policies because the intrinsic reward is dense and the range of values is
small, whereas we would like the highest possible discount factor for the exploitative
policy in order to be as close as possible from optimizing the undiscounted return."*
A dense bonus does not need a long horizon; a sparse extrinsic reward does.

#### 4.4.3 How the index actually enters — the mechanism the report needs

Three sentences from the paper, in order:

1. *"We propose to use a universal value function approximator (UVFA) `Q(x, a, β_i)` to
   simultaneously approximate the optimal value function with respect to a family of
   augmented rewards of the form `r^{β_i}_t = r^e_t + β_i r^i_t`."*
2. *"We adapt the R2D2 agent that uses the dueling network architecture of Wang et al.
   (2015) with an LSTM layer after a convolutional neural network."*
3. *"We concatenate to the output of the network a one-hot vector encoding the value of
   `β_i`, the previous action `a_{t−1}`, the previous intrinsic reward `r^i_t` and the
   previous extrinsic reward `r^e_t`."*

**So: a one-hot over `N = 32` indices, concatenated with three other scalars/vectors,
consumed by the recurrent core of a dueling DQN.** Things it is *not*, all of which
appear in secondhand descriptions:

- **Not an embedding.** There is no learned embedding table over `β_i`; the one-hot goes
  in raw. (Agent57 — paper #5 — changes this. See §5.)
- **Not the scalar `β_i`.** The paper says *"a one-hot vector encoding the value of
  `β_i`"*, i.e. the **index** is encoded, not the value. This matters: the network
  cannot interpolate to an unseen `β` and gets no ordering information for free.
- **Not separate heads.** All `N` policies share every weight including the output
  layer; only the input differs. This is the point of the CMR ablation below.
- **Not the discount.** `γ_i` never enters the forward pass.
- **Not modulation of any kind.** No `γ ⊙ h + β`, no gating, no routing.

*Data flow at act time (App. A).* Each actor `j` is assigned a fixed index — printed as
`h = j mod N − 1` — and acts `ε`-greedily w.r.t. that policy. The actor obtains
`x_t, r^e_t, r^i_{t−1}` and the discount `γ_i`, runs the forward pass to get `a_t`,
computes `r^i_t` from the embedding network, and pushes
`(x_t, a_t, r_t = r^e_t + β_i r^i_t, γ_i, r^i_t)` into replay **together with the value
of `β_i` used and the initial recurrent state**. At learn time the intrinsic reward is
*sampled from replay* rather than recomputed, *"because it is fed as an input to the
network."*

Two small textual snags to record rather than silently fix: the index assignment is
printed as `h = j mod N − 1`, which for `N = 32` would never assign the most-exploratory
index 31; and the sentence *"the most exploratory policy `β_{N−1}` with the smallest
discount factor `γ_0 = γ_min`"* misprints the subscript (it appears twice, in §3 and in
App. A). Both are typographical.

#### 4.4.4 Weight sharing vs. data sharing — the Cross Mixture Ratio

Because all `N` policies share one network, there are two possible channels for
knowledge to move between them: **shared weights** and **shared experience**. The paper
isolates them with the **Cross Mixture Ratio (CMR)** — the proportion of a training
batch drawn from actors running a *different* `β_j ≠ β_i` than the index being trained.
`CMR = 0` (the default) trains each policy only on its own data; `CMR = 0.5` mixes.

Result: *"sharing experience from all the actors (with CMR of 0.5) slightly harms
overall average performance on hard exploration games. This suggests that the power of
acting differently for different conditioning mixtures is mostly acquired through the
shared weights of the model rather than shared data."*

**This is the most transferable finding in the paper for a modulation report.** The
benefit of a conditioned family is a *representation-sharing* effect, not a
*data-augmentation* effect. Whatever the injection operator, the mechanism by which
conditioning helps is that gradients from all regimes shape one trunk.

### 4.5 Results, as printed

Return averaged over **3 seeds**, 35 B frames, same data budget as R2D2.

**Table 1 — hard-exploration games.** *"Best baseline"* is the per-game best of R2D2,
DQN+PixelCNN, DQN+CTS, RND, and PPO+CoEx. `MR` = Montezuma's Revenge.

| Algorithm | Gravitar | MR | Pitfall! | PrivateEye | Solaris | Venture |
|---|---|---|---|---|---|---|
| Human | 3.4k | 4.8k | 6.5k | 69.6k | 12.3k | 1.2k |
| Best baseline | 15.7k | 11.6k | 0.0 | 11k | 5.5k | 2.0k |
| RND | 3.9k | 10.1k | −3 | 8.7k | 3.3k | 1.9k |
| R2D2 + RND | 15.6k ± 0.6k | 10.4k ± 1.2k | −0.5 ± 0.3 | 19.5k ± 3.5k | 4.3k ± 0.6k | 2.7k ± 0.0k |
| R2D2 (Retrace) | 13.3k ± 0.6k | 2.3k ± 0.4k | −3.5 ± 1.2 | 32.5k ± 4.7k | 6.0k ± 1.1k | 2.0k ± 0.0k |
| NGU(N=1) − RND | 12.4k ± 0.8k | 3.0k ± 0.0k | **15.2k ± 9.4k** | 40.6k ± 0.0k | 5.7k ± 1.8k | 46.4 ± 37.9 |
| NGU(N=1) | 11.0k ± 0.7k | 8.7k ± 1.2k | 9.4k ± 2.2k | 60.6k ± 16.3k | 5.9k ± 1.6k | 876.3 ± 114.5 |
| **NGU(N=32)** | 14.1k ± 0.5k | **10.4k ± 1.6k** | 8.4k ± 4.5k | **100.0k ± 0.4k** | 4.9k ± 0.3k | 1.7k ± 0.1k |

*"in 4 of the 6 games, NGU(N = 32) appears to substantially improve against the single
mixture case NGU(N = 1)."* Pitfall! is the exception, where the single policy wins —
the authors' reading: *"a single policy should be simpler to learn ... since exploration
and exploitation policies are greatly similar"* on that game.

**Table 2 — dense-reward games.** This is where conditioning earns its keep.

| Algorithm | Pong | QBert | Breakout | Space Invaders | Beam Rider |
|---|---|---|---|---|---|
| Human | 14.6 | 13.4k | 30.5 | 1.6k | 16.9k |
| R2D2 | 21.0 | 408.8k | **837.7** | 43.2k | **188.2k** |
| R2D2 + RND | 20.7 ± 0.0 | 353.5k ± 41.0k | 815.8 ± 5.3 | **54.5k ± 2.8k** | 85.7k ± 9.0k |
| R2D2 (Retrace) | 20.9 ± 0.0 | 415.6k ± 55.8k | 838.3 ± 7.0 | 35.0k ± 13.0k | 111.1k ± 5.0k |
| NGU(N=1) − RND | **−8.1 ± 1.7** | 647.1k ± 50.5k | 864.0 ± 0.0 | 45.3k ± 4.9k | 166.5k ± 8.6k |
| NGU(N=1) | **−9.4 ± 2.6** | **684.7k ± 8.8k** | 864.0 ± 0.0 | 43.0k ± 3.9k | 114.6k ± 2.3k |
| **NGU(N=32)** | **19.6 ± 0.1** | 465.8k ± 84.9k | 532.8 ± 16.5 | 44.6k ± 1.2k | 68.7k ± 11.1k |

**The Pong row is the paper's cleanest conditioning result and belongs in any report on
conditioned policies.** A single fixed exploration weight (`β = 0.3`, no index input)
produces a **−9.4**, well below the −21-to-+21 midpoint and far below human 14.6:
*"NGU(N=1) catastrophically fails to learn to perform well. Here is where NGU(N=32)
solves this issue: the exploitative policy learned by the agent is able to reliably
learn to play the game."* The conditioned family recovers 29 points of score at the cost
of 32 input bits.

**And the honest counterweight, printed in the same paragraph:** `NGU(N=32)` loses to
plain R2D2 on Breakout (532.8 vs 837.7) and Beam Rider (68.7 k vs 188.2 k), and the
authors attribute this to **cross-member interference in the shared representation**,
proposing *"non-shared representations between mixtures"* as the fix. That proposal is
one of the threads Agent57 picks up.

**Atari-57 aggregate.** Median human-normalised score **1354.4 %** (§4.2; the abstract
prints **1344.0 %** — an internal inconsistency, record both), vs. Nature DQN 95 %,
IMPALA 191.8 %, R2D2 **1920.6 %**, R2D2-with-Retrace 1451.8 %. Above human on **51 of
57** games. So NGU trades aggregate median against hard-exploration coverage — a
trade Agent57 is explicitly built to remove.

**Ablation table (Table 3, `NGU(N=32)`, 8 games, 3 seeds).**

| Variant | Pong | QBert | Breakout | SpaceInv | BeamRider | MR | Pitfall! | PrivateEye |
|---|---|---|---|---|---|---|---|---|
| **NGU(N=32)** | 19.6 ± 0.1 | 465.8k | 532.8 | 44.6k | 68.7k | 10.4k ± 1.6k | **8.4k ± 4.5k** | **100.0k ± 0.4k** |
| N = 2 | 20.6 ± 0.1 | 457.7k | 576.0 | 48.0k | 71.8k | 11.1k ± 1.4k | **−1.6 ± 0.9** | 40.6k |
| N = 8 | 20.0 ± 0.3 | 481.8k | 524.1 | 43.1k | 64.0k | 7.8k ± 0.3k | **−1.9 ± 0.4** | 38.5k |
| N = 16 | 17.2 ± 1.0 | 444.2k | 549.0 | 46.4k | 73.9k | 9.5k ± 0.8k | 5.0k ± 1.2k | 52.0k |
| CMR = 0.5 | 19.0 ± 0.3 | 502.9k | 516.9 | 40.3k | 74.5k | **12.0k ± 0.8k** | 5.1k ± 2.4k | 58.8k |
| β = 0.2 | 20.3 ± 0.2 | 350.1k | 525.0 | 43.9k | 75.6k | 6.9k ± 0.1k | 3.3k ± 1.4k | 40.6k |
| β = 0.5 | 16.8 ± 1.2 | 480.4k | 451.6 | 40.2k | 62.3k | 11.3k ± 0.5k | 1.3k ± 0.5k | 44.5k |
| w/o RND | 19.7 ± 0.4 | 550.3k | 553.7 | 47.6k | 87.1k | **3.0k ± 0.0k** | 7.7k ± 0.9k | 40.5k |
| w/o `r^e` | −8.4 ± 1.9 | 28.1k | 383.0 | 5.5k | 6.4k | 3.4k ± 0.7k | 600.4 | 7.5k |

Readings the authors give and the numbers support:
- **Family size matters, non-monotonically and mostly on hard exploration.** `N = 2` and
  `N = 8` score **negative** on Pitfall! where `N = 32` scores 8.4 k; on the five dense
  games all `N` are within noise. *"`N = 2` and `N = 8` have lower average human
  normalized score on the set of 3 hard exploration games ... they only achieve
  super-human performance on Montezuma's Revenge."*
- **`β` has an optimum at 0.3**, with 0.2 *"not having highly enough exploratory
  variants"* and 0.5 making *"policies ... too biased towards exploratory behavior"*.
  Table 4 shows this is game-dependent — on Gravitar/Solaris/Venture both 0.2 and 0.5
  are slightly *better*, because those games' learned policies *"focus on exploitation
  rather than extended exploration"*.
- **RND matters only for Montezuma's Revenge** (10.4 k → 3.0 k without it) and is
  actively *harmful* on Pitfall! (7.7 k without vs 8.4 k with, and `NGU(N=1)−RND`'s
  15.2 k is the best Pitfall! score in the paper). Three reasons offered: room aliasing
  in Pitfall!, an on-screen timer as a spurious novelty source, and RND agents'
  tendency to *"keep 'interacting with danger' instead of exploring further"*.
- **The exploration policy alone is a strong prior.** *"even without extrinsic reward
  `r^e`, we can still obtain average superhuman performance on the 5 dense reward games"*
  — Breakout reaches 383 (human 30.5) with **no task reward at all**, because *"the
  exploratory policy learns to survive"*.
- **Dense games are insensitive to all of it** *(all error bars overlapping)*, *"as
  extrinsic rewards become dense, intrinsic rewards ... naturally become less relevant."*

**Controlled setting (§4.1, Random Disco Maze).** A 21×21 pycolab maze, regenerated each
episode, in which **every wall tile's colour is resampled every timestep** so the agent
*"is likely to never see the same state twice"* — a purpose-built adversary for
novelty bonuses. No extrinsic reward. With the learned inverse-dynamics embedding, NGU
(`N = 1`, `β = 0.3`) *"learns a strategy that resembles depth-first search: it explores
as far as possible along each branch before backtracking (often requiring backtracking a
few dozen steps)"*. With a **fixed random projection** instead of a learned embedding,
and with an **RND baseline**, that behaviour does not appear; both merely learn to avoid
walls, because *"simply oscillating between two states will produce different (and
novel) controllable states at every time step."* This is the paper's argument that the
*embedding*, not the memory, is what makes the bonus meaningful.

**Behaviour across family members (Fig. 6).** Evaluating `NGU(N=32)` at `β_0 = 0` versus
`β_31 = 0.3` gives three regimes: on Q\*Bert the two are near-identical (*"common in
many games"*); on Pitfall! and Beam Rider they are quantitatively different behaviours,
with the exploitative member benefiting from the exploratory member's learning (R2D2
*"never achieves a positive score"* on Pitfall!); and on Montezuma's Revenge the
**exploratory member outscores the exploitative one**, because consolidating the
knowledge needs *"extremely long-term credit assignment ... many non-greedy and
sometimes irreversible actions"*. That last case is another thread Agent57 picks up.

### 4.6 Relevance to this project

- **This is the precedent for conditioning a policy on an internal control setting
  rather than on a task label.** Every other paper in this batch conditions on
  *something about the environment* (task ID, description, inferred task belief). NGU
  conditions on *how the agent should currently behave*. For a project whose modulator
  is meant to represent an internal state, that is the closer structural analogue.
- **The operator is a one-hot concatenation, and the paper works anyway.** Any report
  claim that "modulation in RL means FiLM" is refuted by the highest-profile
  conditioned-policy result of the era using the simplest possible operator. Cite this
  as the low-bar baseline.
- **The conditioning benefit comes from weight sharing, and is demonstrated so.** The
  CMR ablation is the mechanism evidence: `CMR = 0.5` (more data sharing) *hurts*, so
  the transfer between regimes is happening in the trunk. Directly relevant to any
  project design where one network must host several behavioural modes.
- **Interference is real and is reported.** Two dense games regress below the
  unconditioned base agent, and the authors' own diagnosis is shared-representation
  interference, with *"non-shared representations between mixtures"* proposed as the
  fix. If the project's report has a section on the costs of conditioning, this is the
  citation — from a paper that is otherwise a success story.
- **The `(β, γ)` anti-correlation is a reusable design idea**, independent of Atari:
  a regime that acts on a dense, low-variance signal can afford a short horizon; the
  regime optimising the real objective should be as far-sighted as possible. If the
  project ever indexes a policy family by "how strongly does the internal signal
  count", pairing the index with a horizon is precedent-backed.
- **Caution on the numbers.** 3 seeds; the Atari-57 median is *lower* than the base
  agent's; and the abstract and §4.2 disagree on that median (1344.0 % vs 1354.4 %).

### 4.7 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Learn a *range* of directed exploratory policies. Episodic-memory intrinsic reward via `k`-nearest neighbours over recent experience, encouraging repeated revisiting of all states. Self-supervised **inverse dynamics** trains the embedding so novelty is biased toward *what the agent can control*. **UVFA** used to learn many exploration policies in the same network with different exploration/exploitation trade-offs; transfer flows from exploratory to exploitative members. Compatible with distributed RL. *"doubles the performance of the base agent in all hard exploration in the Atari-57 suite"*, median human-normalised score **1344.0 %**; first algorithm to get non-zero reward on Pitfall! (mean 8,400) without demonstrations or hand-crafted features. |
| 1 | **Introduction** | Maintaining exploration requires infinitely-often visitation; `ε`-greedy and Boltzmann are exponentially inefficient though fine in dense-reward settings. Existing intrinsic rewards decay — *"after the novelty of a state has vanished, the agent is not encouraged to visit it again, regardless of the downstream learning opportunities"* — and forward-model bonuses are expensive and brittle, requiring *"careful calibration between the speed of the learning algorithm and that of the vanishing rewards"*. Proposal: **jointly learn separate exploration and exploitation policies from the same network** via UVFA; the exploratory policies act as auxiliary tasks that keep the shared architecture developing even with no extrinsic reward. Novelty = episodic (fast, memory-based) × life-long (slow, gradient-based, **multiplicative modulation**). Three contributions: the combined bonus, *"a family of policies that separate exploration and exploitation using a conditional architecture with shared weights"*, and scalability evidence. Delimitation from Savinov et al. (not navigation-specific, adds long-term novelty, separates the two policies), Stanton & Clune (no privileged info), Beyer et al. (shares **weights**, not just a replay buffer; no exact counts). |
| 2 | **The Never-Give-Up Intrinsic Reward** | Augmented reward `r_t = r^e_t + β r^i_t`; performance always measured on `r^e` only. Three required properties (fast within-episode discouragement, slow across-episode discouragement, ignore uncontrollable aspects). Eq. 1 combines episodic bonus with the clipped life-long modulator, `L = 5`. **Embedding network**: Siamese inverse-dynamics model, `p(a\|x_t,x_{t+1}) = h(f(x_t), f(x_{t+1}))`, trained by maximum likelihood. **Episodic memory**: slot-based, emptied each episode, holds `{f(x_0),…,f(x_{t−1})}`. Eq. 2 the `1/√n` pseudo-count with `k`-NN kernel sum and floor `c = 0.001`; the Dirac-kernel remark on generalisation. Eq. 3 the inverse kernel with running distance normalisation `d²_m`, `ε = 10⁻³`. **Life-long modulator**: RND, `α_t = 1 + (err(x_t) − µ_e)/σ_e`. |
| 3 | **The Never-Give-Up Agent** | Intrinsic rewards can turn the MDP into a POMDP; mitigated by (a) **feeding the intrinsic reward to the agent as an input** and (b) a recurrent internal state over the episode's inputs. Base agent **R2D2**. The NGU bonus does not vanish, so the exploratory drive *"cannot be easily turned off"* — hence an explicit exploitative member. **Proposed architecture**: UVFA `Q(x,a,β_i)` over `r^{β_i}_t = r^e_t + β_i r^i_t`, `N` discrete values with `β_0 = 0` and `β_{N−1} = β`; acting greedily w.r.t. `Q(x,a,0)` switches exploration off. Rationale for `N > 2`: smoothly-changing policies train more efficiently. Dueling architecture with an LSTM after a CNN; **one-hot `β_i`, previous action, previous intrinsic and extrinsic reward concatenated**. **RL loss**: transformed **Retrace** double Q-learning. **`γ_i` paired with `β_i`**, `γ_0 = 0.997` (exploitative, far-sighted) down to `γ_{N−1} = 0.99` (exploratory, short-sighted), justified by the intrinsic reward being dense and small-range. **Distributed training**: 256 actors, prioritised distributed replay, one learner. |
| 4 | **Experiments** | Roadmap: controlled gridworld analysis, then Atari. |
| 4.1 | Controlled Setting Analysis | **Random Disco Maze** (pycolab): 21×21 maze regenerated each episode, four actions, fully observable, episode ends on wall contact, **wall colours resampled every timestep from 5 colours** — a continual stream of spurious novelty. No extrinsic reward. NGU (`N=1`, `β=0.3`) with the learned embedding produces depth-first-search-like exploration with long backtracks; random-projection embedding and an RND baseline do not, learning only to avoid walls, since oscillating between two cells already yields novel states. |
| 4.2 | Atari Results | Same setting and data budget as R2D2 (35 B frames, 3 seeds); two extra in-house baselines (R2D2 with Retrace; R2D2 with Retrace + RND) because *"comparing distributed and non-distributed methods is in general difficult"*. Hyperparameters for controllable-state size, clipping `L` and `k` chosen on `NGU(N=1)` on Montezuma's Revenge and Pitfall! (App. B) then frozen. Ablations on 8 games (5 dense + 3 hard). Findings: CMR 0.5 slightly harms hard exploration ⇒ **weights, not data, carry the transfer**; larger `N` helps hard exploration; `β = 0.3` optimal on average; RND greatly beneficial on hard exploration; dense games insensitive to everything except removing `r^e`; the bonus alone gives superhuman play on the 5 dense games. Table 1 (6 hard-exploration games), Table 2 (5 dense games), Fig. 4 (mean/median HNS), Fig. 5 (Pitfall! and Montezuma's learning curves; NGU(N=32) explores **46 rooms per episode**, crossing **14 rooms before the first extrinsic reward**). RND analysis on Pitfall!: room aliasing, the on-screen timer as spurious novelty, and RND's "interacting with danger" failure. Atari-57 median **1354.4 %**, above human on **51/57**, below R2D2's 1920.6 %. Fig. 6 analysis of family members at `β_0` vs `β_31`. |
| 5 | **Conclusions** | Effective on both sparse and dense reward; high scores on all Atari hard-exploration games while maintaining broad performance. |
| A | **Evaluation Setup** | R2D2-identical evaluation worker. Learner: sample `(r_t, r^i_t, x, a, γ_i)` sequences; train Retrace on `(r_t, x, a)` with `r^i_t` **sampled from replay because it is a network input**; last 5 frames per sequence train the action-prediction net (and RND predictor). Actor/evaluator loop. Distributed: 1 GPU learner at ~5 updates/s on 64 × length-80 sequences; each actor ~260 env steps/s; actor `j` assigned `β_h`, `h = j mod N − 1`, acting `ε`-greedily. **The `β_i` sigmoid schedule.** Replay stores length-80 sequences overlapping by 40, never crossing episode boundaries, **plus the `β_i` used and the initial recurrent state**; prioritisation by a max/mean mixture of TD errors, exponent `η = 1.0`. **Eq. 4, the `γ_i` schedule**, log-spaced in `1−γ`; `γ_max = 0.997`, `γ_min = 0.99`. **A.1** the intrinsic-reward algorithm and its notation. **A.2** complexity analysis (constant space). |
| B | Ablations for NGU(N=1) | **B.1** size of controllable states, **B.2** number of nearest neighbours, **B.3** clipping factor `L` — Pitfall! robust, Montezuma's Revenge prefers the highest clipping. These three hyperparameters were chosen here and then frozen for everything else. |
| C | Ablations for NGU(N=32) | **C.1** Table 3, the 8-game ablation grid (`N`, CMR, `β`, RND, `r^e`). Notes: best Montezuma's Revenge comes from **non-zero CMR**; `N = 2` and `N = 8` under-perform on hard exploration; `β = 0.2`/`0.5` still beat RND/R2D2/R2D2-Retrace/R2D2+RND on Pitfall! and Private Eye; Private Eye's score gaps are inflated by two ~30 k rewards; Breakout scores well with **no extrinsic reward** because surviving suffices. **C.2** Table 4 — on Gravitar/Solaris/Venture both `β = 0.2` and `β = 0.5` are slightly *better* than 0.3, because those policies are exploitation-dominated. |
| D | Algorithm Computation Comparison | Table 5; notes that actor-count changes both learner throughput and how off-policy the replayed data is, so compute comparisons remain hard. |
| E | Details on the Retrace Algorithm | The Retrace(λ) loss as used. |
| F | Hyperparameters | **F.1** selection procedure. **F.2** common table: 3 seeds, **CMR 0.0, N = 32**, Adam (lr 1e-4 for R2D2, 5e-4 for RND and action prediction, clip norm 40), **discount for `r^i` 0.99 / for `r^e` 0.997**, batch 64, trace length 80, replay period 40, Retrace `λ = 0.95`, R2D2 reward transform `sign(x)(√(\|x\|+1)−1)+0.001x`, **episodic memory capacity 30000 (ring buffer)**, `β = 0.3`, kernel `ε = 1e-4`, **`k = 10` neighbours**, cluster distance `ξ = 0.008`, pseudo-count `c = 0.001`, max similarity `s_m = 8`, replay priority exponent 0.9, replay capacity 5e6, target-network period 1500, embedding target updated once per episode, **RND clipping `L = 5`**, evaluation/target `ε = 0.01`. **F.3** Disco Maze overrides. **F.4** Atari pre-processing (standard DQN, **no frame stacking**). **F.5** hyperparameter ranges. |
| G | Detailed Atari Results | Per-game scores across all 57 games. |
| H | Network Architectures | **H.1** embedding network — DQN conv stack (32@8×8/4, 64@4×4/2, 64@3×3/1) → FC 32 per Siamese branch → FC 128 → FC 18 → softmax. **H.2** RND — same conv stack → FC 128, for both the random and predictor networks. **H.3** R2D2 agent — conv torso → FC 512 → **LSTM 512** → dueling head (FC 512 → 1 value; FC 512 → 18 advantage; mean-subtracted). Figures only, no prose. |
| I | Controllable States | **I.1** probing whether player `(x,y)`, room id, level and key count are decodable from the learned 32-dim controllable state. **I.2** Montezuma's Revenge with **hand-crafted** oracle controllable states, used to analyse the long-horizon credit-assignment failure noted in §4.2. **I.3** the hand-crafted feature definitions, extracted from game RAM. |

---
