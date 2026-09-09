---
title: "CASH: Capability-Aware Shared Hypernetworks for Heterogeneous Multi-Robot Coordination"
slug: fu_2025_cash
topic: Hypernetwork
split_from: tmp/20260909_153028_filmhyper_rl/reviews_hypernet_apps.md
note: "Written 2026-09-09 as part of a batch review; split into a per-paper file and filed here so the corpus holds it rather than a scratch directory."
---

## 3. Fu et al. 2025 — CASH

**Full title as printed:** *CASH: Capability-Aware Shared Hypernetworks for **Flexible** Heterogeneous
Multi-Robot Coordination* (the "Flexible" is in the paper's title but not in the local filename).
**Venue as printed in the PDF:** "9th Conference on Robot Learning (**CoRL 2025**), Seoul, Korea."
Sidebar stamp: **arXiv:2501.06058v5 [cs.MA] 01 Sep 2025**.
**Authors:** Kevin Fu\*, Shalin Anand Jain\*, Pierce Howell, Harish Ravichandar (Georgia Tech; \*equal
contribution). Project site: https://star-lab.cc.gatech.edu/papers/fu-jain-CASH-CoRL/
**PDF:** `docs/project/references/Hypernetwork/sources/Fu et al. 2025 - Capability-aware shared hypernetworks for heterogeneous multi-robot coordination (CASH).pdf`

### Plain-language entry point

**The question.** A team of robots with different physical abilities — one is fast but carries little, one
is slow but carries a lot — must coordinate. How should you parameterize their policies? There are two
standard answers, and both are bad in a different way. **Give every robot its own network**, and you get
diverse specialized behavior but you need a lot of data, and a robot whose abilities you never trained on
has no network at all. **Give every robot the same shared network** (optionally with its ID or its ability
numbers glued to the input), and you get data efficiency and can handle new robots, but in practice
everyone learns nearly the same behavior.

**What this paper does.** It treats those two answers as the **ends of a spectrum** and puts a
hypernetwork in the middle. One shared network reads each robot's *capability vector* — literally the
numbers "your speed is 2.1, your water capacity is 0.09" plus the same numbers for teammates — and writes
out the weights of that robot's small action decoder. **All learnable parameters are shared across robots;
the *used* parameters differ per robot and per timestep.** The authors call this **soft weight sharing**:
one backbone, per-agent modulation. Because the conditioning is on *what a robot can do* rather than on
*who a robot is*, a robot with capabilities never seen in training still gets sensible weights.

**Why this is the most relevant paper in the batch for us.** It is the only one that (a) is genuinely
reinforcement learning — three learning paradigms, value-based, policy-gradient, and imitation — and (b)
runs the **three-way comparison** the standing question actually needs: shared network with the context
concatenated to the input (the closest available stand-in for FiLM-style conditioning), per-agent
networks, and the hypernetwork.

**Headline numbers.** Across two simulated tasks × three learning algorithms, on *unseen* robot
capabilities: CASH wins in 6/6 conditions on success rate against the concatenation baseline. The
starkest is imitation learning on the firefighting task — CASH reaches **0.92** success on unseen teams
where the concatenation baseline reaches **0.08** and the no-capability baseline **0.00**. And it does
this with **60–80 % fewer learnable parameters** (e.g. 162 K vs 401 K on the hardware testbed).

**The stability finding you should not skip.** Appendix B is titled "**Layer normalization is crucial to
CASH**". A four-layer hypernetwork was found to be better but *un-trainable* without LayerNorm before every
ReLU. Without it, imitation learning on one task "plummets around timestep 4000 and never recovers", and
on the other "never demonstrates better than random performance". That is the single most actionable
engineering fact in this batch.

### Phase 1 — Foundational overview

**Problem setting.** A Dec-POMDP $(D,S,A,O,\mathcal{O},R,T)$ with $n$ robots acting on local
observations. The paper modifies it by giving every policy access to the **team's capability vectors**:
$a^t_i\sim\pi_i(o^t_i, C^t)$ where $C^t=\{c^t_1,\dots,c^t_n\}$ and $c^t_i\in\mathbb{R}^m$. Capabilities are
"nominal" — speed, payload, sensing radius, capture radius — and are stated to be "readily obtained from
robot specifications or sensors", i.e. they are given, not inferred.

**What generates what.** Three modules, all sharing one parameter set $\{\psi,\phi\}$:
1. **RNN Encoder** $f_\psi$ — a GRU over local observations, producing $z^t_i=f_\psi(o^t_i)$. Shared,
   *not* generated. This handles partial observability and history.
2. **Hyper Adapter** $h_\phi$ — the hypernetwork. Emits
   $\theta^t_i=h_\phi\!\left(o^t_i,\ c^t_i,\ C^t_{/i}\right)$, where $c^t_i$ is the ego robot's
   capabilities and $C^t_{/i}=\{c^t_j\mid j\ne i\}$ the teammates'. Shared.
3. **Adaptive Decoder** $g_{\theta^t_i}$ — a **one- or two-layer MLP** whose weights are the emitted
   $\theta^t_i$. Produces $a^t_i=g_{\theta^t_i}(z^t_i)$ (actions for policy-gradient/imitation, Q-values
   for value-based).

So: **static shared GRU trunk + per-robot, per-timestep generated MLP head.** The same
"static-trunk / generated-head" pattern as Hyper-GoalNet (§2), independently arrived at.

**Key findings.**
1. **Soft sharing matches per-agent networks in performance and beats them in efficiency.** Compared
   against INDV (separate network per robot, no sharing), CASH is more sample-efficient, "performs
   marginally better", and has a fraction of the parameters — while INDV *cannot generalize to unseen
   robots at all*.
2. **CASH is less behaviourally diverse than INDV, and the paper argues that is correct.** Behavioural
   diversity (measured by SND, below) is *lower* for CASH than INDV, but task performance is not worse; the
   authors conclude INDV produces "superfluous behavioral diversity that doesn't improve performance".
3. **Against the concatenation baseline, in-distribution is often a tie and out-of-distribution is not.**
   On QMIX/Firefighting, in-distribution success 0.96 (CASH) vs 0.97 (concat) — a tie — but out-of-
   distribution 0.67 vs 0.56. On QMIX/Mining, 1.00 vs 0.98 in-distribution, 0.88 vs 0.83 out. **The
   mechanism's value is concentrated in generalization, not in fitting.**
4. **Explicit capability conditioning beats implicit.** RNN-IMP (no capability input, must infer speed
   from observation history via the GRU) is worst everywhere and has **exactly zero** measured behavioural
   diversity in all six conditions. So the ladder is: implicit < concatenated < hypernetwork.
5. **It transfers to hardware.** On the Robotarium physical testbed, CASH beats both shared baselines on
   reward, makespan and collisions, in simulation and on real robots.
6. **It handles capability changes mid-episode.** Because weights are regenerated every timestep from the
   current capability vector, a robot whose speed is cut by 75 % halfway through an episode gets different
   weights immediately, with no retraining.

**Initial takeaway.** Conditioning a *shared* network on *what an agent can do* — and routing that
conditioning to the weights rather than the input — buys generalization to agents you never trained on,
at a lower parameter count than either alternative. The paper's own framing is the useful one: shared
parameters and individualized parameters are two ends of a spectrum, and the hypernetwork is a way to sit
anywhere on it adaptively.

### Phase 2 — Graduate-level deep dive

#### 2.1 Formalism

Dec-POMDP with the capability augmentation. At each timestep, robot $i$ observes $o^t_i\sim\mathcal{O}(\cdot\mid s^t)$
and acts under $a^t_i\sim\pi_i(o^t_i,C^t)$; the fully cooperative optimum is the set of policies maximizing
$\mathbb{E}\big[\sum_{t=0}^{T} r_t\big]$. The design objective is explicit and worth quoting because it is
the whole thesis: *design a **single shared-parameter** policy architecture ($\pi_i=\pi\ \forall i$) that can
produce **diverse** behaviors and generalize to unseen robots by reasoning about robot capabilities.*

The forward pass, in order:

$$z^t_i=f_\psi(o^t_i),\qquad \theta^t_i=h_\phi\!\left(o^t_i,\,c^t_i,\,C^t_{/i}\right),\qquad a^t_i=g_{\theta^t_i}\!\left(z^t_i\right).$$

Note carefully: **$f_\psi$ and $h_\phi$ carry no index $i$** — they are literally the same weights for every
robot — while $\theta^t_i$ does. That is the precise technical content of "soft parameter sharing": the
*learnable* parameter set is fully shared, the *effective* parameter set is per-agent. And because $\theta^t_i$
is regenerated at every $t$, the architecture responds to capability changes during a rollout.

One nuance for the standing question: **the Hyper Adapter is conditioned on the observation as well as on
capabilities.** So this is not a pure "context → weights" design; it is "context + current input → weights",
the same hybrid Hyper-GoalNet's main variant uses. There is no ablation isolating the observation input to
the hypernetwork.

#### 2.2 Where it sits on the capacity spectrum

The paper draws the spectrum itself (their Fig. 1), from **shared parameters** (left) through **CASH**
(middle) to **individualized parameters** (right). Mapping that onto our capacity ladder:

| Rung | Instance here |
|---|---|
| Input concatenation (weakest) | RNN-EXP: capabilities appended to observations, one fixed network |
| **FiLM (per-channel scale + shift)** | **not evaluated** |
| Low-rank / LoRA | not evaluated |
| Parameter composition | selective parameter sharing (discussed in Related Work as prior art: sharing within groups defined by robot type / action space / inferred role; criticized for needing a small number of *known* types and being unable to generalize) |
| **Full weight generation of a small head** | **CASH** — all weights and biases of a 1–2 layer decoder |
| Full independent parameterization | INDV |

CASH's generated object is small by design: a one- or two-layer MLP decoder sitting on top of a GRU whose
weights are shared and static. **This is what makes the parameter count go down rather than up** — the
hypernetwork replaces a wide decoder rather than adding to it, and the RNN is deliberately narrowed to pay
for the hypernetwork (e.g. MAPPO: baselines use RNN width 128, CASH uses RNN width 32 plus hypernetwork
width 16).

#### 2.3 Measuring behavioural diversity: SND, and its modification

The paper uses **System Neural Diversity** (SND), originally defined for independent policies. Since CASH's
policies are shared but capability-conditioned, they redefine the pairwise distance as the average, over a
set of observations $\mathcal{O}$ collected from rollouts, of the total-variation distance between the
action distributions the *same* network produces when given *different* capability vectors:

$$d(i,j)=\frac{1}{|\mathcal{O}|}\sum_{o_t\in\mathcal{O}} \mathrm{TVD}\!\left(\pi_\theta(o_t\,\Vert\,c^i),\ \pi_\theta(o_t\,\Vert\,c^j)\right),$$

with SND the mean of the upper triangle of the resulting distance matrix. For value-based methods, Q-values
are softmaxed into a categorical distribution first.

**Read this carefully before citing an SND number.** It measures *how much the policy's output changes when
only the capability vector changes, holding the observation fixed*. That is exactly a measure of
**conditioning strength** — and it is why RNN-IMP scores exactly $0.00\pm0.00$ in all six conditions: it
does not take capabilities as input at all, so changing them changes nothing, by construction. SND is
therefore not an independent validation of CASH so much as a direct readout of how much the conditioning
signal moves the policy. It is a useful diagnostic; it is not evidence of good behavior. The paper is
reasonably careful about this — it explicitly says higher diversity does not always correlate with better
performance (citing the INDV comparison), and hypothesizes diversity is "necessary but not sufficient" for
generalization.

*Aside for our own work:* this metric is directly portable. If we ever want to ask "is the modulator
actually doing anything?", the TVD-between-outputs-under-different-context-with-fixed-observation
construction is a clean, cheap answer, and it has a published name.

#### 2.4 The three-way comparison — the valuable part

**The four architectures**, all sharing a common GRU-encoder → MLP-decoder skeleton for fairness:

| Name | Mechanism | Can it handle an unseen robot? |
|---|---|---|
| **INDV** | separate architecture per robot, no sharing | **No** — no network exists for a new robot |
| **RNN-IMP** | shared network, capabilities **not** given; must be inferred from observation history by the GRU | Yes, but poorly |
| **RNN-EXP** | shared network, capabilities **appended to the observation vector** — this is the concatenation-conditioning baseline | Yes |
| **CASH** | shared network, capabilities drive a hypernetwork that emits the decoder's weights | Yes |
| *(RNN-ID, appendix)* | shared network with a one-hot agent ID appended | **No** — IDs do not transfer |

**(a) CASH vs INDV (per-agent networks).** Reported **only via training-curve figures** (their Fig. 2:
returns, SND, and parameter counts), not in a table. The stated findings: CASH is *more sample-efficient*,
performs *marginally better* on both tasks, uses a fraction of the parameters, and has *lower* SND. INDV is
trained on a single fixed team per seed because it cannot handle team changes. **The absence of a numeric
table for this comparison is the weakest evidential point in the paper** — the strongest form of the claim
("soft sharing costs nothing relative to full individualization") rests on smoothed, downsampled,
rolling-averaged curves. Cite it as directional, not quantitative.

**(b) CASH vs the shared baselines, success rate (their Table 1).** JaxMARL, 10 seeds for QMIX and MAPPO,
3 seeds for DAgger. "Out-of-distribution" = teams whose capabilities were sampled outside the training
ranges.

| Algorithm | Architecture | Firefighting ID | Firefighting OOD | Firefighting OOD SND | Mining ID | Mining OOD | Mining OOD SND |
|---|---|---|---|---|---|---|---|
| **QMIX** (value-based) | RNN-IMP | 0.54±0.28 | 0.49±0.22 | 0.00±0.00 | 0.79±0.08 | 0.63±0.12 | 0.00±0.00 |
| | RNN-EXP (concat) | **0.97±0.05** | 0.56±0.26 | 0.15±0.07 | 0.98±0.03 | 0.83±0.15 | 0.07±0.00 |
| | **CASH** | 0.96±0.10 | **0.67±0.09** | 0.28±0.03 | **1.00±0.00** | **0.88±0.12** | 0.16±0.01 |
| **MAPPO** (policy-gradient) | RNN-IMP | 0.21±0.20 | 0.15±0.14 | 0.00±0.00 | 0.61±0.24 | 0.43±0.17 | 0.00±0.00 |
| | RNN-EXP (concat) | 0.71±0.30 | 0.43±0.27 | 0.64±0.03 | **1.00±0.00** | 0.74±0.11 | 0.18±0.03 |
| | **CASH** | 0.71±0.43 | **0.68±0.17** | 0.58±0.03 | 0.98±0.04 | **0.83±0.12** | 0.22±0.06 |
| **DAgger** (imitation) | RNN-IMP | 0.08±0.14 | 0.00±0.00 | 0.00±0.00 | 0.00±0.00 | 0.07±0.08 | 0.00±0.00 |
| | RNN-EXP (concat) | 0.17±0.14 | 0.08±0.14 | 0.02±0.00 | 0.35±0.10 | 0.30±0.10 | 0.03±0.00 |
| | **CASH** | **1.00±0.00** | **0.92±0.14** | 0.08±0.01 | **0.88±0.11** | **0.83±0.10** | 0.06±0.00 |

**How to read this table honestly.**
- **CASH wins all 6 out-of-distribution columns.** That is the paper's claim and it holds.
- **In-distribution, CASH and concatenation are statistically indistinguishable in 4 of 6 cells** (QMIX
  Firefighting 0.96 vs 0.97; MAPPO Firefighting 0.71 vs 0.71; QMIX Mining 1.00 vs 0.98; MAPPO Mining 0.98
  vs 1.00). **Concatenation conditioning is not weak — it is weak *off-distribution*.** This is the single
  most important nuance for the FiLM-vs-hypernetwork question, and it generalizes the same finding from
  HyPoGen (§1) and Hyper-GoalNet (§2): the mechanisms separate under distribution shift, not under fit.
- **The DAgger rows are the outlier and deserve caution.** CASH 1.00/0.92 vs concat 0.17/0.08 is an
  enormous gap — but DAgger uses only **3 seeds**, both baselines are near-total failures (a baseline at
  0.08 is not a calibrated comparison), and DAgger receives "two to three orders of magnitude fewer
  samples" than the RL settings. The paper's own reading is that this shows CASH "can better handle
  data-scarce regimes", which is consistent with HyPoGen's data-fraction sweep (§1, Table 19). I would cite
  the QMIX and MAPPO rows as the primary evidence and the DAgger rows as a data-scarcity observation.
- **Variance is large.** MAPPO/Firefighting CASH is 0.71±0.43 in-distribution — a standard deviation of
  0.43 on a quantity bounded in [0,1] means seeds are bimodal (some runs solve it, some fail). Do not read
  single-cell differences under ~0.15 as real.

**(c) Parameter counts — the efficiency claim (their Tables 2 and 18).**

| Setting | Baselines (RNN-IMP / RNN-EXP) | CASH | Reduction |
|---|---|---|---|
| Robotarium Material Transport | 401 K | **162 K** | 60 % |
| Robotarium Predator-Capture-Prey | 402 K | **164 K** | 59 % |
| 12-agent Firefighting, QMIX | 103 K | **43 K** | 58 % |
| 12-agent Firefighting, MAPPO | 468 K | **170 K** | 64 % |
| 12-agent Mining, QMIX | 403 K | **165 K** | 59 % |
| 12-agent Mining, MAPPO | 469 K | **170 K** | 64 % |

**Protocol note, and it is a good one:** baseline widths were *tuned* (RNN hidden width swept over
{32, 64, 128, 256}, or {512, 1024, 2048, 4096} for DAgger, best selected by test return), and **CASH was
then deliberately built smaller** — e.g. for MAPPO, baselines at width 128 vs CASH at RNN width 32 +
hypernetwork width 16. So the comparison is *tuned-best baseline* vs *deliberately-undersized CASH*, which
is the conservative direction. Smaller baselines were tested and were worse.

**(d) vs ID-based sharing (Appendix G.1, Fig. 9 only — no table).** RNN-ID appends a one-hot agent ID. The
reported finding: ID-sharing is more sample-efficient than INDV but learns lower behavioural diversity, and
"CASH matches or outperforms ID-based methods in both sample efficiency and behavioral diversity". Again
figure-only, so directional.

#### 2.5 Hardware, online adaptation, and scaling

**Robotarium (their Table 2)** — trained with QMIX via MARBLER/EPyMARL; simulation over 3 seeds × 500
episodes; hardware = best seed × 5 episodes.

| Task | Arch | #Params | Sim reward ↑ | Sim makespan ↓ | Sim collisions ↓ | Real reward ↑ | Real makespan ↓ |
|---|---|---|---|---|---|---|---|
| MT | RNN-IMP | 401 K | 2.32±11.86 | 63.85±12.41 | 0.03±0.17 | 21.52±1.57 | 54.20±3.92 |
| MT | RNN-EXP | 401 K | 12.94±8.21 | 53.59±13.10 | 0.02±0.13 | 23.12±2.96 | 50.20±7.39 |
| MT | **CASH** | **162 K** | **14.84±7.91** | **49.79±12.87** | **0.01±0.12** | **23.84±3.72** | **48.40±9.31** |
| PCP | RNN-IMP | 402 K | 64.65±31.92 | 79.72±6.29 | 0.03±0.18 | 69.40±32.65 | 81.00±0.00 |
| PCP | RNN-EXP | 402 K | 61.05±30.54 | 79.60±6.75 | 0.03±0.17 | 31.00±33.12 | 81.00±0.00 |
| PCP | **CASH** | **164 K** | **89.21±33.54** | **76.86±9.28** | **0.02±0.13** | **96.60±18.49** | 81.00±0.00 |

Standard deviations here are enormous relative to the means (PCP sim reward 89.21±33.54 vs 61.05±30.54) —
these are 3-seed hardware-testbed numbers and should be treated as supporting, not decisive.

**Online capability change (their Table 3).** Two zero-shot perturbations applied to already-trained
policies: *Failure* (one random robot's key capability cut by 75 % halfway through) and *Battery Drain*
(all robots' capabilities decay by a discount factor each step). CASH leads in every cell, e.g. PCP Battery
Drain reward 82.56±34.25 (CASH) vs 57.02±29.90 (concat) vs 61.09±31.51 (implicit); MT Battery Drain
11.26±7.91 vs 9.18±8.55 vs −0.39±11.98. **This is the capability that only per-timestep weight generation
gives you** — a concatenation policy also sees the changed capability number, but it must have learned to
respond to that number within one fixed weight matrix.

**Team-size generalization (Appendix F.1, Table 16).** Policies trained on 4 robots, zero-shot deployed on
12: MT task-completion 0.67±0.40 (CASH) vs 0.45±0.39 (implicit) vs 0.32±0.39 (concat); PCP 0.68±0.21 vs
0.67±0.21 vs 0.58±0.25 — i.e. a real gain on MT and a tie on PCP, which the paper attributes to increased
predator/prey density reducing the need for tight coordination.

**Training on 12-agent teams (Appendix G.2.3, Table 18).** CASH wins in-distribution in all four
algorithm×task cells and out-of-distribution in three of four — with **MAPPO/Mining a stated exception**
(CASH 0.71±0.34 vs RNN-IMP 0.90±0.10 out-of-distribution). The paper flags this honestly and suggests
curriculum approaches for large teams. Worth carrying: **the mechanism's advantage is not universal at
scale.**

#### 2.6 Training stability — the most transferable section in the batch

This paper is unusually forthcoming about hypernetworks being hard to train, and gives specific fixes.

1. **LayerNorm before every ReLU in the hypernetwork is mandatory (Appendix B, "Layer normalization is
   crucial to CASH").** A four-layer Hyper Adapter was found to be the better architecture but "difficult to
   optimize... both in reinforcement and imitation learning regimes", attributed to "the combination of
   instabilities inherent in both the learning paradigms as well as hypernetworks themselves". Adding
   LayerNorm before each ReLU "stabilizes learning and greatly improves performance". The ablation (their
   Fig. 5, curves only) reports: improved training stability and **decreased between-seed variance in all
   tasks × algorithms**; significantly better converged returns in all cases except MAPPO/Mining; and for
   DAgger, without LayerNorm, Mining "plummets around timestep 4000 and never recovers" while Firefighting
   "never demonstrates better than random performance".

   **The diagnostic hypothesis they offer is the useful part.** They note prior meta-RL hypernetwork work
   omits normalization and still succeeds, and speculate this is because *those* hypernetworks are fed a
   **strong pretrained encoder's output**, whereas CASH's is "conditioned directly on task observations and
   team capabilities, without the benefit of an encoder for preprocessing." **Prediction for our own work:
   the more raw the conditioning signal, the more a hypernetwork needs normalization.** They explicitly
   leave a systematic study of normalization schemes for deep hypernetworks to future work — an open
   problem, flagged by practitioners who hit it.
2. **Separate hypernetworks for weights and for biases (Appendix C.1).** The Hyper Adapter is implemented as
   *two* hypernetworks — one emitting the target linear layer's weight matrix, one emitting its bias vector.
3. **An unusual initialization scheme, reported with commendable honesty.** Both hypernetworks use
   orthogonal weights and zero bias, but with the **initialization scale set to 0 for the bias-generating
   hypernetwork and 0.2 for the weight-generating one**. Their own comment: *"We could not find a reference
   for this odd initialization scheme in the literature."* Note this is functionally the same family of trick
   as the Bias-Init scheme Hyper-GoalNet had to give HyperZero (§2.6 above): scale down the generated
   perturbation at initialization so the target network starts near a sane default. **Three of the four
   papers in this batch independently report needing an output-scale intervention at initialization; that is
   a pattern, not a coincidence.**
4. **Gradient clipping is on in every configuration.** Max gradient norm: 0.5 (MAPPO), 25 (QMIX-JaxMARL),
   10 (QMIX-EPyMARL), 1 (DAgger). Optimizers: Adam (MAPPO), AdamW with weight decay 1e-5 (QMIX-JaxMARL),
   RMSprop (QMIX-EPyMARL), AdamW with weight decay 0 (DAgger).

**Other hyperparameters worth having.** MAPPO: 10e6 timesteps, lr 2e-3 annealed, 4 update epochs, 4
minibatches, γ 0.99, GAE λ 0.95, clip 0.2, entropy coef 0.01, value coef 0.5. QMIX-JaxMARL: 10e6 timesteps,
lr 0.005 with linear decay, buffer 5000, batch 32, ε 1.0→0.05 over 100 000 steps, mixer embedding dim 32,
mixer hypernetwork hidden dim 64, mixer init scale 1e-5, target update 200, TD(λ) with λ 0.6, γ 0.9.
DAgger: expert buffer 10 000, 1000 initial expert trajectories, 10 iterations × 1000 trajectories,
lr 1e-4, β 1.0 with linear decay, 100 updates/iteration, batch 64.

#### 2.7 Limitations, as stated

- **Lossless communication is assumed** — partial observability is simulated by appending the three nearest
  teammates' relative positions to each robot's observation. Suggested fix: a GNN communication module.
- **New capability *dimensions* cannot be handled at inference** — CASH generalizes to unseen *values* of
  known capabilities, not to a robot that has a capability type never seen in training.
- **The JaxMARL tasks are simple** relative to the hardest heterogeneous-coordination benchmarks. Their
  defence is that the tasks retain "the crucial property that better grounding of heterogeneous capabilities
  tends to yield better performance, as evidenced by RNN-EXP outperforming RNN-IMP and CASH outperforming
  RNN-EXP" — i.e. the benchmark is validated by the monotone ordering of the three conditioning mechanisms.
  That is a reasonable argument but it is also somewhat circular as a defence of the benchmark.

#### 2.8 Notes for this project

- **This is the paper to cite for the RL half of the standing question.** It is the only one in the batch
  where a hypernetwork is trained *inside* an RL loop (QMIX and MAPPO), and it shows the mechanism works
  under both value-based and policy-gradient training, plus imitation, without algorithm-specific
  modification.
- **The three-way result, compressed:** against a per-agent network, the hypernetwork matches performance
  with far fewer parameters and adds generalization the per-agent design cannot have. Against
  concatenation, it *ties in-distribution* and wins out-of-distribution. If our own setting never leaves
  the training distribution, this paper predicts a hypernetwork buys nothing over concatenation.
- **LayerNorm before every ReLU in the hypernetwork, and scale the generated-weight output down at
  initialization.** If anyone here builds a weight generator, those two lines are the difference between a
  run that converges and a run that "never demonstrates better than random performance".
- **The SND metric is directly borrowable** as a "does the modulator actually modulate?" diagnostic:
  hold the observation fixed, vary only the context, measure total-variation distance between the resulting
  action distributions. A modulator with SND ≈ 0 is decorative, by definition.
- **Parameter-count framing matters for how a hypernetwork is sold.** CASH is *smaller* than its baselines
  because it replaces a wide decoder rather than adding a generator on top. Any proposal here should be
  costed the same way.

### Appendix: Section-by-Section Backbone

- **Abstract.** Existing heterogeneous-teaming architectures force a trade-off between expressivity and
  efficiency: shared-parameter designs are sample-efficient but limit behavioural diversity; per-robot
  policies are diverse but inefficient and don't generalize. Key insight — treat these as ends of a
  spectrum. CASH is a **soft weight sharing** architecture using hypernetworks to learn a flexible shared
  policy that adapts to each robot post-training, explicitly encoding the impact of capabilities (speed,
  payload) on collective behavior, enabling **zero-shot generalization to unseen robots or team
  compositions**. Evaluated on multiple tasks, three learning paradigms (imitation, value-based RL,
  policy-gradient RL), JaxMARL and Robotarium — outperforming baselines on performance and sample
  efficiency "all with 60 %–80 % fewer learnable parameters".
- **§1 Introduction.** The wildfire motivating example; team composition unknown until runtime and
  capabilities can deteriorate; five claimed practical benefits (learning efficiency, zero-shot
  generalization, automatic diversity level, online capability adaptation, paradigm-agnostic).
- **§2 Related work.** *Architectures for heterogeneous coordination* — shared-parameter designs improve
  cooperation/efficiency/scalability but limit diversity; ID-appending designs "often fail to learn
  sufficient behavioral diversity and are not robust to noisy environments"; individualized policies are
  diverse but costly and cannot generalize to unseen robots; **selective parameter sharing** (groups by
  robot type / action space / inferred role) is the existing middle ground but assumes a small number of
  known types. *Hypernetworks in multi-agent learning* — QMIX is the notable prior use, but there the
  hypernetwork **mixes individual value estimates** for centralized training; CASH instead uses it to
  determine parameters **inside** each robot's policy/value network. One parallel work conditions a
  multi-agent hypernetwork on **agent IDs**; CASH conditions on **capabilities and observations**, which
  is what enables generalization to unseen robots.
- **§3 Problem formulation and objectives.** Dec-POMDP tuple; per-robot decentralized policies; the
  capability augmentation $C^t=\{c^t_1,\dots,c^t_n\}$, $c^t_i\in\mathbb{R}^m$; nominal capabilities obtained
  from specs or sensors; modified policy $a^t_i\sim\pi_i(o^t_i,C^t)$; the stated objective of a single
  shared-parameter architecture that is diverse and generalizes.
- **§4 CASH.** Three modules — **RNN Encoder** (GRU, for long horizons and partial observability),
  **Adaptive Decoder** (1- or 2-layer MLP; only its *structure* is identical across robots, its parameters
  are not), **Hyper Adapter** (hypernetwork conditioned on ego capabilities, team capabilities, and ego
  observation). Justification for hypernetworks: adaptation across data contexts, robustness to
  distributional shift, prior successes in multi-task policy encoding, gradient estimation in Q-learning,
  and meta-learning parameter efficiency. Formal forward pass; the observation that $f_\psi$ and $h_\phi$
  lack the index $i$; the soft-parameter-sharing framing; per-timestep regeneration enabling online
  capability adaptation.
- **§5 Experimental evaluation.**
  - *§5.1 JaxMARL.* Architecture variants INDV / RNN-IMP / RNN-EXP / CASH, all sharing an
    RNN-encoder→MLP-decoder skeleton. Learning paradigms QMIX (off-policy), MAPPO (on-policy), DAgger
    (imitation, contributed by the authors as a new JaxMARL implementation); CTDE assumption; 10 seeds for
    QMIX/MAPPO, 3 for DAgger. Tasks: **Firefighting** (3 robots, 2 fires, robots vary in speed and water
    capacity) and **Mining** (4 robots, 2 deposit zones, robots vary in per-resource carrying capacity).
    Metrics: training returns, success rate, and modified SND. Training teams sampled from a capability pool
    covering a set range; unseen teams sampled from ranges *outside* it. Findings, in order: CASH improves
    sample efficiency and generalization without sacrificing performance vs INDV (and learns *appropriate*
    rather than superfluous diversity); CASH improves parameter and sample efficiency among shared-parameter
    methods (60–80 % fewer parameters), with benefits "exaggerated for imitation learning" where sample
    budgets are 2–3 orders of magnitude smaller; CASH improves zero-shot generalization to unseen
    compositions and capabilities (Table 1), with the explicit observation that RNN-EXP matches CASH
    **in-distribution** under QMIX/MAPPO but is "vastly outperformed" out-of-distribution; the hypothesis
    that behavioural diversity is necessary but not sufficient for generalization.
  - *§5.2 Robotarium.* MARBLER platform bridging Robotarium to EPyMARL; QMIX training. Tasks **Material
    Transport** (4 robots, varying speed and carrying capacity) and **Predator Capture Prey** (2 sensing +
    2 capture robots, varying sensing and capture radii). Two online-adaptation scenarios: **Failure**
    (random robot's capability cut 75 % mid-episode) and **Battery Drain** (all capabilities decayed each
    step). Metrics reward / makespan / collisions; 3 seeds × 500 episodes in sim, best seed × 5 episodes on
    hardware. Results Tables 2–3; the note that hardware rewards exceed simulation because Robotarium
    barrier certificates prevent collisions.
- **§6 Conclusion.** CASH establishes a new middle ground between shared and individualized parameters;
  deployable decentralized; supports imitation, value-based and policy-based RL.
- **§7 Limitations.** Lossless communication assumed (3 nearest neighbours' relative positions appended);
  cannot handle entirely new capability *dimensions* at inference; JaxMARL tasks simpler than the hardest
  benchmarks, defended by the monotone RNN-IMP < RNN-EXP < CASH ordering.
- **Appendix A.** SND definition and the modification for capability-conditioned shared policies; TVD over
  softmaxed Q-values for value-based methods.
- **Appendix B.** *Layer normalization is crucial to CASH* — the LayerNorm ablation (Fig. 5), the DAgger
  collapse cases, corroboration of the original Hypernetworks paper's gradient-flow suggestion, and the
  speculation that prior meta-RL hypernetworks escape the problem by being fed a pretrained encoder.
- **Appendix C.** C.1 Hyper-Adapter — four-layer hypernetwork, difficulty optimizing it, LayerNorm before
  each ReLU, separate weight- and bias-generating hypernetworks, orthogonal/zero-bias initialization with
  scales 0 and 0.2. C.2–C.5 hyperparameters for MAPPO, QMIX-JaxMARL, QMIX-EPyMARL and DAgger (Tables 4–7),
  each with the width-ablation protocol and the resulting CASH width choice.
- **Appendix D.** Capability sampling — Firefighting (fires 0.2–0.3 strength; training capacity 0.1–0.3,
  acceleration 1–3; test teams sampled out of bounds in both, with other agents matched to keep the task
  feasible), Mining (training capacities summing to 0.5 per agent, test capacities summing to 1.0),
  Material Transport, Predator Capture Prey (capture radii 0.10–0.20, sensing radii 0.20–0.40).
- **Appendix E.** Environment implementations (JaxMARL extensions plus a DAgger training script; MARBLER
  tasks extended to sample from capability sets).
- **Appendix F.** MARBLER training curves; F.1 team-size generalization, 4 → 12 robots zero-shot (Table 16).
- **Appendix G.** G.1 comparison against ID-based methods (RNN-ID, Fig. 9). G.2 training on 12-agent teams —
  scaled environments, width/learning-rate ablation protocol (Table 17), and results (Table 18) including
  the MAPPO/Mining exception where RNN-IMP generalizes better.

---
