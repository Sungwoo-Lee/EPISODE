---
title: "Backpropamine: Training self-modifying neural networks with differentiable neuromodulated plasticity"
authors: "Thomas Miconi, Aditya Rawal, Jeff Clune, Kenneth O. Stanley"
year: 2019
venue: "Published as a conference paper at ICLR 2019 (Uber AI Labs); arXiv:2002.10585v1 [cs.NE]"
slug: "miconi_2019_backpropamine"
source_pdf: "sources/Miconi et al. 2019 - Backpropamine - Training self-modifying neural networks with differentiable neuromodulated plasticity.pdf"
topic: "neuromodulatory_algorithms"
---

## Plain-English entry point

Almost every neuromodulation paper in this corpus modulates **what a neuron outputs** — a signal computed inside the network multiplies or shifts the activity of other units, and the network's weights sit still while this happens. This paper does something categorically different: its neuromodulatory signal modulates **how fast the network's own weights change**. Nothing about the activations is gated. What is gated is the *learning rule* — specifically, the size and sign of the weight update that a connection receives at each timestep.

The setup is: every recurrent connection carries two parts. A **fixed part**, the ordinary trained weight, which does not change during an episode. And a **plastic part**, a running "Hebbian trace" that accumulates the product of the sending neuron's activity and the receiving neuron's activity — the textbook "fire together, wire together" rule — and which *does* change, continuously, inside a single episode. The network's effective connection strength at any moment is the fixed part plus a scaled copy of the plastic part. Backpropamine's contribution is to put a scalar signal `M(t)`, computed by the network itself from its own hidden state, in front of that Hebbian accumulation. When `M(t)` is near zero the connection is frozen; when it is large and positive the connection writes in what just happened; when it is negative it writes in the *opposite* of what just happened. The network therefore decides, moment to moment, when and where to rewrite itself. Because every step of this is differentiable, ordinary backpropagation-through-time can train the machinery that produces `M(t)` — which had previously only been achievable with evolutionary algorithms on networks of a few hundred connections.

**What the evidence actually is.** Two of the three experiments are reinforcement learning, meta-trained with **A2C** (Advantage Actor-Critic, a standard policy-gradient algorithm), on two small custom tasks the authors built themselves: a cue-reward association task and a 9×9 grid-maze foraging task. Neither is a standard RL benchmark suite — there is no Atari, no MuJoCo, no Meta-World here. The third experiment is **supervised**, not RL: word-level language modelling on Penn TreeBank, where a neuromodulated plastic LSTM beats a parameter-matched standard LSTM by about 1.7 perplexity points. So the paper's headline "works on RL and supervised tasks" is true, but the RL evidence is two toy tasks at the scale of a few hundred recurrent neurons, and the large-scale evidence (24 M parameters) is entirely supervised. Any report citing this paper for RL should say "small custom meta-RL tasks under A2C", not "RL benchmarks".

**Why it matters for the FiLM-in-RL axis.** Backpropamine is the clean statement of the *plasticity-gating* branch, as opposed to the *activity-gating* branch that FiLM, ANML and Ben-Iwhiwhu 2022 all belong to. Both branches let a network compute a signal that changes what other parts of the network do — but the target of the change is different, and the difference is structural, not stylistic. Activity-gating changes a **forward-pass quantity that is discarded at the end of the timestep**; plasticity-gating changes a **state variable that persists across timesteps and accumulates**. That makes plasticity-gating a memory mechanism as much as a modulation mechanism, which activity-gating is not.

## Section-by-section backbone

### Abstract
Lifelong learning in brains is enabled by synaptic plasticity, which is itself actively controlled by neuromodulation under the brain's own control. The paper shows *for the first time* that artificial networks with neuromodulated plasticity can be trained with gradient descent, extending the earlier differentiable-Hebbian-plasticity framework with a differentiable formulation for neuromodulation of plasticity. Claimed improvements on both reinforcement learning and supervised learning tasks; in one task, neuromodulated plastic LSTMs with millions of parameters outperform standard LSTMs on a benchmark language-modelling task, controlling for parameter count.

### 1. Introduction
Networks handling temporally extended tasks must store traces of past events; typically via recurrent activity, memory networks, or temporal convolutions. In nature the primary basis for long-term memory is **synaptic plasticity** — automatic weight modification as a function of ongoing activity. Crucially these modifications are not passive: they are modulated moment-to-moment by dedicated systems (particularly dopamine), so the brain can "decide" where and when to modify its own connectivity. This neuromodulation of plasticity lets the brain filter out irrelevant events, combat catastrophic forgetting, and implement a self-contained reinforcement learning algorithm by altering its own connectivity in a reward-dependent manner. Evolution designed this machinery — a meta-learning process. Prior evolutionary work built neuromodulated plastic networks of only a few hundred connections; the aim here is to make them gradient-trainable so modern deep-learning scale becomes available. The framework is named **backpropamine** ("backprop" + "dopamine").

