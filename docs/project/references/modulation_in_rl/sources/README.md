# `modulation_in_rl/sources/` — raw source PDFs

**Read-only.** Reviews live at the topic root, not here:
[`../modulation_in_rl_lit_review.md`](../modulation_in_rl_lit_review.md).

**26 PDFs are held.**

## Scope — widened 2026-09-09

This folder originally held only papers implementing **FiLM-style scale-and-shift
modulation**, and explicitly excluded hypernetworks ("full weight generation"),
mixture-of-experts routing and plain concatenation. That boundary was lifted on
2026-09-09 for the cross-corpus field review of *FiLM **and** hypernetworks in RL*
([`field_review/`](../field_review/)), which needs the excluded papers as first-class
evidence rather than as appendix mentions — HyperMARL in particular, whose
conditioner/observation entanglement result is the corpus's only mechanism story for
why self-conditioning might hurt.

**The scope is now: conditioning mechanisms in reinforcement learning and robot policy
learning** — affine modulation, hypernetworks, low-rank adapters, routing, and
concatenation baselines. Concatenation is in scope deliberately: it is the control every
other mechanism is measured against, and the review's most controlled study finds a
FiLM-style gate *losing* to it.

The ten-paper review at the topic root still reflects the narrow scope. It has not been
rewritten; the field review supersedes it for cross-mechanism questions.

## Added 2026-09-09 (9)

Acquired for the field review. Per-paper reviews are in
`tmp/20260909_153028_filmhyper_rl/reviews_modrl_*.md` pending merge into the topic-root
review.

| File | Venue as printed in the PDF | Why acquired |
|---|---|---|
| `Beukman et al. 2023 - Dynamics generalisation … (Decision Adapter).pdf` | **NeurIPS 2023** | The corpus's most controlled comparison: 5 arms, parameter-matched, 16 seeds, concatenation vs FiLM-style gate vs generated adapter |
| `Xiong et al. 2023 - Universal morphology control … (ModuMorph).pdf` | **ICML 2023 (PMLR 202)** | Dissociates attention-routing from weight generation; proves concatenating a time-invariant context *is* an additive bias |
| `Benad et al. 2026 - Dynamics-aligned shared hypernetworks for contextual RL.pdf` | unstated — **"Preprint."** (arXiv 2602.06550v2) | One shared hypernetwork feeding dynamics model, policy and value function |
| `Roeder et al. 2025 - DALI ….pdf` | **NeurIPS 2025** | Context conditioning inside a Dreamer-style world model — but it concatenates |
| `Yang et al. 2020 - … soft modularization.pdf` | **NeurIPS 2020** | Per-task soft routing; the discrete-composition alternative to FiLM |
| `Sodhani et al. 2021 - … context-based representations (CARE).pdf` | **ICML 2021 (PMLR 139)** | Attention-mixture over encoders; carries a FiLM head-to-head |
| `Zintgraf et al. 2020 - VariBAD ….pdf` | **ICLR 2020** | Belief-latent conditioning; the base architecture other FiLM-vs-hypernet numbers are measured on |
| `Badia et al. 2020 - Never Give Up ….pdf` | **ICLR 2020** | Hyperparameter-index conditioning, by one-hot concatenation |
| `Badia et al. 2020 - Agent57 ….pdf` | unstated (ICML template, arXiv 2003.13350v1) | Adds a bandit-selected index and a scalar output gain |

## Reviewed in full (10)

## Reviewed in full (10)

| File | Venue as printed in PDF | Review |
|---|---|---|
| `Yuan 2024 - Unpacking the individual components of diffusion policy (preprint).pdf` | unstated (arXiv 2412.00084v1) | §6 |
| `Reuss et al. 2025 - FLOWER - democratizing generalist robot policies.pdf` | **CoRL 2025** | §7 |
| `Yoon et al. 2026 - PAPL - phase-aware policy learning via FiLM.pdf` | unstated (arXiv 2602.09370v2) | §8 |
| `Zhu et al. 2025 - EquAct - SE(3) equivariant FiLM.pdf` | unstated — "Preprint. Under review." | §9 |
| `Li et al. 2025 - CogVLA - modulation as routing.pdf` | **NeurIPS 2025** | §10 |
| `NVIDIA et al. 2025 - GR00T N1 (preprint).pdf` | unstated (industrial report) | §11 |
| `Marquis et al. 2026 - Hypernetwork-conditioned RL under actuator failures (preprint).pdf` | unstated (arXiv 2604.03392v1) | §12 |
| `Kang et al. 2026 - SplitAdapter - two-source factorised FiLM (preprint).pdf` | unstated (arXiv 2606.03297v1) | §13 |
| `Guo et al. 2026 - GEAR - drone aerobatics (preprint).pdf` | unstated (arXiv 2602.10997v1) | §14 |
| `Guo et al. 2026 - MoE-ACT (preprint).pdf` | unstated (arXiv 2603.15265v1) | §15 |

## Held as context only — NOT reviewed (6)

These do not implement scale-and-shift modulation. Where one bears on a question
*about FiLM* it appears in the review's §17 "Adjacent evidence" appendix, and nowhere
else; their own contributions are not assessed.

| File | Mechanism | Why excluded |
|---|---|---|
| `Tessera et al. 2024 - HyperMARL - adaptive hypernetworks for multi-agent RL.pdf` | full weight generation | hypernetwork. **Retained in §17** — principal counter-evidence on self-conditioning |
| `Zhang et al. 2025 - DyMoDreamer - world modeling with dynamic modulation.pdf` | 32×32 categorical latents **concatenated** into an RSSM state | not affine, and not modulation — concatenation |
| `Huang et al. 2024 - MENTOR - mixture of experts for single-task visual RL.pdf` | mixture-of-experts backbone | conditional computation, not conditional gain |
| `Grooten et al. 2025 - SPARC.pdf` | plain concatenation | negative control. **Retained in §17** |
| `Black et al. 2024 - pi0 - a vision-language-action flow model (preprint).pdf` | decoder-only MoE + cross-attention | **Retained in §17** as displacement evidence |
| `Li et al. 2025 - Neuro-Vesicles - critique of FiLM as neuromodulation (preprint).pdf` | position paper, no experiments | no evidence to contribute |

## Known gap

**e-nmRNN** — *Volume Transmission Implements Context Factorization to Target Online
Credit Assignment and Enable Compositional Generalization*, NeurIPS 2025 Poster,
OpenReview `S9Y89poypx`. **Download attempted 2026-09-09 and failed** — OpenReview
serves a Cloudflare challenge to plain `curl`; it needs `academic-pdf-fetch`'s headed-
Chrome tier. Still absent.
It was the earlier surveys' provisional candidate for a grouped-modulation precedent,
so the review's answer to that question is stated over the reviewed corpus and does
**not** include it. Under the narrowed scope it would in any case have been
context-only (biophysically derived modulation, not affine).

~~Also uncovered: *Hyper-GoalNet* (NeurIPS 2025) and *HyPoGen* (ICLR 2025).~~
**Both acquired 2026-09-09** and filed in `../../Hypernetwork/sources/`, which is their
mechanism home; they are in scope under the widened definition but the Hypernetwork
shard owns them.

## Conventions

- Filenames follow `<Author> <year> - <short title>.pdf`; the year is the **arXiv v1**
  year and may differ from the venue year printed inside (e.g. HyperMARL's file says
  2024, the held PDF is v4 and states NeurIPS 2025).
- Text extracts used during review were written to `tmp/` and are not committed.
