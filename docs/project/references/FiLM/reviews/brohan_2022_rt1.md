---
title: "RT-1: Robotics Transformer for Real-World Control at Scale"
authors: ["Anthony Brohan", "Noah Brown", "Justice Carbajal", "Yevgen Chebotar", "Joseph Dabis", "Chelsea Finn", "Keerthana Gopalakrishnan", "Karol Hausman", "Alex Herzog", "Jasmine Hsu", "Julian Ibarz", "Brian Ichter", "Alex Irpan", "Tomas Jackson", "Sally Jesmonth", "Nikhil J Joshi", "Ryan Julian", "Dmitry Kalashnikov", "Yuheng Kuang", "Isabel Leal", "Kuang-Huei Lee", "Sergey Levine", "Yao Lu", "Utsav Malla", "Deeksha Manjunath", "Igor Mordatch", "Ofir Nachum", "Carolina Parada", "Jodilyn Peralta", "Emily Perez", "Karl Pertsch", "Jornell Quiambao", "Kanishka Rao", "Michael Ryoo", "Grecia Salazar", "Pannag Sanketi", "Kevin Sayed", "Jaspiar Singh", "Sumedh Sontakke", "Austin Stone", "Clayton Tan", "Huong Tran", "Vincent Vanhoucke", "Steve Vega", "Quan Vuong", "Fei Xia", "Ted Xiao", "Peng Xu", "Sichun Xu", "Tianhe Yu", "Brianna Zitkovich"]
year: 2022
venue: "\"Preprint\" — the running header on every page; arXiv:2212.06817v2 [cs.RO], 11 Aug 2023. No conference or journal line is printed anywhere in the file; the commonly used \"RSS 2023\" attribution is NOT verifiable from this PDF."
slug: brohan_2022_rt1
source_pdf: docs/project/references/FiLM/sources/Brohan et al. 2022 - RT-1 - Robotics transformer for real-world control at scale.pdf
topic: FiLM
---

# RT-1: Robotics Transformer for Real-World Control at Scale

## Plain-English entry point

A fleet of 13 mobile manipulator robots, 17 months of data collection, 130,000 human-teleoperated demonstrations, 700-plus distinct spoken instructions ("pick green jalapeno chip bag from paper bowl and place on counter"), and one 35-million-parameter network that runs all of them at 3 Hz on the robot. RT-1 succeeds on **97 %** of the instructions it was trained on, **76 %** of instructions it has never seen (new verb-noun combinations of familiar pieces), **83 %** of trials with distractor objects cluttering the scene, and **59 %** of trials in kitchens it never trained in. Every one of those numbers beats the best prior architecture — retrained on the same data for fairness — by 24 to 36 percentage points.

