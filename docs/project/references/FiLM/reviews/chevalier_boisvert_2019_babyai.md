---
title: "BabyAI: A Platform to Study the Sample Efficiency of Grounded Language Learning"
authors: ["Maxime Chevalier-Boisvert", "Dzmitry Bahdanau", "Salem Lahlou", "Lucas Willems", "Chitwan Saharia", "Thien Huu Nguyen", "Yoshua Bengio"]
year: 2019
venue: "Published as a conference paper at ICLR 2019 (PDF running header); arXiv:1810.08272v4 [cs.AI], 19 Dec 2019"
slug: chevalier_boisvert_2019_babyai
source_pdf: docs/project/references/FiLM/sources/Chevalier-Boisvert et al. 2019 - BabyAI - A platform to study the sample efficiency of grounded language learning.pdf
topic: FiLM
---

# BabyAI: A Platform to Study the Sample Efficiency of Grounded Language Learning

## Plain-English entry point

This is the paper that made **FiLM the default architecture for instruction-following agents in gridworlds** — and it is worth being blunt up front about *how* it did that: not by testing the mechanism, but by using it in a benchmark that everyone subsequently adopted.

The paper's own subject is sample efficiency. The authors build **MiniGrid**, a fast partially-observed 2-D gridworld, and **BabyAI**, a suite of 19 levels of increasing difficulty in which an agent is given a synthetic-English instruction ("put the blue key next to the green ball") and must carry it out from a 7×7 egocentric view. They also ship a hand-written **bot** that solves any level, standing in for a human teacher who can supply demonstrations on demand. The question they ask is: *how much teaching does a modern deep agent need before it can follow these instructions?* The answer is a deliberate embarrassment — on the order of **10⁵ demonstrations** for tasks a child would master in minutes, and **10⁶ episodes** of reinforcement learning for the same tasks. Their stated conclusion is that human-in-the-loop language teaching needs "an improvement of at least three orders of magnitude".

For this corpus, the load-bearing content is **four sentences in §4.1** describing the baseline agent. The instruction is encoded by a GRU; the 7×7×3 observation is processed by a small convolutional network containing **two batch-normalized FiLM layers**, which is where the instruction enters; an **LSTM** downstream of the FiLM module carries memory across steps; the whole thing is trained either by behavioral cloning or by **PPO**. The authors then state the equivalence that this corpus has been circling: *"Our model is thus similar to the gated-attention model used by Chaplot et al. (2018), inasmuch as gated attention is equivalent to using FiLM without biases and only at the output layer."* That is the FiLM authors' own lineage claim, restated by a different group, in print — and it is the cleanest citation available for treating [`chaplot_2018_gated_attention.md`](chaplot_2018_gated_attention.md) and [`perez_2018_film.md`](perez_2018_film.md) as the same mechanism family.

**The honest verdict on evidence: there is none here.** BabyAI contains no FiLM ablation, no concatenation baseline, no gain statistics, no architecture sweep of any kind. The FiLM choice is asserted in one clause and never tested. Its influence on the field comes entirely from being the reference implementation of a widely-used benchmark. Anyone citing BabyAI as *evidence* that FiLM helps in gridworld RL is citing an architecture description.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | The **Baby Language instruction** $c$ for the mission (a variable-length token string), encoded by a GRU — bidirectional, 256 units, with Bahdanau attention over its states in the Large model; unidirectional, no attention, in the Small model. **Episode-constant** and exogenous. Not the observation; not internal state. |
| **What is modulated** | The **observation encoder** — a small convolutional network over the 7×7×3 symbolic egocentric view. Modulation happens **upstream of the LSTM memory** and therefore upstream of both the actor and critic heads, which share the trunk. |
| **Modulation operator** | **Full affine FiLM** (per-channel scale + shift), applied after batch normalisation. The paper names it only as "two batch-normalized FiLM (Perez et al., 2017) layers" and gives no equations. |
| **Granularity** | Per-channel, per-FiLM-layer (two layers ⇒ two independent $(\gamma, \beta)$ sets). |
| **Placement / number of sites** | **Two sites**, inside the conv stack, before the recurrent memory. Explicitly contrasted with Chaplot's *one* site "only at the output layer". |
| **What it is for** | Grounded language understanding + compositional generalization over a language with $2.48 \times 10^{19}$ possible instructions; a shared architecture across all 19 levels and both learning paradigms. |
| **RL algorithm** | **PPO** with parallel data collection (4 epochs, 64 rollouts of length 40, $\gamma = 0.99$, GAE $\lambda = 0.99$, Adam $\alpha = 10^{-4}$). Imitation arm: behavioral cloning from bot demonstrations, plus interactive (DAgger-like) variants. |
| **Ablated against concatenation?** | **No.** No architectural ablation appears anywhere in the paper. All experiments vary the *data* (how much, from which expert, in what curriculum), never the *model*. |
| **Reported instability / failure mode** | None attributed to modulation. The reported failure modes are (a) catastrophic sample inefficiency, and (b) a **counter-intuitive negative curriculum result** — pretraining on `GoToObjMaze` makes the target level *harder* (444–602 k demos with pretraining vs. 341–409 k without). |

