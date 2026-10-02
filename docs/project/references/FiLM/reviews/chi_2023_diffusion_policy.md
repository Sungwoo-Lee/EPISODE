---
title: "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion"
authors: ["Cheng Chi", "Zhenjia Xu", "Siyuan Feng", "Eric Cousineau", "Yilun Du", "Benjamin Burchfiel", "Russ Tedrake", "Shuran Song"]
year: 2023
venue: "No venue line printed anywhere in the PDF — SAGE-journal two-column layout (Abstract + Keywords block, running header 'Diffusion Policy'), stamped arXiv:2303.04137v5 [cs.RO], 14 Mar 2024. Commonly cited as RSS 2023 / IJRR; that attribution is NOT verifiable from this file."
slug: chi_2023_diffusion_policy
source_pdf: docs/project/references/FiLM/sources/Chi et al. 2023 - Diffusion Policy - Visuomotor policy learning via action diffusion.pdf
topic: FiLM
---

# Diffusion Policy: Visuomotor Policy Learning via Action Diffusion

## Plain-English entry point

Most robot-learning-from-demonstration methods train a network to look at what the robot sees and output the next action directly. That breaks when the demonstrations are **multimodal** — when a human sometimes goes around an object to the left and sometimes to the right, averaging the two produces a move straight into the object. Diffusion Policy replaces "predict the action" with "**denoise** the action": start from a sequence of pure random noise the shape of the next 16 actions, and run a learned network 100 times, each pass nudging the noise a little closer to a plausible action sequence. Because the starting noise is random, the same observation can produce the left-hand solution on one run and the right-hand solution on another — the policy represents the whole distribution instead of its average. Across 15 tasks from 4 benchmarks the method improves average success rate by **46.9 %** over prior state-of-the-art imitation learning, and it drives real bimanual robots that fold shirts and beat eggs.

**Why this paper is in the FiLM corpus, and the precise point it settles.** This corpus has repeatedly flagged an open question: *does any published policy let the modulator read the current observation?* Diffusion Policy is the closest published case, and the answer needs to be stated carefully, because it is easy to get wrong in both directions.

- The FiLM conditioner **does** read an **observation embedding**: the last $T_o$ frames (typically 2) are passed through a ResNet-18 vision encoder trained end-to-end, concatenated with the robot's proprioceptive pose into a feature $O_t$, and *that* is what generates the per-channel scales and shifts. Together with $O_t$, the **denoising iteration index $k$** also conditions the modulation. So the conditioner is genuinely observation-driven, not a task label, not a language embedding, not a frozen episode-constant vector — it changes every control step.
- But the **modulated network is not the observation pathway**. What FiLM modulates is the **action-denoising network** — a 1-D temporal convolutional U-Net running over the *action sequence*, which has no other access to the observation at all. Feature-wise modulation is the *only* channel by which the observation reaches the action generator. So this is "observation modulates a different stream", not "a stream modulates itself".

That distinction is the whole content of the paper's relevance here, and it is why the corpus's standing claim survives in weakened form: **an observation-driven conditioner is published, deployed and successful — but never as a self-modulation of the pathway that already reads the observation.**