### 2. Related work
Neuromodulated plasticity has a long history in **evolutionary computation** (Soltoggio et al. 2008; Risi & Stanley 2012; Soltoggio et al. 2017 review), where a key focus is mitigating catastrophic forgetting: activating plasticity *only* in weights relevant to the current task leaves knowledge in other weights untouched (Ellefsen et al. 2015; Velez & Clune 2017). But evolved networks were small and low-dimensional. The **differentiable plasticity** framework (Miconi 2016; Miconi et al. 2018) made per-connection plasticity gradient-optimisable, but only *passive, non-modulated* plasticity — weight changes occur automatically from pre/post activity with no gate. This paper extends it so the network itself computes the gate. Alternative approaches compute weight modifications with a second network (Schmidhuber 1993b; Schlag & Schmidhuber 2017; Munkhdalai & Yu 2017; Wu et al. 2018), but none directly optimise *the neuromodulation of plasticity itself* within a single network by gradient descent.

### 3. Methods — 3.1 Background: differentiable Hebbian plasticity
Each connection has a fixed and a plastic component:

$$x_j(t) = \sigma\!\left\{ \sum_{i \in \text{inputs to } j} \big(w_{i,j} + \alpha_{i,j}\, \mathrm{Hebb}_{i,j}(t)\big)\, x_i(t-1) \right\} \tag{1}$$

$$\mathrm{Hebb}_{i,j}(t+1) = \mathrm{Clip}\!\big(\mathrm{Hebb}_{i,j}(t) + \eta\, x_i(t-1)\, x_j(t)\big) \tag{2}$$

$\sigma$ is $\tanh$ in all experiments. `Hebb` is initialised to zero at the start of each episode and is a purely **intra-life / episodic** quantity; $w$, $\alpha$, $\eta$ are the **structural** parameters optimised by gradient descent *between* episodes. `Clip` constrains `Hebb` to $[-1,1]$ to negate Hebbian instability — here a hard clip, which the authors report performed equal or better than the decay term or Oja's-rule normalisation used previously. Note the distinction: $\eta$ is the intra-life *learning rate* (how fast new information enters), $\alpha_{i,j}$ is a *scale* (the maximum magnitude of the plastic component, since `Hebb` is bounded). Unlike uniform-plasticity approaches including "fast weights" (Ba et al. 2016), the amount of plasticity per connection is itself **trainable**. Implementation cost: fewer than four extra lines of code over a standard recurrent net.

### 3.2 Backpropamine: differentiable neuromodulation of plasticity
Two methods. In both, plasticity is modulated moment-to-moment by a network-controlled signal $M(t)$. $M(t)$ is a single scalar output of the network, used either directly (simple RL tasks) or passed through a meta-learned vector of weights (one per connection, for language modelling).

**3.2.1 Simple neuromodulation.** Make the global $\eta$ depend on network output: replace $\eta$ in Eq. 2 with $M(t)$:

$$\mathrm{Hebb}_{i,j}(t+1) = \mathrm{Clip}\!\big(\mathrm{Hebb}_{i,j}(t) + M(t)\, x_i(t-1)\, x_j(t)\big) \tag{3}$$

This requires *no additional code* over differentiable plasticity — only a modification of it.

**3.2.2 Retroactive neuromodulation and eligibility traces.** Inspired by short-term retroactive dopamine effects: dopamine retroactively gates plasticity induced by *past* activity within a ~1 s window (Yagishita et al. 2014; He et al. 2015; Fisher et al. 2017; Cassenaer & Laurent 2012). Hebbian activity creates a fast-decaying "potential" weight change, incorporated into actual weights only if dopamine arrives in the window — i.e. an **eligibility trace** (Sutton et al. 1998). Eq. 2 is replaced by two equations:

$$\mathrm{Hebb}_{i,j}(t+1) = \mathrm{Clip}\!\big(\mathrm{Hebb}_{i,j}(t) + M(t)\, E_{i,j}(t)\big) \tag{4}$$
$$E_{i,j}(t+1) = (1-\eta)\, E_{i,j}(t) + \eta\, x_i(t-1)\, x_j(t) \tag{5}$$

$E_{i,j}$ is an exponential moving average of the Hebbian product with **trainable** decay factor $\eta$. $M(t)$ can be positive or negative, approximating both rises and dips in baseline dopamine.

### 4. Experiments — 4.1 Task 1: cue-reward association
A meta-learning problem emulating an animal behavioural task. Each episode, one of four input cues is arbitrarily chosen as the Target. Repeatedly, two cues are shown in succession (randomly from the four), then a Response cue during which the agent must respond 1 if the Target was in the pair, 0 otherwise. Correct → reward $+1.0$; incorrect → $-1.0$ (two-alternative forced choice, always a response). Episode = 200 timesteps. Cues are **20-bit binary vectors regenerated randomly at the start of each episode**. Variable numbers of zero-input timesteps are inserted to defeat time-locked scheduling; mean ≈ 15 trials/episode.

Architecture: simple recurrent network, 200 hidden recurrent neurons. **Only the recurrent layer is plastic**; input and output weights have only $w_{i,j}$. 24 inputs: 20 binary cue bits, 1 elapsed-time input, 2 one-hot previous response, 1 real-valued previous reward (standard meta-learning practice per Wang et al. 2016; Duan et al. 2016). Four outputs: 2 softmax response logits, a value output $V(t)$ (linear; required by the **A2C** meta-training algorithm following Wang et al. 2016), and the neuromodulatory signal $M(t)$ passed through $\tanh$. Gradients clipped at norm 7.0.