## Section-ordered backbone

**Abstract.** Introduces BabyAI: 19 levels of increasing difficulty teaching a combinatorially rich synthetic language that is a proper subset of English, plus a hand-crafted bot agent simulating a human teacher. Reports the estimated supervision needed by neural RL and behavioral-cloning agents. Headline claim: "current deep learning methods are not yet sufficiently sample-efficient in the context of learning a language with compositional properties".

**1. Introduction.** Motivation is human-in-the-loop training of language-following agents, from both a technological angle (users will want to customise their assistants) and a scientific one (synergy with developmental psychology and language acquisition). BabyAI substitutes a simulated expert for a real human. Two capabilities of human teachers are targeted: **curriculum learning** (19 levels of graded difficulty) and **interactive teaching** (the bot can generate fresh demonstrations on the fly, or advise mid-episode, supporting DAgger/TAMER/preference-style protocols). The obstacle is data volume: current methods need "millions of reward function queries or hundreds of thousands of demonstrations". Contributions: the platform, and baseline sample-efficiency results for all levels.

**2. Related Work.** Positions BabyAI against other synthetic-language environments (Hermann et al. 2017; **Chaplot et al. 2018**; Yu et al. 2018; Wu et al. 2018) by three combined features: **world-state manipulation** (the 3-D environments including Chaplot's Doom world allow navigation but not moving objects), **partial observability** (unlike Bahdanau et al. 2018's gridworld), and a **systematically defined language** — a context-free grammar with defined semantics for every utterance, rather than instruction templates. Adds the simulated human expert as the distinguishing asset. Notes that general-purpose testbeds (ALE, DM-30, MazeBase, ViZDoom, AI2-Thor, PycoLab, Gazebo) have no language, and that under a human-in-the-loop cost model imitation learning is more appealing than RL because more learning is extracted per unit of human input.

**3. BabyAI Platform.**

*3.1 MiniGrid environment.* Partially observable 2-D gridworld; entities are agent, balls, boxes, doors, keys, walls, goals, each with a colour; objects can be picked up, dropped and moved; doors unlock with colour-matched keys. Per step the agent receives a **7×7 view of the cells in front of it** plus the instruction string. Throughput exceeds **3000 frames/second** on a laptop — the design is explicitly optimised for the many-runs-per-experiment demands of sample-efficiency research.

*3.2 Baby Language.* A synthetic subset of English defined by a BNF grammar (Figure 2) with **$2.48 \times 10^{19}$ possible instructions**. Clauses: `go to`, `pick up`, `open`, `put ... next to`. Composition via `and` (unordered conjunction), `then` and `after you` (sequencing). Descriptors combine article, colour, object type and a relative location spec (`on your left`, `behind you`, …). A **verifier** checks whether an action sequence satisfies an instruction. Descriptors may be ambiguous by design ("go to a red door" is satisfied by any red door), and instructions leave execution details implicit — the agent may have to find a key or move obstacles without being told.

