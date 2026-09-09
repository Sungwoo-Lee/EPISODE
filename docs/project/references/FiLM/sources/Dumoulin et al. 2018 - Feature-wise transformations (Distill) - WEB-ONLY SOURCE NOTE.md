# Dumoulin et al. 2018 — *Feature-wise transformations* (Distill)

**No PDF exists.** Distill is a browser-native journal; this article has no print
artefact to download. This note stands in for the PDF so the citation is not lost.

- **Citation**: Dumoulin, V., Perez, E., Schucher, N., Strub, F., de Vries, H.,
  Courville, A., Bengio, Y. (2018). *Feature-wise transformations.* **Distill**, 3(7).
- **DOI**: [10.23915/distill.00011](https://doi.org/10.23915/distill.00011)
- **URL**: https://distill.pub/2018/feature-wise-transformations/
- **Why it is held**: flagged as high-priority gap item #1 in
  [`../film_in_rl_survey.md`](../film_in_rl_survey.md) §11.1 — the canonical umbrella
  survey of the whole FiLM family, written by FiLM's own authors, **and it contains an
  RL section**. A referee expects it as the general "conditional modulation" citation;
  the corpus previously cited only Perez et al. 2018.

## Content captured 2026-09-09 (fetched from the live article)

**General formulation.** A FiLM layer computes `FiLM(x) = γ(z) ⊙ x + β(z)` — the
conditioning input `z` predicts a per-channel scale `γ` and shift `β`, applied
element-wise to features `x`.

**Taxonomy — three foundational operations:**

| Operation | Form | Note |
|---|---|---|
| Additive (conditional biasing) | `x + β(z)` | conditioning-derived bias added to hidden layers |
| Multiplicative (conditional scaling) | `γ(z) ⊙ x` | includes sigmoidal gating as the bounded special case |
| Combined (affine) | `γ(z) ⊙ x + β(z)` | maximal flexibility; this is FiLM proper |

The article's efficiency argument: parameter prediction scales **linearly in the
number of features**, which is why affine modulation is "a happy compromise between
effectiveness and efficiency" against full weight generation.

**The RL section — four papers cited:**

1. **Chaplot et al.** — sigmoidal gating fuses language and vision in a VizDoom agent
   following navigation instructions. *(Held: `Chaplot et al. 2018 - Gated-Attention…pdf`)*
2. **Bahdanau et al.** — FiLM layers condition Neural Module Network and LSTM policies
   for instruction following in grid worlds, trained adversarially.
3. **Kirkpatrick et al.** — **game-specific scale and bias conditioning a single shared
   policy network trained across 10 Atari games.** The earliest per-task affine
   modulation of an RL policy in the survey.
4. **Oh et al.** (bibliographic notes) — computes convolutional policy-network
   *parameters* conditioned on a task description, i.e. the hypernetwork end of the
   spectrum rather than the affine end.

## Status

Recorded, not reviewed. Nothing in this note is a substitute for reading the article
if a claim is to rest on it.