Result (Fig. 1, medians + IQR over 10 runs): **both neuromodulatory variants learn the task; non-modulated plastic networks and non-plastic simple recurrent networks fail to learn it.** The authors hypothesise this is tied to the high dimensionality of the cues. Plots of the modulator neuron output reveal it reacts to reward in a complex, time-dependent way (Appendix).

### 4.2 Task 2: maze navigation
Grid-maze exploration from Miconi et al. (2018). 9×9 squares surrounded by walls; every other square in either direction is a wall, giving 16 wall squares in a regular grid except the centre. Maze shape is **fixed and unchanging** across the task. Each episode one non-wall square is randomly chosen as the reward location; hitting it gives reward and teleports the agent to a random location. Episode = 200 timesteps; reward location fixed within an episode, randomised across episodes. **The reward is invisible** — the agent only knows it hit the location via the reward input at the next step (and possibly by detecting teleportation).

Architecture: same as Task 1 but only **100 recurrent neurons**. Outputs: 4 softmax action channels (left/right/up/down), linear $V(t)$, and $\tanh$-squashed $M(t)$. Inputs: binary vector for the 3×3 neighbourhood centred on the agent (wall / not wall), 4 one-hot previous action, 1 previous reward. Again **only recurrent weights are plastic**. Result (Fig. 2, median + IQR over 9 runs): modulatory approaches outperform non-modulated plasticity; cyan stars mark timesteps where simple neuromodulation differs significantly from non-modulated plasticity at $p<0.05$ (Wilcoxon rank-sum).

### 4.3 Task 3: language modelling (supervised)
Word-level LM on **Penn TreeBank** (929 k train / 73 k valid / 82 k test words, 10 k vocabulary). Two models: a basic ~4.8 M-parameter model after Zaremba et al. (2014), and a large 24.2 M-parameter model forked from Merity & Socher (2017).

Basic model: embedding → two LSTM layers (≈ size 200) → 10 k softmax. **LSTM layer sizes are adjusted so total trainable parameters stay constant across all conditions**, including all plasticity ($\alpha$) and neuromodulation parameters. Unrolled 20 steps for BPTT; gradient norm clipped at 5; extra L2 penalty added (improves all models). Four conditions: (1) baseline LSTM; (2) LSTM with differentiable plasticity — plasticity added to one of the four recurrent paths inside each LSTM node, per Eqs. 1–2, with **each plastic connection having its own individual $\eta$**; (3) simple neuromodulation per Eq. 3, with $\eta$ replaced by the output of a neuron $M(t)$ taking a learned weighted combination of the hidden layer's activations as input, **one $M(t)$ per LSTM layer**; (4) retroactive neuromodulation using Eqs. 4–5.

Table 1 (test perplexity, lower better; mean ± 95 % CI over 16 runs for the basic model, median (min, max) over 5 runs for the large model):

| Model | Test perplexity |
|---|---|
| Baseline LSTM (similar to Zaremba et al. 2014) | $104.26 \pm 0.22$ |
| LSTM with differentiable plasticity | $103.80 \pm 0.25$ |
| LSTM with simple neuromodulation | $102.65 \pm 0.30$ |
| LSTM with retroactive neuromodulation | $102.48 \pm 0.28$ |
| Baseline large LSTM (Merity & Socher 2017) | $62.48\ (62.40,\ 62.60)$ |
| Large LSTM with neuromodulated plasticity | $61.44\ (61.37,\ 61.68)$ |

Statistics: plasticity beats baseline ($p = 0.0044$); neuromodulation beats plasticity ($p = 10^{-6}$); retroactive beats baseline by ~1.7 perplexity ($p = 10^{-7}$). **Retroactive vs. simple neuromodulation is not significant at $p<0.05$ ($p = 0.066$)** — stated explicitly by the authors. Each of the four basic-model conditions got its own equally-powered grid search before the 16 runs. The large model uses simple neuromodulation only (no retroactive), per-neuron rather than per-connection $\alpha_i$, and the plastic version reduces LSTM cells from 1150 to 1149 so its parameter count (24 198 893) does not exceed the non-plastic baseline's (24 221 600).

### 5. Discussion and future work
First demonstration that neuromodulated plastic networks can be trained by gradient descent. The LM result matters because LSTMs are used in high-impact real-world applications. Conceptual comparison to **"Learning to Reinforcement Learn" (L2RL)** (Wang et al. 2016; 2018): in L2RL, weights do not change during episodes — all within-episode learning is in *activity state*. Backpropamine adds the ability to store state information in **weight changes** as well as hidden-state changes. Speculatively, this could extend L2RL one level higher: rather than A2C as a hand-designed reward-based weight-modification scheme, the system could determine its own arbitrary weight-modification scheme using any signal it can compute (reward prediction, surprise, saliency) — "meta-meta-learning". Improvements required: multiple neuromodulatory signals each with own inputs/outputs (as in the brain); more complex tasks that use the eligibility traces fully; addressing the known interference between the unsupervised component of Hebbian learning and reward-based modification (Frémaux et al. 2010; Frémaux & Gerstner 2015); and letting meta-training design the architecture rather than only the parameters.

