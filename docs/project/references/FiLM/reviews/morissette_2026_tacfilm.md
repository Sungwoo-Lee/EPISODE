---
title: "Tactile Modality Fusion for Vision-Language-Action Models (TacFiLM)"
authors: ["Charlotte Morissette", "Amin Abyaneh", "Wei-Di Chang", "Anas Houssaini", "David Meger", "Hsiu-Chin Lin", "Jonathan Tremblay", "Gregory Dudek"]
year: 2026
venue: "No venue line printed anywhere in the PDF — Springer LNCS two-column-free layout with running head 'C. Morissette et al.'; stamped arXiv:2603.14604v2 [cs.RO], 15 Jul 2026. The 'ECCV 2026' attribution is NOT verifiable from this file. Note also that the printed title has no 'TacFiLM:' prefix — the method name appears only in the abstract and body."
slug: morissette_2026_tacfilm
source_pdf: docs/project/references/FiLM/sources/Morissette et al. 2026 - TacFiLM - Tactile modality fusion for vision-language-action models.pdf
topic: FiLM
---

# Tactile Modality Fusion for Vision-Language-Action Models (TacFiLM)

## Plain-English entry point

A robot arm has to push a peg into a hole with three millimetres of slack, or plug in an HDMI cable. Cameras are close to useless at the moment of contact: the gripper occludes the hole, and the corrections needed are sub-millimetre. Humans do this by *feel*. So the question is how to give a large pretrained robot policy — a **vision-language-action model**, meaning a network that takes camera images plus a spoken instruction and outputs motor commands — a sense of touch, without retraining the whole thing.

The default answer in the literature is **concatenation**: run the tactile image through its own encoder and append the resulting tokens to the model's input sequence. This paper argues that is the wrong shape of fix — it makes the sequence longer (slower, and long contexts degrade), and it needs a new encoder trained per sensor. Their alternative, **TacFiLM**, is to leave the token sequence untouched and instead use the touch signal to **re-tune the vision network from the inside**: at each block of the vision transformer, a pooled tactile embedding produces one scale and one shift per feature channel, applied to that block's activations. Touch does not become another thing the model reads; touch becomes a *modulation of how the model sees*.

**Why this is the most valuable paper in this batch for the corpus's standing question.** It is the corpus's cleanest published head-to-head between the three candidate conditioning mechanisms — **FiLM vs. concatenation vs. cross-attention** — with everything else held fixed: the same base model (OpenVLA-OFT), the same pretrained tactile encoder, the same demonstrations, the same tasks, the same finetuning recipe. Over 1,000 real-robot rollouts. And the result is not marginal:

- Averaged over four in-distribution tasks: **TacFiLM 86.7 % success**, concatenation 64.8 %, vision-only 58.1 %, cross-attention 48.0 %.
- Averaged over five out-of-distribution tasks: **TacFiLM 86.7 %**, concatenation 73.3 %, vision-only 54.7 %, cross-attention 49.3 %.
- **Concatenation and cross-attention can both be worse than not using touch at all.** On the drawer-opening task, concatenation scores 26.7 % against the vision-only baseline's 33.3 %; cross-attention is below the vision-only baseline on most tasks.
- TacFiLM applies roughly **one third of the peak contact force** on the hardest out-of-distribution insertions (7.1 N vs. 27.7 N for concatenation, 26.2 N for cross-attention, 34.3 N vision-only).

Like RT-1, this paper writes the modulation as $(1+\gamma)$ with $\gamma$ and $\beta$ **zero-initialized**, so conditioning starts at exactly the identity and the pretrained vision-language priors survive the surgery. And it runs the injection-depth sweep almost nobody runs, finding that a **third** of the blocks is enough.

Two caveats to keep the citation honest: this is **not reinforcement learning** (it is imitation learning — LoRA finetuning of a pretrained VLA with an L1 regression action head), and the reported failure of cross-attention is explicitly attributed by the authors to the small task-specific dataset rather than to anything intrinsic about attention.

## Conditioning at a glance