*3.3 BabyAI levels.* A **level** is a distribution over missions (instruction + initial state). 19 levels are built by selecting **competencies**: ROOM, DISTR-BOX, DISTR, MAZE, UNBLOCK, UNLOCK, IMP-UNLOCK ("guessing" to unlock a door not mentioned in the instruction), GOTO, OPEN, PICKUP, PUT, LOC, SEQ. Table 1 maps levels to competencies, culminating in `BossLevel`.

*3.4 The bot agent.* A hand-engineered solver standing in for the human teacher, with direct access to the parsed instruction tree (it does not parse language). It runs a **stack machine** over subgoals — `Open`, `Close`, `Pickup`, `Drop`, `GoNextTo`, `Explore` — which can interrupt and resume each other. Critically it maintains a **visibility mask** of seen and unseen cells so that it uses only information it could realistically have acquired, and it uses shortest-path search for navigation.

**4. Experiments.**

*4.1 Setup — the architecture (the FiLM section).* Inputs: 7×7×3 symbolic egocentric observation $x_t$ and variable-length instruction $c$. "We use a GRU to encode the instruction and a convolutional network with **two batch-normalized FiLM layers** to jointly process the observation and the instruction. An **LSTM** memory is used to integrate representations produced by the FiLM module at each step." Then the equivalence statement to Chaplot's gated attention (FiLM without biases, at the output layer only). Two model sizes: **Large** (LSTM 2048 units, bidirectional GRU 256 with attention over GRU states) and **Small** (LSTM 128, unidirectional GRU, no attention). Optimiser Adam, $\alpha = 10^{-4}$, $\beta_1 = 0.9$, $\beta_2 = 0.999$, $\epsilon = 10^{-5}$. IL truncates backpropagation through time at 20 steps (Small) / 80 steps (Large). RL uses **PPO** with 4 epochs over 64 rollouts of length 40 from parallel processes; reward is non-zero **only on full mission completion**, with magnitude $1 - 0.9\,n/n_{\max}$; $\gamma = 0.99$, GAE $\lambda = 0.99$. Metric is success rate. Compute cost: **20–50 GPUs for two weeks**, with at least as much again for preliminary work.

*4.2 Baseline results.* Large model, 1 M demonstrations per level, 40 epochs (single-room levels) / 20 epochs (maze levels), validation on 512 episodes (Table 2). All single-room levels reach 100 %; success degrades with demonstration length, down to **`BossLevel` 77 %** and `GoToImpUnlock` 87.2 %. Sample efficiency is then defined as the minimum data needed to reach **99 % success**, estimated by fitting a **Gaussian Process** to (dataset size, best smoothed validation score) pairs on a geometric grid of sizes and reading off the posterior over $k_{\min}$; a 99 % credible interval is reported (Table 3). RL sample efficiency is **2–10× worse** than IL: e.g. `GoToLocal` needs 148–193 k demonstrations versus 903 k–1114 k RL episodes. Demonstrations produced by an **RL-trained expert** are easier to imitate than the bot's — dramatically so on `GoToRedBallGrey` (1.53–2.11 k vs. 8.43–12.4 k) — which the authors attribute to the RL expert sharing the learner's architecture.

*4.3 Curriculum learning.* Five (base, target) pretraining pairs (Table 4). Pretraining on `GoToLocal` helps in four cases (e.g. `PickupLoc`: 204–241 k → 71.2–88.9 k). Pretraining on `GoToObjMaze` alone **hurts** (`GoTo`: 341–409 k → 444–602 k). The authors flag this as an interesting counter-intuitive result showing that current methods cannot exploit an available curriculum.

*4.4 Interactive learning.* Start from $2^{10}$ demonstrations; iteratively grow the dataset by $2^{1/4}$ using bot demonstrations **on missions the agent failed**, retraining from scratch each round. Gains of 4× on `GoToRedBallGrey` and 1.5–2× on `GoToRedBall` / `GoToLocal` (Table 5).