### Appendix A.1 — Plastic LSTMs, basic model
Standard LSTM equations (6)–(11). Plasticity is introduced only in the path through $i_t$ (the "actual data" path); $j_t$, $f_t$, $o_t$ are control paths and adding plasticity to them is left as future work. The pre- and post-synaptic activations $x_i(t-1), x_j(t)$ in Eqs. 1–2 are $h_{t-1}$ and $i_t$. A layer of size 200 has $200 \times 200 = 40\,000$ plastic connections, each with its own backprop-learned $\eta$. For neuromodulated LSTMs, the individual $\eta$ per plastic connection is replaced by the output of a neuron $M(t)$ with **fan-out equal to the number of plastic connections**, taking $h_{t-1}$ as input; one dedicated neuromodulatory neuron per LSTM layer. Variants tried and found worse: one modulatory neuron per node, and one for the whole network.

### Appendix A.2 — LM training details
All four models trained with SGD, initial LR 1.0, 13 epochs; LSTM hidden states initialised to zero with carry-over between minibatches. Grid search over four hyperparameters: LR decay factor 0.25–0.40 in steps of 0.01; epoch at which decay begins ∈ {4, 5, 6}; initial weight scale ∈ {0.09, 0.10, 0.11, 0.12}; L2 penalty ∈ {1e-2 … 1e-6}.

### Appendix A.3 — Large word-modelling network
Three stacked LSTMs (1150, 1150, 400), embedding 400, weight-tied output softmax; variational dropout between LSTMs; variable BPTT horizon centred on 70 words; switch from SGD to Averaged-SGD at epoch 45. Deviations from Merity & Socher: no recurrent weight-dropout, forced ASGD switch at 45 for all runs, batch size 7 (computational limits), no hyperparameter tuning. Plasticity coefficients are **per neuron** ($\alpha_i$ applied to all incoming connections of neuron $i$), reducing $\alpha$ from an $N \times N$ matrix to a length-$N$ vector, while `Hebb` traces remain per-connection. A single $\tanh$ modulator neuron per LSTM receives input from all recurrent neurons; its scalar output is passed through a per-neuron weight vector to produce a different $\eta_i$ per neuron — all fixed multiples of a common value. This is an intermediate between one global $\eta(t)$ and fully independent per-neuron $\eta_i$ (which would need $N \times N$ weights rather than $2N$).

### Appendix A.4 — Dynamics of neuromodulation
Modulator output plotted against perceived reward for random trials from several well-trained Task-1 runs (Fig. 3). Dynamics are rich, complex, and vary greatly between runs. The modulator clearly reacts to reward, but the reaction is time-dependent and run-specific: one retroactive run produces *negative* modulation in response to *positive* reward and vice versa, while one simple-modulation run does the opposite. A common pattern is negative neuromodulation on the timestep just after reward perception. Two retroactive runs show reward → strongly positive → strongly negative modulation. The authors state that **understanding the mechanism by which these dynamics perform efficient within-episode learning is future work**.

### Appendix A.5 — Cue-reward association control experiment
Why could neuromodulated plasticity learn Task 1 when non-modulated plasticity could not? A prior version of the task used only four **fixed 4-bit** cues ('1000', '0100', '0010', '0001'), so there is nothing to memorise about the cues themselves — only which known cue is rewarded. **In this simplified version, non-modulated plasticity does learn the task**, though more slowly than neuromodulated plasticity (Fig. 4; the figure also compares "soft clip" vs the "hard clip" used in the paper). This suggests neuromodulated plasticity has its strongest advantage specifically when the association involves **arbitrary high-dimensional cues that must be memorised jointly with the association**, echoing Miconi et al. (2018) on plastic vs non-plastic networks and fast memorisation of high-dimensional inputs. The authors close by saying more work is needed to identify which problems benefit most.

## Phase 1 — Undergraduate-level synthesis