| Question | Answer for this paper |
|---|---|
| **Conditioning signal** | A **pooled tactile embedding** $z_t$: the tactile image from a DIGIT vision-based touch sensor on the gripper, encoded by a **frozen pretrained tactile representation model** (Sparsh-DINO by default; T3 and other Sparsh variants also evaluated), with patch features averaged. Recomputed **every timestep** — a fast, exogenous *sensory* conditioner, not a task label, not language, not the visual observation. |
| **What is modulated** | The **visual backbone** of the VLA — the fused SigLIP + DINOv2 vision encoder — at the ViT-block level. The Llama-2 7B language decoder and the MLP action head are not modulated. No critic exists. |
| **Modulation operator** | **Full affine FiLM in residual/identity form**: $\text{FiLM}(F_n \mid \gamma_n, \beta_n) = F_n \odot (1 + \gamma_n) + \beta_n$, with $\gamma_n, \beta_n$ produced by an MLP from $z_t$ and **initialized to zero** so "conditioning starts near identity". |
| **Granularity** | Per-channel, **applied to the entire feature map** (shared across patch tokens), one $(\gamma_n, \beta_n)$ pair per ViT block. Placement: **after normalization, before the multi-head self-attention** of each block. |
| **Placement / number of sites** | Default **all ViT blocks**; ablated against early-third, middle-third and late-third variants. |
| **What it is for** | Adding a *new sensory modality* to a large pretrained policy under a parameter-efficient post-training budget, without lengthening the token sequence, without training a task-specific encoder, and without disturbing the pretrained vision-language priors. |
| **RL algorithm** | **Not RL.** Imitation learning: 80 teleoperated demonstrations per task, L1 regression on continuous action chunks, LoRA finetuning of the VLA and tactile-backbone linear layers with the FiLM layers trained from scratch. |
| **Ablated against concatenation?** | **Yes — this is the paper's central experiment**, and it also includes cross-attention and a no-tactile baseline, all on a shared backbone "so that differences in performance can be attributed to the fusion strategy rather than the underlying architecture". Plus an injection-depth ablation and a visual-degradation stress test. Numbers in §Phase 2.3–2.5. |
| **Reported instability / failure mode** | For the **alternatives**, not for FiLM: cross-attention "consistently underperforms across all tasks", hypothesised to need substantially more data because it introduces additional trainable visual-tactile interactions; concatenation's exerted force rises sharply under distribution shift, indicating it "may be more susceptible to variations in contact geometry and exhibit lower sensitivity to contact dynamics". No FiLM-side instability, gain blow-up, or saturation is reported (and none is measured). |

## Section-ordered backbone

**Abstract.** Proposes TacFiLM, a lightweight modality-fusion approach integrating visual-tactile signals into VLA models. States the problem: VLAs are vision-dominant, and vision "cannot capture the complex interaction dynamics that occur during contact-rich manipulation, including contact forces, surface friction, compliance, and shear", while existing tactile integrations add complexity through token concatenation or large-scale pretraining. TacFiLM is a **post-training finetuning** method conditioning intermediate visual features on **pretrained tactile representations** via FiLM. Results on insertion and drawer-opening tasks show consistent improvements in success rate, direct task performance, completion time and force stability, both in and out of distribution.

**1. Introduction.** Humans integrate vision, touch and proprioception; tactile signals carry object geometry, surface friction and contact forces, which matter exactly where occlusion and millimetre-scale adjustment defeat vision. Vision-based tactile sensors (DIGIT, GelSight) render touch as images, so it can be fed to vision architectures. Two problems with existing tactile-VLA work: (i) VLAs need substantial data and compute, motivating lightweight fusion inside a post-training paradigm; (ii) the common concatenation baseline requires training separate tactile encoders and appends tokens, "increasing sequence length and computational cost while risking performance degradation as context grows". TacFiLM's stated rationale for choosing FiLM over cross-modal fusion modules such as cross-attention is that it "enables parameter-efficient adaptation without extensive multimodal pretraining" and "preserves pretrained visual-language priors". Headline results previewed: 100 % success on 3 mm Circle-Peg in distribution, up to +50 % over the next-best baseline on selected tasks, 100 % on 3 mm out-of-distribution pegs, +30 % on HDMI plugging, and roughly one third of the baselines' applied force on select tasks. Contributions: the method; comprehensive experiments versus **concatenation and cross-attention**; an investigation of pretrained tactile encoders (Sparsh, T3).

**2. Related Work.** *2.1 VLA models* — visual encoder + projector + language-model backbone producing actions (OpenVLA, $\pi_{0.5}$, RT-1-X/RT-2-X); almost all are vision-and-language only. *2.2 Tactile sensing in robot learning* — GelSight/DIGIT/STS capture gel deformation with an embedded camera, giving high-resolution slip, contact geometry and deformation. Existing tactile-VLA work splits into **post-training finetuning** (tactile as extra tokens, attention-based fusion) and **multimodal pretraining / contrastive alignment**. Within fusion, "the most prevalent methods are concatenation and cross-attention", both of which either lengthen the token sequence or add attention parameters. Pretrained tactile representations (Sparsh, T3) are the enabling ingredient for the lightweight route.

**3. Methodology.**

