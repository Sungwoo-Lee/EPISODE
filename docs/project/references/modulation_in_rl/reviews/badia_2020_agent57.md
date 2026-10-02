---
title: "Agent57: Outperforming the Atari Human Benchmark"
slug: badia_2020_agent57
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_modrl_classics.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 5. Badia et al. 2020b — *Agent57: Outperforming the Atari Human Benchmark*

**PDF:** `docs/project/references/modulation_in_rl/sources/Badia et al. 2020 - Agent57 - Outperforming the Atari human benchmark.pdf`
**Venue as printed:** **none.** This PDF carries **no venue line, no proceedings footer, no acceptance note** — only the arXiv stamp `arXiv:2003.13350v1 [cs.LG] 30 Mar 2020`. It is typeset in the ICML template (author block with `*Equal contribution ¹DeepMind`, `Correspondence to:`), but the copyright/proceedings line that an ICML camera-ready carries is absent. **Cite the held copy as a 2020 preprint**; if the merged review needs the published venue, it must come from a source outside this PDF.
**Authors:** Adrià Puigdomènech Badia\*, Bilal Piot\*, Steven Kapturowski\*, Pablo Sprechmann\*, Alex Vitvitskyi, Daniel Guo, Charles Blundell — DeepMind (\* equal contribution).
**Builds directly on:** [Never Give Up](#4-badia-et-al-2020a--never-give-up-learning-directed-exploration-strategies-ngu) (paper #4 above). Read that section first.

### 5.1 Plain-English entry point

Atari-57 had a long-standing embarrassment: every leading agent was superhuman on
about fifty games and *catastrophically bad* on the remaining five or six. The failures
clustered into two kinds. **Hard exploration** — *Montezuma's Revenge*, *Pitfall!* —
where reward is so sparse that random behaviour never finds it. And **long-term credit
assignment** — *Skiing*, *Solaris* — where a decision pays off thousands of frames
later, so an agent that discounts the future even slightly cannot see the connection.
Never Give Up (paper #4) solved the first kind and *lost ground* on the aggregate.

Agent57 keeps NGU's design — one network hosting 32 policies indexed by an
exploration weight — and makes **three changes**, each ablated:

1. **Split the value function into two networks.** One learns the value of the task
   reward, one learns the value of the curiosity bonus, and they are combined
   afterwards by the very mixing weight that indexes the family. NGU had asked one
   network to represent both, and it broke when the two rewards had very different
   scales.
2. **Let a small learning algorithm pick which family member to run.** A bandit —
   the simplest kind of adaptive chooser — watches which index earns the most **task**
   score lately and biases the agent toward it, per episode, separately on each of the
   256 parallel workers. Early in training that tends to be an exploratory index; later
   it shifts to an exploitative one. This also lets the agent pick its own **discount
   factor per game** rather than having one hard-coded for all 57.
3. **Double the truncation window** used when propagating gradients back through the
   recurrent network — from 80 steps to 160.

**Headline result.** The first agent above the human benchmark on **all 57** games —
capped human-normalised score **100.00** and **57/57 games above human**, against 51–54
for NGU, R2D2 and MuZero. The last game to fall, *Skiing*, needed **78 billion frames**
and a discount of 0.9999.

**Why the project cares.** Agent57 is where the hyperparameter-conditioned policy
becomes a **closed loop**: the index is still concatenated as a one-hot, but it is now
*also* a multiplicative scalar in the output combination, and it is *chosen online by a
learner rather than assigned*. Both of those are mechanism changes a report on
conditional modulation should get exactly right, and both are easy to misdescribe.

### 5.2 Fixed extraction block

| Field | Value |
|---|---|
| **Venue + year** | **Unstated in the PDF.** ICML-template preprint, `arXiv:2003.13350v1`, 30 Mar 2020. |
| **RL algorithm** | **NGU / R2D2** lineage: distributed recurrent DQN, 256 actors, one GPU learner, prioritised FIFO replay, **transformed Retrace** losses. Trace length **160** (NGU: 80), replay period **80** (NGU: 40). |
| **Conditioning signal** | A **one-hot vector `j` over `N = 32` indices**, each naming a **`(β_j, γ_j)` pair** — Agent57's own phrasing is the clearest statement of NGU's mechanism in either paper: *"NGU trains a recurrent neural network `Q(x, a, j; θ)`, where **`j` is a one-hot vector indexing one of `N` implied MDPs (in particular `(β_j, γ_j)`)**"*. `β_j` weights the curiosity bonus (sigmoid ladder, `β_0 = 0`, `β_31 = 0.3`); `γ_j` is the discount — **and Agent57 widens its range from NGU's `[0.99, 0.997]` to `[0.99, 0.9999]`**, which is what makes *Skiing* learnable. **New vs NGU: `j` is selected online by a bandit, not assigned to an actor.** |
| **What is modulated** | The **Q-network**, now **two networks**: an extrinsic value network `θ^e` and an intrinsic value network `θ^i` *with identical architecture*. **Both are conditioned on `j`.** The intrinsic-reward machinery (episodic memory, inverse-dynamics embedding, RND) remains unconditioned. |
| **The operator** | **Two operators, and the distinction matters.** (i) **Concatenation of a one-hot**, exactly as in NGU — App. E lists the network's per-step inputs verbatim as `(x_s, r^e_{s−1}, r^i_{s−1}, j, a_{s−1}, h_{s−1})`, so `j` enters as a plain input beside the previous rewards, previous action and recurrent state. (ii) **A scalar multiplicative gain at the output**: `Q(x,a,j;θ) = Q(x,a,j;θ^e) + β_j·Q(x,a,j;θ^i)`. That second use is the closest thing to affine modulation in either NGU or Agent57 — but it is **one scalar applied to a whole value stream**, not a per-unit `(γ, β)` on a hidden layer, and the scalar is a **fixed hyperparameter read off the index**, not produced by a modulator network. Describing Agent57 as "FiLM-like" would be wrong; describing it as "a hyperparameter-indexed two-stream value function with a scalar output mix" is right. |
| **Granularity and placement** | The one-hot: **one site, whole-vector**, at the recurrent core's input, in **each** of the two networks. The scalar `β_j`: **one site, at the output**, applied to the entire intrinsic Q-vector over actions. Nothing per-unit or per-layer anywhere. |
| **Ablated against no-conditioning?** | **Each of the three changes is ablated separately** on a 10-game "challenging set", with per-game score tables (App. H.1) and CHNS progression figures. Removing the separate networks costs Agent57 *"greater than 20 %"* CHNS; the meta-controller alone adds *"close to 20 % CHNS"* to R2D2. The identity-vs-`h`-transform mixing choice is ablated and found **not to matter**. **Not ablated:** one-hot concatenation vs. any other injection mechanism — inherited unexamined from NGU. |
| **Reported instability** | **Yes, and it is the paper's stated motivation for change #1.** Verbatim: *"In practice, NGU can be unstable and fail to learn an appropriate approximation of `Q*_{r_j}` for all the state-action value functions in the family, even in simple environments. This is especially the case when the scale and sparseness of `r^e` and `r^i` are both different, or when one reward is more noisy than the other."* Demonstrated on a purpose-built 15×15 gridworld (§5.5). Second instability: a **fixed** high discount `γ = 0.9999` across all games *"renders the algorithm very unstable and damages its end performance"* — the bandit exists partly to avoid committing to it. Third: longer backprop windows are *"initially slower, but result in better overall stability"*. |
| **Single-task or multi-task** | **Single-task, per game**, like NGU. The family indexes *objectives on one task*. |
| **Claim strength** | **Ablated** — three independent ablations plus a controlled gridworld diagnostic, 3 seeds for ablations, **6 seeds for Agent57 itself**, full per-game score tables. Strongest evidence base in this batch. |

### 5.3 Phase 1 — Foundational overview

**The problem, restated with numbers.** No single algorithm exceeded 100 % HNS on all
57 games with one hyperparameter set: MuZero managed 51 games, R2D2 52 — and in the
games they miss, *"they often fail to learn completely."* Two failure families are
named: **long-term credit assignment** (*Skiing*, *Solaris*) and **exploration**
(*Montezuma's Revenge*, *Pitfall!*).

**Why NGU was the right base and the wrong endpoint.** NGU's family-of-policies design
already covers exploration. But it (a) trains **all family members equally**,
*"regardless of their contribution to the learning progress"*, and (b) asks **one
network** to represent value functions whose magnitudes differ by orders of magnitude
across the family — which the authors show breaks.

**The three fixes, in one line each.**
- *Separate value networks*: give the extrinsic and intrinsic returns their own network
  and their own optimiser state, so each can adapt to its reward's scale and variance;
  recombine linearly with `β_j`. Proved (App. B) to optimise the same objective as NGU's
  single network under plain gradient descent — **so the change is purely a
  parameterisation change, not an objective change.** That is what makes it a clean
  architectural result.
- *Meta-controller*: a per-actor non-stationary bandit whose arms are the 32
  `(β_j, γ_j)` pairs and whose reward is the **undiscounted extrinsic episode return**.
  Two benefits: a training curriculum (exploratory early, exploitative late), and
  automatic **per-task discount selection** at evaluation.
- *Longer BPTT window*: 80 → 160.

**Initial takeaway.** A conditioned family of policies is not just an architecture — it
is a **space to be searched during training**. Agent57's contribution over NGU is
mostly about *how the index is chosen and how the conditioned outputs are combined*,
not about how the index is injected. The injection stayed a one-hot concatenation
through both papers and through the result that closed Atari-57.

### 5.4 Phase 2 — Graduate-level deep dive

#### 5.4.1 The split value function, and the proof it is equivalent

**The parameterisation.**

$$
Q(x,a,j;\theta) \;=\; Q(x,a,j;\theta^{e}) \;+\; \beta_j\, Q(x,a,j;\theta^{i}),
\qquad \theta = \theta^{e}\cup\theta^{i},
$$

where `θ^e` and `θ^i` parameterise **two networks of identical architecture**, both
still taking `j` as an input. Training: the *same* replayed sequence, **two** transformed
Retrace losses — an extrinsic one on rewards `r^e` and an intrinsic one on rewards
`r^i` — but **a single shared target policy**

$$
\pi(x) \;=\; \arg\max_{a\in\mathcal{A}} \; Q(x,a,j;\theta).
$$

The greedy policy is defined on the *combined* value, so the two streams are coupled
through the policy even though their losses are separate.

**The equivalence argument (App. B), in full.** Let `G(·)` denote the greedy operator
and `T^π_r` the Bellman evaluation operator for reward `r` under policy `π`. Single-value
iteration on `r = r^e + βr^i` is

$$
\pi_k = G(Q_k),\qquad Q_{k+1} = T^{\pi_k}_{r} Q_k .
$$

The split scheme is

$$
\tilde\pi_k = G\big(Q^{e}_{k} + \beta Q^{i}_{k}\big),\qquad
Q^{i}_{k+1} = T^{\tilde\pi_k}_{r^{i}} Q^{i}_{k},\qquad
Q^{e}_{k+1} = T^{\tilde\pi_k}_{r^{e}} Q^{e}_{k}.
$$

Define `Q̃_k = Q^e_k + β Q^i_k` and expand, using that `T^π_r Q = r + γP^π Q` is **affine
in `r` and linear in `Q`** for a *fixed* `π`:

$$
\begin{aligned}
\tilde Q_{k+1} &= Q^{e}_{k+1} + \beta Q^{i}_{k+1}\\
&= T^{\tilde\pi_k}_{r^{e}} Q^{e}_{k} + \beta\, T^{\tilde\pi_k}_{r^{i}} Q^{i}_{k}\\
&= \Big(r^{e} + \gamma P^{\tilde\pi_k} Q^{e}_{k}\Big) + \beta\Big(r^{i} + \gamma P^{\tilde\pi_k} Q^{i}_{k}\Big)\\
&= \big(r^{e} + \beta r^{i}\big) + \gamma P^{\tilde\pi_k}\big(Q^{e}_{k} + \beta Q^{i}_{k}\big)\\
&= T^{\tilde\pi_k}_{r^{e}+\beta r^{i}}\,\tilde Q_{k} \;=\; T^{\tilde\pi_k}_{r}\,\tilde Q_k .
\end{aligned}
$$

Together with `π̃_k = G(Q̃_k)` this is exactly the single-value iteration scheme on `r`,
so `Q̃_k → Q*_r`. **The step that makes it work is that both streams are evaluated under
the *same* policy `π̃_k`** — if the two streams each used their own greedy policy, the
`P^π` factors would differ and the linearity would fail.

**So why does it help, if the objective is identical?** The paper's answer is entirely
about optimisation, and is worth quoting because it is the transferable claim: *"we
allow each network to adapt to the scale and variance associated with their
corresponding reward, and we also allow for the associated optimizer state to be
separated for intrinsic and extrinsic state-action value functions."* Two separate Adam
states, two separate weight scales. Same fixed point, different conditioning of the
optimisation problem.

**The transformed variant.** With the Pohlen et al. value-transform `h`
(the `sign(x)(√(|x|+1) − 1) + 0.001x` squashing used throughout R2D2),

$$
Q(x,a,j;\theta) \;=\; h\Big(h^{-1}\big(Q(x,a,j;\theta^{e})\big) + \beta_j\, h^{-1}\big(Q(x,a,j;\theta^{i})\big)\Big),
$$

with the same equivalence proved in App. B. Agent57 **uses the identity split**
(`h = id` in the mix) while still using **transformed Retrace losses**. App. H.3 ablates
the choice and finds no difference, with a clean argument: at `β = 0` and `β ≫ 1` the
two forms share an `argmax` because `h^{-1}` is strictly increasing, so they differ only
at intermediate `β`; there *"the value iteration scheme approximates a state-action
value function that is optimal with respect to a **non-linear** combination of the
intrinsic and extrinsic rewards"*. The paper's summary is quotable: *"The only real
important thing is that a combination between extrinsic and intrinsic happens whether
it is linear or not."*

#### 5.4.2 The meta-controller

**Setup.** `N = 32` arms, arm `j` ↔ the policy indexed by `(β_j, γ_j)`. At the start of
episode `k` the meta-controller draws `J_k`; actor `l` then acts `ε_l`-greedily w.r.t.
`Q(x, a, J_k; θ_l)` **for the whole episode**. The bandit's reward is the **undiscounted
extrinsic episode return** `R^e_k(J_k)` — note carefully: **the intrinsic reward is not
in the meta-controller's objective.** The bandit optimises the thing the benchmark
measures, and uses the exploration index only as a means.

**Why per-actor rather than global.** *"each actor follows a different `ε_l`-greedy
policy which may alter the choice of the optimal arm."* An actor with high `ε_l` is
effectively a noisier policy and may prefer a different family member. So there are 256
independent bandits.

**Why sliding-window UCB.** `R^e_k(J_k)` is **non-stationary** — the agent improves, so
an arm's value changes — and *"a classical bandit algorithm such as UCB ... will not be
able to adapt."* Standard UCB uses

$$
A_k = \arg\max_{a}\ \hat\mu_{k-1}(a) + \beta\sqrt{\frac{\log(k-1)}{N_{k-1}(a)}},
\qquad
\hat\mu_{k}(a) = \frac{1}{N_{k}(a)}\sum_{m=0}^{k-1} R_k(a)\mathbb{1}\{A_m = a\}.
$$

The sliding-window version restricts both count and mean to the last `τ` episodes,
`N_k(a,τ) = Σ_{m = 0∨k−τ}^{k−1} 1{A_m = a}` and `µ̂_k(a,τ)` correspondingly. Agent57
then uses a **simplified** form with `ε_UCB`-greedy exploration and, notably, a
**bonus term with the logarithm dropped**:

$$
A_k =
\begin{cases}
k & 0 \le k \le N-1 \quad \text{(one forced pull per arm)}\\[4pt]
\arg\max_{0\le a\le N-1}\ \hat\mu_{k-1}(a,\tau) + \beta\sqrt{\dfrac{1}{N_{k-1}(a,\tau)}} & U_k \ge \epsilon_{\text{UCB}}\\[8pt]
Y_k \sim \mathrm{Unif}\{0,\dots,N-1\} & U_k < \epsilon_{\text{UCB}}
\end{cases}
$$

with `U_k ~ Unif[0,1]`. Dropping `log(k−1∧τ)` makes the exploration bonus depend only on
the within-window pull count — a constant-scale bonus rather than a growing one, which
is the sensible choice when the window is fixed and the horizon is effectively infinite.

**Actor vs. evaluator.** The actors sample from the bandit; the **evaluator** takes the
greedy arm `arg max_a µ̂_{k−1}(a)` and reports the average over 5 episodes before
switching mode. **This is how the discount factor gets selected per game**: with a wide
`{γ_j}` range and `β_j ≈ 0` at the exploitative end, the evaluator's greedy arm *is* a
per-task discount choice.

**Hyperparameter inconsistency to record.** §4 states *"a window size of `τ = 160`
episodes and `ε = 0.5` for the actors and a window size of `τ = 3600` episodes and
`ε = 0.01`"* (for the evaluator), while Table 3 lists **"Bandit window size 90, Bandit
UCB β 1, Bandit ε 0.5"** and Table 4's search range is `τ ∈ {160, 224, 320, 640}`. The
160/90 discrepancy is unresolved in the PDF; report as printed.

#### 5.4.3 The widened `(β, γ)` ladders

`β` is unchanged from NGU:

$$
\beta_j = \begin{cases}
0 & j = 0\\
\beta = 0.3 & j = N-1\\
\beta\cdot\sigma\!\big(10\tfrac{2j-(N-2)}{N-2}\big) & \text{otherwise}
\end{cases}
$$

`γ` is **new and piecewise in three regimes**, with `γ_0 = 0.9999`, `γ_1 = 0.997`,
`γ_2 = 0.99`, `N = 32`:

$$
\gamma_j = \begin{cases}
\gamma_0 & j = 0\\[2pt]
\gamma_1 + (\gamma_0-\gamma_1)\,\sigma\!\big(10\tfrac{2i-6}{6}\big) & j \in \{1,\dots,6\}\\[2pt]
\gamma_1 & j = 7\\[2pt]
1 - \exp\!\Big(\dfrac{(N-9)\log(1-\gamma_1) + (j-8)\log(1-\gamma_2)}{N-9}\Big) & \text{otherwise}
\end{cases}
$$

(reproduced as printed, including the index `i` appearing in the second branch where `j`
is expected). Read structurally: **indices 0–7 densely sample the very-far-sighted
region between `γ = 0.997` and `γ = 0.9999`** (effective horizons 333 → 10 000 steps),
and indices 8–31 fall back to NGU's log-spaced ladder from 0.997 down to 0.99. The
extra resolution at the far-sighted end is entirely in service of *Skiing* and
*Solaris*. NGU's range was `[0.99, 0.997]`; Agent57's is `[0.99, 0.9999]`.

### 5.5 The gridworld diagnostic — where NGU's single network breaks

Purpose-built and worth describing precisely, because it is the cleanest published
demonstration of a **conditioning-induced representational conflict**.

**"Random coin":** an empty 15×15 room; a coin and the agent are placed at random each
episode; four actions; ≤ 200 steps; stepping on the coin gives reward 1 **and ends the
episode**.

**Why the termination is the whole point.** The extrinsic-optimal behaviour is *"taking
the shortest path towards the coin (obtaining an extrinsic return of one)"*. The
augmented-optimal behaviour is *"avoiding the coin and visiting all remaining states
(obtaining an extrinsic return of zero)"* — because collecting the coin **ends the
episode and cuts off the curiosity income**. So the family's two ends want *maximally
opposed* behaviours, and their value functions differ by orders of magnitude. The paper
notes the effect *"would not occur if the episode did not terminate after collecting the
coin"*, in which case *"exploratory and exploitative policies would be allowed to be
very similar"*.

**Result (Fig. 5, 150 M frames).** *"the exploitative policy in NGU struggles to solve
the task as intrinsic motivation reward scale increases. As we increase the scale of the
intrinsic reward, its value becomes much greater than that of the extrinsic reward. As a
consequence, the conditional state-action value network of NGU is required to represent
very different values depending on the `β_j` we condition on. This implies that the
network is increasingly required to have more flexible representations. Using separate
networks dramatically increases its robustness to the intrinsic reward weight."*

**The Atari analogue.** *Surround* — *"as the player makes progress in the game, they
have the choice to surround the opponent snake, receive a reward, and start from the
initial state, or keep wandering around without capturing the opponent, and thus
visiting new states"* — the same structure. NGU scores *"on par with a random policy"*
there; with separate networks it *"reaches a score that is nearly optimal"*. App. H.1
shows the magnitude: `NGU` **−7.57 ± 0.05** vs `NGU sep. nets` **9.77 ± 0.23** (optimal
10).

**Generalise the lesson, because it is the one most transferable to this project.** When
a single conditioned network must output quantities whose *magnitudes* differ sharply
across the conditioning range, conditioning alone is not enough — the network spends
capacity on scale rather than on structure. The fix here was **structural separation
plus a scalar recombination**, not a stronger modulation operator.

### 5.6 Results, as printed

**Table 1 — Atari-57 aggregate.** 3 seeds for baselines, **6 seeds for Agent57**;
undiscounted returns, windowed mean over 50 episodes, maximum over training reported.
`CHNS = max{min{HNS, 1}, 0}` — capped human-normalised score, which *"puts an emphasis
on the games that are below the average human performance benchmark"*.

| Statistic | **Agent57** | R2D2 (bandit) | NGU | R2D2 (Retrace) | R2D2 | MuZero |
|---|---|---|---|---|---|---|
| **Capped mean (CHNS)** | **100.00** | 96.93 | 95.07 | 94.20 | 94.33 | 89.92 |
| **Games > human** | **57** | 54 | 51 | 52 | 52 | 51 |
| Mean HNS | 4766.25 | 5461.66 | 3421.80 | 3518.36 | 4622.09 | **5661.84** |
| Median HNS | 1933.49 | 2357.92 | 1359.78 | 1457.63 | 1935.86 | **2381.51** |
| 40th percentile | 1091.07 | **1298.80** | 610.44 | 817.77 | 1176.05 | 1172.90 |
| 30th percentile | 614.65 | **648.17** | 267.10 | 420.67 | 529.23 | 503.05 |
| 20th percentile | **324.78** | 303.61 | 226.43 | 267.25 | 215.31 | 171.39 |
| 10th percentile | **184.35** | 116.82 | 107.78 | 116.03 | 115.33 | 75.74 |
| 5th percentile | **116.67** | 93.25 | 64.10 | 48.32 | 50.27 | 0.03 |

**Read the percentile ladder, not the mean.** Agent57 is **beaten on mean and median**
by both MuZero and R2D2 (bandit), and the paper says so plainly: MuZero *"obtains the
highest uncapped mean and median human normalized scores, but also the lowest capped
scores ... performs remarkably well in some games, such as Beam Rider, where it shows an
uncapped score of 27469 %, but at the same time catastrophically fails to learn in games
such as Venture."* The contribution is at the **bottom of the distribution**: the 5th
percentile is 116.67 for Agent57 and **0.03** for MuZero. Any citation of Agent57 that
implies it is the best agent on average is wrong; it is the first agent with **no
failures**.

**The meta-controller transfers off NGU.** `R2D2 (bandit)` — plain R2D2 (Retrace) with a
family of discounts `{γ_j}` and the same meta-controller, **no intrinsic reward at
all** — jumps to 96.93 CHNS / 54 games from R2D2 (Retrace)'s 94.20 / 52, and posts the
best mean (5461.66) and median (2357.92) of any agent in the table besides MuZero's.
This is the paper's evidence that **conditioning a value function on a discount index
and letting a bandit choose it is independently useful**, with no exploration bonus in
sight. For a report on conditional modulation this is arguably the cleanest single
result in the batch: the conditioning signal here is *purely a hyperparameter*, the
operator is *purely a one-hot concatenation*, and it buys ~3 points of CHNS and two
games.

**The long tail (Fig. 3).** Agent57 clears human on 51 games in the first **5 billion**
frames; then come the hard-exploration games; *Skiing* falls last, at **78 billion
frames**, and needs a high discount, which *"naturally leads to high variance in the
returns, which leads to needing more data"*. Context the paper supplies: on *Skiing* the
human baseline is **−4336.9**, random is **−17098.1**, and the optimum is **−3272** — a
narrow band, so the benchmark is unusually demanding there.

**Challenging-set ablations (App. H.1, 10 games: Beam Rider, Freeway, Montezuma's
Revenge, Pitfall!, Pong, Private Eye, Skiing, Solaris, Surround, Venture).** Selected
rows as printed:

| Game | R2D2 (Retrace) long trace | R2D2 (Retrace) high `γ` | NGU sep. nets | NGU | Agent57 small trace |
|---|---|---|---|---|---|
| montezuma revenge | 566.67 ± 235.70 | 1664.89 ± 1177.26 | **11539.69 ± 1227.71** | 7619.70 ± 3444.76 | 7966.67 ± 2531.58 |
| pitfall | 0.00 | 0.00 | 15195.27 ± 8005.22 | 2979.57 ± 2919.08 | **16402.61 ± 10471.27** |
| private eye | 21729.91 ± 9571.60 | 22480.31 ± 10362.99 | 63953.38 ± 26278.51 | 43823.40 ± 4808.23 | **80581.86 ± 28331.16** |
| skiing | −10784.13 ± 2539.27 | **−4596.26 ± 601.04** | −19817.99 ± 7755.19 | **−4051.99 ± 569.78** | −4278.86 ± 270.96 |
| solaris | **52500.89 ± 2910.14** | 14814.76 ± 11361.16 | 44771.13 ± 4920.53 | 43963.59 ± 5765.41 | 17254.14 ± 5840.70 |
| **surround** | 10.00 | 10.00 | **9.77 ± 0.23** | **−7.57 ± 0.05** | 9.60 ± 0.20 |
| venture | 2100.00 | 1774.89 ± 83.79 | **3249.01 ± 544.19** | 2228.04 ± 305.50 | 2576.98 ± 394.84 |

(The column headed *"NGU Bandit"* in the PDF is the `NGU` column in the source table;
labels reproduced as printed. The `Surround` row is the separate-networks demonstration:
−7.57 → 9.77.)

**Per-improvement CHNS effects, as stated in prose:**
- **Separate networks**: *"Agent57 suffers a drop of performance that is greater than
  20 % when the separate network improvement is removed"*; *"it does not show worse
  performance on any of the 10 games of the challenging set"*.
- **Meta-controller**: *"enhancing the final performance of R2D2 by close to 20 % CHNS"*;
  *"the benefit on NGU with separate networks is more modest ... a slight overlap in the
  contributions of the separate network parameterization and the use of the
  meta-controller"*, because *"the bandit algorithm can adaptively decrease the value of
  `β` when the difference in scale between intrinsic and extrinsic rewards is large."*
- **BPTT window 80 → 160**: *"initially slower, but results in better overall stability
  and slightly higher final score"*, largest gain on *Solaris*, *"enhances performance on
  all the challenging set games"*.
- **Fixed high discount is not a substitute for the bandit**: `γ = 0.9999` alone beats
  human on *Skiing*, but *"using that hyperparameter across the full set of games renders
  the algorithm very unstable and damages its end performance"* — visible in the table as
  `R2D2 (Retrace) high γ` scoring 14.8 k on *Solaris* against the long-trace variant's
  52.5 k.

**What the bandit actually selects over training (Fig. 8).** Three regimes are named:
a fixed preference for high `γ` on *Skiing*, *"quickly picked up when the agent starts
to learn"*; a fixed preference for high `β` / low `γ` on *Hero*; and a **shift** on
*Gravitar, Crazy Climber, Beam Rider, Jamesbond*, where the agent *"initially chooses to
focus on exploratory policies with low discount, and, as training progresses, ... shifts
into producing experience from higher discount and more exploitative policies."* This
is the paper's evidence for the "natural curriculum" claim, and it is qualitative.

### 5.7 Relevance to this project

- **The corrected description of the NGU/Agent57 mechanism.** Agent57 §2 is the
  authoritative one-sentence statement for both papers: a **one-hot vector `j` indexing
  one of `N` implied MDPs, in particular the pair `(β_j, γ_j)`**, fed to a recurrent
  Q-network alongside the previous action and the previous extrinsic and intrinsic
  rewards. If the report needs one citation for "hyperparameter-conditioned policy",
  quote that sentence. It is **not** an embedding, **not** a modulation, **not** separate
  heads.
- **But `β_j` does double duty in Agent57**, and only in Agent57: as the one-hot index
  *into* the network, and as a **literal scalar multiplier on the intrinsic value
  stream at the output**. Any table row that assigns one mechanism to Agent57 should say
  "concatenation + scalar output mix", not just "concatenation".
- **The strongest instability evidence in this batch, and it is about conditioning.**
  NGU's single conditioned network *"can be unstable and fail to learn ... even in
  simple environments"* when the conditioned outputs differ sharply in scale. If the
  project's report has a section on failure modes of one-network-many-behaviours, this
  is the citation, with the random-coin gridworld as the mechanism and *Surround*
  (−7.57 → 9.77) as the magnitude.
- **The fix was separation, not a better operator.** Agent57 did not respond to a
  conditioning failure by upgrading concatenation to FiLM or a hypernetwork; it split
  the network in two and recombined with a scalar, and proved the objective unchanged.
  That is a directly relevant precedent for any project design choice framed as
  "stronger modulation vs. separate pathways".
- **`R2D2 (bandit)` is the cleanest isolated conditioning result available.** No
  intrinsic reward, no curiosity machinery — just a value network conditioned on a
  discount index with a bandit choosing it, worth ~3 CHNS and two games over its own
  base. Cite it when the claim is "conditioning a value function on a control
  hyperparameter helps, on its own".
- **Closed-loop conditioning.** NGU assigns the index; Agent57 *learns* which index to
  run from the task reward. If the project ever wants a modulator whose setting is
  selected online rather than supplied, the sliding-window-UCB-per-worker design is the
  simplest published instance, and its objective — **undiscounted extrinsic return, not
  the augmented reward** — is the detail that makes it work.
- **Citation hygiene.** The held PDF has **no venue line**; it is `arXiv:2003.13350v1`.
  Also note the internal `τ = 160` vs `90` bandit-window discrepancy and the `i`/`j`
  index typo in the `γ_j` formula.

### 5.8 Appendix: Section-by-Section Backbone

Sections in the paper's original order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | First deep RL agent above the standard human benchmark on **all 57** Atari games. *"we train a neural network which parameterizes a family of policies ranging from very exploratory to purely exploitative"*, plus **an adaptive mechanism to choose which policy to prioritize** and *"a novel parameterization of the architecture that allows for more consistent and stable learning."* |
| 1 | **Introduction** | ALE's three virtues (varied, individually interesting, bias-free). No algorithm exceeds 100 % HNS on all 57 with one hyperparameter set — MuZero 51, R2D2 52 — and where they fail *"they often fail to learn completely"*. Two named failure families: **long-term credit assignment** (Skiing, Solaris) and **exploration** (Montezuma's Revenge, Pitfall!). Related work on dynamic hyperparameter adjustment: evolution (PBT), gradients, bandits (Schaul et al.). Two stated differences from Schaul et al.: this bandit controls **exploration rate *and* discount factor**, and *"the bandit controls a family of state-action value functions that back up the effects of exploration and longer discounts, rather than linearly tilting a common value function by a fixed functional form."* **Three contributions**: (1) the extrinsic/intrinsic value decomposition, giving stability *"over a large range of intrinsic reward scales"*; (2) the meta-controller; (3) the all-57 result, plus the incidental finding that **doubling the BPTT window** improves long-term credit assignment. |
| 2 | **Background: Never Give Up (NGU)** | NGU recap: `r^i_t = r^episodic_t · min{max{α_t,1}, L}`, `L = 5`; `N` reward scales `r_{j,t} = r^e_t + β_j r^i_t`; each `Q*_{r_j}` gets its own discount `γ_j`; `(β_j,γ_j)` chosen so exploitative (low `β`) is far-sighted (high `γ`) and exploratory (high `β`) is short-sighted (low `γ`), because the intrinsic reward is dense and the extrinsic sparse. **The canonical mechanism sentence**: *"NGU trains a recurrent neural network `Q(x,a,j;θ)`, where `j` is a one-hot vector indexing one of `N` implied MDPs (in particular `(β_j,γ_j)`)."* **The stability critique**: NGU *"can be unstable and fail to learn an appropriate approximation of `Q*_{r_j}` for all the state-action value functions in the family, even in simple environments"*, especially when the two rewards differ in scale, sparseness or noise; conjecture that *"learning a common state-action value function for a mix of rewards is difficult when the rewards are very different in nature."* Distributed setup recap (Fig. 2): actors → prioritised replay → learner; actor `l` uses its own `ε_l`; **NGU is described as uniformly selecting `(β_j, γ_j)` per episode per actor** — note this differs from NGU's own App. A, which assigns each actor a fixed index. |
| 3 | **Improvements to NGU** | — |
| 3.1 | **State-Action Value Function Parameterization** | `Q(x,a,j;θ) = Q(x,a,j;θ^e) + β_j Q(x,a,j;θ^i)`; two identical-architecture networks; **two separate transformed Retrace losses on the same replayed sequence** but a **single shared target policy** `π(x) = argmax_a Q(x,a,j;θ)`. Equivalence to single-network optimisation proved in App. B *"under a simple gradient descent optimizer"*. Motivation: *"allow each network to adapt to the scale and variance associated with their corresponding reward"* and separate optimiser state. Transformed variant with `h`; identity chosen; App. H.3 shows no difference. |
| 3.2 | **Adaptive Exploration over a Family of Policies** | The limitation: *"all policies are trained equally, regardless of their contribution to the learning progress."* A meta-controller selects policies **at training and evaluation time**, allocating network capacity to the currently-relevant members and *"naturally building a curriculum"* — expected to prefer high `β` / low `γ` early and the reverse later. Evaluation-time benefit: with a wide `{γ_j}` and `β_j ≈ 0`, this is *"a way of automatically adjusting the discount factor on a per-task basis."* Implementation: **non-stationary multi-arm bandit per actor** (rather than global, because each actor's `ε_l` changes the optimal arm); arm `J_k` chosen at each episode start; the actor acts `ε_l`-greedily w.r.t. `Q(x,a,J_k;θ_l)` for the whole episode; the bandit reward is the **undiscounted extrinsic episode return** `R^e_k(J_k)`. Non-stationarity motivates **sliding-window UCB with `ε_UCB`-greedy exploration**. Also introduces **R2D2 (bandit)**: R2D2 with the Retrace loss plus joint training over `{γ_j}` and a meta-controller, **no intrinsic reward**, to isolate the meta-controller's contribution. |
| 4 | **Experiments** | Setup: `N = 32`; `{γ_j}` widened to `[0.99, 0.9999]` (NGU: `[0.99, 0.997]`); meta-controller `τ = 160`, `ε = 0.5` for actors and `τ = 3600`, `ε = 0.01` for the evaluator (Table 3 instead prints window 90); all other hyperparameters as NGU. Separate evaluator process; undiscounted returns averaged over **3 seeds** (**6 for Agent57**), windowed mean over 50 episodes, **maximum over training** reported. Metrics: HNS and **CHNS** = clipped to `[0,1]`, chosen because it *"puts an emphasis in the games that are below the average human performance benchmark"*. |
| 4.1 | Summary of the Results | Table 1. MuZero highest uncapped mean/median but **lowest capped** (Beam Rider 27469 % vs random-level Venture). R2D2 (bandit) transfers the meta-controller off NGU. Agent57 CHNS **100.00**, **57/57** above human, dominant up to the 20th percentile. Fig. 3: 51 games in the first 5 B frames, then hard exploration, then **Skiing at 78 B frames**; Skiing needs a high discount ⇒ high return variance ⇒ more data; Skiing's human baseline (−4336.9) sits close to the optimum (−3272) against random (−17098.1). Introduces the **10-game challenging set**: Beam Rider, Freeway, Montezuma's Revenge, Pitfall!, Pong, Private Eye, Skiing, Solaris, Surround, Venture. Fig. 4: each improvement adds performance, and *"each one of the improvements that is part of Agent57 is necessary in order to obtain the consistent final performance of 100 % CHNS."* |
| 4.2 | State-Action Value Function Parameterization | The **"random coin"** 15×15 gridworld diagnostic (see §5.5 above), 150 M frames; NGU's exploitative member degrades as `max_j β_j` grows; separate networks *"dramatically increases its robustness"*. The effect requires the coin to **terminate the episode** — otherwise the two ends of the family would want similar behaviour. Transfers to the challenging set: >20 % CHNS drop when removed from Agent57; no game made worse; largest gain on **Surround**, structurally analogous to random coin. |
| 4.3 | Backprop Through Time Window Size | 80 vs 160, tested on **both** R2D2 (to isolate it from NGU) and Agent57. Longer window: initially slower, better stability, slightly higher final score, largest effect on **Solaris** (Fig. 6). General improvement across the challenging set. |
| 4.4 | Adaptive Exploration | Meta-controller ablated on **R2D2** and on **NGU with separate networks**. R2D2 gains *"close to 20 % CHNS"*; NGU-sep-nets gains less, indicating overlap — *"the bandit algorithm can adaptively decrease the value of `β` when the difference in scale between intrinsic and extrinsic rewards is large."* Enables including `γ = 0.9999` in the family: fixed `γ = 0.9999` beats human on Skiing but *"across the full set of games renders the algorithm very unstable and damages its end performance"*, whereas the bandit adapts per task. Fig. 8: best arm over training — Skiing locks onto high `γ`; Hero onto high `β` / low `γ`; Gravitar, Crazy Climber, Beam Rider, Jamesbond shift from exploratory-low-`γ` to exploitative-high-`γ`. |
| 5 | **Conclusions** | First agent above the human benchmark on all 57 games; balances exploration/exploitation and long-term credit assignment through simple improvements to NGU. |
| A | Background on MDP | MDP `(X, A, P, r, γ)`, notation, transformed Bellman operator with function `h`. |
| B | **Extrinsic-Intrinsic Decomposition** | The equivalence proof reproduced in §5.4.1: `Q̃_k = Q^e_k + βQ^i_k` satisfies the value-iteration recursion for `r = r^e + βr^i`, using linearity of `T^π_r` in `r` and `Q` at fixed `π`; hence `Q̃_k → Q*_r`. Same argument for the `h`-transformed form. |
| C | Retrace and Transformed Retrace | The Retrace(λ) and transformed-Retrace operators. **C.1** their extrinsic/intrinsic decomposition. **C.2** the corresponding neural-network losses. |
| D | **Multi-arm Bandit Formalism** | MAB setup; stationary vs non-stationary rewards; `N_k(a)` and `µ̂_k(a)`; classic UCB; sliding-window UCB with `N_k(a,τ)`, `µ̂_k(a,τ)` and the `log(k−1∧τ)` bonus; **Agent57's simplified `ε_UCB`-greedy variant with the logarithm dropped from the bonus**, one forced pull per arm at the start. |
| E | Implementation details of the distributed setting | Replay stores fixed-length sequences with transitions `ω_s = (r^e_{s−1}, r^i_{s−1}, a_{s−1}, h_{s−1}, x_s, a_s, h_s, µ_s, j_s, r^e_s, …)` — **`j` is stored in replay**. Actor loop; evaluator alternates a bandit-sampled mode and a **greedy** mode (`arg max_a µ̂_{k−1}(a)`), averaging over 5 episodes. Learner: online and target networks, target updated every **1500** steps, `θ = θ^e ∪ θ^i`; forward pass inputs listed verbatim as `(x^b_s, r^{e,b}_{s−1}, r^{i,b}_{s−1}, j^b, a^b_{s−1}, h^b_{s−1})`; two transformed Retrace losses; shared greedy target policy; Adam for all losses including the inverse-dynamics and RND losses; priorities recomputed per sequence. Compute: 1 GPU learner at ~5 updates/s on 64 × length-**160** sequences, **256 actors** at ~260 env steps/s. |
| F | Network Architectures | Figures 9 (sketch) and 10 (detailed) only — **no prose description of the architecture in this appendix**. |
| G | Hyperparameters | **G.1** the `β_j` sigmoid ladder (unchanged from NGU) and the **new three-branch `γ_j` ladder** with `γ_0 = 0.9999`, `γ_1 = 0.997`, `γ_2 = 0.99`. **G.2** Atari pre-processing. **G.3** full table: `N = 32`, Adam (1e-4 R2D2, 5e-4 RND/action-prediction, clip 40), discount `r^i` 0.99 / `r^e` 0.997, batch 64, **trace length 160, replay period 80**, Retrace `λ = 0.95`, R2D2 reward transform, episodic memory 30000 (ring buffer), `β = 0.3`, kernel `ε = 1e-4`, `k = 10`, replay capacity 5e6, priority exponent 0.9, **importance-sampling exponent 0.0**, target update 1500, RND clip `L = 5`, eval/target `ε = 0.01`, **bandit window 90, bandit UCB `β` 1, bandit `ε` 0.5**. **G.4** search ranges: `τ ∈ {160, 224, 320, 640}`, `ε_UCB ∈ {0.3, 0.5, 0.7}`. |
| H | Experimental Results | **H.1** per-game ablation scores on the 10-game challenging set. **H.2** BPTT window comparison. **H.3** identity vs `h`-transform mixes — no difference; argument that both share an `argmax` at extreme `β` because `h^{-1}` is strictly increasing, and that at intermediate `β` the transformed mix implicitly optimises *"a non-linear combination of the intrinsic and extrinsic rewards"*; *"The only real important thing is that a combination between extrinsic and intrinsic happens whether it is linear or not."* **H.4** full Atari-57 score table (Agent57, R2D2 (bandit), MuZero, human, random). **H.5** Atari-57 learning curves. **H.6** videos; includes the note that R2D2 (retrace) clears a game at ~30,000 points where R2D2 (bandit) behaves differently. |

---

## 6. Cross-paper notes for the merge

Recorded here rather than in any single paper's section, because they only become
visible once all five are read together.

**6.1 Only one of the five applies anything resembling affine modulation, and it is a
single scalar.** Tally of operators: routing (#1 Soft Modularization), attention-mixture
plus concatenation (#2 CARE), concatenation (#3 VariBAD), one-hot concatenation (#4 NGU),
one-hot concatenation plus a scalar output gain (#5 Agent57). **No FiLM.** The
historical backbone of conditioning in RL is not affine modulation, and a report that
presents these five as FiLM precursors overstates the lineage. The correct framing is
that they are the **alternatives** against which FiLM has to justify itself.

**6.2 The one head-to-head comparison in the corpus is CARE's, and FiLM does not win
it.** Sodhani et al. run `SAC + FiLM` on the same context signal, same benchmark, same
10 seeds: 0.75 vs CARE's 0.84 on MT10 @2 M (not significant), 0.40 vs 0.54 on MT50 @2 M
(significant). FiLM does beat Soft Modularization on MT10 @2 M (0.75 vs 0.73) and lose
to it on MT50 (0.40 vs 0.50). Nobody in this batch tests FiLM against plain
concatenation while holding everything else fixed.

**6.3 Soft beats hard, twice, independently.** Yang et al.: hard routing collapses to
20.8 % where soft routing reaches 87.0 % on MT10-Fixed, attributed to policy-gradient
variance from a discrete router in an RL loop. Sodhani et al.: top-`k` hard attention
peaks at 0.71 against soft attention's 0.84. Two different operators, two different
papers, same direction. If the report makes one claim about *discreteness* in
conditioning, this is it.

**6.4 Three of five deliberately keep the conditioner's gradients away from the
conditioned pathway.** CARE stop-gradients the context inside the attention (stated
reason: keeps interpretability, prevents co-adaptation with the mixing weights);
VariBAD does not backpropagate the RL loss through the encoder at all (stated reasons:
speed, and *"prevents interference between gradients of opposing losses"*); Yang et al.
train the actor's and critic's routers as entirely separate parameter sets. This is a
corpus-level design pattern that no single paper states as a principle.

**6.5 Conditioning has a reported cost, and both DeepMind papers report it.** NGU:
sharing one representation across the family costs Breakout (837.7 → 532.8) and Beam
Rider (188.2 k → 68.7 k) relative to the unconditioned base agent, with
*"non-shared representations between mixtures"* proposed as the fix. Agent57 implements
a version of that fix (two value networks) and shows the failure it addresses in a
purpose-built gridworld: when the conditioned outputs' *magnitudes* diverge across the
conditioning range, one conditioned network cannot hold both. **The cost is
representational interference, and the published fix was structural separation rather
than a stronger operator.**

**6.6 Two distinct kinds of conditioning signal, and the project should not conflate
them.** Papers #1–#3 condition on *something about the environment* — a task label
(#1), a task description (#2), an inferred task belief (#3). Papers #4–#5 condition on
*a setting of the agent itself* — how strongly to weight curiosity, how far to look
ahead. Only the second kind is a family of objectives on **one** task, and only the
second kind is a knob the agent could in principle set for itself (Agent57's bandit does
exactly that). For a project whose modulator is meant to carry an internal state rather
than an external label, #4 and #5 are the closer structural analogues, despite being the
least sophisticated operators in the batch.

**6.7 Benchmark numbers do not transfer across papers.** Meta-World multi-headed SAC on
MT10 is reported at 0.88 (Yu et al., 1 seed), 0.85 (Yang et al., 3 seeds, MT10-Fixed)
and 0.61 (Sodhani et al., 10 seeds). Same nominal baseline, three numbers. CARE also
documents that evaluation *frequency* moves scores by 3–5 points because the reported
figure is a max over the evaluation series. **Any merged table must carry seed count,
evaluation protocol and the fixed-vs-goal-conditioned variant alongside every Meta-World
figure.** Similarly, NGU's Atari-57 median is printed as 1344.0 % in its abstract and
1354.4 % in its §4.2.

**6.8 Venue provenance.** Four of the five carry an explicit venue line inside the PDF
(NeurIPS 2020 footer; ICML 2021 PMLR 139 footer; ICLR 2020 page headers, twice).
**Agent57's held PDF carries none** — it is `arXiv:2003.13350v1` in ICML template. Record
it as a preprint unless the merged review sources the venue elsewhere.