**The problem.** A neural network that has to remember things during a task usually does it one of two ways: it keeps information alive in its recurrent activity (like an LSTM's hidden state), or it is trained offline so the relevant facts are baked into its weights. Biology has a third route that machine learning had largely ignored: the brain rewrites its own synapses *while it is doing the task*, and — this is the part that matters — it rewrites them **selectively**. Dopamine and other neuromodulators tell particular synapses "this moment was worth learning from; write it in" or "ignore this, nothing important happened". So the brain is not a passive learner: it is a system that decides when to learn.

**The idea.** Give every recurrent connection two strengths added together. The first is the ordinary weight, trained offline and frozen during the task. The second is a *Hebbian trace* — a running record of how often the sending and receiving neurons were active together — that changes during the task and resets to zero at the start of each episode. Then put a knob in front of the Hebbian trace's update. That knob is a single number, `M(t)`, and it is computed by the network itself from its own hidden state at every timestep. Turn `M(t)` to zero and the network is frozen. Turn it up and the network writes the current moment into its own connections. Turn it negative and it writes in the opposite. Because everything here is smooth arithmetic, ordinary backpropagation can train the machinery that produces `M(t)` — which is the paper's actual claim to novelty. Previous work on neuromodulated plasticity had to use evolution, which limited networks to a few hundred connections.

**The refinement.** In real brains dopamine acts *retroactively* — it arrives after the activity it is reinforcing and decides, within a window of about a second, whether that already-past activity gets consolidated. The authors reproduce this by inserting an **eligibility trace**: a fast-decaying memory of "which connections were recently active together", which sits waiting until the modulatory signal arrives to convert it into an actual weight change. This solves a version of the credit-assignment problem — reward arrives late, but the eligibility trace still remembers who deserves credit.

**The experiments, honestly.** Three tasks. (1) *Cue-reward association*, a small custom meta-learning task where the agent must figure out, within each 200-step episode, which of four randomly-generated 20-bit patterns is the rewarded one. Trained with A2C, a standard RL algorithm. Result: the modulated networks learn it; the non-modulated plastic network and the plain recurrent network both **fail entirely**. (2) *9×9 grid maze foraging*, where an invisible reward location is randomised each episode and the agent must find and re-find it within 200 steps. Also A2C. Result: modulated beats non-modulated, statistically significantly at many points in training. (3) *Penn TreeBank language modelling*, which is **not RL at all** — plain supervised next-word prediction. Result: with parameter count held constant, plasticity gives a small significant gain over a baseline LSTM, and neuromodulation gives a further significant gain on top, ~1.7 perplexity total.

**The most instructive result is a control experiment in the appendix.** When the authors made the cue-reward task easier — four *fixed* 4-bit cues instead of random 20-bit ones, so there is nothing to memorise about the cues themselves — the non-modulated plastic network suddenly *could* solve it. That tells you where the advantage comes from: neuromodulated plasticity earns its keep specifically when the network must memorise an arbitrary, high-dimensional thing *and* learn an association about it at the same time. That is a much more precise claim than "neuromodulation helps", and it is the kind of localisation this corpus's other papers usually do not provide.

## Phase 2 — Graduate-level deep dive

### The core object: an effective weight matrix with a rank-accumulating additive term

The whole framework is one modification to the forward pass. Write the recurrent update with the *effective* weight $\tilde{w}_{i,j}(t)$:

$$x_j(t) = \sigma\!\left\{ \sum_{i} \underbrace{\Big(w_{i,j} + \alpha_{i,j}\, \mathrm{Hebb}_{i,j}(t)\Big)}_{\tilde{w}_{i,j}(t)}\, x_i(t-1) \right\}$$

Glossing every symbol:

| Symbol | Meaning | Timescale | Trained by |
|---|---|---|---|
| $x_i(t)$ | output (activation) of neuron $i$ at time $t$ | per-step | — |
| $\sigma$ | nonlinearity; $\tanh$ in all experiments | — | — |
| $w_{i,j}$ | baseline non-plastic weight, $i \to j$ | fixed within episode | gradient descent, between episodes |
| $\alpha_{i,j}$ | plasticity coefficient — scales the magnitude of the plastic component | fixed within episode | gradient descent, between episodes |
| $\mathrm{Hebb}_{i,j}(t)$ | Hebbian trace, bounded in $[-1,1]$, zeroed at episode start | **changes every step** | not trained; *evolves* |
| $\eta$ | intra-life plastic learning rate (decay rate in the retroactive form) | fixed within episode | gradient descent |
| $M(t)$ | neuromodulatory signal, scalar, $\tanh$-squashed to $[-1,1]$ | **changes every step** | its input weights are trained |
| $E_{i,j}(t)$ | eligibility trace (retroactive variant only) | **changes every step** | not trained; evolves |

The two-timescale structure is the point. $w$, $\alpha$, $\eta$ and the weights producing $M$ are the **structural / meta-level** parameters, optimised across episodes to minimise expected episode loss. `Hebb` and $E$ are **intra-life state**, reset per episode, carrying whatever the agent has learned *within* this episode. This is a genuine two-loop learning system, but unlike MAML-style meta-learning the inner loop is not a gradient step — it is a Hebbian update whose gate the outer loop learns to control.

### What exactly is modulated

$M(t)$ multiplies the **increment** to the plastic state, not any activation:

$$\mathrm{Hebb}_{i,j}(t+1) = \mathrm{Clip}\Big( \mathrm{Hebb}_{i,j}(t) + M(t)\, \underbrace{x_i(t-1)\, x_j(t)}_{\text{outer product}} \Big)$$

In matrix form, with $x(t-1) \in \mathbb{R}^N$ the presynaptic activity vector and $x(t) \in \mathbb{R}^N$ the postsynaptic vector, the un-clipped increment to the whole trace matrix is

$$\Delta H(t) = M(t)\, x(t)\, x(t-1)^\top$$

which is a **rank-one outer product scaled by a scalar gain**. This single equation is the sharpest available statement of how Backpropamine differs from FiLM-family modulation, and it is worth reading component by component:

- The modulated quantity $H \in \mathbb{R}^{N \times N}$ is **matrix-valued** and lives in weight space, whereas FiLM's modulated quantity is **vector-valued** and lives in activation space.
- The modulation is **integrated over time** — $H(t) = \mathrm{Clip}\big(\sum_{s \le t} M(s)\, x(s)\, x(s-1)^\top\big)$ — so $M$ at one timestep influences behaviour at every subsequent timestep of the episode. A FiLM coefficient influences exactly one forward pass and is then discarded.
- The modulatory signal is a **single global scalar** (in the RL tasks), not a per-feature vector. Its selectivity comes entirely from the outer product $x(t) x(t-1)^\top$, which is nonzero only where pre- and post-synaptic activity coincide. So *where* to write is determined by activity coincidence; *whether and how strongly* to write is determined by $M(t)$. This is the classic **three-factor learning rule** decomposition (pre × post × modulator; Frémaux & Gerstner 2015), and Backpropamine is precisely a differentiable three-factor rule.

The `Clip` to $[-1,1]$ is not cosmetic. Hebbian accumulation is unstable — the outer product is positively correlated with the activity it itself amplifies, so unbounded accumulation diverges. Miconi et al. 2018 handled this with a decay term or Oja's rule; this paper reports a hard clip performing equal or better. A consequence worth noting: the clip makes $\alpha_{i,j}$ interpretable as the *saturation magnitude* of the plastic component, since $|\alpha_{i,j} \mathrm{Hebb}_{i,j}| \le |\alpha_{i,j}|$.

### The retroactive variant and its credit-assignment role

The eligibility-trace form separates *what was active* from *whether it counted*:

$$E_{i,j}(t+1) = (1-\eta)\, E_{i,j}(t) + \eta\, x_i(t-1)\, x_j(t) \tag{5}$$
$$\mathrm{Hebb}_{i,j}(t+1) = \mathrm{Clip}\big( \mathrm{Hebb}_{i,j}(t) + M(t)\, E_{i,j}(t) \big) \tag{4}$$

Unrolling Eq. 5 from $E(0)=0$:

$$E_{i,j}(t) = \eta \sum_{s=1}^{t} (1-\eta)^{t-s}\, x_i(s-1)\, x_j(s)$$

so $E$ is an exponentially-weighted average of the Hebbian product with effective memory horizon $\approx 1/\eta$ steps. Substituting into Eq. 4 (ignoring the clip) gives the total plastic change up to time $T$:

$$\mathrm{Hebb}_{i,j}(T) \;=\; \eta \sum_{t=1}^{T} M(t) \sum_{s=1}^{t} (1-\eta)^{t-s}\, x_i(s-1)\, x_j(s)$$

Exchanging the order of summation to see it from the perspective of a past event at time $s$:

$$\mathrm{Hebb}_{i,j}(T) \;=\; \eta \sum_{s=1}^{T} \Big[\underbrace{\textstyle\sum_{t=s}^{T} (1-\eta)^{t-s} M(t)}_{\text{future modulator, exponentially discounted}}\Big]\; x_i(s-1)\, x_j(s)$$

This rearrangement is the whole biological point made algebraically. The coincidence event at time $s$ is written into the weights with a coefficient equal to a **discounted sum of the modulatory signal over all future timesteps**, with discount $(1-\eta)$. That is structurally the same object as an eligibility-trace return in TD($\lambda$) — activity now is credited by reward-related signal later. Simple neuromodulation (Eq. 3) is the $\eta \to 1$ special case, where the bracket collapses to $M(s)$ alone and only *simultaneous* modulation counts. And because $M(t) \in [-1,1]$ via $\tanh$, a *negative* $M$ implements anti-Hebbian writing — the model of a dopamine *dip*, not just a burst.

The authors note (Appendix A.4) that the learned $M(t)$ dynamics are not interpretable as "$M \approx$ reward". Across runs, some networks produce negative modulation for positive reward and vice versa. The sign is arbitrary because the outer loop can absorb an overall sign flip into $\alpha_{i,j}$ or the downstream readout weights; what the outer loop optimises is the *joint* $(\alpha, M)$ convention, not $M$ in isolation. This is an important caveat for anyone tempted to read $M(t)$ as a dopamine analogue with a fixed valence.

### Where $M(t)$ comes from, at three different granularities

The paper uses three architectures for the modulator, worth distinguishing because the report's "conditioning signal / injection site" columns depend on which one:

1. **RL tasks (Sections 4.1–4.2).** $M(t)$ is one of the network's output units, computed from the recurrent hidden state and squashed by $\tanh$. It sits alongside the policy logits and the A2C value head $V(t)$. It is **global**: one scalar applied identically to all plastic recurrent connections. Its input is the hidden state, which itself receives the previous reward and previous action as inputs — so $M(t)$ can be a learned function of reward history, but is not *defined* as reward.
2. **Basic LM model (Appendix A.1.2).** One dedicated modulatory neuron **per LSTM layer**, taking $h_{t-1}$ as input, with **fan-out equal to the number of plastic connections** — i.e. the scalar is expanded through a learned weight vector to give a distinct $\eta_{i,j}$ per connection. Variants tried and reported worse: one modulator per node, one modulator for the whole network.
3. **Large LM model (Appendix A.3).** A single $\tanh$ modulator neuron per LSTM, receiving input from all recurrent neurons, whose scalar output is multiplied by a **per-neuron weight vector** to give $\eta_i$ — so all $\eta_i$ are fixed multiples of a common time-varying value. Explicitly described as an intermediate between a single global $\eta(t)$ ($2N$ params for the vector route) and fully independent per-neuron modulators ($N \times N$). Plasticity coefficients are also reduced to per-neuron $\alpha_i$ here for parameter economy, while `Hebb` traces stay per-connection.

Note the trajectory: as models scale, the modulator becomes *more* structured (scalar → learned expansion vector), which is exactly the low-rank conditioning pattern that hypernetwork and FiLM work converges on independently.

### Relationship to affine (FiLM-style) modulation — the precise statement

FiLM applies, per feature channel $c$, an affine transform of the **activation**:

$$\mathrm{FiLM}(h_c) = \gamma_c(z)\, h_c + \beta_c(z)$$

where $z$ is an external conditioning input, $\gamma$ and $\beta$ are produced by a conditioning network, and the result is consumed and discarded within the same forward pass. Comparing term by term:

| Axis | FiLM / activity-gating (ANML, Ben-Iwhiwhu 2022, Vecoven 2020) | Backpropamine / plasticity-gating |
|---|---|---|
| Object modulated | activation vector $h \in \mathbb{R}^C$ | weight-space state $H \in \mathbb{R}^{N \times N}$ |
| Operator | multiplicative $\gamma \odot h$ (+ additive $\beta$) | scalar gain on a **rank-one outer product**; the result is *added* to $H$ |
| Persistence | one forward pass, then discarded | accumulates across the whole episode |
| Selectivity | per-channel, from the conditioning vector | from activity coincidence $x_i x_j$; the modulator itself is global in the RL tasks |
| Effect on weights | none | this *is* a weight change |
| Nearest classical analogue | gain modulation / attention | three-factor Hebbian learning rule, TD($\lambda$) eligibility |

So the honest answer to "is Backpropamine multiplicative, additive, or Hebbian outer-product?" is: **it is a Hebbian outer-product term whose accumulation rate is multiplicatively gated**. Both operations are present, but at different levels — multiplicative on the *update*, additive on the *effective weight*. It is not affine modulation of activations in any sense, and a report that groups it with FiLM on the strength of the word "modulation" would be making a category error. Conversely, the two are not incompatible: nothing prevents a network from carrying both a FiLM layer and a plastic layer, and the corpus contains no paper that does so.

There is one further asymmetry worth stating. FiLM is **stateless**: given the same $(h, z)$ it always produces the same output, so a FiLM-conditioned network is a function of its current input and conditioning signal. Backpropamine is **stateful in weight space**: given the same input, the network's response depends on the entire history of $(M, x)$ within the episode. That makes plasticity-gating a *memory* mechanism first and a *modulation* mechanism second, which is why its wins appear on memorisation-heavy tasks (the appendix control experiment) rather than on task-switching tasks.

### Two-timescale gradient flow

Why this is trainable at all is worth spelling out. `Hebb` is a differentiable function of past activations, and past activations are differentiable functions of $w$, $\alpha$, $\eta$ and the modulator weights. So BPTT through an episode of length $T$ yields, for instance,

$$\frac{\partial L}{\partial \alpha_{i,j}} = \sum_{t} \frac{\partial L}{\partial x_j(t)}\, \mathrm{Hebb}_{i,j}(t)\, x_i(t-1)$$

and for a modulator weight $\theta$ (with $M(t) = \tanh(\theta^\top h(t))$),

$$\frac{\partial L}{\partial \theta} = \sum_{t} \frac{\partial L}{\partial M(t)}\, \big(1 - M(t)^2\big)\, h(t), \qquad \frac{\partial L}{\partial M(t)} = \sum_{t' > t} \sum_{i,j} \frac{\partial L}{\partial \mathrm{Hebb}_{i,j}(t')}\, E_{i,j}(t)$$