*3.1 Policy architecture.* Built on **OpenVLA-OFT**: fused **SigLIP + DINOv2** visual backbone, MLP projector, decoder-only **Llama-2 7B**. Per timestep, images and language follow the standard VLA path; **in parallel, tactile observations are encoded by a pretrained tactile model, and that embedding conditions intermediate vision representations**. The tactile-conditioned visual features are projected into the language-model input space, concatenated with text tokens, processed by the decoder, and the final hidden states go to an MLP action head that regresses continuous actions with an **L1 objective**.

*FiLM-based fusion.* Tactile patch features are averaged to a pooled embedding $z_t$; for each selected ViT block $n$ in **both** DINOv2 and SigLIP encoders, an MLP projects $z_t$ to $\gamma_n, \beta_n$; FiLM is applied **after normalization and before multi-head self-attention**:

$$\text{FiLM}(F_n \mid \gamma_n, \beta_n) = F_n \odot (1 + \gamma_n) + \beta_n. \tag{1}$$

"Following the design principles from OpenVLA-OFT, $\gamma$ and $\beta$ are applied to the entire feature map. We initialize $\gamma$ and $\beta$ to zero, so conditioning starts near identity." Stated reasons for choosing FiLM: computationally lightweight; provides "a low-dimensional, inspectable global tactile bias"; no extra tokens; integrates cleanly into ViT blocks. Default is all blocks, ablated in §4.3.

*3.2 Pretrained tactile representations.* Encoder-agnostic by design; two families evaluated. **T3** — sensor-specific ViT encoders plus a shared transformer trunk (only the encoder and trunk are retained), tactile frames resized to 224×224. **Sparsh** — ViT trained with three self-supervised objectives: MAE (masked reconstruction), I-JEPA (latent prediction of masked regions), DINO (self-distillation). Sparsh preprocessing: **two tactile frames five timesteps apart concatenated channel-wise**, background removed, resized to 224×224.

*3.3 Training.* Off-the-shelf VLAs lack the precision for specialised tasks, so **LoRA** finetuning adapts the generalist without losing pretrained representations. Concretely: LoRA-finetune the linear layers of the OpenVLA-OFT and tactile backbones, **train the FiLM layers from scratch**, freeze everything else.

**4. Experiments.** Research questions: **Q1** how do different pretrained tactile encoders influence policy performance; **Q2** how do different fusion mechanisms compare; **Q3** does TacFiLM improve success, efficiency and contact sensitivity.

*4.1 Setup.* Franka Emika Panda 7-DoF arm with a two-finger gripper carrying a **DIGIT** sensor; Polymetis high-level control, libfranka over the Franka Control Interface at 1 kHz; teleoperation via a 3Dconnexion SpaceMouse. **80 demonstrations per task, ~70 steps each, recorded at 10 Hz** with joint states, end-effector pose, gripper width/status, RGB (RealSense) and tactile (DIGIT) images, and executed actions. Fixed language prompt per task ("Insert the [colour] [shape] peg into the [colour] base"; "Hook the gripper under the green handle of the top drawer and pull it open"). The object starts in hand — grasping is out of scope. **Baselines, all on the shared OpenVLA-OFT backbone**: (1) **OpenVLA-OFT** vision-only; (2) **TactileConcat** — tactile embedded by the same pretrained encoder, projected by a learned two-layer MLP, appended as tokens to the language and image tokens; (3) **Cross-Attn** — following PolyTouch, six stacked cross-attention blocks with residual connections after the vision backbone, visual patches as queries attending to projected tactile embeddings as keys/values. Metrics: success rate, **percentage of direct** (first-attempt, no-recovery) insertions/openings, **average maximum force (N)**, and average completion time (s). All methods trained to 80 k steps.

*4.2 Results.* Over **1,000 rollouts**: 480 in-distribution (30 per method), 300 out-of-distribution (15 per method), 240 for ablations. In-distribution tasks: Circle-Peg 3 mm, Circle-Peg 2 mm, USB-Cable-Plug, Open-Drawer. Out-of-distribution: Square-Peg 3 mm/2 mm, Pentagon-Peg 3 mm/2 mm, HDMI-Cable-Plug. Narrative findings: on the easiest task, TacFiLM and TactileConcat both beat vision-only and cross-attention on success, but TacFiLM's *direct* insertion rate is much higher and its force and time are lower; TactileConcat's relative performance **degrades as tasks get harder**; on the 2 mm out-of-distribution insertions TactileConcat's force magnitude rises sharply relative to its in-distribution behaviour while TacFiLM stays low; on HDMI plugging vision-only and TactileConcat are near zero while TacFiLM is markedly better; cross-attention underperforms everywhere, hypothesised to be data-hungry.