**5. Conclusion & Future Work.** Current IL and RL methods "scale and generalize poorly" on compositional tasks; curriculum and interactive learning give measurable but insufficient gains; three orders of magnitude are needed for a real human in the loop. Suggested direction: architectures with **explicit modularity and subroutines** — Neural Module Networks, Neural Programmer-Interpreters — i.e. the authors' own proposed fix is *more* structured conditional computation, not less.

**Appendices.** *A*: sample-efficiency estimation, including the GP regression protocol for IL and the RL confidence intervals. *B*: MiniGrid specification — grid world, sparse reward $1 - 0.9\,(\text{step\_count}/\text{max\_steps})$, seven actions (turn left, turn right, forward, pick up, drop, toggle, done), and the **observation space**: partial, egocentric, 7×7 tiles, blocked by walls and closed doors, encoded as a 7×7×3 integer tensor (object type, colour, door state) — explicitly **not RGB**, chosen for space efficiency and training speed. *C*: bot implementation — instruction-to-subgoal stacks and the subgoal processing diagrams.

## Phase 1 — Undergraduate-level synthesis

**What the platform is.** A small grid of rooms seen through a 7×7 window in front of the agent, plus a sentence telling it what to do. The sentences come from a generative grammar, so you can produce as many as you like, verify automatically whether the agent obeyed, and grade tasks from "go to the blue ball in one room" up to "pick up the grey box behind you, then go to the grey key and open a door" — where the door in question happens to be locked and the instruction never says so.

**What the agent is.** One neural network reused for every level. A recurrent text encoder reads the sentence. A small convolutional network reads the current 7×7 view. The sentence does not get pasted onto the picture features; instead it is turned into a set of per-channel multipliers and offsets that **re-tune the convolutional network** at two points inside it — that is FiLM. The re-tuned picture features then go into an LSTM, which remembers what the agent has seen across the episode, and the LSTM feeds the action and value outputs.

**Why FiLM here rather than concatenation.** The authors give the reason implicitly by citing Chaplot: the earlier gated-attention agent showed that multiplying instruction-derived gains into visual channels helps in exactly this kind of task, and FiLM is the strictly more general version of that operation (it has offsets as well as multipliers, and can be applied at any depth, not only at the top). BabyAI adopts the more general version without re-running the comparison.

**The headline finding — and it is a negative one.** Even the easiest level, "go to the red ball" in a single room with grey distractors, needs roughly 8–12 thousand demonstrations, or 16–17 thousand reinforcement-learning episodes, before the agent is 99 % reliable. Slightly harder levels need hundreds of thousands. `BossLevel` is not solved at all — 77 % with a million demonstrations. Reinforcement learning is 2–10× hungrier than imitation. Curriculum pretraining sometimes helps and sometimes actively hurts. The paper's own summary is that a **1000×** improvement is needed before a human could plausibly teach one of these agents.

**Initial takeaway for this corpus.** BabyAI is the reason "FiLM-conditioned CNN + LSTM + PPO" is the *de facto* reference agent for gridworld instruction following. It is a strong precedent for what such an architecture should look like, and **zero evidence** about whether the FiLM part is doing any work.

## Phase 2 — Graduate-level deep dive

### 2.1 The architecture, reconstructed from the four sentences the paper gives

The paper provides no architecture figure and no equations, so what follows is the literal content of §4.1 written out, with the FiLM operator supplied from Perez et al. 2018 (which the paper cites as its definition) and *nothing else inferred*.

Let $x_t \in \mathbb{Z}^{7 \times 7 \times 3}$ be the symbolic egocentric observation (object type, colour, door state per cell) and $c = (w_1, \dots, w_T)$ the instruction tokens.

**Instruction encoder.**

$$
z \;=\; \mathrm{GRU}_{\theta_{\text{gru}}}(c) \;\in\; \mathbb{R}^{256} \quad \text{(Large: bidirectional, plus attention over GRU states; Small: unidirectional, 128-unit memory downstream)} .
$$