The second expression makes the credit path explicit: the gradient reaching the modulator at time $t$ is the eligibility trace at time $t$, dotted against the loss-sensitivity of every *future* plastic state. This is a long path — hence the aggressive gradient clipping the authors report (norm 7.0 for RL, 5 for LM, "which greatly improved stability"). Two practical consequences for anyone implementing this: the clip on `Hebb` is a hard clip, whose gradient is zero in the saturated region, so a saturated trace silently stops passing gradient to the modulator; and the plastic state is $O(N^2)$ per timestep and must be kept in the autodiff graph, so memory cost scales as $O(T N^2)$ unless truncated — the paper's 20-step and ~70-word BPTT windows are doing real work.

### Parameter accounting

For a recurrent layer of $N$ neurons: baseline recurrent net has $N^2$ weights. Adding per-connection differentiable plasticity adds $N^2$ for $\alpha$ plus $N^2$ for per-connection $\eta$ — a 3× parameter count. Adding simple neuromodulation *removes* the $N^2$ $\eta$ matrix (replaced by a network-computed scalar), so simple neuromodulation is **cheaper than non-modulated plasticity with per-connection $\eta$**, needing only the modulator's $N$ input weights, plus $N^2$ fan-out weights if the per-connection expansion of Appendix A.1.2 is used. The large model's per-neuron compromise costs $2N$. The authors control for all of this explicitly in the LM experiments by shrinking hidden sizes (1150 → 1149) until parameter counts match or fall below baseline, which is the correct comparison and is done properly.