*4.3 Ablations.* **FiLM integration stage** — All vs. Early vs. Middle vs. Late third of ViT blocks, on in-distribution 3 mm Circle-Peg and out-of-distribution 3 mm Pentagon-Peg. All variants perform comparably and well; EarlyFiLM has a notably higher direct-insertion rate in distribution; all are equivalent out of distribution. Conclusion: "applying FiLM conditioning to a limited number of ViT blocks suffices for tactile integration, keeping computational overhead low." **Camera condition** — 80 % dimmed lighting and a 50 %-frame-rate frozen stream; TacFiLM holds 100 % success in both while the vision-only baseline drops to 93.3 % and 73.3 %. **Tactile encoder evaluation** — T3 and three Sparsh variants compared on three binary classification probes (Rotation-High, Rotation-Low, Contact) and TacBench force regression; **Sparsh-DINO** wins (97.72 % average classification, 36.09 RMSE) and is adopted throughout.

**5. Conclusion.** Pretrained tactile representations allow effective visuotactile policy adaptation without task-specific encoder training; TacFiLM improves task performance, direct insertion rate, completion time and interaction forces; "feature-level tactile conditioning yields more stable generalization behaviour than concatenation- and cross-attention-based fusion as well as vision-only models."

*5.1 Limitations.* A broader task suite would strengthen the results, but the absence of precise visuotactile simulators forced real-world-only experiments with expensive data collection and slow rollouts. The method is designed around OpenVLA-OFT; extending it to other VLA backbones such as $\pi_{0.5}$ is future work.

## Phase 1 — Undergraduate-level synthesis

**The setting.** Big pretrained robot policies read a camera and a sentence and output motor commands. They are good at knowing *what* to do and bad at the last millimetre of *doing* it, because at contact the camera cannot see what matters. A fingertip camera pressed against a gel pad (a DIGIT sensor) can: the gel deforms, and the deformation image encodes force, slip and contact geometry.

**Three ways to add touch, and why the choice matters.** (1) *Concatenate*: encode the touch image, turn it into extra tokens, staple them onto the model's input. Simple, standard, but the sequence gets longer — slower, and long contexts are known to dilute performance — and you have to train an encoder. (2) *Cross-attend*: add attention layers where the visual features query the tactile features. Expressive, but you are adding brand-new trainable machinery that has to learn the visual-tactile correspondence from scratch. (3) *Modulate*: turn the touch embedding into one multiplier and one offset per feature channel, and apply them inside the vision transformer. Nothing is appended, nothing new attends to anything, and the pretrained model's own structure is preserved — you are just nudging its features.

**The result.** Option 3 wins, and not narrowly. Averaged across tasks it succeeds 87 % of the time versus 65 % for concatenation and 58 % for using no touch at all. Cross-attention actually does *worse* than ignoring touch — the authors think there simply is not enough data (80 demonstrations per task) to teach a new attention mechanism what touch means. Concatenation is fine on easy tasks and falls away on hard ones.

**The safety-flavoured number.** Because the policy can feel how hard it is pressing, it presses less: on the hardest out-of-distribution insertions it peaks at about 7 N where the alternatives peak at 26–34 N. It also finishes faster and succeeds on the first attempt far more often, instead of jamming and recovering.

**Two engineering points worth remembering.** First, the modulation is written as *(1 + multiplier) × features + offset* with the multiplier and offset starting at exactly zero, so on the first training step the modified model is bit-for-bit the original pretrained model, and it only departs from that as it learns. Second, you do not need to modulate every layer: modulating a third of them works essentially as well as all of them.

## Phase 2 — Graduate-level deep dive

### 2.1 The architecture and the modulation, stated precisely

The base policy is OpenVLA-OFT: a fused **SigLIP + DINOv2** visual encoder producing patch embeddings, an MLP projector into the language-model embedding space, and a decoder-only **Llama-2 7B**, with an MLP head regressing continuous action chunks under an $L_1$ loss.

Let the tactile observation at time $t$ be $T_t$ (for Sparsh, two DIGIT frames five timesteps apart, concatenated channel-wise, background removed, resized to $224 \times 224$). The conditioner is

$$
z_t \;=\; \frac{1}{P}\sum_{p=1}^{P} \mathrm{Enc}^{\text{tac}}_{\text{pretrained}}(T_t)_p ,
$$

i.e. the mean over patch tokens of a **pretrained** tactile representation model — Sparsh-DINO in the main experiments. For each selected ViT block $n$ of the visual encoders, an MLP $g_n$ yields