One more thing to be precise about: **Diffusion Policy is not reinforcement learning.** It is behavior cloning from human demonstrations, with a supervised mean-squared-error loss. The paper's own Limitations section names applying it to RL as future work.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | $(O_t, k)$: the **observation feature** $O_t$ — the last $T_o$ steps of images encoded by per-camera ResNet-18 encoders (spatial-softmax pooling, GroupNorm, no pretraining, trained end-to-end) concatenated with proprioception — **plus the denoising iteration index** $k$. Changes at every control step and at every denoising step; not episode-constant. |
| **What is modulated** | The **noise-prediction network** $\varepsilon_\theta$ in the CNN variant: a 1-D temporal convolutional U-Net over the *action sequence*. This network has no other input path for the observation. Not an encoder; not a value function (there is none); the "policy" here is the denoiser itself. |
| **Modulation operator** | **Full affine FiLM** (Perez et al. 2018), cited by name: per-channel $a \cdot x + b$ produced by two linear layers from the conditioner. Figure 2(b) draws the two `Linear` blocks and the `a·x+b` operation explicitly. |
| **Granularity** | Per-channel, **at every convolution layer** of the denoising U-Net ("applied to every convolution layer, channel-wise"). This is the densest injection scheme in the corpus's RL-adjacent set. |
| **What it is for** | Making the action-generation process conditional on the observation, i.e. modelling $p(A_t \mid O_t)$ rather than the joint $p(A_t, O_t)$ used by trajectory-planning diffusion (Janner et al.). Motivation is stated as speed and accuracy: excluding $O_t$ from the denoiser's *output* speeds inference and makes end-to-end vision-encoder training feasible. |
| **RL algorithm** | **Not RL.** Behavior cloning / imitation learning; training loss is $\mathrm{MSE}(\varepsilon^k, \varepsilon_\theta(O_t, A^0_t + \varepsilon^k, k))$. |
| **Ablated against an alternative conditioning route?** | **Partially, twice.** (1) FiLM vs. **inpainting** (the Diffuser-style route of fixing observation dimensions inside the generated trajectory): "we found using FiLM conditioning to pass-in observations is better than inpainting on all tasks except Push-T" — stated in Appendix A.4 with **no numbers**. (2) FiLM-in-a-CNN vs. **cross-attention-in-a-transformer** — this *is* numerically resolved, across 20 benchmark cells, and the answer flips with the conditioner's modality. Never ablated against plain concatenation. |
| **Reported instability / failure mode** | The CNN (FiLM) variant "performs poorly when the desired action sequence changes quickly and sharply through time (such as velocity command action space), likely due to the inductive bias of temporal convolutions to prefer low-frequency signals". Separately: **BatchNorm had to be replaced by GroupNorm** in the vision encoder for stable training under exponential moving average. No gain blow-up or modulation-specific instability is reported. |

## Section-ordered backbone

**Abstract & Keywords.** Introduces Diffusion Policy: a visuomotor policy represented as a conditional denoising diffusion process. 15 tasks, 4 benchmarks, average improvement **46.9 %**. Claims three properties inherited from diffusion models — graceful handling of multimodal action distributions, suitability for high-dimensional action spaces, and training stability. Names three technical contributions: **receding-horizon control**, **visual conditioning**, and the **time-series diffusion transformer**. Keywords: imitation learning, visuomotor policy, manipulation.

**1. Introduction.** Behavior cloning as supervised regression fails for robot actions because of multimodality, sequential correlation and precision requirements. Figure 1 contrasts three policy representations: (a) explicit (regression / categorical / mixture-of-Gaussians), (b) implicit (an energy-based model minimised over actions), (c) diffusion (refining noise into actions via a learned gradient field). Lists the properties diffusion buys: expressing arbitrary normalizable — hence multimodal — distributions; scaling to high-dimensional outputs, which enables predicting whole action *sequences*; stable training, because no negative sampling is needed.

**2. Diffusion Policy Formulation.**

*2.1 DDPMs.* Denoising is $x^{k-1} = \alpha\bigl(x^k - \gamma\,\varepsilon_\theta(x^k, k) + \mathcal{N}(0, \sigma^2 I)\bigr)$ (Eq. 1), reinterpreted as one noisy gradient-descent step $x' = x - \gamma \nabla E(x)$ (Eq. 2) with $\varepsilon_\theta$ playing the role of the gradient field and the noise schedule $(\alpha, \gamma, \sigma)$ playing the role of a learning-rate schedule.

*2.2 DDPM training.* Sample a clean example $x^0$, a random iteration $k$, and noise $\varepsilon^k$; regress the network onto the noise: $L = \mathrm{MSE}(\varepsilon^k, \varepsilon_\theta(x^0 + \varepsilon^k, k))$ (Eq. 3). Minimising this also minimises the variational bound on the KL between data and model distributions.

*2.3 Diffusion for visuomotor policy learning.* Two modifications. **Closed-loop action-sequence prediction**: at step $t$ the policy consumes the last $T_o$ observations and predicts $T_p$ actions, of which $T_a$ are executed before replanning — a receding horizon that trades temporal consistency against reactivity. **Visual observation conditioning**: model $p(A_t \mid O_t)$ rather than the joint $p(A_t, O_t)$, giving $A^{k-1}_t = \alpha(A^k_t - \gamma\,\varepsilon_\theta(O_t, A^k_t, k) + \mathcal{N}(0,\sigma^2 I))$ (Eq. 4) and $L = \mathrm{MSE}(\varepsilon^k, \varepsilon_\theta(O_t, A^0_t + \varepsilon^k, k))$ (Eq. 5). Excluding $O_t$ from the denoiser's output speeds up inference and "helps to make end-to-end training of the vision encoder feasible".

