---
title: "Learning to Continually Learn (ANML — A Neuromodulated Meta-Learning algorithm)"
authors: "Shawn Beaulieu, Lapo Frati, Thomas Miconi, Joel Lehman, Kenneth O. Stanley, Jeff Clune, Nick Cheney"
year: 2020
venue: "Published as a conference paper at ECAI 2020 (24th European Conference on Artificial Intelligence); arXiv:2002.09571v2 [cs.LG]"
slug: "beaulieu_2020_anml"
source_pdf: "sources/Beaulieu et al. 2020 - Learning to continually learn (ANML).pdf"
topic: "neuromodulatory_algorithms"
---

## Plain-English entry point

A neural network trained on one task and then on a second task typically destroys what it learned first. This is **catastrophic forgetting**, and the field's standard responses are all hand-designed: replay old data, penalise changes to weights judged important, freeze subnetworks, or add an auxiliary loss that encourages sparse representations in the hope that sparsity reduces interference. This paper's argument is that all of these optimise for a *proxy* and hope the thing you actually want follows. Instead, it says, **optimise directly for the thing you want** — set "learn a long sequence of tasks without forgetting" as the objective, and use meta-learning to discover the mechanism.

The mechanism ANML discovers is architectural. There are two networks running side by side, both seeing the same input image. One, the **prediction network**, is an ordinary classifier and does the actual learning. The other, the **neuromodulatory network**, does no classification at all — its only output is a vector of numbers between 0 and 1, one per unit of the prediction network's penultimate layer, which is multiplied into those units during the forward pass. Because a sigmoid bounds the gate to $[0,1]$, the modulator can only **suppress** activity; it cannot amplify it and cannot flip its sign. The authors call this **selective activation**.

The consequential part is what selective activation does to *learning*. In backpropagation, the gradient reaching a weight is proportional to the activity of the unit it feeds. So a unit the modulator has gated to zero receives essentially no weight update — the modulator has, without being asked to, decided which parts of the network are allowed to change on this input. The authors call this consequence **selective plasticity**, and it is *indirect*: nothing in ANML touches the learning rule. The forward pass is modulated, and the backward pass follows.

**Is any of this reinforcement learning? No.** The entire empirical content is supervised image classification on **Omniglot**, a dataset of handwritten characters from many alphabets, in a meta-learning protocol (MAML-style outer loop around an inner loop of SGD). Reinforcement learning appears exactly once, in the future-work section: *"One example is extending the work to reinforcement learning (RL) tasks."* Any report citing ANML must say "supervised continual learning", not "RL".

**The headline number.** After sequentially learning 600 Omniglot character classes — roughly 9,000 SGD updates, each image seen exactly once — ANML classifies **63.8 %** of held-out instances correctly, against **18.2 %** for OML, the previous state of the art it builds on and shares a protocol with. Its accuracy drops only **10 %** relative to an i.i.d.-trained version of itself (where forgetting is not a problem at all), where OML drops 70 % and ordinary training drops 99 %. Strikingly, the *sequentially* trained ANML beats the *i.i.d.* oracle versions of every competing method.

**Why it matters for the FiLM-in-RL axis.** ANML is the corpus's cleanest instance of **activity-gating done by a dedicated, input-conditioned side network**, and it is the direct architectural ancestor of Ben-Iwhiwhu et al. 2022, which this corpus already holds. Its operator is exactly the multiplicative half of FiLM — a per-unit gain, no additive shift — with a sign constraint FiLM does not have, applied at exactly one site. It is the counterpole to Backpropamine's plasticity-gating: ANML gates activations and lets the plasticity consequence fall out; Backpropamine gates plasticity directly and leaves activations untouched. The two papers share an author (Miconi) and both come out of Uber AI Labs, so the contrast is deliberate — ANML's own Related Work says of the neuromodulation literature that *"in such work neuromodulation directly modulates learning rates, instead of the approach taken in this work of directly modulating activations and thus indirectly controlling learning."*

## Section-by-section backbone

### Abstract
Continual lifelong learning requires learning many sequentially ordered tasks without catastrophically forgetting. Virtually all prior work uses manually designed solutions; the authors advocate **meta-learning** a solution to catastrophic forgetting. Inspired by neuromodulatory processes in the brain, they propose **A Neuromodulated Meta-Learning algorithm (ANML)**, which differentiates through a sequential learning process to meta-learn an **activation-gating function** enabling context-dependent selective activation within a deep network. A neuromodulatory (NM) network gates the forward pass of another otherwise-normal network, the **prediction learning network (PLN)**, and **thus indirectly controls selective plasticity (i.e. the backward pass) of the PLN**. State-of-the-art continual learning, sequentially learning as many as **600 classes (over 9,000 SGD updates)**.

### 1. Introduction
Catastrophic forgetting (CF) is acute for sequential learners; deep learning's successes are in the i.i.d./shuffled setting. The authors survey manual solutions and their limits:
- **Replay** — expensive in storage and compute, does not scale to many tasks.
- **Selective plasticity by hand** — limiting how much parameters can change. Extreme case: freeze all learned weights and add capacity (progressive nets), or freeze hand-designed modules in an overparameterised net (PathNet). Scales poorly and, by design, old pathways cannot improve from new tasks. **EWC** alters plasticity indirectly via regularisation proportional to Fisher information — a *manually selected* importance criterion. Related: synaptic intelligence, contrastive excitation backprop attention, pseudo-example interleaving, L2 on inter-task weight change, CopyWeight-with-Reinit.
- **Sparse / disjoint representations** — sparsity indirectly affects which parameters update. But the authors' stated position: *"when possible, we should not optimize for one thing (e.g. sparse representations) and hope doing so leads to another thing… Instead, we should optimize directly for what we want."*
- **Conditional-computation gating** — learned via REINFORCE, or at scale via sparsely-gated mixture-of-experts, but those works target computational capacity/efficiency, not CF.

**The critical prior work is Masse et al. [32]**, which showed gating mitigates CF up to 500 classes — but in an *easier* setting where the algorithm is **explicitly told which task it is on**, where **which neurons were gated was randomly chosen**, where gating **depended on the task label, not the data**, and where masks were **binary**. ANML removes the task oracle, meta-learns the gatings, makes them data-dependent, and makes them **continuous rather than binary**.