### What is ablated versus what is asserted

**Ablated (supported by controlled experiment):**
- Non-plastic RNN vs. non-modulated plastic vs. simple neuromodulation vs. retroactive neuromodulation, on the cue-reward task (10 runs, medians + IQR) and the maze task (9 runs, Wilcoxon rank-sum with marked significance).
- All four LM conditions with **matched trainable-parameter counts** and per-condition equally-powered grid search, 16 runs each, with reported $p$-values.
- Task difficulty as the source of the advantage: the Appendix A.5 fixed-4-bit-cue control, where non-modulated plasticity succeeds, isolating high-dimensional arbitrary cue memorisation as the operative factor. This is the strongest single piece of evidence in the paper.
- Clipping operation: hard clip vs soft clip compared (Fig. 4).
- Modulator granularity for LSTMs: per-layer vs per-node vs per-network — the authors state the latter two "performed worse" in preliminary experiments, but **do not report those numbers**, so this is a weak ablation.
- Retroactive vs simple: measured and reported **as not significant** ($p = 0.066$) on LM. Honest reporting; but it means the paper's more biologically-motivated variant has no demonstrated advantage over the simpler one.

**Asserted, not demonstrated:**
- **Catastrophic-forgetting mitigation.** Introduction and Related Work motivate the framework partly by selective plasticity avoiding overwriting. **No continual-learning experiment appears in this paper.** That claim is imported from the evolutionary literature (Ellefsen et al. 2015; Velez & Clune 2017). A report must not cite Backpropamine as evidence for continual learning.
- **"Self-contained reinforcement learning algorithm by altering its own connectivity"** — motivational framing; no experiment isolates an emergent RL rule inside the plastic weights.
- **Meta-meta-learning / extending L2RL one level higher** — explicitly speculative future work.
- **Multiple neuromodulatory signals** — named as needed future work; not implemented.
- **Generalisation of the LM benefit** — "if plasticity and neuromodulation consistently improve LSTM performance… the potential benefits could be considerable" is conditional, and the authors say they intend to test forecasting in future work.
- **Mechanism of the learned modulator dynamics** — Appendix A.4 explicitly declares this not understood.

