---
title: "DyMoDreamer: World Modeling with Dynamic Modulation"
slug: zhang_2025_dymodreamer
topic: modulation_in_rl
split_from: tmp/20260909_153028_filmhyper_rl/reviews_held_unreviewed.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 3. Zhang et al. — DyMoDreamer

**Full title:** *DyMoDreamer: World Modeling with Dynamic Modulation*
**PDF:** `docs/project/references/modulation_in_rl/sources/Zhang et al. 2025 - DyMoDreamer - world modeling with dynamic modulation.pdf`
**Venue as printed inside the PDF (page 1 footer, verified):** *"39th Conference on
Neural Information Processing Systems (NeurIPS 2025)."* Margin stamp:
`arXiv:2509.24804v1 [cs.LG] 29 Sep 2025`. So: **NeurIPS 2025**, confirmed — the
folder's README already had this right. Authors: Boxuan Zhang, Runqing Wang, Wei Xiao,
Weipu Zhang, Jian Sun, Jie Chen, Gang Wang (Beijing Institute of Technology) and Gao
Huang (Tsinghua). Code released.

### 3.1 What the paper is about, and the verdict on the "it's just concatenation" reading

**The question this review was asked to settle.** The folder's `sources/README.md`
excluded this paper from full review on the grounds that its "dynamic modulation" is
*not* modulation at all — it concatenates an extra latent vector into a world-model
state rather than scaling or shifting anything. Is that reading right?

**Verdict: yes, and it can be stated more strongly than the README does.**

A keyword search of the full 36-page PDF returns **zero** occurrences of *element-wise*,
*elementwise*, *Hadamard*, *⊙*, *multiplicative*, *affine*, *scale-and-shift*, or
*FiLM*. The extra latent $d_t$ — the thing the title calls a "modulator" — enters the
network at **five** sites, and every one of them is a concatenation into an MLP or GRU
input: the sequence model $h_t = f_\phi(h_{t-1}, z_{t-1}, d_{t-1}, a_{t-1})$; the
decoder $\hat o_t = p_\phi(\hat o_t \mid h_t, z_t, d_t)$; the reward head
$\hat r_t = p_\phi(\hat r_t \mid h_t, z_t, d_t)$; the continuation head
$\hat c_t = p_\phi(\hat c_t \mid h_t, z_t, d_t)$; and the actor–critic input state
$s_t = \{h_t, z_t, d_t\}$. The paper says so in as many words — "**The model state is
formed by concatenating $h_t$, $z_t$ and $d_t$**" (§2.2). There is no gain, no bias, no
gating of any activation by any other activation anywhere in the architecture.

**One refinement to the README's wording.** The paper does contain exactly **one**
multiplicative operation, and it is worth naming precisely so the record is not
overstated in the other direction:

$$o'_t = M(o_t) \cdot o_t,$$

an element-wise product of a **binary mask** with the raw pixel observation. But it is
not modulation in the sense this corpus uses the word, for three separate reasons: (i)
it acts on the **raw input image**, not on any hidden activation; (ii) the mask is
**not generated** by any network — $M(o_t)$ is a deterministic function of the
observation itself (threshold the inter-frame difference at $\epsilon = 0.001$, then
dilate by convolution); and (iii) it is **binary**, so there is no continuous gain and
no shift. Structurally it is a hand-designed hard attention mask in pixel space. So the
accurate statement for the report is: **the paper's own multiplicative operation is a
non-learned binary pixel gate in input space; everything the paper calls "modulation"
is concatenation.**

**But the negative finding is not the whole value of this paper.** The README's
exclusion was correct on mechanism, and the master review's §17 entry drew the right
lesson (a second stream earning its keep by carrying information the main stream cannot
represent). What full reading adds is that this paper carries an unusually
well-controlled ablation table, and it answers a question the corpus repeatedly asks
about FiLM and hypernetworks — *is the benefit just extra capacity?* — with a clean,
numeric **no**. It also contains, in an appendix nobody has read here, an **emergent
functional dissociation** between the two streams that was never trained for. Both are
transferable to the report regardless of the operator.

### 3.2 Direct answers to the required questions