**Where the modulation comes in, and what its conditioner actually reads.** The instruction sentence is turned into a fixed-length vector by an off-the-shelf sentence encoder (Google's *Universal Sentence Encoder*, pretrained on text and used here as a black box). That vector — and nothing else — drives **FiLM layers inserted into all 26 MBConv blocks of an ImageNet-pretrained EfficientNet-B3 image encoder**, producing per-channel scales and shifts that re-tune the vision network for the sentence at hand. The re-tuned image features become 81 "vision-language tokens", which a learned attention module (TokenLearner) compresses to 8, which a small decoder-only Transformer reads across a 6-frame history to emit discretized action tokens.

Two precise readings matter for this corpus's standing questions:

- **The conditioner reads the instruction, not the observation.** RT-1 is the FiLM-conditioned-by-a-language-encoder case in its purest, largest form. The modulation signal is constant for the whole episode, computed once from a string, by an encoder that was trained on text and knows nothing about robots. The image never touches the modulator. So RT-1 is *not* a counterexample to the corpus's claim that nothing conditions on the current observation — it is the strongest possible instance of the opposite design.
- **The paper contributes one genuinely new mechanism detail: identity-initialized FiLM.** Dropping a FiLM layer into the middle of a *pretrained* network would scramble the pretrained activations and throw away the pretraining. RT-1's fix is to zero-initialize the dense layers that produce $\gamma$ and $\beta$, and to write the modulation as $(1 + \gamma)\,x + \beta$, so that at step zero the layer is exactly the identity and the pretrained function is preserved. The network then learns to depart from identity as needed. This is the single most transferable engineering result in the paper for anyone inserting modulation into an existing trained network.

**What RT-1 is not:** it is not reinforcement learning. Training is behavior cloning — minimising the negative log-likelihood of demonstrated actions, on successful episodes only. The Limitations section names that as the method's first limitation.

**And the honest evidence verdict:** RT-1 runs a six-way model ablation and it does **not** include removing or replacing FiLM. The closest relevant number is that removing ImageNet pretraining of the FiLM-EfficientNet costs **33 points** on unseen tasks — which quantifies what the identity-initialization trick is protecting, but says nothing about affine modulation versus concatenation.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | The natural-language instruction, embedded by the **Universal Sentence Encoder** (Cer et al. 2018), a pretrained off-the-shelf text encoder. Episode-constant, exogenous, computed once. *(The PDF says "pretrained language embedding" but never states whether USE weights are frozen or fine-tuned — do not assert either.)* |
| **What is modulated** | The **image encoder**: an ImageNet-pretrained **EfficientNet-B3**, 16 M parameters, **26 MBConv blocks each with a FiLM layer**. The downstream TokenLearner and Transformer are *not* modulated; they see already-fused vision-language tokens. There is no critic. |
| **Modulation operator** | **Full affine FiLM**, written in Figure 1(a) as $(1 + \gamma)\cdot x + \beta$, with $\gamma, \beta$ produced by dense layers (`fc` and `hC`) that are **zero-initialized** so the layer starts as the identity. |
| **Granularity** | Per-channel, **per MBConv block** — 26 injection sites. The densest per-layer injection in the corpus's robotics set. |
| **What it is for** | **Early fusion** of language into vision: "allowing extraction of task-relevant image features early on and improving performance of RT-1". Explicitly contrasted (Appendix D.5) with Gato's late fusion, and offered as the explanation for RT-1's distractor robustness. |
| **RL algorithm** | **Not RL.** Behavior cloning: negative log-likelihood of demonstrated actions, categorical cross-entropy over 256 discretization bins per action dimension, causal masking. Successful episodes only. |
| **Ablated against concatenation?** | **No.** The six-way ablation covers model size, presence of the Transformer, continuous vs. discrete actions, autoregressive actions, ImageNet pretraining, and observation history. Neither the FiLM operator nor its placement is varied. |
| **Reported instability / failure mode** | The named hazard is **pretraining disruption**: "inserting a FiLM layer into the interior of a pretrained network would disrupt the intermediate activations and negate the benefit of using pretrained weights" — solved by identity initialization. No gain blow-up, no training-instability report. System-level limitations: cannot exceed demonstrator performance; generalizes only to *recombinations* of seen concepts, never to a genuinely new motion. |

## Section-ordered backbone

**Abstract.** Argues that generalist robot models require open-ended, task-agnostic training plus high-capacity architectures that can absorb diverse data, and verifies this with a study of model classes and their generalization as a function of data size, model size, and data diversity, on real robots.

**1. Introduction.** Contrasts the robotics norm — narrow, task-specific datasets — with the vision/NLP shift to large pretrained general models. Two challenges: assembling the dataset (breadth *and* scale, with tasks well-connected enough that patterns transfer) and designing the model (high capacity, but fast enough for real-time control). Introduces RT-1 as a Transformer that encodes high-dimensional inputs and outputs into compact token representations, and Figure 1(a) which draws the architecture with the FiLM operator printed explicitly as $(1+\gamma) \cdot x + \beta$.

**2/3. Related Work and Preliminaries.** Positions RT-1 among multi-task and language-conditioned robot learning and Transformer-based controllers. The learning problem is stated as behavior cloning over a dataset of *successful* episodes, optimising the negative log-likelihood of $a_t$ given images and the language instruction.

**4. System Overview.** Everyday Robots mobile manipulators: 7-DoF arm, two-finger gripper, mobile base. Three environments — a purpose-built "robot classroom" training environment plus two real office kitchens (Kitchen1, Kitchen2) differing in lighting, background and geometry. Data is human demonstrations annotated with a textual description; instructions are grouped into *skills* (verbs) and *objects* (nouns). The architecture pipeline in one sentence: images and text → ImageNet-pretrained convolutional network conditioned on a pretrained instruction embedding **via FiLM** → TokenLearner → Transformer → discretized action tokens. Action space: 7 arm dimensions (x, y, z, roll, pitch, yaw, gripper), 3 base dimensions (x, y, yaw), and a 3-way mode variable (arm / base / terminate). Closed-loop at 3 Hz until "terminate" or timeout.

**5. RT-1: Robotics Transformer.**

*5.1 Model.* **Instruction and image tokenization** — 6 images at 300×300 through EfficientNet-B3, giving a 9×9×512 feature map flattened to **81 visual tokens** (deliberately *not* patchified as in Gato). Language enters as a Universal Sentence Encoder embedding driving **identity-initialized FiLM layers** inserted into the pretrained EfficientNet, with the rationale and the zero-initialization trick stated verbatim (see §Phase 2.2 below). An additional reported finding: "identity-initialized FiLM also produces better results when training with an EfficientNet initialized from scratch, without ImageNet pretraining, but it does not surpass the initialization described above." Totals: **16 M parameters, 26 MBConv + FiLM layers, 81 vision-language tokens out**. **TokenLearner** — an elementwise attention module that soft-selects the 81 tokens down to **8**. **Transformer** — 8 images-worth of tokens concatenated across the 6-frame history into 48 tokens with position encodings, into a decoder-only model with 8 self-attention layers and 19 M parameters. **Action tokenization** — each dimension uniformly discretized into 256 bins. **Loss** — categorical cross-entropy with causal masking. **Inference speed** — humans take 2–4 s per instruction, so the target is ≥3 Hz and <100 ms of model latency; achieved via TokenLearner and by computing image tokens once and reusing them.

*5.2 Data.* ~130 k demonstrations, 13 robots, 17 months, **744 instructions** across skills: Pick Object (130 instructions), Move Object Near Object (337), Place Object Upright (8), Knock Object Over (8), Open/Close Drawer (3 each), Place Object into Receptacle (84), Pick from Receptacle and Place on Counter (162), plus 9 long-horizon kitchen instructions.

**6. Experiments.** Baselines are **Gato** (Transformer, per-patch image tokens with no language, no pretrained text embedding, no TokenLearner, autoregressive actions; shrunk from 1.2 B to 37 M parameters so it can run on the robot) and **BC-Z** (ResNet, feedforward with no history, continuous actions) plus **BC-Z XL** at RT-1 scale. All baselines are **retrained on RT-1's data**, so the comparison is architecture-only. Over **3000 real-world trials**.

*6.1 Setup.* Evaluations: seen tasks (200+ instructions with varied object placement, lighting, robot position); unseen tasks (21 novel verb-object combinations, with each object and skill seen separately in training); robustness (30 distractor tasks at easy/medium/hard levels, 22 background tasks in new kitchens and on patterned surfaces); long-horizon (15 SayCan-generated instruction sequences of ~10 steps in two real kitchens).

*6.2 Main result (Table 2).* Seen / Unseen / Distractors / Backgrounds: Gato **65 / 52 / 43 / 35**; BC-Z **72 / 19 / 47 / 41**; BC-Z XL **56 / 43 / 23 / 35**; **RT-1 97 / 76 / 83 / 59**. Note the authors' own caveat that all baselines are conditioned on natural language too, so the generalization gap needs the ablations to explain.

*6.3 Heterogeneous data.* Adding simulation data leaves real-object performance essentially unchanged (90, −2) while raising performance on sim-only objects with seen skills from 23 to **87 (+64)** and with unseen skills to **33 (+26)**. Data from a different robot embodiment (Kuka) is likewise absorbed without degrading original-task performance.

*6.4 Long-horizon.* Within the SayCan framework, RT-1 executes sequences of up to **50 steps**, at 87 % / 67 % execution success in Kitchen1 / Kitchen2.

*6.5 Data quantity vs. diversity (Table 7).* Removing 25 % of the *tasks* while keeping 97 % of the *data* hurts generalization as much as cutting the dataset by 49 %. Takeaway: **diversity beats quantity**.

**7. Conclusions, Limitations, Future Work.** 700+ instructions at 97 %; absorbs heterogeneous data; 50-step SayCan sequences. Limitations: imitation learning cannot exceed the demonstrators; generalization is limited to *recombinations* of seen concepts, not new motions; the task set is broad but not dexterous. Future: non-expert data collection, environment diversity for background robustness, scalable attention and memory. Code open-sourced.

**Appendix D.4 — Model ablations (Table 13).** Six ablations against full RT-1 (97 / 76 / 83 / 59, 15 ms inference): *w/o big model* (35 M → 21 M) 89 (−8) / 62 (−14) / 77 (−6) / 53 (−6); *w/o ImageNet pretraining* 84 (−13) / **43 (−33)** / 60 (−23) / 41 (−18); *w/ continuous actions* 68 (−29) / 43 (−33) / 37 (−46) / 35 (−24); *w/ autoregressive actions* 85 (−12) / 71 (−5) / 67 (−16) / 65 (+6) but 36 ms (>2× slower); *w/o history* 82 (−15) / 62 (−14) / 50 (−33) / 59 (+0); *w/o Transformer* 86 (−13) / 62 (−14) / 67 (−16) / 59 (+0). Discretized actions and ImageNet pretraining are the two decisive choices; history matters mainly for distractors; the Transformer contributes a uniform small gain.

**Appendix D.5 — Summary and analysis.** Four findings, the last of which is the paper's only mechanism-level argument about FiLM: *"RT-1 fuses language into the image pipeline early via FiLM conditioning, compared to e.g., Gato's late fusion. This enables image tokens that focus only on relevant features for the instruction at hand, which may be the cause of poor distractor performance for Gato."* Figure 13 supports it qualitatively with attention maps showing heads focusing on graspable objects and on the gripper-object interaction.

**Model card (Appendix).** "Transformer-based model, built upon a FiLM-conditioned EfficientNet, a TokenLearner, and a Transformer. Trained with imitation learning."

## Phase 1 — Undergraduate-level synthesis

**The problem.** One robot, hundreds of different spoken commands, real kitchens, real clutter, and a hard requirement to decide what to do three times a second. Prior systems either trained one network per task or trained a general network that fell apart when someone put an unfamiliar object on the counter.

**The architecture in four steps.** (1) A pretrained sentence encoder turns the command into a vector. (2) That vector re-tunes an image network: at each of the 26 blocks of a pretrained EfficientNet, the sentence vector produces one multiplier and one offset per feature channel, and the block's features are rescaled and shifted accordingly. This is FiLM, and the crucial point is that it happens **early and throughout**, so what the image network computes is already "the parts of this scene relevant to *this* instruction". (3) A small attention module keeps only the 8 most informative of the 81 resulting tokens per frame. (4) A Transformer looks across the last 6 frames and outputs the action, quantized into 256 bins per dimension.

**The one trick worth stealing.** You cannot just staple a FiLM layer into the middle of a network that has already been trained — the moment you multiply its activations by random numbers, everything it learned stops being valid. RT-1's answer is to make the layer *start out doing nothing*: initialize the weights that produce the multipliers and offsets to exactly zero, and write the operation as (1 + multiplier) × features + offset. At step zero the multiplier and offset are 0, so the operation is "1 × features + 0" — the identity. Training then moves it away from identity gradually. Their ablation shows why this matters: throwing away the ImageNet pretraining costs 33 points on unseen tasks, and identity initialization is the device that makes the pretraining survive the surgery.

**The headline numbers.** 97 % on trained instructions, 76 % on new ones, 83 % with distractors, 59 % in new kitchens — versus 65/52/43/35 for a Transformer baseline and 72/19/47/41 for a ResNet baseline trained on identical data.

**What is *not* shown.** Nobody removed FiLM. The ablation study varies six other things. So RT-1 is a very large, very careful demonstration that this architecture works, and not a measurement of what the modulation contributes.

## Phase 2 — Graduate-level deep dive

### 2.1 The conditioning path, precisely

$$
z \;=\; \mathrm{USE}(\ell) \in \mathbb{R}^{512}, \qquad \ell = \text{instruction string},
$$

computed **once per episode** by the pretrained Universal Sentence Encoder. For each MBConv block $m = 1, \dots, 26$ of EfficientNet-B3 with activation $F^{(m)} \in \mathbb{R}^{H_m \times W_m \times C_m}$:

$$
\gamma^{(m)} = \mathrm{fc}^{(m)}(z) \in \mathbb{R}^{C_m}, \qquad
\beta^{(m)} = h_C^{(m)}(z) \in \mathbb{R}^{C_m},
$$

$$
\widetilde F^{(m)}_{h,w,c} \;=\; \bigl(1 + \gamma^{(m)}_c\bigr)\, F^{(m)}_{h,w,c} \;+\; \beta^{(m)}_c .
$$

The $(1 + \gamma)$ form is printed in Figure 1(a) and drawn again in Figure 3. The output is a $9 \times 9 \times 512$ map flattened to 81 tokens, compressed by TokenLearner to 8, stacked over a 6-frame history into 48 tokens, and read by an 8-layer decoder-only Transformer that emits 11 action tokens per step, each a categorical over 256 bins.

**Note what is *not* modulated.** The Transformer — which is where temporal integration and action selection actually happen — receives no FiLM at all. Language reaches it only through the already-fused tokens. RT-1 therefore modulates *perception* and leaves *control* unmodulated, which is the opposite of the arrangement in Diffusion Policy ([`chi_2023_diffusion_policy.md`](chi_2023_diffusion_policy.md)) and the same arrangement as BC-Z ([`jang_2022_bcz.md`](jang_2022_bcz.md)) and BabyAI ([`chevalier_boisvert_2019_babyai.md`](chevalier_boisvert_2019_babyai.md)).

### 2.2 Identity-initialized FiLM: the mechanism, and why the form matters

The paper's statement, in full:

> "Normally, inserting a FiLM layer into the interior of a pretrained network would disrupt the intermediate activations and negate the benefit of using pretrained weights. To overcome this, we initialize the weights of the dense layers (fc and $h_C$) which produce the FiLM affine transformation to zero, allowing the FiLM layer to initially act as an identity and preserve the function of the pretrained weights."

Written out: with $W_{\mathrm{fc}} = 0$, $b_{\mathrm{fc}} = 0$, $W_{h_C} = 0$, $b_{h_C} = 0$ at initialization,

$$
\gamma^{(m)}(z)\big|_{t=0} = 0, \qquad \beta^{(m)}(z)\big|_{t=0} = 0
\qquad\Longrightarrow\qquad
\widetilde F^{(m)}\big|_{t=0} = (1 + 0)\,F^{(m)} + 0 = F^{(m)},
$$

so the modulated network computes *exactly* the pretrained function on the first step, for every input, regardless of the instruction.

Two subtleties deserve stating because they are easy to get wrong in an implementation.

**(a) The $(1+\gamma)$ parameterisation is load-bearing.** Under the plain $\gamma\, x + \beta$ form, zero-initialization gives the *zero map*, not the identity — every activation is annihilated and the pretrained weights are destroyed even more thoroughly than by random initialization. The identity trick requires the residual form. Equivalently one may write it as $x + (\gamma x + \beta)$: FiLM as a *residual branch* whose output is initially zero. This is the same device as zero-initialized residual branches (`Fixup`, `ReZero`) and as AdaLN-Zero in diffusion transformers, and it is the reason the corpus's newer entries keep encountering "AdaLN-**Zero**" rather than plain AdaLN.

**(b) The gradient at initialization is not zero — it is one-sided.** $\partial \widetilde F / \partial \gamma = F$ and $\partial \widetilde F / \partial \beta = 1$ are both nonzero at $t=0$, so the modulator receives gradient immediately and starts departing from identity on the first update. What *is* zero at initialization is the gradient flowing *back through the modulation into the conditioner path* in a compounding sense — since $\gamma = W_{\mathrm{fc}} z$ with $W_{\mathrm{fc}} = 0$, the update to $W_{\mathrm{fc}}$ is proportional to $z \cdot (\partial L/\partial \gamma)$, which is well-scaled, while $z$'s own gradient $W_{\mathrm{fc}}^\top(\cdot) = 0$ vanishes on the first step. If the sentence encoder were being fine-tuned, it would therefore receive no gradient at step 0 and only gradually come online — a soft warm-up on the conditioner that is worth knowing about. (The PDF does not state whether USE is fine-tuned, so this is a property of the construction, not a claim about RT-1's training.)