The Large model's attention (Bahdanau et al. 2015) means $z$ is a *weighted read* over the token states rather than a final hidden state; the paper does not say what the attention query is.

**Observation encoder with two FiLM sites.** Writing $F^{(\ell)} \in \mathbb{R}^{H_\ell \times W_\ell \times C_\ell}$ for the pre-activation of conv block $\ell \in \{1, 2\}$, batch normalisation $\mathrm{BN}$, and per-channel affine parameters produced from $z$,

$$
\gamma^{(\ell)}(z) = W^{(\ell)}_\gamma z + b^{(\ell)}_\gamma, \qquad
\beta^{(\ell)}(z) = W^{(\ell)}_\beta z + b^{(\ell)}_\beta, \qquad W^{(\ell)}_\bullet \in \mathbb{R}^{C_\ell \times 256},
$$

$$
\widetilde F^{(\ell)}_{h,w,c} \;=\; \gamma^{(\ell)}_c(z)\;\bigl[\mathrm{BN}(F^{(\ell)})\bigr]_{h,w,c} \;+\; \beta^{(\ell)}_c(z),
\qquad
h^{(\ell)} = \mathrm{ReLU}\bigl(\widetilde F^{(\ell)}\bigr).
$$

The phrase "batch-normalized FiLM layers" matters: because $\mathrm{BN}$ removes the per-channel mean and scale *before* the conditional affine is applied, the modulator is not competing with an unconditional affine for the same degree of freedom — this is exactly the **conditional batch normalisation** construction (see [`dumoulin_2017_cond_instance_norm.md`](dumoulin_2017_cond_instance_norm.md)), of which FiLM is the generalisation. Placing normalisation between the convolution and the gain also means a large $\gamma$ cannot compound across layers through drifting activation statistics, which is a quiet stability property worth naming because the corpus has flagged gain blow-up as unmeasured everywhere.

**Memory and heads.**

$$
m_t \;=\; \mathrm{LSTM}\bigl(m_{t-1},\; \mathrm{flatten}(h^{(2)}_t)\bigr), \qquad
\pi(a \mid m_t) = \mathrm{softmax}(W_\pi m_t), \qquad V(m_t) = w_V^\top m_t .
$$

Two placement facts follow, and both are directly relevant to any recurrent modulated policy:

1. **Modulation is upstream of memory.** The FiLM layers act on the *current frame only*; the LSTM integrates already-modulated features. The recurrent state is therefore a summary of a conditionally-filtered observation stream, not an unfiltered one. If the conditioner changed mid-episode, the LSTM's memory would contain features computed under a *previous* modulation — a representational discontinuity that BabyAI never encounters because $z$ is fixed per episode.
2. **Actor and critic share the modulated trunk.** There is no separate critic modulator, and the value head's gradient flows back through $\gamma, \beta$. BabyAI thus provides a large-scale existence proof that a **modulated shared trunk trains stably under PPO** in a sparse-reward gridworld — 19 levels, up to $10^6$ episodes — even though it provides no comparison to the unmodulated alternative.

### 2.2 The lineage claim, quoted exactly

> "Our model is thus similar to the gated-attention model used by Chaplot et al. (2018), inasmuch as **gated attention is equivalent to using FiLM without biases and only at the output layer**." (§4.1)

This is the citation the corpus should use whenever it treats gain-only gating and full affine FiLM as one mechanism family with two settings of two switches — *is there a shift term?* and *how many injection sites?* Read together with Chaplot's Table 1 (gain-only, one site, beats concatenation decisively in A3C) and BabyAI's silence (full affine, two sites, never compared to anything), the pair makes the shape of the evidence gap very visible: **the field moved from the tested variant to the untested, more expressive one without measuring the step.**

### 2.3 The sample-efficiency numbers (Tables 2, 3, 5)