**3. Key Design Decisions.**

*3.1 Network architecture options.* **CNN-based**: the 1-D temporal CNN of Janner et al. with three modifications — (i) condition on $O_t$ via **FiLM (Perez et al. 2018)** as well as on the denoising iteration $k$; (ii) predict only the action trajectory, not the concatenated observation-action trajectory; (iii) drop inpainting-based goal conditioning as incompatible with a receding horizon, noting that "goal conditioning is still possible with the same FiLM conditioning method used for observations". Reported behaviour: works out of the box on most tasks with little tuning, but poorly when actions change sharply in time. **Transformer-based**: noisy actions are input tokens to a minGPT-style causal decoder, the sinusoidal embedding of $k$ is prepended as the first token, and $O_t$ enters through **multi-head cross-attention** in every decoder block. Best on state-based tasks with high action-change rates, but more hyperparameter-sensitive. Recommendation: start with the CNN version; escalate to the transformer if performance is limited by task complexity or high-rate action changes. Figure 2(b) shows the FiLM path as two `Linear` layers producing $a$ and $b$ applied as $a \cdot x + b$ inside each Conv1D block; Figure 2(c) shows the cross-attention alternative.

*3.2 Visual encoder.* ResNet-18 without pretraining, per camera view, images encoded independently per timestep then concatenated to form $O_t$; trained end-to-end with the policy. Two modifications: **global average pooling → spatial softmax** (retains spatial information) and **BatchNorm → GroupNorm** ("important when the normalization layer is used in conjunction with Exponential Moving Average").

*3.3 Noise schedule.* Square-cosine schedule (iDDPM) works best; the schedule controls which frequency content of the action signal the policy captures.

*3.4 Accelerating inference.* DDIM decouples training and inference iterations: 100 training / 10 inference on the real robot, giving 0.1 s inference latency on an RTX 3080.

**4. Intriguing Properties.** *4.1* Multimodality arises from stochastic initialisation (which basin) plus stochastic Langevin sampling (moving between basins). *4.2* Position control beats velocity control for Diffusion Policy, contrary to prevailing behavior-cloning practice. *4.3* Action-sequence prediction gives temporal consistency and robustness to idle actions (paused demonstrations) that trip up single-step policies. *4.4* Training stability: implicit policies need an InfoNCE loss with negative samples to approximate the intractable partition function $Z(o,\theta)$, and inaccurate negative sampling destabilises training; DDPMs sidestep $Z$ entirely. *4.5* Connections to control theory: for a linear plant imitating a linear feedback policy $a = -Ks$, the optimal denoiser at $T_p = 1$ is $\varepsilon_\theta(s,a,k) = \frac{1}{\sigma_k}[a + Ks]$ and DDIM sampling converges to $a = -Ks$; for $T_p > 1$ the optimal denoiser produces $a_{t+t'} = -K(A - BK)^{t'} s_t$, showing that action-sequence cloning implicitly requires learning a task-relevant dynamics model.

**5. Evaluation.** *5.1* Benchmarks: **Robomimic** (Lift, Can, Square, Transport, ToolHang; proficient-human and multi-human datasets; state and image variants), **Push-T** (from IBC; contact-rich planar pushing, image or 9-keypoint variants), **Multimodal Block Pushing** (from BET; scripted-oracle demonstrations with long-horizon order multimodality), **Franka Kitchen** (7 objects, 566 human demonstrations, 4 tasks per demonstration in arbitrary order). *5.2* Methodology: 3 seeds × 50 environment initialisations, averaging the last 10 checkpoints and also reporting best checkpoint; 4500 epochs state / 3000 epochs image; each method evaluated in its best action space (position for Diffusion Policy, velocity for baselines). A footnote discloses that a bug meant only 22 initialisations were used for robomimic tasks, applied equally to all methods. *5.3* Key findings: wins on all tasks and variants; short-horizon multimodality (approaches the Push-T contact point from either side, whereas LSTM-GMM and IBC are biased and BET cannot commit); long-horizon multimodality (+32 % on Block Push $p_2$, +213 % on Kitchen $p_4$); position control beats velocity control; action horizon 8 is optimal; performance is maintained with up to 4 steps of simulated latency; stable training with task-consistent hyperparameters. **Vision-encoder ablation** (Table 5, Square-ph): ViT from scratch reaches only 22 %; frozen pretrained encoders perform poorly ("diffusion policy prefers different vision representation than what is offered in popular pretraining methods"); fine-tuning a pretrained encoder at 10× lower learning rate is best, with CLIP ViT-B/16 reaching 98 % in 50 epochs.