**How much is the trick worth?** The paper gives one direct sentence — identity initialization also helps when the EfficientNet is trained from scratch, but scratch training does not reach pretrained performance — with no numbers. The indirect quantification is the ablation: **removing ImageNet pretraining costs 33 points on unseen tasks and 23 on distractors.** Identity initialization is precisely the mechanism that lets FiLM be inserted without forfeiting that 33 points. So the correct summary is: *the trick's value is bounded above by the value of the pretraining it protects, which is large and measured; the trick itself is not separately measured.*

### 2.3 Early fusion versus late fusion — the corpus-relevant argument, and its limits

Appendix D.5 makes the paper's only mechanism claim about modulation: RT-1's early FiLM fusion "enables image tokens that focus only on relevant features for the instruction at hand, which may be the cause of poor distractor performance for Gato". The supporting numbers are the distractor column of Table 2: **RT-1 83, BC-Z 47, Gato 43, BC-Z XL 23**, and the "hard" distractor sub-column of Table 13 where RT-1 scores **64** against BC-Z's **7** and Gato's **29**.

This argument should be cited with two explicit caveats:

1. **BC-Z also uses FiLM.** BC-Z is a ResNet-18 with FiLM at four blocks driven by a sentence embedding — architecturally the same early-fusion family — and it scores 47 on distractors and 19 on unseen tasks. So "early FiLM fusion" cannot by itself be the explanation for the gap between RT-1 and BC-Z. The other differences (history vs. feedforward, discrete vs. continuous actions, TokenLearner, Transformer) are separately shown by Table 13 to be worth 15, 29, and 13 points respectively. The honest reading is that RT-1's margin is *multi-causal and mostly attributable to the ablated factors*, and the FiLM claim is the residual hypothesis for the Gato comparison only.
2. **Gato differs in more than fusion timing** — per-patch tokenization, no pretrained text encoder, autoregressive actions. Attributing the distractor gap to fusion timing alone is not supported by an ablation.