Sample efficiency is defined as the minimum number of demonstrations (IL) or episodes (RL) required to reach **99 % success**, estimated by GP interpolation over runs at geometrically spaced dataset sizes $k_i = 2^{l_0 + (i-1)d}$ with $d = 0.2$, scoring each run by the best smoothed validation performance within $2T$ training steps, where $T$ is the mean number of steps needed at $10^6$ demonstrations. Intervals are 99 % credible (IL) or confidence (RL). All figures in thousands.

| Level | IL from bot | **RL (PPO)** | IL from RL expert | Interactive IL from bot |
|---|---|---|---|---|
| GoToRedBallGrey | 8.43 – 12.4 | **15.9 – 17.4** | 1.53 – 2.11 | 1.71 – 1.88 |
| GoToRedBall | 49.7 – 62.0 | **261.1 – 333.6** | 36.6 – 44.5 | 31.8 – 36.0 |
| GoToLocal | 148.5 – 193.2 | **903 – 1114** | 74.2 – 81.8 | 93 – 107 |
| PickupLoc | 204.3 – 241.2 | **1447 – 1643** | — | — |
| PutNextLocal | 244.6 – 322.7 | **2186 – 2727** | — | — |
| GoTo | 341.1 – 408.5 | **816 – 1964** | — | — |

Baseline success with 1 M demonstrations (Table 2, Large model, 512-episode validation): 100 % on all single-room levels; `GoToSeq` 95.4 %; `SynthSeq` 87.7 %; `GoToImpUnlock` 87.2 %; **`BossLevel` 77 %**. Demonstration length is the best single predictor of difficulty (`BossLevel` mean 84.3 ± 64.5 steps).

Curriculum results (Table 4, thousands of demonstrations to solve `GoTo`): from scratch 341–409; pretrained on `GoToLocal` 183–216; pretrained on `GoToObjMaze` **444–602** (worse than scratch); pretrained on both 173–216. And `GoToLocal` → `PickupLoc`: 204–241 → 71.2–88.9.

Three observations worth carrying forward. (i) The **RL/IL ratio grows with level difficulty** — 1.4× on `GoToRedBallGrey`, ~5× on `GoToRedBall`, ~6× on `GoToLocal`, ~7× on `PickupLoc` — consistent with the sparse terminal reward giving progressively less signal per episode as horizons lengthen. (ii) **A learned expert is a better teacher than an optimal one**: imitating the RL agent needs 4–6× fewer demonstrations than imitating the bot, which the authors attribute to architecture matching (the RL expert's state–action distribution is realisable by the learner; the bot's shortest-path behaviour is not). This is a general caution about distilling from a hand-written oracle. (iii) **A curriculum can be actively harmful**, and the paper does not diagnose why — an unexplained negative transfer result sitting in a benchmark paper that thousands of later papers cite for its numbers.

### 2.4 What is and is not evidence here

**Is evidence:** that a FiLM-conditioned CNN + LSTM trunk trains to 100 % on single-room instruction following under behavioral cloning, and to 99 % under PPO with a sparse terminal reward, across 19 procedurally generated levels — i.e. the architecture *works* and is *stable* at scale in an on-policy gridworld agent. This is the closest environment class in the whole corpus to a small gridworld RL setting, so as an existence proof it carries real weight.

**Is not evidence:** anything comparative about the modulation operator. Specifically the paper contains **no** concatenation baseline, **no** gain-only vs. affine comparison, **no** injection-depth sweep, **no** report of $\gamma$ statistics, saturation, or dead channels, and **no** ablation of the batch-normalisation placement. Every experiment in §4 varies the *data* — quantity, expert source, curriculum, interactivity — with the model held fixed. The word "FiLM" appears in the body exactly twice, both in §4.1.

**A lead, flagged as outside this PDF:** a follow-up by an overlapping author group ("BabyAI 1.1") is reported to have revised this baseline architecture, and if so it would be the natural place to look for the missing architecture ablation. That claim is **not verifiable from this source file** and should be checked before being cited; the `literature-curator` or a fresh `academic-pdf-fetch` is the right route.

### 2.5 Relevance to the corpus's standing questions