**6. Real-world Evaluation.** Real Push-T (harder than simulation: 3-DoF end-effector, latency, perturbations), Mug Flipping, Sauce Pouring and Spreading — including robustness to three types of live perturbation.

**7. Real-world Bimanual Tasks.** Extended proprioceptive observation and action spaces, teleoperation setup, and three tasks: Egg Beater, Mat Unrolling, Shirt Folding (a 9-stage long-horizon sequence).

**8. Related Work.** Explicit policies (regression, discretisation, mixture density networks, clustering-with-offset) versus implicit policies (EBMs — expressive but unstable due to negative sampling) versus diffusion models (Janner et al.'s planning; Wang et al.'s diffusion policies in RL with state observations). Positions this work as diffusion for *behavior cloning of visuomotor control*, contributing effective action spaces, the receding horizon, and the mechanism for integrating visual inputs into action diffusion.

**Limitations and Future Work.** Inherits behavior cloning's dependence on demonstration quality — RL is named as the route to exploiting suboptimal and negative data; higher computational cost and inference latency than LSTM-GMM.

**Appendix A.4 (Hyperparameters) — the conditioning ablation statement.** "For CNN-based Diffusion Policy, We found using FiLM conditioning to pass-in observations is better than [inpainting] on all tasks except Push-T. Performance reported for DiffusionPolicy-C on Push-T in Tab. 1 used [inpainting] instead of FiLM." Also: CNN hyperparameters are consistent across tasks and more parameters always helped, whereas transformer optimal dropout and weight decay vary greatly and more layers sometimes hurt. Appendix A also reports the **observation-horizon ablation** (vision-based policies prefer a low but $>1$ horizon; 2 is a good compromise) and the **data-efficiency ablation** (Diffusion Policy beats LSTM-GMM at every dataset size from 40 to 200 demonstration episodes).

## Phase 1 — Undergraduate-level synthesis

**The core idea.** Instead of a network that maps *what I see* → *what I do*, train a network that takes a **noisy guess** at the next 16 actions plus what I see, and returns a slightly less noisy guess. Run it 100 times from random noise and out comes a clean, plausible action sequence. Execute the first 8 of those actions, then look again and repeat.

**Where the conditioning problem arises.** The denoising network's job is defined over *action sequences*; its layers are 1-D convolutions along time, over action dimensions. The observation is a completely different kind of object — a stack of camera images plus joint positions. There are three obvious ways to let the observation influence the denoiser:

1. **Inpainting** — put the observation into the sequence being generated, and hold those slots fixed while denoising the rest. This is what earlier trajectory-diffusion planners did. It forces the model to also generate future *states*, which is slow and, in a receding-horizon controller, structurally awkward.
2. **Concatenation** — glue the observation vector onto the action tokens. (Not tried in this paper.)
3. **FiLM** — turn the observation into a set of per-channel multipliers and offsets and use them to re-tune every convolution layer of the denoiser. This is what they chose.

**What FiLM buys here.** The denoiser stays a pure function of the action sequence in its *input*, so nothing about future observations has to be predicted, inference is fast enough for real-time control, and the vision encoder can be trained end-to-end through the modulation path. The authors report that this beat inpainting on every task but one — though they give no numbers for that comparison.

**The comparison they do quantify.** They build a second version in which the observation enters a transformer through **cross-attention** instead of FiLM. Across the benchmarks, which one wins depends on **what the conditioner is looking at**:

- When the conditioner is a **camera image embedding** (the vision-based tables), the FiLM-CNN version is better on most tasks and much better on the hardest ones — e.g. 0.73 vs. 0.47 on ToolHang, 0.69 vs. 0.50 on the hardest Transport variant.
- When the conditioner is a **low-dimensional ground-truth state**, the cross-attention transformer wins, sometimes by a lot — 0.87 vs. 0.30 on state-based ToolHang, and 0.94 vs. 0.11 on the Block Push multimodality metric.