**Scale and scope limitations to state plainly:** RL evidence is two custom tasks at 100–200 recurrent neurons; no standard RL benchmark, no continuous control, no image observations, no comparison to a strong RL baseline other than the ablated variants of its own architecture. In both RL tasks **only the recurrent layer is plastic** — input and output weights are ordinary. The large-scale evidence is supervised. The LM gain, while statistically robust (16 runs, tight CIs), is ~1.7 perplexity on a non-state-of-the-art baseline, and ~1.0 perplexity on the large model over 5 runs.

## Connections

Backpropamine is the corpus's canonical **plasticity-gating** reference, and its main value here is as the contrasting pole to almost everything else in the folder, which does activity-gating.

- **[beniwhiwhu_2022_context_meta_rl](beniwhiwhu_2022_context_meta_rl.md)** — cites Miconi/backpropamine explicitly in its Related Work as "plasticity-gating", against which it positions its own activity-gating choice, and names "try plasticity-gating modulation instead of activity-gating" as future work in its conclusion. The two papers are the two halves of the same axis; read them as a pair.
- **[beaulieu_2020_anml](beaulieu_2020_anml.md)** — the other paper acquired in this batch. ANML gates the **forward pass** of a learner; Backpropamine gates the **learning rule**. Note that ANML's modulation does end up shaping *which weights get updated* (a zero activation kills its own gradient), so ANML is best read as activity-gating with an indirect plasticity consequence, while Backpropamine gates plasticity directly and leaves activations alone. That distinction is easy to blur and worth stating in any report that names both.
- **[kolouri_2019_attention_plasticity](kolouri_2019_attention_plasticity.md)** — attention-based *structural* plasticity for continual learning; the closest thing in the corpus to a direct plasticity-modulation cousin, and the continual-learning evidence Backpropamine itself does not supply.
- **[doya_2002_metalearning_neuromodulation](doya_2002_metalearning_neuromodulation.md)** — the canonical mapping of neuromodulators onto RL hyperparameters, in which acetylcholine ≈ learning rate. Backpropamine is essentially that mapping made differentiable and per-connection, with $M(t)$ playing the learning-rate role that Doya assigns to ACh and the dopamine role in the retroactive variant.
- **[vecoven_2020_neuromod_dnn](vecoven_2020_neuromod_dnn.md)** — the activity-gating alternative applied to deep RL; a useful contrast because Vecoven modulates *activation function shape* while Backpropamine modulates *weight change rate*.
- **[kudithipudi_2022_lifelong_learning](kudithipudi_2022_lifelong_learning.md)** and **[durstewitz_2025_neuroscience_continual_learning](durstewitz_2025_neuroscience_continual_learning.md)** — survey-level placements of metaplasticity and three-factor rules; useful for situating Backpropamine inside the broader lifelong-learning taxonomy.
- **[mei_2022_multiscale_neuromod](mei_2022_multiscale_neuromod.md)** — multiscale neuromodulation principles; treats plasticity modulation as one of several scales at which neuromodulation can act.
- **[lee_2024_lifelong_rl](lee_2024_lifelong_rl.md)** — neuromodulation for lifelong RL; the setting where Backpropamine's motivating catastrophic-forgetting claim would actually need to be tested.
- **Cited inside Backpropamine but not held in this corpus:** Miconi et al. 2018 (differentiable plasticity — the direct predecessor and required reading for Eq. 1–2), Soltoggio et al. 2008 / 2017 (evolutionary neuromodulated plasticity), Wang et al. 2016 / 2018 (L2RL and prefrontal cortex as a meta-RL system — the explicit conceptual comparison point), Frémaux & Gerstner 2015 (three-factor learning rules — the theoretical frame for Eq. 4), Gerstner et al. 2018 (eligibility traces on behavioural timescales), Ba et al. 2016 (fast weights — the uniform-plasticity contrast), Merity & Socher 2017 (AWD-LSTM, the large LM baseline).