The claim is therefore a **reasoned hypothesis with corroborating attention visualisations**, not a measurement. It belongs in the corpus's "asserted" column.

### 2.4 The ablation table, read for what it *does* license

| Ablation | Seen | Unseen | Distractors (all) | Backgrounds | Inference |
|---|---|---|---|---|---|
| **RT-1 (full)** | **97** | **76** | **83** | **59** | 15 ms |
| w/o big model (35 M → 21 M) | 89 (−8) | 62 (−14) | 77 (−6) | 53 (−6) | 13.5 ms |
| **w/o ImageNet pretraining** | 84 (−13) | **43 (−33)** | 60 (−23) | 41 (−18) | 15 ms |
| w/ continuous actions | 68 (−29) | 43 (−33) | **37 (−46)** | 35 (−24) | 16 ms |
| w/ autoregressive actions | 85 (−12) | 71 (−5) | 67 (−16) | 65 (+6) | 36 ms |
| w/o history (6 frames → 1) | 82 (−15) | 62 (−14) | 50 (−33) | 59 (+0) | 15 ms |
| w/o Transformer | 86 (−13) | 62 (−14) | 67 (−16) | 59 (+0) | 26 ms |

What this licenses: that discretized multi-modal action representation and pretrained visual features are the two dominant design choices; that history is mainly about distractor rejection; that the Transformer contributes a uniform ~13-point gain over a plain EfficientNet head; and that autoregressive action generation costs 2× latency for no benefit.