**The failure mode worth remembering.** The FiLM-CNN denoiser struggles when the action signal changes fast — for instance with velocity commands — because stacked temporal convolutions are biased toward smooth, low-frequency outputs. That is a property of the modulated backbone, not of FiLM itself, but in practice the two ship together.

## Phase 2 — Graduate-level deep dive

### 2.1 From unconditional DDPM to a conditional policy

The unconditional denoising step and its gradient-descent reading:

$$
x^{k-1} \;=\; \alpha\Bigl(x^k \;-\; \gamma\,\varepsilon_\theta(x^k, k) \;+\; \mathcal{N}\bigl(0, \sigma^2 I\bigr)\Bigr),
\qquad\text{compare}\qquad
x' \;=\; x - \gamma\,\nabla E(x).
$$

The identification $\varepsilon_\theta(x,k) \approx \nabla E(x)$ (up to the schedule's scaling) is what licenses reading the denoiser as a *learned gradient field over action space* and the sampler as noisy gradient descent on it. Training regresses the network onto the injected noise, $L = \mathrm{MSE}(\varepsilon^k, \varepsilon_\theta(x^0 + \varepsilon^k, k))$, which bounds the KL divergence between the data distribution and the sampler's marginal.

Making this a policy requires the denoiser to be conditional. Two options existed: model the **joint** $p(A_t, O_t)$ and condition by inpainting the observed slots (Janner et al.'s planner), or model the **conditional** $p(A_t \mid O_t)$ directly. The paper takes the second:

$$
A^{k-1}_t = \alpha\Bigl(A^k_t - \gamma\,\varepsilon_\theta\bigl(O_t, A^k_t, k\bigr) + \mathcal{N}(0,\sigma^2 I)\Bigr),
\qquad
L = \mathrm{MSE}\Bigl(\varepsilon^k,\ \varepsilon_\theta\bigl(O_t,\, A^0_t + \varepsilon^k,\, k\bigr)\Bigr).
$$

The stated consequences are (i) no need to infer future observations, hence faster sampling and better action accuracy, and (ii) end-to-end training of the visual encoder becomes feasible — because the encoder now sits on a *conditioning* path with a short gradient route to the loss, rather than being asked to also be a generative model of its own outputs.

**This is the structural reason FiLM appears.** Once you decide to model $p(A_t \mid O_t)$ with a network whose native input space is the action sequence, the observation has to enter as a *side channel*, and a per-channel affine on every layer is the cheapest side channel that touches the whole computation.

### 2.2 The FiLM path, exactly as printed

Let $F^{(\ell)} \in \mathbb{R}^{T_p \times C_\ell}$ be the activation of the $\ell$-th 1-D convolution block of $\varepsilon_\theta$ (time along the *action-sequence* axis, $C_\ell$ channels), and let the conditioner be

$$
z_t^{(k)} \;=\; \bigl[\,O_t \,;\, \mathrm{emb}(k)\,\bigr],
\qquad
O_t \;=\;\bigl[\,\mathrm{Enc}(I_{t-T_o+1}), \dots, \mathrm{Enc}(I_t)\,;\ \text{proprioception}\,\bigr],
$$

where $\mathrm{Enc}$ is the per-view ResNet-18 with spatial-softmax pooling and GroupNorm, applied independently per timestep and concatenated, and $\mathrm{emb}(k)$ is the diffusion-iteration embedding. Then, per Figure 2(b) and §3.1,

$$
a^{(\ell)} = W^{(\ell)}_a z_t^{(k)} + c^{(\ell)}_a \in \mathbb{R}^{C_\ell},
\qquad
b^{(\ell)} = W^{(\ell)}_b z_t^{(k)} + c^{(\ell)}_b \in \mathbb{R}^{C_\ell},
$$

$$
\widetilde F^{(\ell)}_{\tau, c} \;=\; a^{(\ell)}_c \cdot F^{(\ell)}_{\tau, c} \;+\; b^{(\ell)}_c
\qquad \text{for every convolution layer } \ell,\ \text{every channel } c,\ \text{broadcast over } \tau .
$$

Three properties distinguish this from every other FiLM use in the corpus:

1. **The conditioner is fast.** $O_t$ is recomputed at every control step; $\mathrm{emb}(k)$ changes at every one of the $K$ denoising iterations *within* a single control step. So $(a, b)$ are re-derived $K$ times per action, from a signal that is a function of the live camera stream. Every other conditioner in the RL/robotics part of this corpus — task ID, instruction, language embedding, achievement index — is constant for an episode or a task.
2. **The modulated stream is causally disjoint from the conditioner's source.** $\varepsilon_\theta$ sees actions and noise; the observation exists for it *only* as $(a, b)$. There is no additive path, no concatenation, no skip connection carrying $O_t$. That makes this an unusually clean instance of modulation-as-sole-channel, and it is why the design is informative: if the affine were a weak channel, the policy would simply fail.
3. **Density of injection is maximal**: every convolution layer, following Perez et al.'s prescription rather than the one-or-two-site practice of the RL papers.

### 2.3 What "conditioned on the observation" does and does not mean here

Spelling this out because the corpus's standing claim turns on it. Write the two architectures as maps:

$$
\textbf{Diffusion Policy: } \quad \varepsilon_\theta\bigl(A^k_t;\ \gamma = g_\gamma(O_t, k),\ \beta = g_\beta(O_t, k)\bigr)
$$

$$
\textbf{A self-modulating policy: } \quad \pi_\theta\bigl(O_t;\ \gamma = g_\gamma(O_t),\ \beta = g_\beta(O_t)\bigr)
$$

In the first, the modulated network's *own input* is $A^k_t$ — noise — and $O_t$ enters once, through $g$. The gradient of the loss with respect to the encoder flows through exactly one path. In the second, $O_t$ appears **twice**, and gradients from the direct path and the modulation path both terminate at the same input; that double path is the structure the corpus has flagged (via HyperMARL's gradient-interference argument) as the plausible mechanism for harm. **Diffusion Policy does not exhibit it.** So the correct citation is: *observation-derived conditioners are viable and successful (Chi et al.), but the self-conditioning double path remains untested in the literature.*

A second caveat: $O_t$ is an aggregate over the last $T_o$ observations (ablation says $T_o = 2$ works best for vision), so even the "current observation" is a short window, not a single frame.

### 2.4 The mechanism comparison the paper actually quantifies: FiLM-CNN vs. cross-attention transformer

The two variants differ in backbone *and* in conditioning route, so this is not a clean single-variable ablation — but it is the only head-to-head between affine modulation and attention conditioning on identical data in this corpus, and the pattern is striking. Values are (max checkpoint) / (average of last 10 checkpoints), 3 seeds × 50 initialisations.

**State-based observations (Table 1) — the conditioner is a low-dimensional ground-truth state:**

| Task | DiffusionPolicy-**C** (FiLM) | DiffusionPolicy-**T** (cross-attn) |
|---|---|---|
| Lift ph / mh | 1.00/0.98, 1.00/0.97 | **1.00/1.00, 1.00/1.00** |
| Can ph / mh | 1.00/0.96, **1.00/0.96** | **1.00/1.00**, 1.00/0.94 |
| Square ph / mh | **1.00/0.93, 0.97/0.82** | 1.00/0.89, 0.95/0.81 |
| Transport ph / mh | 0.94/0.82, **0.68/0.46** | **1.00/0.84**, 0.62/0.35 |
| ToolHang ph | 0.50/0.30 | **1.00/0.87** |
| Push-T | 0.95/0.91 *(inpainting, not FiLM)* | 0.95/0.79 |

**Vision-based observations (Table 2) — the conditioner is an end-to-end-trained image embedding:**

| Task | DiffusionPolicy-**C** (FiLM) | DiffusionPolicy-**T** (cross-attn) |
|---|---|---|
| Lift ph / mh | **1.00/1.00, 1.00/1.00** | 1.00/1.00, 1.00/0.99 |
| Can ph / mh | 1.00/0.97, 1.00/0.96 | **1.00/0.98, 1.00/0.98** |
| Square ph / mh | **0.98/0.92, 0.98/0.84** | 1.00/0.90, 0.94/0.80 |
| Transport ph / mh | **1.00/0.93, 0.89/0.69** | 0.98/0.81, 0.73/0.50 |
| ToolHang ph | **0.95/0.73** | 0.76/0.47 |
| Push-T | **0.91/0.84** | 0.78/0.66 |

**Multi-stage, state-based (Table 4):** Block Push $p_2$ — C **0.11** vs. T **0.94**; Kitchen $p_4$ — C 0.99 vs. T 0.96.

The regularity: **with an image-embedding conditioner, per-channel affine modulation wins, and its margin grows with task difficulty** (ToolHang +0.26, Transport-mh +0.19, Push-T +0.18 on the averaged metric). **With a low-dimensional state conditioner, cross-attention wins**, catastrophically so on the two tasks with sharp, order-multimodal action structure (state ToolHang, Block Push). The paper's own explanation for the CNN's weakness is spectral — temporal convolutions prefer low-frequency action signals — and it recommends the transformer precisely when "the rate of action change" is high.

For the corpus this is a genuinely new axis. Previous entries argue *FiLM vs. concatenation*; this argues *FiLM vs. attention*, and finds the answer is conditioner-dependent rather than universal. It also aligns with the note already recorded in [`film_rl_recent_variants_survey.md`](../film_rl_recent_variants_survey.md) that frontier vision-language-action models are displacing affine conditioning with attention and mixtures of experts — but adds the qualifier that the displacement is not uniformly an improvement when the conditioner is high-dimensional and visual.

### 2.5 The FiLM-vs-inpainting statement, and how much weight it can bear

Appendix A.4, in full: *"For CNN-based Diffusion Policy, We found using FiLM conditioning to pass-in observations is better than [inpainting] on all tasks except Push-T. Performance reported for DiffusionPolicy-C on Push-T in Tab. 1 used [inpainting] instead of FiLM."*

Three things follow. (i) It **is** a real comparison of conditioning mechanisms, run on all tasks, and it favours FiLM. (ii) It reports **no numbers whatsoever** — no table, no figure, no per-task deltas — so the claim strength is *asserted*, not *ablated*, and it should be cited as an author report rather than as evidence with an effect size. (iii) It has a concrete consequence for reading Table 1: the **state-based Push-T cell for DiffusionPolicy-C is not a FiLM result**, so any per-cell comparison involving that number is comparing inpainting against cross-attention. The vision-based Push-T cell in Table 2 is not flagged, so it is presumably FiLM.

Note also what inpainting *is*, since it is not the same alternative the corpus usually argues about: it conditions by fixing part of the generated object to the observed value, which requires the model to also generate observations. It is a *generative* conditioning route, not an *architectural* one. So this comparison does not speak to FiLM-vs-concatenation at all — that comparison is simply absent from the paper.

### 2.6 Stability notes worth extracting

- **GroupNorm instead of BatchNorm** in the visual encoder, required for stability when combined with an exponential moving average of weights. The corpus's other FiLM-in-RL entry with normalisation (BabyAI) uses BatchNorm; the interaction of conditional affine parameters with EMA and with batch statistics is a real implementation hazard, and this is the one paper that names it.
- **No modulation-specific instability is reported.** No gain statistics, no saturation analysis, no dead-channel counts — consistent with the corpus-wide finding that *nobody measures the modulator's own behaviour*.
- **The CNN variant's hyperparameters were stable across tasks and monotone in size** ("increasing the number of parameters in CNN-based Diffusion Policy always improves performance"), whereas the attention variant's dropout and weight decay "varies greatly across different tasks" and extra layers sometimes hurt. If robustness-to-tuning is a criterion, the affine-conditioned CNN wins that comparison outright, and this is stated explicitly.
- **Diffusion training is stable by construction** relative to the energy-based alternative: the InfoNCE loss (Eq. 7) needs negative samples to approximate the intractable $Z(o,\theta)$, and their inaccuracy destabilises training; the denoising objective never forms $Z$. This is an argument about the *objective*, not the conditioning, but it is why the paper can afford a densely modulated network without checkpoint-hunting.

### 2.7 The control-theoretic sanity check (§4.5)

For a linear plant $s_{t+1} = A s_t + B a_t + w_t$ with demonstrations from $a_t = -K s_t$, at $T_p = 1$ the loss $L = \mathrm{MSE}(\varepsilon^k, \varepsilon_\theta(s_t, -K s_t + \varepsilon^k, k))$ is minimised by

$$
\varepsilon_\theta(s, a, k) \;=\; \frac{1}{\sigma_k}\bigl[a + K s\bigr],
$$

so DDIM sampling converges to $a = -Ks$: the diffusion policy recovers the linear feedback law exactly. Extending to $T_p > 1$, the optimal denoiser must output $a_{t+t'} = -K(A - BK)^{t'} s_t$, since noise terms vanish in expectation. The consequence the authors draw is important and often overlooked: **predicting an action sequence forces the policy to implicitly learn a task-relevant dynamics model.** In the FiLM reading, $(a^{(\ell)}, b^{(\ell)})$ derived from $O_t$ must encode enough of $s_t$ to reproduce a *propagated* feedback law $-K(A-BK)^{t'}$ at every horizon offset — i.e. the affine parameters are carrying dynamical, not merely perceptual, information. That is a much heavier demand on a modulator than "select the relevant visual channels", and it is empirically met.

## Connections

- **[`perez_2018_film.md`](perez_2018_film.md)** — cited by name as the definition; Diffusion Policy follows Perez et al.'s prescription most faithfully of any paper in the applied set (every convolution layer, channel-wise, full affine), while inverting the usual arrangement: here the *conditioner* is perceptual and the *modulated* network is generative over actions, whereas in CLEVR the conditioner is linguistic and the modulated network is perceptual.
- **[`jang_2022_bcz.md`](jang_2022_bcz.md) (BC-Z)** and **[`brohan_2022_rt1.md`](brohan_2022_rt1.md) (RT-1)** — the same corner of robotics, opposite conditioner design. BC-Z and RT-1 modulate a *vision* backbone with a *language* embedding; Diffusion Policy modulates an *action-denoising* backbone with a *vision* embedding. Reading the three together gives the corpus its cleanest statement of the design space: the affine operator is agnostic to which modality plays conditioner and which plays modulatee.
- **[`vaswani_2017_attention.md`](vaswani_2017_attention.md)** — the transformer variant's cross-attention conditioning is the alternative mechanism, and §2.4 above is the numerical head-to-head. Anyone arguing "attention subsumes FiLM" must account for the vision-conditioned columns, where the affine version wins on the hardest tasks.
- **[`nikulin_2023_anti_exploration_rnd.md`](nikulin_2023_anti_exploration_rnd.md)** — the corpus's other dense-injection study (`film_first` / `film_last` / `film_full`). Diffusion Policy uses the equivalent of `film_full` without comment or sweep, in a setting where the conditioner is the *only* information channel — so it is an existence proof that full-depth injection is safe when the alternative is no information at all.
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §10.1** — the standing "nobody conditions on the observation" item should be **amended, not deleted**, with the distinction in §2.3 above: observation-derived conditioning is published and works; observation *self*-conditioning (double gradient path into the same input) remains untried.
- **[`film_rl_recent_variants_survey.md`](../film_rl_recent_variants_survey.md) §5.4** — that survey already cites a third-party component study (arXiv 2412.00084) that ablates Diffusion Policy's FiLM against feeding the observation as a direct network input, with numbers (ManiSkill PegInsertionSide 80 % vs. 44 %). **That is the numeric ablation this paper itself lacks**, and the two should always be cited together: Chi et al. for the design and the author's qualitative FiLM-beats-inpainting claim, the component study for the measured effect size. Note the venue of the component study is unconfirmed.
- **Project-side relevance.** Three transferable points. (1) **A fast, observation-derived conditioner is not exotic** — this system recomputes $(\gamma, \beta)$ at every control step and every denoising iteration, on real hardware, at 10 Hz, without reported instability; that removes "nobody has ever driven a modulator at observation timescale" as an objection to our design. (2) **What is still unprecedented is the double path** — our modulator and our main network read the same input, which Diffusion Policy structurally avoids; if a project ablation is run, the informative arm is *modulation-only* (the conditioner's information reaching the policy solely through $\gamma, \beta$) versus *both paths*, because the modulation-only arm is exactly the published, working configuration. (3) **Normalisation choice is load-bearing** — GroupNorm was required here for stability under EMA; if our modulated network uses BatchNorm and any weight averaging, that is a known hazard with a published fix. Any implementation follow-up should be handed to `senior-developer` as an `issue_plan`; this review proposes no code changes.