| Question | Answer |
|---|---|
| **Conditioning signal** | The **differential observation** $o'_t = M(o_t)\cdot o_t$ — the current frame masked to the pixels that changed since frame $t-k$ (with $k=1$ by default), dilated to include their neighbourhoods. This is derived from the agent's own observation stream, with **no learned generator**: a binary threshold at $\epsilon = 0.001$ followed by a dilating convolution. It is encoded by a **dedicated dynamic encoder** into a 32×32 stochastic categorical latent, $d_t \sim q_\phi(d_t \mid h_t, o'_t)$. |
| **What is generated / modulated** | **Nothing is modulated.** A second latent variable $d_t$ is *produced* and then *concatenated* into five consumers: the GRU sequence model, the image decoder, the reward predictor, the continuation predictor, and the actor–critic state. Its size matches $z_t$ exactly: 32 categoricals × 32 classes each, straight-through gradients. |
| **The operator, and where it sits on the capacity spectrum** | **Concatenation — the "not modulation at all" end of the spectrum.** This is the corpus's cleanest positive control for the concatenation baseline that Yuan 2024 and SPARC also occupy: a NeurIPS 2025 paper that calls its mechanism "modulation" in its title and abstract while implementing pure concatenation. The one multiplicative op is the binary pixel mask described above. |
| **RL algorithm** | **DreamerV3** — model-based RL with a recurrent state-space model (RSSM) world model plus an actor–critic trained purely on imagined rollouts. REINFORCE estimator for both discrete and continuous actions; critic with EMA target and symlog two-hot return distribution; imagination horizon 15, discount horizon 333, return $\lambda = 0.95$; batch size 16, batch length 64; world-model LR $10^{-4}$, actor–critic LR $3\times10^{-5}$. **All hyperparameters follow DreamerV3 unless noted** — so the comparison against DreamerV3 is a controlled one. |
| **Environments** | **Atari 100k** (26 games, 100k actions ≈ 400k frames ≈ 1.85 h of play); **DeepMind Visual Control Suite** (all 20 tasks, 1M step budget, pixel observations, continuous actions); **Crafter** (procedurally generated, 1M frames). Plus three extension studies: **DeepMind Proprio** (3 tasks, state-vector observations rather than images), and the mechanism transplanted into **STORM**, a transformer world model (4 Atari games). |
| **Baselines** | DreamerV3 (the direct base method), HarmonyDream, STORM, OC-STORM, DIAMOND, IRIS, Δ-IRIS, TD-MPC2, TWISTER. Model-free and search-based methods (BBF, EfficientZero) are explicitly excluded because "our focus is the refinement of world models". |
| **Seed counts** | **5 seeds**, stated in the appendix figure captions ("the solid lines represent the average scores over 5 seeds, and the filled areas indicate the standard deviation across these 5 seeds"). DMC evaluation is 100 episodes on the final checkpoint; Crafter is the average return over 100 test episodes every 1M frames. Training cost: ~5.5 h per Atari game per 100k steps on one RTX 4090, JAX implementation. |
| **Reported instabilities / failure modes** | No numerical instability is reported. But three **negative ablation results** are reported honestly: (a) adding a dedicated decoder for the differential observations *hurts* performance and costs compute; (b) HarmonyDream-style adaptive loss weighting *hurts* on three of four games, attributed to an inherited learning rate being too aggressive for the added coefficients; (c) halving the modulator's dimensionality to 16×16 costs performance. And there is a substantial, unremarked failure pattern in the per-game data — see §3.4. |

### 3.3 Headline numbers

**Aggregate scores (Table 1, main text).**

| Benchmark | Metric | DreamerV3 (base) | Best prior | **DyMoDreamer** |
|---|---|---|---|---|
| Atari 100k | HNS mean | 125 % | DIAMOND 146 % | **156.6 %** |
| Atari 100k | HNS median | 49 % | OC-STORM 43.8 %, DIAMOND 37 % | **71.3 %** |
| DMC Visual Control (20 tasks) | task mean | 786 | TWISTER 801.8 | **832** |
| DMC Visual Control (20 tasks) | task median | 861 | **TWISTER 907.6** | 871 |
| Crafter | return @ 1M | 9.4 | Δ-IRIS 7.7 | **10.3** (+9.5 %) |

*(Fig. 1 adds STORM 122.3 % / 58.0 % and HarmonyDream 136.5 % / 67.1 % on Atari; the
appendix Table 2 lists STORM's mean as 126.7 % / 58.4 %, a small internal
inconsistency.)*

Two caveats on the headlines. **On DMC, "a new record of 832" is a record on the *mean*
only** — TWISTER's median of 907.6 beats DyMoDreamer's 871, so which method is "better"
depends on which aggregate you pick, and the paper quotes only the one it wins. On
Atari the median *does* favour DyMoDreamer (71.3 % vs 49 %), which is the more robust
statistic, so that headline survives its own robustness check.

**The ablation table (Table 7, App. K) — the most useful thing in the paper.**
Atari scores on four games chosen for their dynamic-object structure: Boxing (large,
sparse dynamic objects), Krull (small and numerous), Pong (small and sparse), Road
Runner (both).

| Variant | Boxing | Krull | Pong | Road Runner |
|---|---|---|---|---|
| **DyMoDreamer (full)** | **93.6** | **9624.8** | **20.9** | **20971.8** |
| Removing dynamic modulation | 80 | 7969 | 18.5 | 12536 |
| Removing $\mathcal{L}_{\text{reg}}$ | 90 | 8961 | 20 | 20918 |
| **High-dimensional DreamerV3 (48×48 $z_t$)** | **76** | **7325** | **18.2** | **16320** |
| With differential reconstruction | 71 | 7895 | 19.9 | 17323 |
| **Latent difference ($\delta_t = z_t - z_{t-1}$)** | **81** | **7855** | **20** | **12266** |
| Low-dimensional modulator (16×16) | 73 | 7423 | 19 | 17465 |

*(Two clerical points: Table 7's caption reads "Game scores in the DeepMind Proprio
benchmark", which is wrong — these are Atari games; Table 6 carries the same wrong
caption. And Table 7's last row is labelled "Low-dimensional $z_t$ (16×16)" while App.
K.5, which it summarises, is about the dimension of $d_t$ and its figure legend reads
"DyMoDreamer (16\*16 $d_t$)". Read it as $d_t$.)*

**Three controls in that table earn their place and should be cited by name.**

1. **The capacity control** (row 4). Plain DreamerV3 with its latent enlarged from
   32×32 to **48×48** — which is 2304 categorical dimensions against DyMoDreamer's
   $32{\times}32 + 32{\times}32 = 2048$, i.e. **more** total latent capacity — is
   *worse on all four games*, and worse than even the "removing dynamic modulation"
   ablation on three of them. The paper's conclusion is exactly right: "dynamic
   modulation is not equivalent to simply increasing dimensions but rather enriching
   the information used by agents for decision making."
2. **The differencing-locus control** (row 6). Replacing $d_t$ with a latent-space
   difference $\delta_t = z_t - z_{t-1}$ — the standard "latent flow" construction from
   model-free RL — and dropping the entire pixel-differencing pipeline gives
   81 / 7855 / 20 / **12266**. It is the *worst* variant on Road Runner, and the paper
   explains why concretely: Road Runner's decision-critical objects "occupy minimal
   pixels (e.g., the seed and steel occupying just 1 pixel)", so if the encoder never
   represented them in $z_t$ or $z_{t-1}$, their difference cannot recover them. So the
   benefit is **not "differencing" in the abstract** — it is specifically that
   differencing happens **before** the lossy encoder.
3. **The integration-site control** (row 2). Keeping $d_t$ (it is still computed, still
   encoded, still used in image reconstruction) but removing it from the RSSM sequence
   model and from the two KL loss terms costs 14 % on Boxing, 17 % on Krull, and
   **40 % on Road Runner**. "Simply appending differential observations, without
   integrating them into the RSSM, fails to direct the world model's focus toward
   dynamic patterns."

**Two mechanism-transfer results (Apps. I and J), both small.**
Into a *transformer* world model (STORM), the same mechanism gives Boxing 81 → 85,
Krull 6824 → **8563**, Pong 18 → 19.1, Road Runner 13866 → **19337**. On *state-vector*
observations (DeepMind Proprio, where differencing "naturally reduces to state
differencing" and encodes velocity/acceleration): Acrobot Swingup 134 → **225**,
Cheetah Run 614 → 625, Swingup 931 → 932. Note that only Acrobot moves; the other two
are flat, and there are only three tasks — this is a plausibility demonstration, not
evidence.

### 3.4 What the per-game Atari data actually shows — a caution the paper does not offer

The paper reports only aggregates in the main text; the per-game table is App. E.1,
Table 2. Comparing DyMoDreamer against its own base method, DreamerV3, game by game:

**DyMoDreamer wins 14 of 26 games and loses 12.** Wins: Amidar, Assault, Asterix, Bank
Heist, Boxing, Breakout, Freeway, Gopher, James Bond, Kangaroo, Krull, Ms Pacman, Pong,
Road Runner. Losses: Alien, Battle Zone, Chopper Command, Crazy Climber, Demon Attack,
Frostbite, Hero, Kung Fu Master, Private Eye, Qbert, Seaquest, Up N Down.

Several of the losses are large: **Frostbite 722 vs 3377** (−79 %), **Chopper Command
740.4 vs 2222** (−67 %), **Up N Down 22321.5 vs 46910** (−52 %), **Qbert 1736.1 vs
2921** (−41 %), Seaquest 591.8 vs 962 (−38 %), Hero 9874.1 vs 13354 (−26 %). Several of
the wins are correspondingly enormous: **Gopher 13456.9 vs 2160** (6.2×), **Pong 20.9
vs −4** (a sign flip), **Breakout 40.2 vs 10** (4×), **Bank Heist 1222.2 vs 398** (3.1×).

This is the well-known structure of Atari-100k mean HNS — a handful of games with low
human baselines dominate the average — and it means the 156.6 % headline should be
read as "this mechanism helps a lot on a subset of games and hurts on a comparable
subset", not as uniform improvement. The **median** (71.3 % vs 49 %) is the statistic
that carries the claim, and it does carry it, so the paper's conclusion stands; but the
mean should never be quoted alone from this paper.

The paper's own §3.2 gestures at the pattern honestly — it says the method excels
"where the key objects related to rewards are sparse and independent with each other"
(Pong, Finger Spin) and in "tasks with distinct phases" (Krull, Crafter) — but it never
inventories the games where the method loses, and it offers no account of *why* Frostbite
or Chopper Command regress. That gap is worth recording: **the corpus has no worked
example of a paper diagnosing when a second information stream is actively harmful**,
and this paper had the data to provide one.

### 3.5 Phase 1 — foundational overview

**The problem.** A "world model" is an agent's learned simulator: it compresses each
frame into a small latent code and predicts how those codes evolve, so the agent can
practise inside its own imagination instead of the real environment. The compression is
lossy by design, and what it tends to throw away is exactly what matters — a one-pixel
ball in Pong survives compression far less reliably than a large static red background,
even though the ball determines the reward and the background determines nothing.

**The idea.** Give the world model a **second, parallel input stream** that has already
had the static parts removed. Subtract consecutive frames, threshold the difference,
grow the surviving regions a little so their surroundings are included, and multiply
that binary mask into the original frame. What comes out is the current image with
everything that did not move blanked out. Encode *that* with its own separate encoder
into its own latent code $d_t$, and hand $d_t$ to the recurrent model, the decoder, the
reward predictor and the policy alongside the ordinary latent code $z_t$.

**Why the name is misleading.** The paper calls $d_t$ a "modulator" and the mechanism
"dynamic modulation", but $d_t$ never scales or shifts anything. It is glued onto the
existing state vector. The only multiplication in the whole system is the binary mask
applied to raw pixels before any network sees them, and that mask is computed by
arithmetic, not learned.

**Key findings.**
- New best mean score on Atari 100k (156.6 % of human) and best median (71.3 %); best
  mean on DeepMind Visual Control (832); best on Crafter (10.3 vs 9.4).
- The gain is **not extra capacity**: giving plain DreamerV3 a *larger* latent than
  DyMoDreamer's two latents combined is worse on all four ablation games.
- The gain is **not differencing in general**: differencing in the compressed latent
  space instead of in pixel space loses most of the benefit, and loses all of it
  exactly where the moving objects are tiny.
- The second stream must be **wired into the recurrent model**, not merely computed:
  removing it from the sequence model while leaving it in the image reconstruction
  costs up to 40 %.

**Initial takeaway.** For the report, this is a **negative finding on mechanism and a
positive one on architecture**. It contributes no evidence about gains, gates or affine
conditioning, because it has none. What it does contribute is one of the cleanest
demonstrations available that **a second pathway can pay for itself by carrying
information the main pathway structurally cannot represent** — and that the payment is
for the *information*, not for the parameters, because the capacity-matched control is
run and fails.

### 3.6 Phase 2 — graduate-level deep dive

**Setting.** POMDP $(\mathcal{O}, \mathcal{A}, \mathcal{T}, \mathcal{R}, \gamma)$ with
high-dimensional image observations $o_t$, objective
$\mathbb{E}_\pi\big[\sum_{t=1}^{\infty}\gamma^{t-1} r_t\big]$,
$r_t = \mathcal{R}(o_{t-1}, a_{t-1})$. Base architecture is DreamerV3's RSSM.

**Constructing the differential observation.** Forward differencing needs the future, so
a **backward** binary difference is used:

$$D(o_{i,h,w,c},\, o_{i-k,h,w,c}) = \begin{cases} 1, & \text{if } \lVert o_{i,h,w,c} - o_{i-k,h,w,c}\rVert_2 > \epsilon \\ 0, & \text{otherwise,}\end{cases}$$

with $\epsilon = 0.001$, $k = 1$ by default, $i$ the time index and $h, w, c$ the
spatial and channel indices. The authors note that after thresholding "very few pixels
may exceed the threshold", so the surviving 1-regions are **dilated** — 0-pixels
adjacent to 1-pixels are set to 1, implemented as a convolution — yielding the mask
$M(o_t)$. The differential observation is then

$$o'_t = M(o_t)\cdot o_t.$$

The dilation is not cosmetic: §2.3 argues rewards depend on "the dynamic parts of
observations **and their adjacent static parts**" — in Boxing, the reward comes from
jabs, which involve the moving fists *and* the stationary torsos they connect with. So
the mask deliberately retains a static collar around each moving region.

**Encoders and the two latents.** Both latents are 32 categoricals × 32 classes,
straight-through gradients:

$$z_t \sim q_\phi(z_t \mid h_t, o_t) = Z_t, \qquad d_t \sim q_\phi(d_t \mid h_t, o'_t) = D_t, \qquad \hat o_t = p_\phi(\hat o_t \mid h_t, z_t, d_t).$$

Note that **both** encoders are conditioned on the recurrent state $h_t$, matching
DreamerV3's posterior. The two encoders are **separate networks** — this is emphasised
in App. K.3 and is the formal basis for the claim that the mechanism is not latent flow:

$$z_t - z_{t-1} \;\ne\; d_t \sim q_\phi(d_t \mid h_t, o'_t),$$

"due to the characteristics of CNNs" — i.e. a convolutional encoder is not a linear map,
so encoding a difference is not the difference of encodings.

**The world model.**

$$\begin{aligned} \text{Sequence model:} \quad & h_t = f_\phi(h_{t-1}, z_{t-1}, d_{t-1}, a_{t-1}) \quad\text{(a GRU)}\\ \text{Latent predictor:} \quad & \hat z_t = p_\phi(\hat z_t \mid h_t)\\ \text{Dynamics predictor:} \quad & \hat d_t = p_\phi(\hat d_t \mid h_t)\\ \text{Reward predictor:} \quad & \hat r_t = p_\phi(\hat r_t \mid h_t, z_t, d_t)\\ \text{Continue predictor:} \quad & \hat c_t = p_\phi(\hat c_t \mid h_t, z_t, d_t) \end{aligned}$$

The **dynamics predictor** for $\hat d_t$ is the structurally interesting addition:
$d_t$ is not merely observed, it is **predicted from $h_t$ alone**, exactly as $z_t$ is.
That is what allows the modulator to exist during imagination, when no real observation
is available — and it is what makes the claim "the modulator captures temporal
information" non-vacuous, since a quantity predictable from the recurrent state is by
construction part of the learned dynamics rather than an input annotation.

**Losses.** $\mathcal{L}(\phi) = \mathbb{E}_\phi\big[\sum_t \mathcal{L}_{\text{pred}} + \omega_{\text{dyn}}\mathcal{L}_{\text{dyn}} + \omega_{\text{rep}}\mathcal{L}_{\text{rep}}\big] + \mathcal{L}_{\text{reg}}$, with $\omega_{\text{dyn}} = 0.5$, $\omega_{\text{rep}} = 0.1$.
Prediction loss $\mathcal{L}_{\text{pred}} = \mathcal{L}_{\text{rec}} + \mathcal{L}_{\text{rew}} + \mathcal{L}_{\text{con}}$,
each a negative log-likelihood conditioned on $(h_t, z_t, d_t)$. The dynamics and
representation losses each gain a **second, mirrored KL term for the modulator**:

$$\mathcal{L}_{\text{dyn}}(\phi) = \max\big(1,\, \mathrm{KL}[\mathrm{sg}(q_\phi(z_t \mid h_t, o_t)) \,\Vert\, p_\phi(\hat z_t \mid h_t)]\big) + \underbrace{\max\big(1,\, \mathrm{KL}[\mathrm{sg}(q_\phi(d_t \mid h_t, o'_t)) \,\Vert\, p_\phi(\hat d_t \mid h_t)]\big)}_{\text{modulation's dynamic loss}}$$

$$\mathcal{L}_{\text{rep}}(\phi) = \max\big(1,\, \mathrm{KL}[q_\phi(z_t \mid h_t, o_t) \,\Vert\, \mathrm{sg}(p_\phi(\hat z_t \mid h_t))]\big) + \underbrace{\max\big(1,\, \mathrm{KL}[q_\phi(d_t \mid h_t, o'_t) \,\Vert\, \mathrm{sg}(p_\phi(\hat d_t \mid h_t))]\big)}_{\text{modulation's representation loss}}$$

with $\mathrm{sg}(\cdot)$ the stop-gradient and the "free bits" clip at 1 nat.

**Differential divergence regularisation.** The one genuinely novel loss term. MSE-style
reconstruction penalises *intra*-frame error and is indifferent to whether the model got
the *change between* frames right. So compute backward differences of predicted and true
reconstructions, $\Delta\hat o_t = \hat o_t - \hat o_{t-1}$ and
$\Delta o_t = o_t - o_{t-1}$, turn each into a distribution by a temperature-sharpened
softmax over the joint channel-height-width index,

$$\sigma(\Delta \hat o_t) = \frac{\exp(\Delta\hat o_t/\tau)}{\sum_{h,w,c}\exp(\Delta\hat o_t/\tau)}, \qquad \sigma(\Delta o_t) = \frac{\exp(\Delta o_t/\tau)}{\sum_{h,w,c}\exp(\Delta o_t/\tau)}, \qquad \tau = 0.1,$$

and penalise their KL divergence averaged over the batch:

$$\mathcal{L}_{\text{reg}}(\phi) = \frac{1}{B}\sum \mathrm{KL}\big(\sigma(\Delta\hat o)\,\Vert\,\sigma(\Delta o)\big).$$

Sharpening with $\tau = 0.1$ makes this a soft **argmax-matching** objective: it asks
the model to put its predicted change in the *same places* as the true change, largely
independent of magnitude. Its ablation (Table 7 row 3) costs 4 % on Boxing and 7 % on
Krull and is essentially free on Pong and Road Runner — the smallest effect of any
component, and the paper says so: removing it still leaves the model above vanilla
DreamerV3.

**Policy learning.** Standard DreamerV3 actor-critic on imagined rollouts, over
$s_t = \{h_t, z_t, d_t\}$. $\gamma = 0.997$; critic trained by maximum likelihood
against $\lambda$-returns with an EMA-regularised term,

$$\mathcal{L}(\psi) = \frac{1}{BL}\sum_{n=1}^{B}\sum_{t=1}^{L}\Big[\big(V_\psi(s_t) - \mathrm{sg}(R^\lambda_t)\big)^2 + \big(V_\psi(s_t) - \mathrm{sg}(V_{\psi_{\mathrm{EMA}}}(s_t))\big)^2\Big],$$

actor by REINFORCE with a percentile-normalised advantage. One implementation wrinkle
worth noting: because differencing is backward, **a random action is taken on the first
frame** (or the first $k$ frames when $k>1$) purely to generate a predecessor frame so
that $o'_1$ exists.

**Why it works, according to the paper — and the one piece of direct evidence.** §2.5
reports that the reconstruction loss of imagined trajectories shows *no significant
reduction* against DreamerV3, but DyMoDreamer "generates substantially less
hallucination on dynamic patterns during imagination". Fig. 3 shows the Boxing case with
DreamerV3's hallucinated regions boxed. So the mechanism's benefit is explicitly **not**
better pixel reconstruction — a point the paper repeats three times, most sharply in
App. K.2: "the goal of dynamic modulation is not to improve the reconstruction accuracy,
but to enable the agent to leverage richer dynamic information for decision making."
This is corroborated by the negative result that *adding* a reconstruction target for
$o'_t$ (a dynamic decoder $\hat o'_t = p_\phi(\hat o'_t \mid h_t, d_t)$ plus
$\mathcal{L}_{\text{dif}} = -\ln p_\phi(o'_t \mid h_t, d_t)$) **hurts** — 71 / 7895 /
19.9 / 17323 against 93.6 / 9624.8 / 20.9 / 20971.8 — because "differential observations
are not strictly edge segmentations" and constraining the modulator to reconstruct them
imposes a coarse and wrong target.

**App. H — the emergent dissociation, and the paper's most interesting unremarked
result.** Add a second decoder that sees **only** $z_t$ (not $d_t$), and reconstruct
additively:

$$\begin{aligned} \text{Decoder:} \quad & \widehat{\mathrm{dyn}}_t = p_\phi(\widehat{\mathrm{dyn}}_t \mid h_t, z_t, d_t)\\ \text{Static decoder:} \quad & \widehat{\mathrm{sta}}_t = p_\phi(\widehat{\mathrm{sta}}_t \mid h_t, z_t)\\ & \hat o_t = \widehat{\mathrm{dyn}}_t + \widehat{\mathrm{sta}}_t. \end{aligned}$$

**The end-to-end loss is left completely unchanged** — no reconstruction target is
assigned to either decoder separately. Yet the two streams specialise: $z_t$ comes to
encode "static environmental factors and passive dynamics (e.g., static backgrounds and
the black NPC in Boxing)", while $d_t$ specialises in "agent-controllable elements
(e.g., the controlled white player in Boxing)". The authors relate this to the denoised
MDP literature.

That is a **functional dissociation into controllable and uncontrollable factors,
emerging from nothing but an architectural split plus an additive output combination.**
For the report's purposes this is the most transferable finding in the paper, because
it is an *architecture* result rather than an *operator* result — it says something
about two-stream designs generally, and it is reached without any affine conditioning.
Caveat: the evidence is qualitative (Fig. 12, one game, reconstructions inspected by
eye), with no quantitative dissociation metric.

**Robustness of the differencing scheme (App. G).** The pixel-difference rule is
swappable. Two alternatives are given with formal definitions: a **moving-average
difference**, thresholding $\lVert o_{i,h,w,c} - \mathrm{avg}_i\rVert_2$ against a
trailing window mean, which wins in egocentric-view games (Battle Zone 20351 vs vanilla
16240); and **multi-frame logical differencing**,
$D_{\log}(o_{i,h,w,c}) = \bigwedge_{k\in\Omega(t)} D_k$ with $\Omega(t) = \{i-\Delta, i\}$,
which keeps only pixels that were flagged at every step in a window and wins where
temporal continuity is high (Road Runner 21378 vs vanilla 20972). Also $k=3$ instead of
$k=1$ (App. K.6): better in smooth environments, worse where fast intermediate motion
matters, "such as the rapid punching in Boxing". These are single-game switches, not
sweeps, but they establish that the mask is a pluggable front-end.

**Modulator dimensionality (App. K.5).** Halving $d_t$ to 16×16 costs performance on all
four games (73 / 7423 / 19 / 17465). The paper motivates this with a task-dependent
"average mask rate" — the fraction of pixels blanked — reporting **98.5 % for Pong,
94.3 % for Boxing, 83.1 % for Krull**, and argues that both too-small and too-large $d_t$
are harmful ("increasing the dimension of $d_t$ effectively enlarges the latent variable
space, potentially introducing redundant information"). Only the two settings 16×16 and
32×32 are actually run, so the "too large is bad" half of that claim is **asserted**;
only "too small is bad" is tested.

### 3.7 What this contributes to the report

- **It is the corpus's cleanest positive control for concatenation.** A NeurIPS 2025
  paper that puts "Modulation" in its title, implements concatenation, and works. When
  the report contrasts affine conditioning against concatenation, this is the entry that
  shows the concatenation arm is not a straw man — with the honest note that the
  *naming* in this literature is unreliable and mechanism must be read from the
  equations, not the abstract.
- **It answers the capacity objection.** The recurring worry that a conditioning
  mechanism's benefit is just added parameters is directly tested here and refuted with
  a control that gives the baseline *more* latent capacity than the method. That
  control's design — enlarge the baseline's own latent to exceed the combined size of
  the two-stream model's latents — is a template the report can recommend for any
  future modulation ablation.
- **It localises the benefit to the pre-encoder position of the operation.** The latent-difference
  control is the sharper of the two: it keeps the differencing idea and moves only
  *where* it happens, and most of the benefit disappears. The general principle —
  *the second stream is valuable exactly to the extent that it carries information the
  main encoder discards* — is stated more precisely here than anywhere else in the
  corpus.
- **It supplies an emergent controllable/uncontrollable dissociation** from a two-stream
  architecture with an additive output combination and no supervision. Qualitative, one
  game, but architecturally suggestive and previously unrecorded here.
- **It is a caution about aggregate metrics.** 156.6 % mean HNS, 14–12 win–loss against
  the base method game by game, with four regressions worse than −38 %. The median
  carries the claim; the mean should not be quoted alone.

### 3.8 Where this reading disagrees with the existing record

The master review's §17 entry and the `sources/README.md` are **substantially correct** —
this is the paper where the prior digest holds up best. Four refinements:

1. **"32×32 categorical latents concatenated into an RSSM state"** (README) — accurate,
   and can be strengthened: the concatenation happens at **five** sites, not just the
   RSSM state (sequence model, decoder, reward head, continue head, actor–critic input).
2. **"a keyword scan of the full 36-page PDF finds no multiplicative interaction
   anywhere"** (§17) — **not quite**. There is exactly one, $o'_t = M(o_t)\cdot o_t$, a
   **binary, non-learned, pixel-space** mask applied before any network. It does not
   change the exclusion verdict but the record should be precise, because "no
   multiplication anywhere" is a stronger and falsifiable claim than the one that is
   actually true.
3. **"pixel-space differencing surfaces small moving objects the encoder *provably*
   discards"** (§17) — **overstated**. The paper *argues* this (App. K.3 gives three
   reasons) and *demonstrates* it on one case (Road Runner, where the critical objects
   are single pixels and the latent-difference variant scores 12266 against 20971.8).
   There is no proof. "Argued and demonstrated on a case" is the accurate phrasing.
4. **"it sets a new Atari-100k record (156.6 % mean human-normalised) with no task
   distribution at all"** (§17) — true, but incomplete in a way that matters if this is
   cited as evidence of single-task gains. The per-game record is **14 wins and 12
   losses against DreamerV3**, with four regressions of 38 % or worse. The median HNS
   (71.3 % vs 49 %) is the statistic that supports the claim.

Two things the existing record does not mention at all and should: the **capacity
control** (48×48 DreamerV3), which is the single most citable ablation in the paper; and
**App. H's emergent static/dynamic dissociation**.

### Appendix: Section-by-Section Backbone

Preserving the paper's own order.

| § | Title | Core content |
|---|---|---|
| — | **Abstract** | Sample inefficiency in DRL; MBRL mitigates via world models. "Conventional world models process observations holistically, failing to decouple dynamic objects and temporal features from static backgrounds." Proposes a dynamic modulation mechanism using **differential observations from an inter-frame differencing mask**, modelled as stochastic categorical distributions and integrated into an RSSM. Claims: 156.6 % mean HNS on Atari 100k, 832 on DMC Visual Control, +9.5 % on Crafter. |
| 1 | **Introduction** | World-model lineage (World Models, Dreamer 1–3, transformer world models, tokenisation). The stated failure: RSSM and transformer world models alike struggle with **small dynamic objects**; VAEs amplify randomness; small dynamic objects carry disproportionate decision relevance (Pong's ball and paddle vs its static red background). IRIS and DIAMOND improve reconstruction precision at heavy compute cost; OC-STORM needs a pretrained segmentation model and prior object counts. Motivation drawn from human-infant cognition — infants attend to dynamic object interactions. Three contributions. **Page-1 footer: NeurIPS 2025.** |
| 2 | **Methodology** | POMDP setup; DreamerV3 base; inspiration cited from modulated ODEs and from latent-flow methods in model-free RL. |
| 2.1 | **Dynamic modulation** | The differencing construction: backward binary threshold at $\epsilon = 0.001$ with interval $k=1$, dilation of surviving regions by convolution to fix sparsity, mask $M(o_t)$, differential observation $o'_t = M(o_t)\cdot o_t$. Eq. (1) gives the stochastic encoder, the **separate** dynamic encoder, and a decoder conditioned on all three of $h_t, z_t, d_t$. Emphasises negligible computational overhead relative to vision-model approaches. |
| 2.2 | **Dynamically modulated world model** | Eq. (3): the five components. **"The model state is formed by concatenating $h_t$, $z_t$ and $d_t$."** Both latents are 32 categoricals × 32 classes; straight-through gradients; GRU sequence model. Three claimed properties: dynamic feature embedding, temporal information capture (via $\hat d_t$ being predicted from $h_t$), and end-to-end joint training with no separate modulator pretraining. |
| 2.3 | **Intuition** | Rewards depend on dynamic parts *and their adjacent static parts* (Boxing jabs need fists and torsos). Not all tasks are dynamics-driven (Gopher's carrots are static and reward-relevant), which is why $z_t$ is **retained** rather than replaced. Argues for differencing in observation space over latent space: a 1-pixel Pong ball missing from both $z_t$ and $z_{t-1}$ makes their difference useless. |
| 2.4 | **End-to-end learning** | Eq. (5) total loss with $\omega_{\text{dyn}} = 0.5$, $\omega_{\text{rep}} = 0.1$. Eq. (6) prediction loss (reconstruction + symlog two-hot reward + cross-entropy continuation). Eqs. (7)–(8) dynamics and representation KLs, **each with a mirrored modulator term**, free-bits clipped at 1 nat. Eqs. (9)–(10) the differential divergence regularisation: softmax-sharpened ($\tau = 0.1$) backward differences of predicted and true frames, matched by KL. |
| 2.5 | **Policy learning** | Actor–critic on imagined rollouts over $s_t = \{h_t, z_t, d_t\}$. A random first action is needed to seed the backward difference. **Reports that imagined-trajectory reconstruction loss is not significantly reduced, but hallucination on dynamic patterns is** — Fig. 3, Boxing. |
| 3 | **Experiments** | |
| 3.1 | Benchmarks and results | Atari 100k (26 games, 100k actions); DMC Visual Control (all 20 tasks, 1M steps); Crafter (1M frames, background moves with the agent so differencing captures relative motion). Table 1 aggregates. |
| 3.2 | Analysis and implementation | Model-free and search-based methods excluded by scope. Wins attributed to sparse, mutually independent reward-relevant objects (Pong, Finger Spin) and to phase-structured tasks (Krull, Crafter). Gopher cited as a case where gains persist even when reward is not carried by dynamics, because $z_t$ is retained. RTX 4090, ~5.5 h per Atari game, JAX. |
| 4 | **Ablations (main text)** | Four games chosen by dynamic-object structure: Boxing (large sparse), Krull (small numerous), Pong (small sparse), Road Runner (both). |
| 4.1 | **Removing dynamic modulation** | The sequence model degenerates to $h_t = f_\phi(h_{t-1}, z_{t-1}, a_{t-1})$ and the modulator constraints are dropped from the dynamics and representation losses; $d_t$ survives only in encoding and reconstruction. Notable drop. "Simply appending differential observations, without integrating them into the RSSM, fails to direct the world model's focus toward dynamic patterns." Cross-referenced to the capacity ablation. **Note: this manipulation changes three things at once** (sequence-model input, dynamics KL, representation KL), so it is a bundle rather than a single factor. |
| 4.2 | Differential divergence regularisation | Removing $\mathcal{L}_{\text{reg}}$ costs performance but the model "still surpasses vanilla DreamerV3". |
| 5 | Related work | Dreamer lineage, HarmonyDream's adaptive loss balancing, transformer world models (TWM, STORM, OC-STORM), tokenised imagination (IRIS, Δ-IRIS, REM), diffusion in pixel space (DIAMOND), hierarchical world models (THICK, HIEROS, Puppeteer). |
| 6 | Conclusion | "Setting a new record for the RSSM architecture." Future direction: soft predictive constraints on future states; more human-like world models learned from cognitive behaviour. |
| A | Further related work | Longer treatment of the same lineage. |
| B | Limitations | *(Short; the substantive limitations surface in the appendix ablations rather than here.)* |
| D | Policy learning | Full DreamerV3 actor–critic specification: $\gamma = 0.997$, critic maximum-likelihood loss with an EMA-target term, REINFORCE actor with percentile-normalised advantage. |
| E.1 | **Atari 100k per-game scores** | **Table 2, all 26 games, against Random / Human / STORM / OC-STORM / DIAMOND / DreamerV3 / HarmonyDream.** The source for the 14–12 win–loss analysis in §3.4. Human mean 156.6 %, median 71.3 %. 5 seeds. |
| E.2 | DMC per-task scores | All 20 tasks vs DreamerV3, TD-MPC2, TWISTER. 100 evaluation episodes on the final checkpoint. |
| E.3 | Crafter | Average return over 100 test episodes per 1M frames, vs IRIS, Δ-IRIS, DreamerV3. |
| F | Differential observations | Visualisations across benchmarks — raw, vanilla frame-differenced, and the proposed dilated version — for Finger Spin, Pendulum Swingup, Reacher Hard, and Crafter. |
| G | **Alternative differencing strategies** | Moving-average differencing (Eqs. 16–17), better in egocentric views: **Battle Zone 20351 vs 16240 vanilla**. Multi-frame logical differencing via AND over a temporal window (Eq. 18), better where temporal continuity is high: **Road Runner 21378 vs 20972 vanilla**. Frames the mask as a pluggable, classical-CV front-end. |
| H | **Static factors** | Adds a static decoder seeing only $(h_t, z_t)$, reconstructs additively $\hat o_t = \widehat{\mathrm{dyn}}_t + \widehat{\mathrm{sta}}_t$, **with the loss unchanged**. Finds an emergent dissociation: $z_t$ → static backgrounds and passive dynamics (the NPC in Boxing); $d_t$ → agent-controllable elements (the player). Related to denoised MDPs. Qualitative evidence only. |
| I | Applicability beyond images | DeepMind Proprio, state-vector observations. Acrobot Swingup 134 → 225; Cheetah Run 614 → 625; Swingup 931 → 932. Argues differencing on state vectors implicitly encodes velocity and acceleration. Three tasks; two are flat. |
| J | **Generality** | The mechanism transplanted into **STORM**, a transformer world model: Boxing 81 → 85, Krull 6824 → 8563, Pong 18 → 19.1, Road Runner 13866 → 19337. Evidence that the mechanism is not RSSM-specific. |
| K | **Ablations (appendix)** | **Table 7 aggregates all seven variants numerically** — the most useful table in the paper. |
| K.1 | **High-dimensional stochastic representations** | The **capacity control**: DreamerV3 with $z_t$ enlarged to 48 categories × 48 classes (2304 dims, exceeding DyMoDreamer's combined 2048) is worse on all four games. "Dynamic modulation is not equivalent to simply increasing dimensions but rather enriching the information used by agents." |
| K.2 | Reconstruction of differential observations | Adding a dynamic decoder and an $\mathcal{L}_{\text{dif}}$ reconstruction target for $o'_t$ **hurts** and costs compute. "Differential observations are not strictly edge segmentations"; their function is to isolate dynamic features, not to be reconstructed. Implicit joint training in one decoder is better. |
| K.3 | **Modulation with latent difference** | Replaces $d_t$ with $\delta_t = z_t - z_{t-1}$ and removes the whole pixel-differencing pipeline. Fails, worst on Road Runner "where the critical objects occupy minimal pixels (e.g., the seed and steel occupying just 1 pixel)". Three stated reasons: encoder precision limits, categorical latents lose fine positional information, small-object frame differences become unreliable. Eq. (23) formalises $z_t - z_{t-1} \ne d_t$ because CNNs are nonlinear. |
| K.4 | Harmonious loss | HarmonyDream-style learnable loss weights $\mathcal{L}_h = \sum \tfrac{1}{\omega_i}\mathcal{L}_i + \ln(1+\omega_i)$, with the stationary point $\omega^* = \tfrac{1}{2}\big(\mathbb{E}[\mathcal{L}] + \sqrt{\mathbb{E}[\mathcal{L}]^2 + 4\mathbb{E}[\mathcal{L}]}\big)$ derived, and the $\ln(1+\omega)$ regulariser justified as preventing runaway weights on small losses. **Result is negative** — comparable only on Pong, worse on Krull, Boxing and Road Runner — attributed to the inherited learning rate being too aggressive for the added coefficients. |
| K.5 | Dimensions of the dynamic modulation | 16×16 $d_t$ underperforms 32×32 on all four games. Motivated by task-dependent **average mask rates: Pong 98.5 %, Boxing 94.3 %, Krull 83.1 %**. The claim that *too large* is also harmful is asserted, not tested. |
| K.6 | Longer difference interval | $k=3$: better in smoother environments, worse where fast intermediate motion matters ("the rapid punching in Boxing"). |
| L | Hyperparameters | Batch 16 × length 64, LayerNorm + SiLU, Adam. World model LR $10^{-4}$, grad clip 1000. Actor–critic: imagination horizon 15, discount horizon 333, $\lambda = 0.95$, critic EMA 0.98, entropy scale $3\times10^{-4}$, LR $3\times10^{-5}$, grad clip 100. Environment emits "done" on life loss but continues to true reset. |
| — | NeurIPS Paper Checklist | Standard. |

---