What it does not license: **any statement about the modulation operator.** There is no "RT-1 w/o FiLM", no "RT-1 w/ concatenated language token", no injection-depth sweep, no gain statistics. Given the scale of this study — 3000 real-world trials, a fleet of robots, 17 months — the absence is the most informative fact about the field's priors: at the frontier of applied FiLM, the operator is treated as settled infrastructure and the ablation budget goes elsewhere.

### 2.5 Two secondary results with modulation relevance

**Heterogeneous data absorption (§6.3).** Adding simulation data raises performance on sim-only objects from 23 % to **87 %** while leaving real-object performance at 90 % (−2). Adding data from a different robot embodiment (Kuka bin-picking) likewise does not degrade original-task performance. Since the *only* task-identifying channel in the network is the language embedding driving FiLM, this is indirect evidence that a single affine modulation channel can index a task space spanning **two robot morphologies and two rendering domains** without the shared backbone tearing itself apart. It is not a controlled test of that claim, but it is the largest-scale demonstration of it available.

**Diversity beats quantity (§6.5).** Removing 25 % of tasks while keeping 97 % of data damages generalization as much as removing 49 % of the data. For a conditioned architecture this is the expected signature: the modulator's generalization is governed by the *coverage of the conditioner space*, not by samples per condition.

### 2.6 What RT-1 settles for the corpus, stated carefully