- **On "does anything condition on the current observation?"** BabyAI does **not**. The conditioner is the instruction, fixed for the whole episode; the modulated stream is the observation encoder. The direction of information flow is instruction → observation features, never observation → its own gains. BabyAI therefore reinforces rather than relieves the corpus's finding that observation-driven modulation is unprecedented in RL.
- **On modulating the critic.** Modulation sits in a shared trunk, so the critic *is* modulated, and no problem is reported over very long PPO runs. That is weak positive evidence — weak because it is unremarked and uncontrolled, positive because the setting (on-policy, bootstrapped value, sparse reward, recurrent) is close to ours.
- **On injection depth.** Two sites, both inside the conv stack, none in the recurrent core, none in the heads. Combined with Chaplot's one site and Nikulin's `film_first`/`film_last`/`film_full` sweep, the corpus's published prior for "how many sites" in RL remains 1–2, well below the per-block saturation used in vision.
- **On instability.** Nothing reported. Note that BN-before-FiLM removes one of the plausible routes to gain blow-up, so BabyAI's silence is not informative about an un-normalised modulated network.

## Connections

- **[`chaplot_2018_gated_attention.md`](chaplot_2018_gated_attention.md)** — the direct predecessor, cited by name in both §2 and §4.1. BabyAI supplies the printed statement that gated attention *is* FiLM without biases at the output layer, and simultaneously demonstrates the field's move to the untested general version. The two reviews should always be read as a pair: Chaplot has the ablation and the weaker operator; BabyAI has the stronger operator and no ablation.
- **[`perez_2018_film.md`](perez_2018_film.md)** — cited as the definition of the operator (as "Perez et al., 2017", the arXiv year). BabyAI transplants FiLM from CLEVR visual question answering into a partially-observed sequential-decision setting with memory, which is the non-trivial step; it does not re-validate any of Perez et al.'s design ablations in that new setting.
- **[`dumoulin_2017_cond_instance_norm.md`](dumoulin_2017_cond_instance_norm.md)** and **[`santurkar_2018_batchnorm_optimization.md`](santurkar_2018_batchnorm_optimization.md)** — the "batch-normalized FiLM layers" phrasing places BabyAI in the conditional-normalisation lineage. Santurkar's analysis of why BN smooths the optimisation landscape is the mechanism by which BN-then-FiLM plausibly keeps a conditional gain well-behaved; nobody has tested this composition in RL.
- **[`andreas_2016_neural_module_networks.md`](andreas_2016_neural_module_networks.md)** — BabyAI's §5 names Neural Module Networks as the *recommended future direction* for closing the sample-efficiency gap. The benchmark's own authors thus regard feature-wise modulation as insufficiently structured for compositional generalization, which is a notable in-corpus endorsement of the discrete-composition alternative over the affine one.
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §8 (evidence-quality table)** — add BabyAI as an **"architecture description only"** row: *"FiLM-conditioned CNN+LSTM is the reference gridworld instruction-following agent — No ablation; the model is held fixed while data is varied — Architecture description."* It should not be counted among the mechanism ablations, and its enormous citation count should not be mistaken for evidential weight on the operator question.
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §10.2 (injection sites in recurrent policies)** — BabyAI is a *data point* for that gap, not an answer: two sites, chosen without justification, never swept, in the most-cited recurrent FiLM agent in the literature.
- **Project-side relevance** — the closest published architecture to a small recurrent gridworld agent with feature-wise conditioning, and therefore the natural template and the natural cautionary tale. Template: conditioning enters the observation encoder upstream of the recurrent core, with normalisation before the conditional affine, and trains stably under PPO with a sparse terminal reward. Caution: the fact that this is standard practice is a fact about citation dynamics, not about measured benefit — so a project ablation comparing our modulated agent against a concatenation control is *not* redundant with the literature; it is measuring something the literature's flagship gridworld paper never measured. Any implementation follow-up belongs with `senior-developer` as an `issue_plan`; this review proposes no code changes.