$$
(\gamma_n, \beta_n) \;=\; g_n(z_t), \qquad
\text{FiLM}(F_n \mid \gamma_n, \beta_n) \;=\; F_n \odot (1 + \gamma_n) \;+\; \beta_n, \tag{1}
$$

applied **after the block's normalization and before its multi-head self-attention**, with $\gamma, \beta$ broadcast over the whole feature map (one value per channel, shared across patch tokens) and **initialized to zero**.

Three structural observations.

**(a) The pre-attention placement is a design choice with consequences.** Inserting the affine between LayerNorm and self-attention means the modulation shapes the *queries, keys and values* of that block — it changes which patches attend to which, not merely how the block's output is scaled. This is a strictly stronger intervention than FiLM applied to a residual-branch output, and it is the natural transformer-era analogue of Perez et al.'s "modulate before the nonlinearity". It also means the modulation is applied to normalized activations, which (as in BabyAI's batch-normalized FiLM and the conditional-normalisation lineage) prevents the conditional gain from having to compete with drifting activation statistics.

**(b) The gain is global over tokens.** $\gamma_n \in \mathbb{R}^{C}$, not $\mathbb{R}^{N \times C}$. Touch supplies "a low-dimensional, inspectable **global tactile bias**" — the paper's own phrasing — so the tactile signal cannot say *where* in the image to look, only *what kind of visual features matter right now*. Given that the tactile sensor has no spatial registration with the camera, this is the right restriction, and it is worth noting as a deliberate limitation of granularity rather than an oversight.

**(c) Identity initialization, again.** $\gamma = \beta = 0$ with the $(1+\gamma)$ form gives $\text{FiLM}(F_n) = F_n$ exactly at step 0. Combined with LoRA (low-rank adapters, also zero-initialized on one factor by construction) and a frozen tactile encoder, the whole tactile pathway is initialized as a **no-op on a pretrained policy**, and training only moves away from that as the demonstrations demand. RT-1 ([`brohan_2022_rt1.md`](brohan_2022_rt1.md)) arrived at the same device for the same reason four years earlier; two independent applied groups converging on zero-initialized $(1+\gamma)$ FiLM is about as strong as "community consensus on an implementation detail" gets in this corpus.

### 2.2 What the conditioner reads — and why this is the closest analogue in the corpus to an interoceptive modulator

The conditioner is a **second sensory stream**, sampled at the control rate, encoded by a *frozen* pretrained encoder, pooled to a single vector, and used to re-tune the *primary* sensory stream's encoder. Written as a map:

$$
\pi_\theta\bigl(\underbrace{I_t}_{\text{vision}},\ \underbrace{\ell}_{\text{language}}\ ;\ \gamma = g_\gamma(\underbrace{z_t}_{\text{touch}}),\ \beta = g_\beta(z_t)\bigr).
$$

Compare the other four papers in this batch. Chaplot and BabyAI: conditioner is an episode-constant *instruction*. RT-1: conditioner is an episode-constant *instruction embedding from a text-pretrained encoder*. Diffusion Policy: conditioner is the *same* observation modality that the task is about, modulating a stream (action denoising) that has no other access to it. TacFiLM is the only one where the conditioner is a **distinct, fast, bodily sensory channel that the modulated network does not otherwise receive**, and where the modulated network is the agent's *primary perceptual pathway*.

That is structurally the same shape as "an internal bodily signal re-tunes how the agent perceives the world". It still is not self-conditioning — vision does not modulate vision, and touch reaches the policy *only* through $(\gamma, \beta)$, so there is no double gradient path into a shared input. But among published work it is the nearest neighbour to a modulator driven by a second, interoceptive-like stream, and it reports that arrangement working better than concatenating that stream as extra input.

### 2.3 The mechanism ablation — the numbers

All values from Table 1; 30 rollouts per method in distribution, 15 out of distribution; shared OpenVLA-OFT backbone, shared Sparsh-DINO tactile encoder, shared demonstrations, 80 k training steps each. "Direct" = succeeded on the first attempt without a recovery adjustment. Force is average maximum exerted force in newtons (lower is better). Time in seconds (lower is better).

**In-distribution, per task (success % / direct %):**

| Task | Vision-only | TactileConcat | Cross-Attn | **TacFiLM** |
|---|---|---|---|---|
| Circle-Peg 3 mm | 86.67 / 3.33 | 96.67 / 16.67 | 63.33 / 10.00 | **100.00 / 36.67** |
| Circle-Peg 2 mm | 66.67 / 23.33 | 73.33 / 0.00 | 60.00 / 20.00 | **86.67 / 23.33** |
| USB-Cable-Plug | 33.33 / 0.00 | 43.33 / 6.67 | 33.33 / 0.00 | **73.33 / 33.33** |
| Open-Drawer | 33.33 / 33.33 | **26.67** / 26.67 | 20.00 / 20.00 | **86.67 / 73.33** |
| **Average** | 58.10 / 12.38 | 64.76 / 10.48 | 48.00 / 12.00 | **86.67 / 37.14** |
| **Average force (N)** | 14.94 ± 9.16 | 10.27 ± 4.12 | 13.43 ± 12.62 | **8.65 ± 3.80** |
| **Average time (s)** | 126.72 | 113.04 | 149.92 | **81.72** |

**Out-of-distribution, per task (success % / direct %):**

| Task | Vision-only | TactileConcat | Cross-Attn | **TacFiLM** |
|---|---|---|---|---|
| Square-Peg 3 mm | 93.33 / 0.00 | 93.33 / 13.33 | 60.00 / 6.67 | **100.00 / 46.67** |
| Pentagon-Peg 3 mm | 46.67 / 0.00 | **100.00** / 20.00 | 53.33 / 6.67 | **100.00 / 33.33** |
| Square-Peg 2 mm | 66.67 / 0.00 | **86.67** / 6.67 | 53.33 / 6.67 | 80.00 / **40.00** |
| Pentagon-Peg 2 mm | 60.00 / 0.00 | 73.33 / 0.00 | 46.67 / 6.67 | **86.67 / 20.00** |
| HDMI-Cable-Plug | 6.67 / 0.00 | 13.33 / 0.00 | 33.33 / 0.00 | **66.67 / 6.67** |
| **Average** | 54.67 / 0.00 | 73.33 / 8.00 | 49.33 / 5.33 | **86.67 / 29.33** |
| **Average force (N)** | 22.46 ± 15.75 | 16.47 ± 10.54 | 19.27 ± 14.62 | **8.40 ± 4.71** |
| **Average time (s)** | 89.48 | 105.79 | 149.77 | 87.84 |

Six readings that the corpus should carry:

1. **FiLM beats concatenation on the aggregate by 21.9 points in distribution and 13.3 out of distribution**, on matched backbones with matched tactile encoders. This is a mechanism ablation in the strict sense, and it is the largest, most controlled FiLM-vs-concatenation comparison in the whole library outside of Chaplot's A3C table.
2. **Concatenation can be worse than not using the extra modality.** Open-Drawer: 26.67 % against the vision-only baseline's 33.33 %. Adding tokens is not free, and the paper's stated mechanism — longer context degrading performance — is a specific, testable cost that affine modulation avoids by construction.
3. **Cross-attention loses everywhere**, and is the worst method overall in distribution (48.0 % average, below vision-only). The authors' explanation is a data-budget argument: cross-attention "introduces additional trainable interactions between visual and tactile representations, which may require substantially more data to learn effective multimodal correspondences". This is the corpus's first published *reason* for preferring affine modulation over attention conditioning that is not merely "it is cheaper" — it is a sample-complexity argument, and it predicts the effect should reverse at scale. Note it is a hypothesis in the paper, not a tested claim.
4. **The direct-insertion metric separates the methods more sharply than success rate does.** Out of distribution, vision-only achieves **0.00 %** direct insertions on every single task while still succeeding 54.7 % of the time — meaning it succeeds *only* by jamming and recovering. Concatenation raises this to 8.0 %, TacFiLM to 29.3 %. The success-rate column understates the difference in behaviour quality; the corpus should note that a modulation gain can be invisible in the headline metric and obvious in a process metric.
5. **Force is the cleanest signal.** Out-of-distribution average peak force: 8.4 N (TacFiLM) vs. 16.5 (concat), 19.3 (cross-attn), 22.5 (vision-only) — and on Square-Peg 2 mm specifically, 7.1 vs. 27.7 / 26.2 / 34.3. The interpretation offered is that concatenated tactile tokens are "susceptible to variations in contact geometry and exhibit lower sensitivity to contact dynamics" under shift, whereas modulation keeps the tactile signal coupled to perception. Whatever the mechanism, this is a *behavioural* difference of a factor of ~3–4 traceable to the fusion operator alone.
6. **The gap widens with difficulty and with distribution shift.** Concatenation is competitive at 3 mm clearance and collapses at 2 mm and on HDMI. This is the same difficulty-dependence Chaplot found for gating-vs-concatenation in A3C, and the same shape reported in the third-party Diffusion Policy component study ("FiLM significantly enhances performance on hard tasks, but is not needed for easy tasks"). **Three independent settings now show the same pattern: on easy tasks the fusion operator does not matter; on hard tasks it decides the outcome.** That is the single most citable cross-paper regularity the FiLM corpus has.

### 2.4 The injection-depth ablation (Table 2)

Almost nobody sweeps this. Variants: **AllFiLM** (all ViT blocks), **EarlyFiLM / MiddleFiLM / LateFiLM** (one third of the blocks at that depth). 15 rollouts each.

| Task | Variant | Success % | Direct % | Force (N) | Time (s) |
|---|---|---|---|---|---|
| Circle-Peg 3 mm (ID) | All | 100.00 | 36.67 | 7.64 ± 2.63 | 52.03 |
| | **Early** | 93.33 | **60.00** | **6.69 ± 0.92** | 60.85 |
| | Middle | 100.00 | 26.67 | 7.14 ± 1.71 | 53.88 |
| | Late | 100.00 | 23.33 | 8.47 ± 2.71 | 54.74 |
| Pentagon-Peg 3 mm (OOD) | All | 100.00 | 33.33 | 7.51 ± 2.88 | 53.15 |
| | Early | 100.00 | 33.33 | 9.96 ± 4.49 | 77.40 |
| | **Middle** | 100.00 | **53.33** | 8.99 ± 4.49 | 53.57 |
| | Late | 100.00 | 40.00 | 9.42 ± 3.31 | 68.57 |

Conclusions the data supports: **success rate is saturated and depth-insensitive** (93–100 % everywhere); the differences live in the *process* metrics and do not order consistently across the two tasks (Early is best in distribution on direct-insertion rate, Middle is best out of distribution). The authors' own summary is the safe one: **a third of the blocks suffices**, so injection depth is a compute knob rather than a performance knob in this regime.

For the corpus, add this to the very short list of published injection-depth sweeps — currently Nikulin's `film_first`/`film_last`/`film_full` on an offline-RL auxiliary network. The two agree on the negative: **depth is not where the leverage is**, provided some modulation exists. Note the caveat that this sweep runs on a task where the all-blocks variant is already at 100 %, so it has little headroom to detect a depth effect.

### 2.5 The visual-degradation stress test (Table 2, lower half)

Circle-Peg 3 mm under two camera corruptions, 15 rollouts each:

| Condition | Vision-only | TactileConcat | Cross-Attn | **TacFiLM** |
|---|---|---|---|---|
| 80 % dimmed lighting | 93.33 % | 86.67 % | 53.33 % | **100.00 %** |
| 50 % frame updates (partially frozen stream) | 73.33 % | 80.00 % | 46.67 % | **100.00 %** |

TacFiLM also holds the lowest force and time in both conditions. The claim this supports is narrow but real: **when the modulated stream degrades, a modulation-based fusion of a second modality substitutes for it better than a concatenation-based one does.** Mechanistically that is plausible — under modulation the tactile signal is present at every block of the visual computation, whereas concatenated tactile tokens must compete for attention against a full set of (now uninformative) visual tokens. The paper does not test that mechanism; it reports the outcome.

### 2.6 Tactile encoder comparison (Table 3)

Four frozen pretrained tactile representations, probed with an MLP classifier on tactile signatures relevant to insertion, plus TacBench force regression:

| | T3 | Sparsh-IJEPA | Sparsh-MAE | **Sparsh-DINO** |
|---|---|---|---|---|
| Rotation-High (%) | 92.73 | 99.15 | 99.36 | **99.36** |
| Rotation-Low (%) | 83.09 | 96.44 | 96.64 | **98.42** |
| Contact (%) | 73.31 | 85.08 | 93.92 | **95.39** |
| Average (%) | 83.04 | 93.56 | 96.64 | **97.72** |
| Force estimation (RMSE ↓) | 58.64 | 40.27 | 36.61 | **36.09** |

Sparsh-DINO is adopted throughout. Two things worth flagging: the fusion approach is explicitly "agnostic to the choice of tactile encoder", so the conditioner can be swapped without touching the modulation; and the encoder was selected by **probing accuracy on offline classification tasks**, not by end-task policy performance — a sensible but not equivalent criterion, and one that assumes representation quality transfers monotonically to modulation quality.

### 2.7 What this paper settles, and its limits

**Settles, with a controlled experiment on 1,000+ real rollouts:** for adding a *new sensory modality* to a large pretrained policy under a small-data post-training budget, **per-channel affine modulation of the primary encoder beats appending tokens and beats adding cross-attention**, on success rate, first-attempt rate, exerted force and completion time, in distribution and under distribution shift, with the margin growing with task difficulty. Also settles that ~1/3 of the blocks is enough injection depth in this setting.

**Does not settle:** anything in reinforcement learning (this is imitation learning with a regression head, no bootstrapping, no exploration, no value function); anything at scale (the authors' own explanation for cross-attention's failure predicts a reversal with more data, and they do not test it); anything about a *self*-conditioning modulator (touch does not reach the policy by any route other than $\gamma, \beta$); and anything about modulator dynamics (no gain statistics, no saturation analysis, no report of what $\gamma$ actually does over training — despite the paper's own claim that FiLM provides "a low-dimensional, **inspectable** global tactile bias", it never inspects it).

That last omission is worth naming, because it is exactly the corpus-wide gap: **the field's best argument for affine modulation is that it is interpretable, and no paper in this library actually reports the modulator's learned behaviour.**

## Connections

- **[`perez_2018_film.md`](perez_2018_film.md)** — cited as [47], the operator definition. TacFiLM updates the canonical form in two ways worth recording: the residual $(1+\gamma)$ parameterisation with zero initialization, and placement inside a **ViT block between normalization and self-attention** rather than inside a convolutional residual block.
- **[`brohan_2022_rt1.md`](brohan_2022_rt1.md) (RT-1)** — independently arrives at the identical zero-initialized $(1+\gamma)$ trick for the identical reason (inserting modulation into a pretrained backbone without destroying it). RT-1 is cited in this paper's bibliography. Cite the two together whenever the project needs to justify identity-initialized modulation.
- **[`chi_2023_diffusion_policy.md`](chi_2023_diffusion_policy.md)** — the complementary conditioner design (vision conditions action generation). Read with TacFiLM, the pair shows that the modality playing conditioner is a free variable and that the operator's advantage over alternatives is **difficulty-dependent** in both cases.
- **[`chaplot_2018_gated_attention.md`](chaplot_2018_gated_attention.md)** — the other rigorous head-to-head against concatenation in this corpus, eight years earlier, gain-only, in on-policy RL. The two papers bracket the corpus's evidence on the operator question: Chaplot in RL with an instruction conditioner and a tiny CNN; TacFiLM in imitation learning with a sensory conditioner and a 7 B-parameter VLA. **Both find concatenation collapsing as the task gets harder.**
- **[`vaswani_2017_attention.md`](vaswani_2017_attention.md)** — the cross-attention baseline is the attention-conditioning alternative, and it *loses* here, with a sample-complexity explanation. This is direct counter-evidence to the trend recorded in [`film_rl_recent_variants_survey.md`](../film_rl_recent_variants_survey.md) that attention is displacing affine conditioning at the frontier — with the important qualification that the trend is observed at large data scale and this result is at 80 demonstrations per task. The honest synthesis is **"affine wins in the small-data regime; attention wins at scale"**, and both surveys should say so.
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §8 (evidence-quality table)** — add as the strongest **ablated** row outside RL: *"Affine modulation of a pretrained vision backbone by a second sensory modality beats token concatenation and cross-attention — Yes: shared backbone, shared tactile encoder, 1,000+ real rollouts, 9 tasks, ID+OOD; 86.7 % vs 64.8 % (concat) vs 48.0 % (cross-attn) vs 58.1 % (no tactile) in distribution — Strong, but imitation learning, not RL, and at small data scale."* Also add the injection-depth sweep as the corpus's **second** such sweep.
- **[`film_in_rl_survey.md`](../film_in_rl_survey.md) §10.1** — does not close the observation-self-conditioning question, but narrows it further: a *fast, per-timestep, sensory* conditioner is now published and works well. What remains untested is only the case where the conditioner's source is also a direct input to the modulated network.
- **Project-side relevance.** This is the closest published architecture to "an internal bodily signal re-tunes perception", and it is the one paper in the batch whose evidence directly supports a modulation-over-concatenation design choice. Four transferable points. (1) **The controlled comparison exists and favours modulation** — if a project reviewer asks "why not just concatenate the interoceptive state into the observation vector?", this is the citation, with the caveat that the demonstrated setting is imitation learning. (2) **Measure process metrics, not just outcome metrics** — the vision-only baseline here succeeds 54.7 % of the time with a 0 % first-attempt rate, i.e. by thrashing; a success-only comparison would have understated the difference. The project analogue is that survival-step counts may hide a behavioural difference that a "did it act correctly the first time" measure would expose. (3) **Zero-initialized $(1+\gamma)$** makes the unmodulated agent an exact point in the modulated agent's parameter space — see the same recommendation in the RT-1 review. (4) **Report the gains.** Every paper in this corpus claims affine modulation is interpretable; none inspects the learned $\gamma$. Logging the gain distribution, saturation fraction and per-channel variance over training would be a genuinely novel contribution rather than a diagnostic afterthought. Any implementation follow-up belongs with `senior-developer` as an `issue_plan`; this review proposes no code changes.