- **Settles:** affine modulation driven by a frozen-style pretrained text encoder scales to production — 26 injection sites, 35 M parameters, 3 Hz on real hardware, 700+ conditions, no reported modulation instability. Also settles the *insertion* problem for pretrained backbones: identity ($1+\gamma$, zero-init) initialization is the published solution, adopted at scale.
- **Does not settle:** whether FiLM outperforms concatenation, cross-attention, or a hypernetwork in this setting; whether 26 sites are better than 4 (BC-Z) or 2 (BabyAI); whether the gains saturate; whether modulating the *policy* (the Transformer) rather than only the *encoder* would help.
- **Does not bear on** the observation-conditioning question at all, except as a contrast case: the conditioner here is maximally slow and maximally exogenous.

## Connections

- **[`jang_2022_bcz.md`](jang_2022_bcz.md) (BC-Z)** — the direct predecessor and, in this paper, a *baseline* that RT-1 beats by 25 (seen) and 57 (unseen) points on RT-1's own data. Same conditioning family — sentence embedding → FiLM on a pretrained vision backbone — differing in depth of injection (4 ResNet blocks vs. 26 MBConv blocks), history (none vs. 6 frames), and action representation (continuous vs. 256-bin discrete). Table 13 attributes the last two of those differences 15 and 29 points respectively, so **the BC-Z → RT-1 improvement is largely not about the modulation**. This pairing is the corpus's best available evidence that scaling the *rest* of the architecture matters more than scaling the modulation.
- **[`perez_2018_film.md`](perez_2018_film.md)** — cited as the operator's definition. RT-1's contribution back to the FiLM literature is the identity initialization, which Perez et al. do not need (they train from scratch) and which becomes essential the moment FiLM is inserted into a pretrained network.
- **[`chi_2023_diffusion_policy.md`](chi_2023_diffusion_policy.md)** — the complementary case: same year, same subfield, opposite conditioner. RT-1 = *language conditions vision*; Diffusion Policy = *vision conditions action generation*. Together they show the affine operator is modality-agnostic, and that the interesting design question is which stream is the modulatee.
- **[`vaswani_2017_attention.md`](vaswani_2017_attention.md)** — RT-1 combines both mechanisms in series: FiLM for language-vision fusion, self-attention for temporal-spatial integration. Notably the authors chose *not* to fuse language by attention, and Appendix D.5 argues the early-affine choice is why distractors are rejected — an argument that runs against the trend toward attention-based conditioning documented in [`film_rl_recent_variants_survey.md`](../film_rl_recent_variants_survey.md).
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §8** — add as an **"architecture description only"** row alongside BC-Z: *"FiLM-conditioned EfficientNet at production scale — No FiLM ablation; six-way model ablation covers everything except the modulation — Architecture description; the early-vs-late fusion argument (App. D.5) is asserted with attention-map support and confounded by three other architectural differences."*
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §10.1** — RT-1 is the canonical *contrast* case for the observation-conditioning question: the conditioner is an episode-constant string embedding from a text-pretrained encoder. It shows how far one can get with a maximally slow conditioner, which sharpens rather than answers the question of what a fast one would do.
- **Project-side relevance.** The single most actionable item is **identity initialization**. If our modulator is inserted into a network whose weights carry prior structure — a pretrained encoder, a warm-started policy, or simply a network we want to be recoverable to its unmodulated behaviour — then writing the modulation as $(1+\gamma)x + \beta$ with zero-initialized $\gamma, \beta$ heads gives an exact identity at initialization, makes "modulation off" a point in the parameter space rather than a separate model, and turns the unmodulated baseline into a strict special case of the modulated one. That last property is worth flagging because it changes what an ablation can claim: under identity initialization, a modulated agent that fails to beat its concatenation baseline has *chosen* to depart from identity and lost, which is a much stronger negative result than one confounded with initialization noise. Any implementation follow-up belongs with `senior-developer` as an `issue_plan`; this review proposes no code changes.