The broader framing is **AI-generating algorithms (AI-GAs)**: manually designed pipelines historically give way to learned ones (features, architectures, hyperparameters), so learn the learning algorithm too. MAML is the exemplar: differentiate through inner-loop SGD to get an outer-loop gradient on the weight initialisation.

### The one prior meta-learning attack on CF: OML
**Online aware Meta-Learning (OML)** [Javed & White 2019] uses a MAML-style meta-learner to produce a *representation* (a set of layers) that, when frozen and used by downstream layers, minimises CF in those downstream layers. Notably, OML produced sparsity **without explicitly encouraging it**, and a *better* version of it: explicitly encouraging sparsity yields many **dead neurons** (never firing across the dataset), whereas OML's representations had **none**. ANML adopts OML's meta-learning procedure and experimental protocol, compares to it, and seeks to improve on it. **Rather than meta-learning representations as OML does, ANML meta-learns a context-dependent gating function.**

The paper's central mechanistic claim, stated here: *"Selective activation in turn enables selective plasticity because the strength of backward gradients is a function of how active neurons were during the (modulated) forward pass, indirectly controlling which subset of the network will learn for each type of input."*

And the argument for why modulating activations beats modulating learning rates directly: modulating learning localises task information, but *"there can still be interference between the tasks during the forward pass. For example, even if an agent's chess playing and bike riding networks are physically separated such that learning in one does not corrupt information in the other, neither task will be performed well if both are actively producing muscle outputs when performing either task."* Modulating activations reduces interference in **both** passes.

Biological inspiration cited: inhibitory mechanisms activated by specific environmental stimuli; cholinergic suppression of synaptic plasticity (Hasselmo & Barkai 1995); suppression of activation by neuromodulatory signals (Bear & Singer 1986).

### 2. The problem formulation
Learn a large number of tasks $T_{1..n}$ sequentially from a common domain $\mathcal{T}$, such that average performance on all $T_{1..n}$ is high **after** sequential learning. Domain: **Omniglot** (1,623 character classes). Each task $T_i$ is a character class, with $k$ training and $v$ validation instances.

**MTT terminology** (the authors' own coinage, which they advocate the community adopt): learning happens in an outer and an inner loop. The phase where the outer loop improves the inner loop's learning ability is **meta-training**; testing the resulting inner-loop learner is **meta-testing**. Within meta-training the inner loop does **meta-train training** and is then evaluated by **meta-train testing** (whose error is the meta-loss). Within meta-testing there is likewise **meta-test training** and **meta-test testing**.

A naive full meta-learning of the whole sequence is infeasible at $n = 600$ (unstable gradients, memory). **OML's elegant approximation**: after each new class ($k$ instances), the meta-loss is the error on the newly learned class **plus** the error on a random sample of characters from all meta-train training classes — the **remember set**. The remember set is used **in meta-training only**; ideally it would contain only previously seen images, but following OML it samples from all meta-training classes. So each inner loop involves only $k$ instances of *one* class, keeping it tractable, while the network is nonetheless meta-trained to learn many classes without forgetting.

Data split: 1,623 Omniglot classes; **660 held out for meta-testing**, remaining **963 for meta-training**. Meta-train training uses $k = 20$ labelled instances per character; the remember set samples from those same 20. Meta-testing uses **15 instances per class for meta-test training** and the remaining **5 held out for meta-test testing**.

### 3. ANML — 3.1 Architecture
**OML's split:** one deep network divided in two. The first 6 (convolutional) layers are the **representation learning network (RLN)**: meta-learned, **frozen during the inner loop**. The final 2 (fully connected) layers are the **prediction learning network (PLN)**: initial weights meta-learned in the outer loop, then updated by inner-loop SGD.

**ANML's split:** two **parallel** networks — a **neuromodulatory (NM)** network and a **prediction** network (Fig. 1). Both sets of weights are meta-learned in the outer loop. **NM weights are never updated in the inner loop.** Prediction-network weights are updated in the inner loop, though which ones differs between meta-training and meta-testing.

To keep architecture and parameter size comparable to OML, **each of the two networks has 3 convolutional layers (each followed by batch norm) and one fully connected layer**. The NM network's final layer has **the same size as the input to the prediction network's final layer** — i.e. the flattened latent representation output by the prediction network's last convolutional layer. The NM output gates that latent representation **via element-wise multiplication** during the forward pass. All activation functions are **ReLU**, except the gating multiplier, which is **restricted to $[0,1]$ by a sigmoid**, *"meaning that in this work it can only suppress activations of the prediction network (instead of negate or amplify them)."*

### 3.2 Meta-training procedure (Algorithm 1)
Inner loop nested inside outer loop. Within each inner loop, a copy $\theta^P$ of the prediction-network weight initialisation $\theta^P_0$ is trained for **20 SGD iterations** — producing $\theta^P_1 \dots \theta^P_{20}$ — on the training set of **a single Omniglot meta-training class** $T_n$.

During each of these 20 forward passes, the inputs to the prediction network's final layer are gated by NM weights $\theta^{NM}$. During each backward pass, the gating *"naturally has the effect of reducing the gradients flowing back towards a subset of its weights, thereby modifying the SGD update and resulting in selective plasticity."* $\theta^{NM}$ is not updated within the inner loop.

After the 20 updates, the meta-loss is computed with the final post-inner-loop weights $\theta^P_{20}$ on **all 20 images of the class just trained on plus a random sample of 64 character instances from the remember set** — this is the **OML objective**. The meta-loss is backpropagated **through the 20 SGD steps** (MAML style) to give gradients on both $\theta^P_0$ and $\theta^{NM}$, and one outer-loop step is taken on each. Outer loop uses **Adam**; all inner-loop updates use **SGD with a fixed learning rate**. Meta-training runs for **20,000 outer-loop iterations**.

**One implementation detail with consequences:** when the prediction-network copy is made at the start of each meta-iteration, the weights in the final layer leading into the output node for the upcoming class are **randomly re-initialised** in that copy (rather than starting from their meta-learned values). This prevents the inner-loop learner from having already converged on the upcoming class through initialisation alone, and yields larger gradient steps — both closer to the meta-test situation where every class is new. Re-initialising the *entire* final layer would be worse, since the network must still make sensible predictions on the remember set. **This re-initialisation is not used during meta-test training.**

Algorithm 1, as printed:
$$\theta^P_i \leftarrow \theta^P_{i-1} - \beta \nabla_{\theta^P_{i-1}} L\big(\theta^{NM}, \theta^P_{i-1}, S_{\text{traj}}\big) \qquad \text{(inner loop, } k \text{ steps)}$$
$$\theta^{NM,P} \leftarrow \theta^{NM,P} - \alpha \nabla_{\theta^{NM,P}} L\big(\theta^{NM}, \theta^P_k, S_{\text{traj}}, S_{\text{rem}}\big) \qquad \text{(meta-update)}$$

with $S_{\text{traj}} = T_n$ the inner-loop trajectory and $S_{\text{rem}} \sim \mathcal{T}$ the remember set.

### 3.3 Performance evaluation in meta-testing (Algorithm 2)
Starting from meta-learned $\theta^P$ and $\theta^{NM}$, **only the weights of the fully connected layer in the prediction network** are fine-tuned on meta-test classes (freezing all but the last few layers, following OML). Fine-tuned for **$q = 15$ instances** of each of the **600 Omniglot meta-test classes**. Unlike meta-training, **no new copy of the prediction network is made for each class** — so the final meta-training weights are fine-tuned through **9,000 iterations of SGD**, meaning the model undergoes **8,985 updates since it last saw an instance of the first meta-test class**.

Two evaluations with the final weights $(\theta^P_{9000}, \theta^{NM})$: all 9,000 meta-test training instances are re-evaluated (**meta-test training** performance = ability to memorise without forgetting), and five held-out instances from each of the 600 classes are evaluated (**meta-test testing** = ability to continually learn *and generalise*, "which is what we ultimately care most about"). Repeated for trajectory lengths **10, 50, 75, 100, 150, 200, 300, 400, 500, 600**, with a **hyperparameter search per sequence length** for the inner-loop learning rate $\beta$.

### 3.4 Baseline controls
All controls have approximately the same total parameter count as ANML (**~6 M**), no NM network, and the OML architecture. **Empirically the batchnorm layers included in ANML were detrimental to OML's performance, so they were omitted from the controls** (consistent with OML's own setup).

- **Training from Scratch** — no meta-training, random init at meta-test training time; the *entire* network can learn since there are no learned features to preserve.
- **Pretraining and Transfer** — pretrains i.i.d. on the meta-training image set, matched to the same number of image evaluations seen during meta-training (**1.68 M image evals**), then fine-tunes the fully connected layers on the meta-test trajectory.
- **OML** — the state of the art on this domain. Same meta-learning procedure as ANML except no NM network; meta-learns only the convolutional layers (its RLN). OML's RLN is frozen at meta-test time and inside each meta-train-training inner loop. **Note the asymmetry the authors flag: in ANML *no* prediction-network weights are frozen during meta-train training**, whereas OML's RLN is. ANML's NM network is frozen during both meta-testing and meta-train training, updated only by outer-loop steps.
- **OML-OLFT (One-Layer Fine-Tuned)** — a fairness control. Original OML fine-tunes **both** fully connected layers at meta-test time (~3 M fine-tuned parameters, ~50 % more than ANML's ~2 M); OML-OLFT fine-tunes only the final layer (~1 M, ~50 % fewer). OML-OLFT often but not always improves on OML, **but never outperforms ANML**. Statistical comparisons in text use original OML as the published method; both are plotted.
- **Interleaved-Training Oracles** — same meta-training, but at meta-test time presented with an **i.i.d.** sample of all meta-test training classes. These bound performance in the absence of catastrophic forgetting.

### 4. Results — 4.1 Continual learning at scale
Longest CF-robust continual learning trajectories previously reported: **200** tasks, from OML. (Footnote: sequences up to 500 have been tried, *but only when providing the network with knowledge of which unique task is being solved* [Masse et al.].) Here: **600** sequential tasks, up to **9,000 SGD updates**.

**10 independent models meta-trained per treatment** on the same 963 meta-training classes; for meta-test testing, each of the 10 meta-trained models is evaluated on **10 independent meta-test training trajectories** with random task sets and orders drawn from the 660 held-out classes. All $p$-values by **Mann-Whitney U test**.

**Meta-test training accuracy (memorisation without forgetting).** ANML significantly outperforms OML at all lengths tested (all $p \le 1.26 \times 10^{-8}$). Both Pretrain-and-Transfer and Scratch are far worse than either OML or ANML at all lengths (all $p \le 6.023 \times 10^{-20}$): Scratch $< 3\%$ on trajectories of $\ge 50$ classes; Pretrain $< 3\%$ on $\ge 400$. OML-OLFT, which fine-tunes fewer parameters, is **better than OML at $\ge 300$ classes** but **significantly worse at $\le 200$** (all $p \le 1.87 \times 10^{-13}$ up to 200 for OML over OML-OLFT; all $p \le 1.33 \times 10^{-29}$ at $\ge 400$ for OML-OLFT over OML).

**Meta-test testing accuracy (generalisation).** ANML significantly better than every other treatment at every length ($p \le 2.58 \times 10^{-12}$). At 600 classes: **ANML 63.8 %**, OML **18.2 %**, OML-OLFT **44.2 %**. ANML beats chance ($p < 7.96 \times 10^{-6}$) on **99.3 % of classes** across the 600-task sequence, including classes not seen for hundreds of tasks (Fig. S9; the corresponding figure for OML is 79.7 % of classes). OML-OLFT is significantly worse than OML up to 150 classes ($p \le 6.23 \times 10^{-8}$) but better at $\ge 300$ ($p \le 4.69 \times 10^{-12}$).

**Versus oracles (Fig. 4).** Each algorithm's i.i.d. oracle beats its sequential counterpart ($p \le 1.27 \times 10^{-34}$ at 600). **But sequentially trained ANML significantly outperforms the oracle versions of OML and all other algorithms at 600 classes** (all $p \le 1.93 \times 10^{-23}$). The only treatment that beats ANML is ANML-Oracle (**71 %** vs 63.8 %, $p = 1.27 \times 10^{-34}$).

**Relative drop from oracle to sequential** — the paper's cleanest measure of forgetting specifically. At 600 classes: Scratch **99 %**, Pretrain-and-Transfer **99 %**, OML **70.32 %**, OML-OLFT **27.2 %**, **ANML 10 %** (all $p \le 3.11 \times 10^{-24}$ relative to ANML). The authors: *"it is remarkable to see such a small performance drop (only 10 %)… meaning that ANML is solving most of the catastrophic forgetting problem on this challenging test across 600 sequential tasks."*

**Multi-epoch context.** The default protocol gives one pass through 15 images per class, which is why absolute numbers look low; with 20 epochs of i.i.d. training on the 600-class set, Scratch reaches 61.8 % and Pretrain-and-Transfer 48.66 %. **Sequentially trained ANML at 63.8 % still beats both of those 20-epoch i.i.d. controls.** ANML i.i.d. one epoch = 71 %; 20 epochs = **75.37 %**, the highest number in the paper, still significantly ahead of all other treatments ($p = 3.38 \times 10^{-12}$). The authors state plainly: *"It is an open, interesting, important research question to figure out exactly why ANML outperforms the controls even in the multi-epoch, i.i.d. setting."*

### 4.2 The meta-learned representations
Does sparsity arise in ANML without an explicit incentive, as it did in OML?

Measured on meta-test test images: the prediction network's representation layer **before** neuromodulation has a mean of **52.77 %** of neurons active (active = activation $> 0.01$); **after** neuromodulation, **5.9 %** ($p < 10^{-6}$). OML's sparsity on the same images is **3.89 %**. The NM network's own last layer has **56.9 %** of neurons active. **Both OML and ANML have 0 % dead neurons** at the representation layer during meta-test training — every neuron is active for at least one class. By contrast, directly encouraging sparse representations creates dead neurons at much higher frequency.

The interpretive point: *"that ANML is more successful at avoiding catastrophic forgetting than OML, yet does so with a less sparse representation, suggests that having sparse representations alone are insufficient. ANML is able to meta-learn a combination of sparse representations and selective plasticity that together are especially important for continual learning."* Fig. 5 shows pre-gate, gate, and post-gate activations for three random inputs plus the mean across the meta-test test set — post-NM activations are sparse **per image** but near-uniformly distributed **on average**, i.e. sparse and orthogonal rather than wasteful.

**Testing the hypothesis that NM discriminates image types.** If the NM network creates different masks for different image types, semantically similar images should cluster in NM-activation space. Using **K-Nearest Neighbours** ($K=5$; qualitatively unchanged for $1 \le K \le 20$) with Euclidean distance in NM-activation space to predict meta-test test labels: **70.9 %** accuracy, against **24.3 %** for a network of the same architecture with **random weights** ($p = 2.58 \times 10^{-31}$). So the NM network has meta-learned to tell apart image types **including classes it has never seen**.

**Testing whether NM improves the PLN's representation.** KNN accuracy on PLN activations **post**-gating is **81.1 %**, versus **57 %** pre-gating ($p = 7.87 \times 10^{-12}$). Confirmed visually by 2-D **t-SNE** projections (Fig. 6) of 15 instances each of 10 meta-test classes when first seen — post-NM activations give more well-separated clusters than either pre-NM PLN activations or OML representations. The stated causal chain: *"The meta-learned NM network further increases that separability via selective activation. That, in turn, creates selective plasticity, causing information about each class to be stored in different parts of the network, reducing catastrophic forgetting."*

### 5. Discussion and future work
Named future directions, all explicitly not done here:
- **Gating more than one layer.** *"the choice to gate selective activations in just one layer of the prediction network was a simplifying assumption made in this initial exploration, but the methodological approach can easily be extended to modulate any and all layers."*
- **Finer granularity.** During development a version was created **where every synapse in the prediction network was gated by the NM network**. It *"was competitive with other versions that were tested, but required too many parameters to be a viable alternative given our current computational resources."* Proposed fix: indirect encoding as in **HyperNEAT**, where a small network generates a geometric gating pattern for a larger one — which would also let the NM network be applied to prediction networks of different sizes at meta-test time.
- **Harder tasks.** Each task here is one Omniglot character type. *"One example is extending the work to reinforcement learning (RL) tasks. If ANML helps in that setting it would be important since RL agents naturally encounter sequential learning environments."*
- **Distribution shift** between meta-test and meta-training distributions.
- **Hybridising** with RNN-based meta-learning (RL², Learning to Reinforcement Learn) and with **differentiable Hebbian plasticity** and **differentiable neuromodulated Hebbian plasticity** — i.e. an explicit call to combine ANML with Backpropamine.
- Forward transfer and backward transfer are unstudied.
- The 10 % remaining drop from ANML-Oracle leaves room for improvement.

Broader framing: this is **Pillar Two** of AI-generating algorithms (meta-learning learning algorithms); architecture search and automatic environment generation are the other pillars.

### 6. Conclusion
ANML meta-learns the parameters of a neuromodulatory network that, conditioned on data, gates the activations of a separate prediction network, creating selective activation and in turn selective plasticity — reducing catastrophic forgetting at unprecedented scale, up to 600 sequentially learned classes over 9,000 SGD updates. *"Although work needs to be done to test how well ANML works on harder challenges, this work provides a promising stepping stone."*

### 7. Supplementary information
**Fig. S7 — multi-epoch.** All treatments improve with 20 epochs vs 1 (all $p < 9.67 \times 10^{-13}$), but ANML-Oracle still beats all other oracles (all $p < 3.38 \times 10^{-12}$) at **75.37 %**.

**Fig. S8 — the freezing ablation.** Layers frozen in the main text are made plastic. Naming: `ANML-Unlimited` fine-tunes everything in both PLN and NM (nothing frozen); `ANML-FT:PLN` fine-tunes the whole prediction network with NM frozen; `ANML-FT:PLN+NM out` fine-tunes the PLN plus the NM's final layer. For OML, `OML-Unlimited` fine-tunes both PLN and RLN; `OML-FT:PLN+RLN final` adds the last convolutional layer.

Results at 600 classes: **`OML-FT:PLN+RLN final` and `OML-Unlimited` both fall below 1 % mean accuracy** — a 95 % drop relative to original OML. By contrast **`ANML-FT:PLN` reaches 31.5 %** and **`ANML-FT:PLN+NM out` 24.7 %**, both beating original OML's 18.19 % ($p = 1.08 \times 10^{-23}$ and $1.43 \times 10^{-20}$) — though these are relative drops of 50.6 % and 61.2 % from unmodified ANML's 63.8 %. Even `ANML-Unlimited` protects against forgetting up to **100 classes** before becoming statistically inferior to original OML ($p = 5.8 \times 10^{-17}$ at 100 classes), and beats `OML-Unlimited` and `OML-FT:PLN+RLN final` at every length (all $p < 4.62 \times 10^{-14}$). Interpretation offered: ANML can learn throughout its entire network with much less forgetting than prior methods, which could matter for transfer to wholly new distributions.

**Fig. S9 — forgetting by task order.** Generalisation error as a function of the order in which classes were seen, binned in groups of 10. Both methods beat chance ($p < 7.96 \times 10^{-6}$) on most classes — **99.3 % of classes for ANML, 79.7 % for OML** — including early classes in the 600-task sequence.

**Acknowledgements** note DARPA Lifelong Learning Machines award HR0011-18-2-0018, and thank Khurram Javed for providing the OML code.

## Phase 1 — Undergraduate-level synthesis

**The problem, concretely.** Show a neural network 600 handwritten character classes, one class at a time, 15 examples each, each example seen exactly once. By the time it reaches class 600 it has taken about 9,000 gradient steps since it last saw class 1. Ask it to still recognise class 1. An ordinary network gets essentially zero — 99 % of its ability is gone. This is catastrophic forgetting, and it is the single largest gap between how neural networks learn and how animals do.

**Why the usual fixes are unsatisfying.** Almost every published remedy is a hand-designed rule someone thought would help: keep a buffer of old examples and mix them in; compute a per-weight "importance" score and penalise changing important weights; freeze subnetworks; add a loss term encouraging sparse activations, on the theory that if two tasks use different neurons they cannot interfere. This paper's philosophical claim is that these all optimise a *proxy*. If you want a network that does not forget, make "does not forget" the objective and let optimisation find the mechanism. That is **meta-learning**: an outer optimisation loop that improves how well an inner learning loop learns.

**What ANML actually is.** Two networks, both looking at the same input image. The **prediction network** classifies. The **neuromodulatory network** classifies nothing — it emits one number between 0 and 1 for each unit in the prediction network's second-to-last layer, and those numbers are multiplied into that layer's activity. Because the numbers come from a sigmoid, they range over $[0,1]$: the modulator can turn units down or off, but cannot turn them up or flip their sign. Both networks' weights are trained by the outer loop. During the inner loop — the actual sequential learning — only the prediction network changes; the modulator is frozen.

**The trick that makes it work.** In backpropagation, a weight's update is proportional to how active the unit it feeds was. So if the modulator silences a unit, that unit's incoming weights barely change. Without anything in the code touching the learning rule, the modulator has decided which parts of the network are allowed to learn on this input. The authors name the two halves: **selective activation** (the forward-pass effect, which is what they implement) and **selective plasticity** (the backward-pass consequence, which they get for free). Their argument for doing it this way rather than modulating learning rates directly — which is what the rest of the neuromodulation literature does — uses a nice analogy: separating your chess-playing and bike-riding circuits so learning one doesn't corrupt the other is good, but useless if both circuits are shouting instructions at your muscles at the same time. You need to suppress interference in the *forward* pass too.

**How it is trained.** The outer loop repeats 20,000 times. Each iteration: copy the prediction network, run 20 SGD steps on 20 images of **one** character class, then evaluate on those 20 images **plus 64 images sampled from all the other classes** — the "remember set". That combined error is the meta-loss: it punishes both failing to learn the new class and forgetting the old ones. Then backpropagate that loss *through all 20 SGD steps* to update both networks' starting weights. This inner-loop-of-one-class trick, inherited from the OML paper this one builds on, is what makes 600-class continual learning computationally possible at all — you never have to differentiate through a 600-class sequence.

**The results.** At 600 classes: ANML **63.8 %** on held-out images versus OML's **18.2 %**. More telling than the raw number is the *forgetting-specific* measure. Train each method i.i.d. instead of sequentially — that removes forgetting entirely and gives an upper bound. ANML loses only **10 %** going from i.i.d. to sequential. OML loses **70 %**. Ordinary training loses **99 %**. And sequentially trained ANML beats the *i.i.d.* versions of all the competitors, which is a genuinely surprising result the authors flag as unexplained.

**What the modulator learned.** Before gating, about 53 % of the prediction layer's units are active; after gating, about 6 %. So the modulator has learned to produce sparse activity — without ever being told to. But unlike networks trained with an explicit sparsity penalty, it has **zero dead neurons**: every unit is used by some class. And running a nearest-neighbour classifier directly on the modulator's *output vector* classifies unseen characters at 70.9 % (a random-weight modulator gets 24.3 %), so the modulator has learned to recognise what kind of image it is looking at, including character classes it has never seen. Gating also makes the prediction network's own representation more separable: nearest-neighbour accuracy on it jumps from 57 % to 81 % once the gate is applied.

**The honest scope.** Everything above is **supervised image classification**. There is no reinforcement learning anywhere in this paper — RL appears once, in future work, as a thing that would be important to try. And the gate is applied at exactly **one layer**; the authors say gating all layers is easy in principle but was not done, and a per-synapse version was built during development, was "competitive", and was abandoned as too expensive with no numbers reported.

## Phase 2 — Graduate-level deep dive

### The operator, and its exact relationship to FiLM

Let $x$ be the input image, $h(x) \in \mathbb{R}^d$ the flattened latent representation output by the prediction network's final convolutional layer, and $g_{\theta^{NM}}$ the neuromodulatory network. The entire modulation is one line:

$$\tilde{h}(x) \;=\; \underbrace{\sigma\!\big(g_{\theta^{NM}}(x)\big)}_{\displaystyle \gamma(x) \,\in\, [0,1]^d} \;\odot\; h(x)$$

where $\sigma$ is the logistic sigmoid, $\odot$ is element-wise product, and $\tilde{h}$ is what feeds the prediction network's final fully connected layer. Symbol gloss:

| Symbol | Meaning |
|---|---|
| $x$ | the input image — **the same input both networks receive** |
| $h(x) \in \mathbb{R}^d$ | prediction-network latent representation, pre-gate |
| $g_{\theta^{NM}}$ | the NM network: 3 conv layers (each + batchnorm) and 1 FC layer, output dimension $d$ by construction |
| $\gamma(x) = \sigma(g(x)) \in [0,1]^d$ | the per-unit gain — the modulatory signal |
| $\theta^{NM}$ | NM weights: meta-learned in the outer loop, **frozen in the inner loop and at meta-test time** |
| $\theta^P$ | prediction-network weights: meta-learned initialisation, updated by inner-loop SGD |
| $\alpha, \beta$ | outer-loop (Adam) and inner-loop (SGD) learning rates |

Now compare to FiLM, $\mathrm{FiLM}(h_c) = \gamma_c(z)\, h_c + \beta_c(z)$:

| Axis | FiLM (canonical) | ANML |
|---|---|---|
| Operator | affine: multiplicative **and** additive | **multiplicative only** — $\beta \equiv 0$; there is no shift anywhere |
| Range of the gain | unconstrained real; can amplify, attenuate, sign-flip | **$[0,1]$ by sigmoid — suppression only.** The paper says so explicitly: it "can only suppress activations… instead of negate or amplify them" |
| Conditioning input $z$ | typically an **external** signal — a task ID, a language embedding, a timestep | **the input image itself.** ANML is *self-conditioned*; there is no task label, and removing the task oracle is one of its stated contributions over Masse et al. |
| Number of injection sites | usually every residual block / every layer | **exactly one** — the penultimate latent representation. Explicitly called "a simplifying assumption" |
| Granularity | per feature channel | per unit of the flattened latent |
| Who trains the conditioner | trained jointly with the main network by the same loss | **meta-learned in the outer loop; frozen in the inner loop** — a strictly two-timescale arrangement FiLM does not have |
| What the modulation is *for* | make one network behave as many task-specific networks | make the backward pass sparse, so tasks write to disjoint weights |

So ANML is **the multiplicative half of FiLM, sign-constrained to $[0,1]$, self-conditioned on the input, applied at a single site, with the conditioner on a slower timescale than the modulated network.** It is not an outer-product or Hebbian operator; nothing here touches weight space directly. Four of those six qualifiers are restrictions relative to FiLM, and the fifth (two-timescale) is an addition. Any report that says "ANML is FiLM" is roughly right about the operator and wrong about everything around it; the safest phrasing is *"a sigmoid-bounded multiplicative gate — FiLM's scale term without the shift"*.

Contrast within the corpus: **Ben-Iwhiwhu 2022** uses $h = \mathrm{ReLU}(h_s \otimes \tanh(W_m g))$, i.e. the same element-wise multiplicative form but with the gain in $[-1,1]$, at *every* layer, with a modulator branch reading the same layer input. Ben-Iwhiwhu's Related Work names ANML as the activation-gating precedent. So the corpus contains the lineage ANML → Ben-Iwhiwhu with the two design changes being (i) sign-permitting $\tanh$ instead of suppress-only sigmoid, and (ii) all layers instead of one.

### Selective activation ⇒ selective plasticity: the derivation the paper states but does not write

The mechanistic claim — gating the forward pass indirectly gates learning — deserves to be made explicit, because it is the paper's whole reason for preferring activation gating over learning-rate gating, and because it has a precise failure mode.

Let the prediction network's final layer compute logits $z = W \tilde{h} + b$ with $\tilde{h} = \gamma \odot h$, and let $L$ be the loss. The gradient with respect to the final-layer weights is

$$\frac{\partial L}{\partial W_{cj}} \;=\; \frac{\partial L}{\partial z_c}\,\tilde{h}_j \;=\; \frac{\partial L}{\partial z_c}\, \gamma_j(x)\, h_j(x)$$

The update to the weights out of unit $j$ is **directly proportional to $\gamma_j(x)$**. If the modulator sets $\gamma_j(x) \approx 0$ for this input, then $\Delta W_{cj} \approx 0$ for every output class $c$: unit $j$'s outgoing weights are frozen *on this input*, with no explicit freezing mechanism. Propagating further back, the gradient reaching $h_j$ is

$$\frac{\partial L}{\partial h_j} \;=\; \gamma_j(x) \sum_c \frac{\partial L}{\partial z_c}\, W_{cj}$$

so the same factor $\gamma_j$ attenuates everything upstream of unit $j$ as well. **The gate acts as a per-unit learning-rate mask on the entire subnetwork feeding that unit**, and it does so simply because multiplication is its own derivative's coefficient. This is the sense in which ANML's selective plasticity is free.

Two consequences worth stating for anyone implementing this:

1. **Suppression and freezing are the same operation here.** Because the gain is bounded in $[0,1]$, ANML cannot express "make this unit louder but do not let it learn", nor "let this unit learn but keep it quiet". Activity and plasticity are tied by a single scalar per unit. This is a real expressive limitation, and it is precisely what Backpropamine's separation of $M(t)$ from the activations avoids.
2. **The modulator's own gradient is not attenuated the same way.** $\partial L / \partial \gamma_j = h_j \cdot \partial L/\partial \tilde h_j$, so the modulator receives gradient wherever the *unmodulated* activity is nonzero, even where it has gated to zero — the modulator can learn to un-gate a unit it currently suppresses. Note this gradient reaches $\theta^{NM}$ only through the **outer loop** (which differentiates through all 20 inner SGD steps), never through the inner loop.

### The meta-objective and why it is tractable

The desired objective is: after sequentially learning $n$ tasks, average performance over all of them is high. Naively meta-learning this requires differentiating through $n \times k$ inner SGD steps, infeasible at $n = 600$. OML's approximation, adopted wholesale here: after learning **one** class for $k = 20$ steps, measure (1) whether it was learned and (2) whether old knowledge was lost. Formally, with $\theta^P_k$ the inner-loop weights after $k$ steps on trajectory $S_{\text{traj}} = T_n$ and $S_{\text{rem}}$ a 64-sample draw from the remember set,

$$\mathcal{L}_{\text{meta}}\big(\theta^{NM}, \theta^P_0\big) \;=\; \underbrace{L\big(\theta^{NM}, \theta^P_k, S_{\text{traj}}\big)}_{\text{did it learn the new class?}} \;+\; \underbrace{L\big(\theta^{NM}, \theta^P_k, S_{\text{rem}}\big)}_{\text{did it keep the old ones?}}$$

with

$$\theta^P_i = \theta^P_{i-1} - \beta \nabla_{\theta^P_{i-1}} L\big(\theta^{NM}, \theta^P_{i-1}, S_{\text{traj}}\big), \qquad i = 1 \dots k$$

and the outer update

$$\big(\theta^{NM}, \theta^P_0\big) \leftarrow \big(\theta^{NM}, \theta^P_0\big) - \alpha \nabla_{(\theta^{NM}, \theta^P_0)} \mathcal{L}_{\text{meta}}$$

The MAML-style second-order term is what carries information from the remember-set loss back into the gate. Expanding $\nabla_{\theta^{NM}} \mathcal{L}_{\text{meta}}$ by the chain rule through the $k$ steps:

$$\nabla_{\theta^{NM}} \mathcal{L}_{\text{meta}} \;=\; \underbrace{\frac{\partial \mathcal{L}_{\text{meta}}}{\partial \theta^{NM}}\bigg|_{\text{direct}}}_{\text{gate's effect on the final forward pass}} \;+\; \underbrace{\frac{\partial \mathcal{L}_{\text{meta}}}{\partial \theta^P_k} \cdot \frac{\partial \theta^P_k}{\partial \theta^{NM}}}_{\text{gate's effect on the whole learning trajectory}}$$

and, unrolling $\partial \theta^P_k / \partial \theta^{NM}$ across the $k$ SGD steps,

$$\frac{\partial \theta^P_k}{\partial \theta^{NM}} \;=\; -\beta \sum_{i=1}^{k} \left(\prod_{m=i+1}^{k} \Big(I - \beta\, \nabla^2_{\theta^P} L_m\Big)\right) \nabla_{\theta^{NM}} \nabla_{\theta^P} L_i$$

The **second term is the one that matters** and is why the paper is called *learning to continually learn*: it says the outer loop's gradient on the gate includes the mixed second derivative $\nabla_{\theta^{NM}}\nabla_{\theta^P} L$ — literally, *how the gate changes the shape of the weight update* — evaluated against the remember-set loss. The gate is therefore optimised not for classification accuracy but for **the interference properties of the SGD updates it induces**. That is a genuinely different training signal from anything a FiLM layer in a standard supervised or RL pipeline receives, and it is the reason ANML's gate ends up sparse without a sparsity penalty.

### Two-timescale structure and where each parameter lives

| Parameter set | Meta-train inner loop | Meta-train outer loop | Meta-test training |
|---|---|---|---|
| NM network $\theta^{NM}$ (3 conv + BN + 1 FC) | **frozen** | updated (Adam) | **frozen** |
| PLN convolutional + batchnorm | updated (SGD) — **note: nothing in ANML's PLN is frozen in the inner loop** | updated | **frozen** |
| PLN final FC layer | updated (SGD), with the upcoming class's output weights randomly re-initialised at copy time | updated | **updated (SGD)** — the only thing that learns at meta-test time, ~2 M params |

Compare OML: its RLN (6 conv layers) is frozen in the inner loop *and* at meta-test time; its PLN (2 FC layers, ~3 M params) is fine-tuned at meta-test time. The parameter-count asymmetry (ANML fine-tunes ~2 M, OML ~3 M, OML-OLFT ~1 M) is exactly what the OML-OLFT control exists to bracket, and it is bracketed correctly — ANML's fine-tuned budget sits *between* the two OML variants, and it beats both.

### The empirical claims, and how well each is supported

**Ablated (a controlled comparison exists):**
- **ANML vs OML vs OML-OLFT vs Pretrain-and-Transfer vs Scratch**, at 10 trajectory lengths from 10 to 600, **10 meta-trained models × 10 meta-test trajectories** per treatment, Mann-Whitney U throughout, with **per-sequence-length hyperparameter search for the inner learning rate**. This is thorough by the standards of this corpus.
- **Total parameter count matched at ~6 M** across all treatments.
- **i.i.d. oracle for every treatment**, which isolates forgetting from raw learning capacity and yields the relative-drop metric (ANML 10 % vs OML 70.32 %). This is the single most convincing analysis in the paper, because it controls for the possibility that ANML is simply a better classifier rather than a better *continual* learner.
- **Multi-epoch comparison (Fig. S7)** — rules out the objection that ANML's advantage is an artefact of the single-epoch budget.
- **Freezing ablation (Fig. S8)** — ANML variants that unfreeze more of the network degrade gracefully (63.8 → 31.5 → 24.7 %) while the corresponding OML variants collapse below 1 %.
- **Sparsity measurement** pre-gate 52.77 % vs post-gate 5.9 % active, with OML at 3.89 % and 0 % dead neurons for both, supporting the specific claim that sparsity alone is not what is doing the work.
- **KNN probes with a proper null**: NM activations give 70.9 % vs **24.3 % for an identically-architected random-weight NM network** ($p = 2.58 \times 10^{-31}$). The random-weight control is what makes this a real result rather than a visualisation.
- **KNN on PLN activations pre- vs post-gate**, 57 % → 81.1 %.

**Asserted, or supported only weakly:**
- **The single most important missing ablation is an ANML with the NM network replaced by something simpler.** There is no arm with a *learned static* mask, a *random* mask, or a mask conditioned on a task label rather than the image. The random-weight NM network appears **only** in the KNN probe, never as a continual-learning treatment. So the paper establishes that *ANML beats OML*, and that *the NM network's outputs are informative*, but does not directly isolate how much of the 63.8 % is attributable to the gate being **meta-learned** and **input-conditioned** rather than merely present. Masse et al. [32] is cited as the random/task-conditioned/binary-gating precedent, but is **not re-run under this protocol**, so the comparison is to a number from a different, easier setting.
- **The sigmoid's $[0,1]$ suppress-only range is never ablated.** No $\tanh$ or unbounded variant is reported. Given that Ben-Iwhiwhu 2022 later chooses $\tanh$ specifically to allow amplification and sign flip, this is a live design question ANML leaves open.
- **Single-site gating is a "simplifying assumption"** with no multi-layer variant reported. The claim that the method "can easily be extended to modulate any and all layers" is untested.
- **The per-synapse gating variant** is described as having been built and being "competitive with other versions that were tested", but **no numbers are given** and it was dropped for compute reasons. This is an anecdote, not a result.
- **A batchnorm confound.** ANML includes batchnorm layers; the authors found batchnorm "detrimental to the performance of OML" and therefore **omitted it from the controls**. This is defensible (it follows OML's own setup and avoids handicapping the baseline), but it means ANML and its controls differ in **two** ways — the NM network *and* batchnorm — rather than one. No ANML-without-batchnorm arm is reported.
- **Why ANML beats the controls even in the i.i.d. multi-epoch setting** is explicitly declared an open question by the authors. This is the right thing to say, but it also means the paper's causal story ("selective activation → selective plasticity → reduced interference") does not account for its own strongest result, since in the i.i.d. setting there is no forgetting to reduce.
- **The causal chain from gating to reduced forgetting** is supported by correlational evidence (sparsity measurements, KNN separability, t-SNE) rather than by an intervention on the gate.
- **The biological framing** (cholinergic suppression of plasticity, stimulus-driven inhibition) is motivational; no biological data is modelled or fitted.

**Scope limitations to state plainly:** single dataset (Omniglot); single modality (small grayscale images); every task is a one-class discrimination of the same kind, so there is **no task diversity** in the sense meta-RL benchmarks mean it; meta-test distribution is drawn from the same distribution as meta-training (the authors name distribution shift as future work); **no reinforcement learning of any kind**; ~6 M parameters. The absolute number 63.8 % would not be impressive i.i.d. — the authors say so — and its meaning depends entirely on the sequential, one-pass, 15-instances-per-class protocol.

### What ANML does and does not license in a FiLM-in-RL report

Licensed:
- That a **meta-learned, input-conditioned multiplicative gate** on a single hidden layer is sufficient to nearly eliminate catastrophic forgetting over 600 sequential supervised tasks, at ~6 M parameters.
- That **gating the forward pass indirectly gates the backward pass**, with the algebra above making the mechanism exact rather than hand-wavy.
- That **sparsity is a consequence, not the cause** — ANML forgets less than OML with a *less* sparse representation (5.9 % vs 3.89 % active).
- That a modulator trained only through a continual-learning meta-objective **spontaneously learns to discriminate input types**, including unseen classes (70.9 % KNN vs 24.3 % random-weight null).

Not licensed:
- Any RL claim. The word appears once, as future work.
- Any claim about gating **many** layers, about **amplifying** rather than suppressing, or about per-synapse granularity.
- Any claim that the *meta-learning* of the gate is what matters, as opposed to the mere presence of a data-conditioned gate — the ablation that would show this does not exist.
- Any claim that ANML's advantage is *entirely* about forgetting, given that it also wins in the i.i.d. setting where forgetting is absent, for reasons the authors state they do not understand.

## Connections

ANML sits at the exact centre of this corpus's activity-gating branch and is the direct ancestor of the design the corpus already holds in Ben-Iwhiwhu 2022.

- **[beniwhiwhu_2022_context_meta_rl](beniwhiwhu_2022_context_meta_rl.md)** — **the direct descendant.** Ben-Iwhiwhu's Related Work names ANML as the activation-gating precedent. The lineage is visible in two design deltas: ANML gates one site with a sigmoid in $[0,1]$ (suppress only); Ben-Iwhiwhu gates every layer with a $\tanh$ in $[-1,1]$ (suppress, amplify, or sign-flip). Ben-Iwhiwhu also moves the setting from supervised continual learning to meta-**RL** (CAVIA and PEARL on Meta-World and CT-graph) — which is exactly the extension ANML names as future work. Read as a pair; ANML supplies the mechanism, Ben-Iwhiwhu supplies the RL evidence ANML lacks.
- **[miconi_2019_backpropamine](miconi_2019_backpropamine.md)** — **the counterpole**, and the other paper in this acquisition batch. Shares an author (Miconi) and an institution (Uber AI Labs), and ANML's Related Work draws the distinction explicitly: prior neuromodulation work *"directly modulates learning rates, instead of the approach taken in this work of directly modulating activations and thus indirectly controlling learning."* ANML also names combining the two ("differentiable neuromodulated Hebbian plasticity") as future work. The axis to state precisely in any report: Backpropamine modulates a **persistent weight-space state** via a scalar-gated **outer product**, and leaves activations alone; ANML modulates **transient activations** via a **per-unit multiplicative gain**, and gets its plasticity effect as a derivative-chain consequence. Both are "neuromodulation"; they modulate different objects on different timescales.
- **[kolouri_2019_attention_plasticity](kolouri_2019_attention_plasticity.md)** — attention-based *structural* plasticity for continual learning, cited by ANML (ref [20]) as one of the manual selective-plasticity approaches it is arguing against. The nearest corpus neighbour on the continual-learning-plus-modulation intersection.
- **[vecoven_2020_neuromod_dnn](vecoven_2020_neuromod_dnn.md)** — activity-gating in deep RL, but by rescaling the *activation function's shape* rather than multiplying the activation. A third point on the activity-gating design space alongside ANML (per-unit gain) and Ben-Iwhiwhu (per-unit gain from a parallel population).
- **[kudithipudi_2022_lifelong_learning](kudithipudi_2022_lifelong_learning.md)** and **[durstewitz_2025_neuroscience_continual_learning](durstewitz_2025_neuroscience_continual_learning.md)** — survey placements of context-dependent gating within the lifelong-learning taxonomy; useful for situating ANML against EWC, replay, and progressive nets.
- **[lee_2024_lifelong_rl](lee_2024_lifelong_rl.md)** — neuromodulation for lifelong **RL**; the setting ANML explicitly defers to future work, so it is the natural place to look for whether ANML's result transfers.
- **[mei_2022_multiscale_neuromod](mei_2022_multiscale_neuromod.md)** — multiscale neuromodulation principles; ANML is a single-scale, single-site instance.
- **[avery_krichmar_2017_models_neuromodulation](avery_krichmar_2017_models_neuromodulation.md)** — background on the biological systems ANML invokes (cholinergic suppression of plasticity, stimulus-driven inhibition), useful for checking how loose the biological analogy is.
- **Cited inside ANML but not held in this corpus:** Javed & White 2019 (**OML** — required reading; ANML inherits its meta-objective, protocol, and evaluation wholesale, and is a strict architectural delta on it), Masse et al. 2018 (context-dependent gating with a task oracle and random binary masks — the precedent ANML is displacing), Finn et al. 2017 (MAML), Kirkpatrick et al. 2017 (EWC), Zenke et al. 2017 (synaptic intelligence), Rusu et al. 2016 (progressive nets), Fernando et al. 2017 (PathNet), Shazeer et al. 2017 (sparsely-gated mixture-of-experts), Stanley et al. 2009 (HyperNEAT — proposed as the fix for per-synapse gating's parameter blow-up, which makes ANML's own future direction a **hypernetwork** one), Clune 2019 (AI-GAs), Miconi et al. 2018 (differentiable plasticity) and Miconi et al. (Backpropamine, ref [34]).
