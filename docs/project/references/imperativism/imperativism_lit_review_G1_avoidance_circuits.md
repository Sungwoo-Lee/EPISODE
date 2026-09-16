# Pain's Unpleasantness and Pain Avoidance in Animal Circuits (2001–2022) — Reference Review, Batch G1

**Topic folder:** `docs/project/references/imperativism/`
**Batch:** G1 of the imperativism field-history corpus — animal circuit studies. Four papers, reviewed one at a time in date order, 2026-09-17.
**Reviewer:** literature-reviewer
**Companion files:** Part A (philosophy of imperative and evaluative theories) is [[imperativism_lit_review_A_imperative_theories]]. The corpus list is `references_manifest.csv`.

## What this batch is about (plain-language entry point)

**The question.** People can report two things about a pain: how *strong* it is and how *bad* it feels. Human studies from the 1960s–1990s suggested the brain handles these separately. The "how bad" side was linked to a frontal region called the anterior cingulate cortex (ACC). Animals cannot give ratings, though. So how would you show in a rat or mouse that one brain circuit carries the *badness* of pain rather than its detection?

**The strategy these papers share.** Each one treats something the animal *does* as a stand-in for unpleasantness. Examples are learning to avoid a room where it was hurt, or tending to and escaping from a painful stimulus. Each paper then checks whether a brain manipulation changes that behaviour while leaving simple reflexes, such as pulling the paw away, unchanged.

**What the four papers report.**
- **Johansen et al. (2001):** destroying the front part of the rat ACC stopped rats from avoiding a room paired with a painful paw injection. Their paw-licking and flinching stayed the same.
- **Johansen & Fields (2004):** chemically exciting that area was enough to make rats avoid a room with no painful stimulus at all. The authors call ACC activity an "aversive teaching signal".
- **Corder et al. (2019):** a group of cells in the mouse amygdala responds to painful stimuli. Silencing them reduced tending, escape and avoidance but not reflexes.
- **Lee et al. (2022):** a pathway from the mouse ACC to the midbrain periaqueductal gray (PAG) increased *both* reflex sensitivity and active avoidance of a shock zone.

**Caution.** "Unpleasantness" is always inferred from behaviour here. The survey this corpus came from summarises two of these papers more strongly than their own text supports (see §6).

## Table of Contents

- [What this batch is about (plain-language entry point)](#what-this-batch-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Johansen, Fields & Manning (2001) — The affective component of pain in rodents [tier: full]](#1-johansen-fields--manning-2001--the-affective-component-of-pain-in-rodents-tier-full)
  - [Phase 1](#phase-1-foundational-overview) · [Phase 2](#phase-2-graduate-level-deep-dive) · [Backbone](#appendix-section-by-section-backbone) · Field-history record at end of entry
- [2. Johansen & Fields (2004) — Glutamatergic activation of anterior cingulate cortex produces an aversive teaching signal [tier: full]](#2-johansen--fields-2004--glutamatergic-activation-of-anterior-cingulate-cortex-produces-an-aversive-teaching-signal-tier-full)
  - [Phase 1](#phase-1-foundational-overview-1) · [Phase 2](#phase-2-graduate-level-deep-dive-1) · [Backbone](#appendix-section-by-section-backbone-1) · Field-history record at end of entry
- [3. Corder et al. (2019) — An amygdalar neural ensemble that encodes the unpleasantness of pain [tier: full]](#3-corder-et-al-2019--an-amygdalar-neural-ensemble-that-encodes-the-unpleasantness-of-pain-tier-full)
  - [Phase 1](#phase-1-foundational-overview-2) · [Phase 2](#phase-2-graduate-level-deep-dive-2) · [Backbone](#appendix-section-by-section-backbone-2) · Field-history record at end of entry
- [4. Lee et al. (2022) — Role of anterior cingulate cortex inputs to periaqueductal gray for pain avoidance [tier: full]](#4-lee-et-al-2022--role-of-anterior-cingulate-cortex-inputs-to-periaqueductal-gray-for-pain-avoidance-tier-full)
  - [Phase 1](#phase-1-foundational-overview-3) · [Phase 2](#phase-2-graduate-level-deep-dive-3) · [Backbone](#appendix-section-by-section-backbone-3) · Field-history record at end of entry
- [5. Batch notes for the synthesis](#5-batch-notes-for-the-synthesis)
- [6. Survey-claim audit (summary)](#6-survey-claim-audit-summary)
- [Not reviewed (no PDF)](#not-reviewed-no-pdf)

(Sub-entry anchors follow GitHub's duplicate-heading numbering: `-1`, `-2`, … in paper order.)

---

## Reading conventions

- **Page citations** are journal pages. All four PDFs are publisher versions with journal pagination:
  - *Johansen et al. 2001*, PNAS: pp. 8077–8082.
  - *Johansen & Fields 2004*, Nature Neuroscience: pp. 398–403.
  - *Corder et al. 2019*, Science: pp. 276–281.
  - *Lee et al. 2022*, Current Biology: pp. 2834–2847 plus STAR Methods pp. e1–e5.
- **Supplementary material is not in the PDFs.** Corder et al. and Lee et al. rely heavily on supplementary figures (Corder: figs. S1–S17 and the full methods; Lee: figs. S1–S6 and videos). Where a claim rests only on a supplementary figure, this review says so and cites the main-text sentence that reports it.
- **Statistics** are given as reported: means ± SEM in seconds for place-conditioning scores, and F / t / p values where the text states them. Corder et al. and Lee et al. report significance mostly as stars on figures, which cannot be read as numbers from the text; this is flagged.
- **No invented mathematics.** None of the papers derives equations. The one quantity defined algebraically in the text, the place-avoidance score of the Johansen papers, is shown as a display block.
- **Vocabulary used below.**
  - *CPA (conditioned place avoidance / aversion)*: the animal spends less time, after training, in a compartment where it earlier received an aversive treatment. *F-CPA* = CPA produced by a formalin injection in the hind paw.
  - *Formalin test*: dilute formalin injected under the paw skin activates nociceptors and produces paw lifting, licking and flinching for about an hour.
  - *Excitotoxic lesion (ibotenic acid)*: kills nerve cell bodies at the injection site while sparing passing fibres.
  - *Acquisition vs. expression*: learning the avoidance vs. showing already-learned avoidance.
  - *DREADD (hM4) + CNO*: an engineered inhibitory receptor, silenced on demand by the drug clozapine-N-oxide.
  - *TRAP*: genetic tagging of the neurons that were active during a chosen stimulus, so that only those neurons express the tool.
  - *Optogenetics*: light-controlled activation (ChR2) or inhibition (Arch) of genetically targeted neurons or axon terminals.
  - *ofMRI*: whole-brain functional MRI combined with optogenetic stimulation.
  - *BLA*: basolateral amygdala. *PAG*: periaqueductal gray, subdivided into dorsolateral/lateral (dl/lPAG) and ventrolateral (vlPAG) columns.
  - *Affective-motivational behaviour*: the authors' label for tending the injured paw, escape and avoidance, as opposed to *reflexive* withdrawal. This is an operational category, not a direct measure of feeling.
- **Project vocabulary.** "Pain" is correct for these animal studies. For this project's artificial agents the internal damage signal is **nociception**, never "pain". This batch draws no link to the agents.

---

## 1. Johansen, Fields & Manning (2001) — The affective component of pain in rodents [tier: full]

**Citation:** Joshua P. Johansen, Howard L. Fields & Barton H. Manning, "The affective component of pain in rodents: Direct evidence for a contribution of the anterior cingulate cortex," *Proceedings of the National Academy of Sciences USA* 98(14): 8077–8082, 2001. DOI 10.1073/pnas.141218998.
**PDF:** `docs/project/references/imperativism/sources/Johansen et al. 2001 - The affective component of pain in rodents - Anterior cingulate cortex.pdf` — published version (typeset PNAS pages with journal pagination).

### Phase 1: Foundational Overview

#### Introduction

By 2001, human evidence suggested that the anterior cingulate cortex (ACC) handles how *unpleasant* a pain is:
- Cingulotomy patients reported pain as less bothersome yet still located and graded it.
- In a hypnosis study (Rainville et al. 1997), changing rated unpleasantness while holding intensity fixed changed ACC activity but not somatosensory cortex activity.

That evidence was correlational or anecdotal. No animal study had shown that the ACC is *necessary* for the aversive side of pain, partly because standard rodent pain tests measure only reflex-like reactions. The authors paired the formalin paw test with place conditioning. The rat receives formalin in one distinctive compartment, and later chooses where to spend its time. Avoiding the compartment is taken as a readout of pain's negative affect. Paw lifting, licking and flinching during conditioning are taken as a readout of stimulus intensity and location.

#### Key Findings

1. **Rostral ACC lesions removed formalin place avoidance.** Sham-lesioned rats spent less time in the formalin-paired compartment after conditioning; rats with the rostral ACC destroyed did not.
2. **Acute pain behaviours were not reduced.** Lesioned rats licked, lifted and flinched the injected paw as much as sham rats (at one 5-minute time bin they scored *higher*).
3. **Anatomical specificity.** Similar-sized lesions of the caudal ACC, which receives less nociceptive input, changed neither avoidance nor acute behaviours.
4. **Stimulus specificity.** Rostral ACC lesions did not prevent avoidance learned with a non-nociceptive aversive drug (the kappa-opioid agonist U69,593). The authors take this as evidence against a general learning deficit.

#### Initial Takeaway

In rats, the forward part of the ACC is needed for a painful stimulus to become something the animal learns to avoid. The animal still reacts to the stimulus in the moment. The authors read this as the first causal animal evidence that the "unpleasantness" component of pain can be separated anatomically from the sensory component. They also note that the result could reflect a failure of pain-specific aversive *learning* rather than a loss of felt unpleasantness, and they suggest the two may not be separable in the brain.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Framework.** The introduction adopts the multi-component view of pain: Melzack & Casey (1968), Melzack (1975), Price (2000), Treede et al. (1999), with Price's alternate view acknowledged. In this view a lateral spinothalamic–somatosensory pathway codes stimulus parameters and a medial thalamus–ACC pathway codes unpleasantness (p. 8077). The authors add that the "ACC system" may also support "the avoidance learning that sometimes follows as a secondary reaction to pain" (p. 8077). This ties affect and avoidance learning together from the start.

**The measurement assumption.** The key bridging premise is stated explicitly: "it is reasonable to assume that F-CPA directly reflects a negative affective state produced by the nociceptive stimulus" (p. 8077). Everything downstream depends on it.

**Design.**

| Element | Detail (as reported) |
|---|---|
| Species / subjects | Male Long Evans rats, 290–320 g |
| Manipulation | Bilateral ibotenic acid (excitotoxic) lesions vs. PBS sham, 6 days' recovery. Rostral ACC = perigenual area 24b, part of 24a, dorsal area 32; caudal ACC = postgenual 24a/24b (p. 8079) |
| Apparatus | Three-compartment box: two conditioning compartments with distinct stripes and odours plus a neutral compartment. Glass floors with a 45° mirror to score paw behaviour; infrared beams for position and locomotion (p. 8078) |
| Protocol | Unbiased, counterbalanced 6-day design. Day 1 free-exploration pre-test (20 min); days 2–5 conditioning (formalin day vs. no-treatment day; 50 min confinement; 2 pairings each); day 6 drug-free test (20 min) (p. 8078) |
| Stimuli | 2.5% formalin in the hind paw (Exps 1–2); U69,593 s.c. (Exp 3; 60-min sessions, vehicle control) |
| Acute measures | Rating-scale nociceptive score and flinch frequency, in 5-min bins over the 50-min conditioning session (p. 8078) |
| Lesion criterion | ≥ 50% bilateral damage and ≥ 30% in the less-damaged hemisphere (p. 8079) |
| Statistics | Two-factor ANOVA (treatment × time, time repeated) with Tukey HSD for acute scores; Student's t tests for CPA, Bonferroni-corrected across multiple t tests (p. 8079) |

**CPA score.** For each rat, the paper defines the magnitude of avoidance as the drop in time spent in the treatment-paired compartment (p. 8079):

$$
\text{CPA magnitude} = t_{\text{paired}}^{\text{pre}} - t_{\text{paired}}^{\text{post}}
$$

A positive score means the rat avoided the compartment after conditioning. Groups were compared on this score, and pre- vs. post-test times were also compared within each group.

#### Key statistics (as reported)

**Experiment 1 — rostral ACC (lesion n = 8, sham n = 10; mean damage 62 ± 4%).**
- *Acute rating-scale scores:* no main effect of lesion. There was a lesion × time interaction, F(9,153) = 5.43, p < 0.05. Post hoc tests found one bin (10–15 min) where lesioned rats scored *higher* than shams; no other bin differed (pp. 8079–8080).
- *Flinch scores:* no main effect, F(1,17) = 0.799, and no interaction, F(9,153) = 1.601 (p. 8080).
- *Place avoidance:* shams went from 417.2 ± 34.2 s to 267 ± 18.9 s (p < 0.05); lesioned rats went from 355.8 ± 29.9 s to 388.6 ± 39.9 s (n.s.). CPA magnitude was lower in lesioned rats (t test, p < 0.05). The figure legend states that rostral ACC lesions "completely abolished F-CPA" (p. 8079); the abstract says "reduced" (p. 8077).

**Experiment 2 — caudal ACC (lesion n = 8, sham n = 11; damage 74 ± 4%).**
- *Acute scores:* rating F(1,13) = 0.439, interaction F(9,117) = 0.58; flinch F(1,12) = 0.138, interaction F(9,108) = 0.369. All n.s.
- *Place avoidance:* present in both groups (sham 414.6 ± 31.8 → 281.1 ± 43.5 s; lesion 391.6 ± 13.5 → 208.1 ± 37.6 s); magnitudes did not differ (p. 8080).

**Experiment 3 — rostral ACC with U69,593 (lesion n = 9, sham n = 8; damage 69 ± 3%).**
- *Place avoidance:* present in both (sham 343.0 ± 11.4 → 197.6 ± 15.1 s; lesion 359.0 ± 37.4 → 201.0 ± 17.3 s); magnitudes did not differ (p. 8081).
- Lesion size did not differ from Experiment 1.

Locomotor activity on conditioning days did not differ between rostral lesion and sham groups, which the authors take to rule out motor impairment (p. 8078).

#### Inferential Step — from result to claim

The argument, reconstructed:

- **P1.** F-CPA reflects the negative affective state produced by the nociceptive stimulus (assumption, p. 8077).
- **P2.** Acute formalin behaviours reflect the intensity and localisation of the stimulus (p. 8077).
- **P3.** Rostral ACC lesions abolish F-CPA but not acute behaviours (Exp 1).
- **P4.** The effect is not a general lesion effect (Exp 2: caudal lesions ineffective) and not a general place-learning deficit (Exp 3: non-nociceptive CPA intact; earlier reports of intact morphine and cocaine place preference after similar lesions, p. 8082).
- **C1 (strong, stated).** ACC neurons are "necessary for the acquisition or expression of CPA elicited by a nociceptive stimulus" (p. 8081).
- **C2 (hedged).** The reduction "may reflect a reduction in the aversiveness or perceived unpleasantness of the nociceptive stimulus" (p. 8081).
- **C3 (conclusion).** The data, with Rainville et al. (1997), "strongly support the contention that neuronal activation of the ACC is causally involved in the perception of pain-related unpleasantness" (p. 8082).

**Alternatives the authors themselves raise.**
1. **Learning/memory account.** The lesion might impair associating the nociceptive stimulus with the context rather than the stimulus's "primary aversive quality". The authors say this "is not ruled out completely" (p. 8082) and argue that the U69,593 control makes a *general* learning deficit unlikely. What remains open is a deficit in *pain-specific* aversive learning (p. 8082).
2. **Non-separability.** "It is possible that the perception of pain-related unpleasantness and pain-related aversion learning are not separable at the neural level" (p. 8082). The authors support this with ACC neurons that respond to both pain-predicting cues and noxious stimuli (Koyama et al. 1998).
3. **Acquisition vs. expression.** Pre-training lesions cannot tell which of the two is affected. The paper states the conclusion as "acquisition or expression" (p. 8081); this gap is what Johansen & Fields (2004) address.
4. **Validity of the animal model.** "it is never possible to know with certainty how closely an animal 'pain' model reflects pain as experienced by humans" (p. 8081).

#### Reviewer notes (for the field history)

- **Thresholds were not measured.** The sensory-side measure is spontaneous acute formalin behaviour (lifting, licking, flinching), not a nociceptive threshold test such as von Frey or hot plate.
- **Acute behaviour was not strictly unchanged.** In one time bin, lesioned rats scored higher on the rating scale.
- **Behaviour at test is the only affect readout.** Unpleasantness during the formalin session itself was not measured independently of learning.
- **Rostral vs. caudal matters.** The authors side with Vogt et al. (1996): rostral (perigenual) ACC for affect, caudal ACC for motor planning (p. 8081). Later mouse work, including Lee et al. (2022) below, targets different ACC coordinates.

### Appendix: Section-by-Section Backbone

**Abstract (p. 8077).** Human and animal evidence implicating the ACC in pain affect is indirect. Formalin paw test combined with place conditioning (F-CPA) measures affect and acute nociceptive behaviours together. Rostral but not caudal ACC lesions reduced F-CPA without reducing acute behaviours. ACC neurons are "necessary for the 'aversiveness' of nociceptor stimulation".

**Introduction (pp. 8077–8078).** Pain has distinct constructs: stimulus parameters (lateral pathway to somatosensory cortex) and unpleasantness (medial/intralaminar thalamus to ACC). Human evidence: nociceptive ACC neurons; cingulotomy reports; PET/fMRI; Rainville et al. 1997 hypnosis dissociation. Animal evidence: nociceptive neurons in area 24b; c-fos; limbic connections. A causal study is missing, partly because rodent pain models lack an affective index. F-CPA supplies one. Hypothesis: ACC lesions reduce F-CPA without affecting acute behaviours.

**Materials and Methods (pp. 8078–8079).** Subjects; drugs; three-compartment apparatus with a mirror for scoring; bilateral ibotenic acid surgery at rostral and caudal coordinates; 6-day counterbalanced unbiased CPA protocol; histology with stereology and lesion inclusion criteria; statistics (ANOVA/Tukey for acute scores; t tests on the CPA difference score with Bonferroni correction).

**Results — Histology (p. 8079).** Clear lesion borders; all included animals met criteria.

**Results — Experiment 1 (pp. 8079–8080).** Rostral ACC. Acute rating scores: interaction, with one bin higher in lesioned rats; flinch n.s. Sham rats showed CPA; lesioned rats did not; CPA magnitude lower in lesioned rats.

**Results — Experiment 2 (p. 8080).** Caudal ACC: no effect on acute behaviours or CPA.

**Results — Experiment 3 (pp. 8080–8081).** Rostral ACC lesion with U69,593: CPA intact. The rostral ACC is not needed for aversion in general.

**Discussion (pp. 8081–8082).** Formalin is a valid persistent-pain model, with the caveat about human comparability. Rostral lesion effects fit rostral-ACC nociceptive anatomy and Vogt et al.'s rostral-affect / caudal-motor proposal. Interpretation 1: loss of the affective salience of the stimulus blocks association. Supported by cingulotomy and Rainville 1997. Interpretation 2: a learning/memory deficit. Not fully excluded, but not general (U69,593; morphine/cocaine CPP). ACC neurons acquire responses to pain-predicting cues, and unpleasantness perception and aversion learning may not be separable neurally. Conclusion: rostral ACC neurons are required for pain-related aversion learning, "a process that directly reflects the affective component of pain" (p. 8082). Future work: ACC interactions with limbic nuclei and brainstem pain modulation.

**Field-history record**
- Year · community: 2001 · animal-circuits
- Question it asked: Is the rodent anterior cingulate cortex causally necessary for the aversive (affective) component of pain, as distinct from acute nociceptive responding?
- Position / finding in one line: Bilateral rostral (not caudal) ACC excitotoxic lesions in rats abolished formalin-conditioned place avoidance while leaving acute formalin paw behaviours and non-nociceptive (kappa-opioid) place avoidance intact.
- Responds to / builds on: Melzack & Casey 1968; Melzack 1975; Price 2000; Treede et al. 1999; Fields 1999; Rainville et al. 1997; Foltz & White 1962; Hurt & Ballantine 1974; Vogt et al. 1996; Gabriel et al. 1991; Koyama et al. 1998; Manning, Fields & Matthies 2000 (F-CPA model abstract)
- Measures (empirical only): intensity rating no (rats; proxy = acute formalin lifting/licking/flinching scores) · unpleasantness rating no (proxy = conditioned place avoidance) · avoidance/escape behaviour yes · desire/urge rating no · neural excitotoxic lesions (ibotenic acid) with histological/stereological verification
- Dissociation reported (empirical only): Rostral ACC lesion → formalin CPA abolished, acute formalin behaviours not reduced (one 10–15-min bin higher), U69,593 CPA intact; caudal ACC lesion → neither CPA nor acute behaviours changed
- Survey claim check: partly — 'ACC lesions abolish pain-conditioned place avoidance without changing nociceptive thresholds' → the abolition is reported for *rostral* ACC only ("Rostral ACC lesions completely abolished F-CPA", p. 8079; abstract says "reduced", p. 8077), and caudal lesions had no effect. No nociceptive *thresholds* were measured: the sensory-side measure was acute formalin behaviour, which was "not reduced" (p. 8081) but was higher in one time bin.
- PDF version: published

---

## 2. Johansen & Fields (2004) — Glutamatergic activation of anterior cingulate cortex produces an aversive teaching signal [tier: full]

**Citation:** Joshua P. Johansen & Howard L. Fields, "Glutamatergic activation of anterior cingulate cortex produces an aversive teaching signal," *Nature Neuroscience* 7(4): 398–403, 2004. DOI 10.1038/nn1207.
**PDF:** `docs/project/references/imperativism/sources/Johansen and Fields 2004 - Glutamatergic activation of anterior cingulate cortex produces an aversive teaching signal.pdf` — published version (typeset journal pages; header notes "Published online 7 March 2004; corrected 12 March 2004").

### Phase 1: Foundational Overview

#### Introduction

The 2001 study showed that destroying the rostral ACC *before* training stopped rats learning to avoid a formalin-paired room. It could not say whether the ACC is needed to *learn* the avoidance (supplying a "this is bad" signal during training) or to *show* it later (retrieving the memory, or giving the room its bad meaning). Nor did it show whether ACC activity alone is *enough* to make something aversive. This paper separates those possibilities with carefully timed manipulations.

#### Key Findings

1. **Not needed for expression.** Rats trained first and lesioned *afterwards* still avoided the formalin-paired room.
2. **Needed for acquisition.** Blocking glutamate receptors in the rostral ACC (kynurenic acid) during formalin training prevented avoidance learning. Acute formalin pain behaviours were unchanged, and the blocker alone had no effect on room preference.
3. **Sufficient for learning.** Exciting the rostral ACC with a glutamate-receptor agonist (homocysteic acid), with **no** painful stimulus, made rats avoid the paired room. A lower dose did not, nor did the same dose in neighbouring cortex.

#### Initial Takeaway

The authors define a "teaching signal" as a neural signal necessary and sufficient to produce a conditioned response. They conclude that glutamate-driven activity in the rostral ACC is such a signal for pain-driven avoidance learning. The learning itself (the plasticity) happens elsewhere, since the ACC is not needed once avoidance has been learned. They propose that one ACC circuit both encodes the negative affective quality of noxious stimuli, as human studies suggest, and supplies this aversive teaching signal.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Concept definition.** "We use the term 'teaching signal' to refer to a neural signal that is necessary and sufficient to produce a conditioned response (CR)" (p. 398). Coincident activation of the teaching pathway and the pathway carrying a neutral stimulus is assumed to strengthen CS→CR connections (p. 398). The framework is associative-learning neuroscience: Kandel; LeDoux (2000); Quirk et al. (1995); Rosenkranz & Grace (2002).

**Competing hypotheses and their predictions (pp. 398–399).** The paper states four readings of ACC function and derives a distinct prediction for each:

| Hypothesis about rostral ACC | Pre-training block / lesion | Post-training lesion | Direct activation alone |
|---|---|---|---|
| (H-expr) Mediates the motivational value of the conditioned stimulus after learning (suggested by ACC neurons that respond to pain-predictive cues) | — | Blocks expression | — |
| (H-teach) Supplies a nociceptive aversive teaching signal during learning | Blocks acquisition | Spares expression | — |
| (H-suff) ACC activity is sufficient as a teaching signal | — | — | Produces CPA |
| (H-plast) ACC is the site of the plasticity | Blocks acquisition | Blocks expression | — |

**Design.**

| Experiment | Manipulation | Groups (n) | Session details |
|---|---|---|---|
| 1. Expression | Bilateral ibotenic acid rostral ACC lesion made **after** a completed formalin CPA protocol and a first post-test; second post-test ≥ 6 days after surgery | lesion 7, sham 10; damage 62 ± 9% | Original 6-day protocol, 2 formalin pairings (p. 402) |
| 2. Acquisition | Kynurenic acid (KyA, 50 mM, 0.5 µl/side) into rostral ACC 5 min before formalin, on conditioning sessions | vehicle 10, KyA 8, KyA-without-formalin 8 | 2-day conditioning with 2 pairings; formalin behaviour scored on one pairing day (p. 402) |
| 3. Sufficiency | Homocysteic acid (HCA) into rostral ACC, **no** formalin | vehicle 9, 5 mM 8, 100 mM 11; off-site 100 mM (2.5 mm lateral) 8 | 30-min sessions, 3 pairings (p. 402) |

Subjects were male Long Evans rats, 300–350 g. Cannulae were aimed at AP +2.6, ML ±0.6 (rostral ACC, as in 2001). Statistics: CPA magnitude (pre − post time, as in the 2001 definition) compared by t tests or one-way ANOVA with Newman–Keuls; within-group pre/post by correlated t tests; acute scores by two-factor ANOVA (p. 402).

#### Key statistics (as reported)

- **Exp 1 (post-training lesion).** Sham: 389.8 ± 54.8 s → 211.6 ± 90.2 s (p < 0.05). Lesion: 392 ± 131.6 s → 184 ± 94.9 s (p < 0.05). Group difference n.s. (p. 399). Authors' conclusions: the rostral ACC "is not a significant site of plasticity for F-CPA learning" and "is not required for retrieval" (p. 399).
- **Exp 2 (glutamate blockade).**
  - KyA + formalin: 357.5 ± 50.6 → 320.6 ± 83.2 s (n.s.).
  - Vehicle + formalin: 388.3 ± 79.4 → 234.8 ± 106.5 s (p < 0.01).
  - KyA alone: 336.6 ± 86.3 → 321.3 ± 137.1 s (n.s.) (p. 399).
  - Acute formalin rating scores: no treatment effect, F(1,12) = 0.97; no interaction, F(9,108) = 0.72 (p. 400).
  - Motor activity unaltered ("data not shown", p. 399).
- **Exp 3 (glutamate stimulation).**
  - 100 mM HCA: 366.8 ± 44.8 → 251.2 ± 59.4 s (p < 0.01).
  - Vehicle: 336.1 ± 58.3 → 308.4 ± 92.2 s (n.s.). 5 mM: 352.1 ± 34.6 → 365.75 ± 69.8 s (n.s.).
  - One-way ANOVA on CPA magnitude F(2,27) = 6.46, p < 0.01. Newman–Keuls: 100 mM > vehicle; 5 mM = vehicle.
  - Off-site 100 mM: 347.4 ± 43.8 → 356.5 ± 157.6 s (n.s.) (p. 400).

#### Inferential Step — from result to claim

- Exp 1 rules out H-expr and H-plast (for the rostral ACC).
- Exp 2 is consistent with H-teach. Because acute formalin behaviours are intact, the block is not "a general decrease in nociceptive processing" (p. 400).
- Exp 3 supports H-suff. The authors call this "direct evidence that ACC neuronal activity is causal rather than permissive for avoidance learning" (p. 400).
- **Stated conclusion:** "ACC neuronal activity is necessary and sufficient for noxious stimuli to produce an aversive teaching signal" (abstract, p. 398).
- **Explicit hedge:** "Although the evidence is not conclusive, a parsimonious explanation of these results is that formalin injection produces an aversive teaching signal through activation of r-ACC neurons during CPA conditioning" (p. 401).

**Circuit model (p. 401).**
1. A nociceptive afferent pathway (spinal → medial thalamus → rostral ACC) terminates in or relays through the ACC.
2. "At some point afferent to the r-ACC, the afferent pathway mediating the aversive teaching signal diverges from that mediating many of the acute behavioral responses elicited by noxious stimuli" (p. 401).
3. The plasticity underlying avoidance occurs in regions receiving convergent ACC and contextual CS input. The amygdala is suggested via Rosenkranz & Grace (2002) and an abstract by Tang & Zhuo (2003).

**Bridge to human affect (p. 401).** "Whereas human studies suggest that the ACC processes information relating to the unpleasantness of the stimulus, our data indicate that this signal is necessary to produce avoidance learning. Together, the human and animal studies support the hypothesis that a circuit through the ACC encodes the negative affective quality elicited by noxious stimuli and concomitantly provides an aversive teaching signal."

**Open issues the authors raise.**
- *CS-responsive ACC neurons.* The results "do not bear on the function" of ACC neurons that respond to pain-predictive cues. Such neurons are not required for F-CPA expression; they may serve other forms of aversive learning or nociceptive modulation (p. 401).
- *Other responses.* Caudal ACC lesions may reduce acute escape responses to noxious heat (Pastoriza et al. 1996), so the unconditioned-response picture is not uniform across ACC subregions (p. 401).
- *Chronic pain.* Persistent input may sensitise the ACC (p. 401).

#### Reviewer notes (for the field history)

- **The sufficiency claim rests on one dose in one paradigm.** It is 100 mM HCA versus vehicle, in place conditioning. The paper does not report whether HCA-injected rats showed acute signs of distress or nocifensive behaviour during the session. So whether the activation is "felt as painful" or is aversive in some other way is not addressed.
- **"Teaching signal" is a learning-theoretic construct.** The paper connects it to unpleasantness only through the human literature, not through any additional animal measure.
- **Acquisition protocol differs from 2001.** The KyA experiment used 2 days with 2 pairings on the same day, not 4 days. The authors report no difference in F-CPA magnitude between regimens ("data not shown", p. 402).

### Appendix: Section-by-Section Backbone

**Abstract (p. 398).** Noxious stimuli support associative learning, but the circuitry is poorly understood. The ACC is implicated in pain affect and in the motivational properties of pain-predictive cues. In rats, excitatory amino acid injection into the ACC during conditioning produces avoidance learning without a peripheral noxious stimulus. Glutamate antagonist injection blocks noxious-stimulus learning. Post-conditioning lesions do not impair expression. ACC activity is necessary and sufficient for an aversive teaching signal; a shared ACC pathway mediates both pain negative affect and the teaching signal.

**Introduction (pp. 398–399).** Teaching-signal definition. Candidate spino-thalamo-cingulate pathway: human imaging correlation with unpleasantness (Rainville 1997), nociceptive ACC neurons across species, cingulotomy. The 2001 lesion study cannot separate acquisition from expression. Electrophysiology showing cue-responsive ACC neurons suggests an expression role. The four hypotheses and their predictions. Plan: temporally specific inactivation, lesion and activation.

**Results — r-ACC lesions do not affect expression (p. 399).** Post-training lesions: CPA intact. Rostral ACC is neither the plasticity site nor needed for retrieval.

**Results — r-ACC glutamate receptor blockade prevents F-CPA acquisition (pp. 399–400).** KyA blocks acquisition; KyA alone is neutral; no sedation; acute formalin behaviours unchanged.

**Results — Glutamatergic r-ACC stimulation produces avoidance learning (p. 400).** HCA is dose-dependent and site-specific; tests whether ACC activation is permissive or sufficient.

**Discussion (pp. 400–401).** Summary of the 2001 and present findings; sufficiency means causal rather than permissive; hedge ("not conclusive"). *A model* subsection: nociceptive afferent pathway; U69,593 result means no general learning deficit; ACC lesions spare other unconditioned responses; divergence of teaching-signal and acute-response pathways; plasticity downstream (amygdala candidates). *CS-responsive neurons in ACC* subsection: role unresolved. *Implications for chronic pain* subsection: ACC sensitisation. Summary: shared circuit for negative affect and teaching signal.

**Methods (pp. 401–402).** Subjects; drugs (IBO, formalin, HCA 5/100 mM, KyA 50 mM); surgery (double guide cannulae at AP +2.6, ML ±0.6; off-site ML 2.5); counterbalanced unbiased CPA; lesion-expression protocol; microinjection protocols (KyA 5 min before formalin, 50 min; HCA 30 min, 3 pairings); histology with methylene-blue site marking; statistics.

**Field-history record**
- Year · community: 2004 · animal-circuits
- Question it asked: Is rostral ACC activity needed to acquire, or to express, pain-driven avoidance, and is ACC activation by itself sufficient to produce avoidance learning?
- Position / finding in one line: In rats, post-training rostral ACC lesions spared formalin place avoidance, glutamate-receptor blockade in the ACC during training prevented it without changing acute pain behaviour, and glutamate-agonist activation of the ACC alone produced place avoidance, which the authors interpret as an aversive teaching signal.
- Responds to / builds on: Johansen, Fields & Manning 2001; Rainville et al. 1997; Foltz & White 1962; Hurt & Ballantine 1974; Koyama et al. 1998; Gabriel et al. 1991; Ploghaus et al. 1999; LeDoux 2000; Rosenkranz & Grace 2002; Vogt & Sikes 2000; Price 2000; Treede et al. 1999; Pastoriza et al. 1996; Tang & Zhuo 2003 (abstract)
- Measures (empirical only): intensity rating no (rats; proxy = acute formalin rating-scale scores) · unpleasantness rating no (proxy = conditioned place avoidance) · avoidance/escape behaviour yes · desire/urge rating no · neural excitotoxic lesion + intracerebral glutamate antagonist (kynurenic acid) and agonist (homocysteic acid) microinjection
- Dissociation reported (empirical only): Post-training lesion → CPA expression intact. KyA during formalin training → CPA acquisition blocked, acute formalin behaviours unchanged, KyA alone neutral. HCA alone (no noxious stimulus) → CPA produced (100 mM, not 5 mM, not off-site); acute behaviour not measured in this condition
- Survey claim check: yes — 'ACC activation is itself an aversive teaching signal' → matches the paper's conclusion that "ACC neuronal activity is necessary and sufficient for noxious stimuli to produce an aversive teaching signal" (p. 398), shown by agonist-induced CPA with no peripheral stimulus (p. 400). Caveats: the claim is limited to the rat rostral ACC, chemical activation and the place-avoidance paradigm, and the authors call the evidence "not conclusive" (p. 401).
- PDF version: published

---

## 3. Corder et al. (2019) — An amygdalar neural ensemble that encodes the unpleasantness of pain [tier: full]

**Citation:** Gregory Corder, Biafra Ahanonu, Benjamin F. Grewe, Dong Wang, Mark J. Schnitzer & Grégory Scherrer, "An amygdalar neural ensemble that encodes the unpleasantness of pain," *Science* 363(6424): 276–281, 2019. DOI 10.1126/science.aap8586.
**PDF:** `docs/project/references/imperativism/sources/Corder et al. 2019 - An amygdalar neural ensemble that encodes the unpleasantness of pain.pdf` — published version (Science Report, CC BY 4.0, 6 journal pages plus an editor's summary page). **Partial with respect to the full paper:** the Materials and Methods, supplementary text, figs. S1–S17 and table S1 are online-only and not in this PDF. Many sample sizes, statistics and some findings (e.g., fig. S13 optogenetic nociceptor experiment) are therefore reviewed only as described in the main text.

### Phase 1: Foundational Overview

#### Introduction

Pain feels bad, and the badness drives protective behaviour. By 2019, spinal and peripheral mechanisms of nociception were well mapped, but not how the brain turns "emotionally inert" nociceptive information into an unpleasant percept (p. 276). The basolateral amygdala (BLA) was a candidate:
- Rare patients with BLA damage detect and discriminate noxious stimuli but find them neither unpleasant nor worth avoiding.
- The BLA is hyperactive in chronic pain.

Earlier recordings were from single neurons in anaesthetised animals. This paper imaged hundreds of BLA neurons at once in awake, freely moving mice, then silenced the pain-responsive ones.

#### Key Findings

1. **A pain ensemble exists.** Noxious heat, cold and pin prick each activated about 13–15% of active BLA principal neurons. Together they formed a "nociceptive ensemble" of about 24% of active neurons, part of it (about 6% of all imaged neurons) responding only to noxious stimuli. The ensemble was largely separate from sucrose-responsive neurons, and partly distinct from neurons responding to other aversive stimuli (bad odour, bitter taste, loud noise, air puff, foot shock).
2. **Activity tracks behaviour.** Stronger ensemble activation predicted stronger pain behaviour.
3. **Silencing reduces affective-motivational behaviour, not reflexes.** Chemogenetically silencing these neurons had several effects:
   - It reduced paw tending and escape.
   - Mice stayed longer in noxiously hot and cold zones of a temperature track.
   - Mechanical detection thresholds, reflexive withdrawal, anxiety-like behaviour and sucrose reward were unchanged.
4. **Chronic pain recruits the ensemble.** After nerve injury, light touch began to activate the nociceptive ensemble. Silencing the touch-activated ensemble strongly reduced tending/escape and made injured mice almost indifferent to a cold floor, without changing reflex hypersensitivity.

#### Initial Takeaway

In mice, a specific group of amygdala neurons appears to be needed for the part of pain that drives tending, escape and avoidance, but not for detecting the stimulus or reflexively withdrawing. In nerve-injury pain, harmless touch comes to engage the same neurons. The authors interpret the ensemble as encoding the "negative affective valence" of pain. They say it supplies an evaluation that motivates protective behaviour, and that it cannot by itself account for the whole pain experience.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Framing.**
- Pain as sensory plus affective (Price 2000); the unpleasant percept is "coupled with the motivational drive to engage protective behaviors" (Baliki & Apkarian 2015) (p. 276).
- BLA as a valence-coding structure (Janak & Tye 2015; Namburi et al. 2015; Kim et al. 2016).
- Clinical dissociations: BLA damage leaves pain "detected and discriminated but … devoid of perceived unpleasantness and do not motivate avoidance" (Hebben et al. 1985; Neimann et al. 1964). The reverse holds for somatosensory cortex impairment (Ploner et al. 1999; Uhelski et al. 2012) (p. 276).
- Philosophical framing in the discussion: Grahek (2007) and Melzack & Casey (1968) on pain as a unified sensory-emotional perception (p. 281).

**Behavioural operationalisation.** Behaviour was tracked with a scope-mounted accelerometer, which "allowed us to track both reflexive withdrawal and affective-motivational behaviors that include attendance to the stimulated tissue and escape" (p. 276). This split between *reflexive* measures (von Frey threshold, withdrawal frequency) and *affective-motivational* measures (attending, escape, operant avoidance on a thermal gradient, cold place aversion) is the paper's central measurement choice.

**Design.**

| Component | Method | Sample (as reported in main text/legends) |
|---|---|---|
| Anatomy | c-Fos FISH: nociceptive c-Fos+ cells are mid-anterior BLA Camk2a+ principal neurons expressing negative-valence marker *Rspo2* (figs. S1) | not in main text |
| Imaging | Head-mounted miniature microscope, GCaMP6m in right (contralateral) BLA; stimuli to left hind paw: 55 °C water, 5 °C water/acetone, pin prick, 0.07 g and 1.4/2.0 g filaments, 10% sucrose, isopentylamine odour, quinine, 85 dB noise, air puff, foot shock, approach/no-contact | 3397 neurons (117 ± 8 per session); n = 9 mice, 3–4 sessions each (Fig. 1) |
| Decoding | Nine-way Naïve Bayes decoder across stimulus classes (Fig. 1L; Wilcoxon, Benjamini–Hochberg) | — |
| Causal (acute) | noci-TRAP: FosCreERT2 mice given pin pricks to tag active neurons with Cre-dependent hM4 (inhibitory DREADD); CNO 10 mg/kg | n = 14/group (reflexive and affective assays); thermal gradient saline 6 / CNO 7; TRAP counts n = 6/group |
| Chronic imaging | Longitudinal BLA imaging before and after sciatic nerve injury | 17,396 neurons, n = 17 mice (13 neuropathic, 4 uninjured) |
| Causal (chronic) | Light-touch TRAP of hM4 at day 21 post-injury; CNO test at day 42; two-chamber cold place aversion (floor 30 → 10 °C) | n = 14/group (reflex/affect); n = 6/group (cold aversion); TRAP counts n = 7/group |

#### Key results (as reported; most statistics are figure stars)

**Encoding.**
- Noxious heat, cold and pin activated 15 ± 2%, 13 ± 2% and 13 ± 2% of active BLA neurons; light touch activated 7 ± 1%. The union across noxious modalities, the "nociceptive ensemble", was 24 ± 2% of active neurons (p. 276).
- A nociception-selective subset was 6 ± 1% of all imaged neurons.
- 11% of 3223 cross-day-aligned neurons kept their noxious responses for more than a week.
- More salient touch recruited more of the ensemble: light touch 18 ± 3%, mild touch 31 ± 4% of the ensemble.
- Anticipation of contact recruited 7 ± 2% of the population (p. 276).
- Sucrose ensemble: 18 ± 3% of neurons, overlapping the nociceptive ensemble at 7% of total neurons (p. 276).
- Other aversive stimuli overlapped with the nociceptive ensemble in about 10% of neurons; about 6% responded only to naturalistic noxious stimuli (p. 277).
- The decoder distinguished noxious from other aversive, innocuous and appetitive stimuli "with even higher fidelity" than noxious stimuli from one another (p. 278).
- "greater activation of this BLA nociceptive ensemble was predictive of increased pain behaviors" (p. 278; Fig. 1M, Spearman).
- BLA activity did not correlate with exploratory locomotion (p. 276).

**Acute silencing.**
- "CNO … significantly reduced both attending and escape behaviors, but not stimulus detection and withdrawal, for both mechanical and thermal noxious stimuli" (p. 278). CNO alone had no effect in control mice (fig. S11C).
- Thermal gradient: CNO mice "visited the noxious zones more frequently and for prolonged periods" than saline mice, which "rapidly acquired an adaptive avoidance strategy" (p. 278).
- Optogenetic nociceptor activation: ensemble inhibition "eliminated pain affective-motivational behaviors" (p. 278; fig. S13 only).
- Elevated plus maze: open-arm visits and occupancy equivalent (p. 278; fig. S14).
- Sucrose: CNO "enhanced sucrose reward in sucrose-naïve conditions" but did not retard preference development or lick rates (p. 279).

**Chronic pain.**
- Nerve injury did not raise spontaneous ensemble activity. Light-touch responses within the ensemble grew by 291 ± 88% in neuropathic mice and fell by 38 ± 14% in uninjured mice (p. 279).
- Ensemble activation correlated with escape acceleration (Spearman r = 0.54 normal, 0.33 neuropathic, 0.58 uninjured; Fig. 3H).
- Silencing the light-touch-TRAPed ensemble did not alter reflexive hypersensitivity (Fig. 4D). The authors observed "a profound decrease in neuropathic affective-motivational behaviors, regardless of stimulus intensity or modality" (p. 280).
- Cold place aversion: CNO in neuropathic TRAP-hM4 mice "generated a near-total indifference between cold and neutral temperature chambers" (p. 280).
- Controls: uninjured light-touch TRAP mice had few tagged neurons and no CNO effect; CNO in neuropathic mice without hM4 had no effect (p. 280).

#### Inferential Step — from result to claim

1. **Encoding claim.** The ensemble responds across noxious modalities, contains pain-selective cells, is separable from reward and partly from general aversion, and scales with behaviour. The authors infer that it encodes "the negative affective valence of pain" (p. 276).
2. **Necessity claim.** Silencing it reduces tending, escape and avoidance but not threshold or withdrawal. The authors infer that it "transforms emotionally inert nociceptive information into an affective signal that is necessary for the selection and learning of motivational protective pain behaviors" (p. 279).
3. **Sensory/affective dissociation.** "disrupting neural activity in a nociceptive ensemble in the BLA is sufficient to reduce the affective dimension of pain experiences, without altering their sensory component" (p. 280).
4. **Title-level claim.** The ensemble "encodes the unpleasantness of pain". This step moves from reduced affective-motivational *behaviour* in mice to *unpleasantness*, a term defined by human report; the bridge is the clinical BLA-damage literature and the human sensory/affective model.

**Interpretive vocabulary (p. 281).**
- A pain-selective subpopulation suggests "the capacity for computing and assigning an accompanying 'pain tag' to valence information". The tag "could prioritize the negative valence of intense noxious stimuli and scale the selection of conative pain protective behaviors".
- The node plays "a critical role in shaping pain experiences, by providing an evaluation of nociceptive information that, in turn, intrinsically motivates protective behaviors associated with pain" (citing LeDoux & Brown 2017).
- Limits: "activity within the BLA nociceptive ensemble cannot account for the instantiation of the entire pain experience". The ensemble is proposed to transmit "abstracted valence information" to central amygdala, striatal and cortical networks.
- Open question: whether chronic recoding arises from peripheral or central sensitisation, amygdalar input, or intra-amygdala plasticity.

#### Reviewer notes (for the field history)

- **Evaluation and motivation language together.** The paper uses both *valence/evaluation* language ("negative affective valence", "an evaluation of nociceptive information") and *motivation/action* language ("intrinsically motivates protective behaviors", "selection … of motivational protective pain behaviors"). It does not adjudicate between evaluative and motivational theories of affect; it uses both.
- **"Silencing removes" vs. "reduces".** For acute pain, the main-text wording is "significantly reduced" (p. 278) and "alleviated" (abstract, p. 276). Stronger words ("eliminated", "profound decrease", "near-total indifference") are used for the supplementary optogenetic-nociceptor experiment and for the chronic-pain assays.
- **What "stimulus detection" means here.** It is operationalised by a von Frey mechanical threshold and withdrawal frequency (Fig. 2D–E). There is no separate test of discriminative capacity (e.g., intensity discrimination).
- **Sex, full statistics and exact methods** are in the online-only materials, which are not in this PDF.
- **Disclosure:** M.J.S. is a co-founder of Inscopix, maker of the miniature microscope (p. 281).

### Appendix: Section-by-Section Backbone

(Science Reports have no numbered sections; the backbone follows the paper's paragraph and figure order.)

**Abstract (p. 276).** Calcium imaging plus activity manipulation in freely behaving mice identifies a BLA ensemble encoding the negative affective valence of pain. Silencing alleviates affective-motivational behaviours without altering detection, withdrawal reflexes, anxiety or reward. After nerve injury, innocuous stimuli activate the ensemble to drive allodynia-like aversion.

**Background (p. 276).** Pain as sensory plus affective. Unknown brain transformation of inert nociceptive information. BLA: valence coding; lesion patients with unpleasantness-free pain; opposite dissociation for somatosensory cortex; chronic pain hyperactivity and fMRI connectivity changes. Need for ensemble-level recording in awake animals.

**Fig. 1 — A distinct nociceptive ensemble (pp. 276–278).** c-Fos anatomy; miniscope imaging; multimodal nociceptive ensemble; pain-selective subset; stability across days; graded recruitment by touch salience; sparse anticipatory activity; sucrose ensemble largely distinct; *Rspo2* marker; overlap with other aversive stimuli but a pain-only subset; decoder; ensemble activity predicts behaviour.

**Fig. 2 — Necessity for protective and avoidance behaviour (pp. 278–279).** noci-TRAP hM4 silencing: attending/escape reduced; threshold and withdrawal intact; thermal-gradient avoidance impaired; optogenetic nociceptor-evoked behaviours eliminated (S13); EPM unchanged; sucrose preference not retarded. Conclusion: an affective signal necessary for selection and learning of protective behaviours.

**Fig. 3 — Convergence of innocuous and noxious representations in chronic pain (p. 279).** Longitudinal imaging through nerve injury; stable nociceptive subset; no spontaneous increase; light-touch responses expand into the ensemble; behavioural correlation before and after injury.

**Fig. 4 — Silencing the neuropathic ensemble (p. 280).** Light-touch TRAP at day 21; day 42: reflex hypersensitivity unchanged, affective-motivational behaviours profoundly decreased; cold place aversion abolished to near-indifference; controls.

**Discussion (pp. 280–281).** The ensemble is sufficient-to-disrupt the affective dimension without altering the sensory component; combinatorial codes for modality/intensity/salience/valence; "pain tag"; hierarchical transformation; evaluation that intrinsically motivates protection; the unified sensory-emotional phenomenology of pain (Grahek; Melzack & Casey); BLA as one node projecting to CeA, striatum and cortex; open mechanism of chronic recoding; translational aim of therapies that reduce unpleasantness while sparing reflexes and discrimination.

**Field-history record**
- Year · community: 2019 · animal-circuits
- Question it asked: How does the basolateral amygdala represent noxious stimuli in awake mice, and is that representation required for the affective-motivational (as opposed to reflexive) side of acute and chronic pain?
- Position / finding in one line: A multimodal nociceptive ensemble of BLA principal neurons, distinct from reward and partly from general-aversion ensembles, is required for paw attending, escape and thermal avoidance but not for mechanical thresholds or withdrawal reflexes, and after nerve injury it is recruited by light touch to drive allodynic aversion.
- Responds to / builds on: Price 2000; Melzack & Casey 1968; Grahek 2007; Baliki & Apkarian 2015; Hebben et al. 1985; Neimann et al. 1964; Ploner et al. 1999; Uhelski et al. 2012; Janak & Tye 2015; Namburi et al. 2015; Kim et al. 2016; Grewe et al. 2017; Neugebauer et al. 2003/2015; Han et al. 2015; Guenthner et al. 2013; LeDoux & Brown 2017
- Measures (empirical only): intensity rating no (mice; proxies = von Frey threshold, reflexive withdrawal frequency) · unpleasantness rating no (proxies = attending and escape behaviour) · avoidance/escape behaviour yes · desire/urge rating no · neural miniscope calcium imaging (GCaMP6m) of BLA neurons, c-Fos in situ, activity-dependent (TRAP) chemogenetic silencing (hM4/CNO)
- Dissociation reported (empirical only): Silencing the BLA nociceptive ensemble → attending, escape, thermal-gradient avoidance and (neuropathic) cold place aversion reduced; von Frey threshold, withdrawal frequency, neuropathic reflex hypersensitivity, elevated-plus-maze anxiety and sucrose preference not reduced
- Survey claim check: yes — 'A BLA ensemble encodes unpleasantness; silencing it removes affective-motivational behavior but not withdrawal reflexes' → the paper reports that silencing "significantly reduced both attending and escape behaviors, but not stimulus detection and withdrawal" (p. 278). "Removes" overstates the acute result, which is a reduction; near-elimination is reported only for a supplementary optogenetic assay (p. 278) and chronic cold aversion (p. 280). "Encodes unpleasantness" is the authors' own title claim, inferred from mouse behaviour.
- PDF version: published

---

## 4. Lee et al. (2022) — Role of anterior cingulate cortex inputs to periaqueductal gray for pain avoidance [tier: full]

**Citation:** Jeong-Yun Lee, Taeyi You, Choong-Hee Lee, Geun Ho Im, Heewon Seo, Choong-Wan Woo & Seong-Gi Kim, "Role of anterior cingulate cortex inputs to periaqueductal gray for pain avoidance," *Current Biology* 32: 2834–2847.e1–e5, 2022. DOI 10.1016/j.cub.2022.04.090.
**PDF:** `docs/project/references/imperativism/sources/Lee et al. 2022 - Role of anterior cingulate cortex inputs to periaqueductal gray for pain avoidance.pdf` — published version (Elsevier typeset article with graphical abstract, highlights and STAR Methods; received 7 Dec 2021, published 23 May 2022). Supplemental figs. S1–S6 and videos S1–S2 are online-only and not in this PDF.

### Phase 1: Foundational Overview

#### Introduction

Clinical psychology's **fear-avoidance model** explains why some chronic pain patients become disabled: fear of pain leads them to avoid activity, and the avoidance spreads even to harmless situations (Vlaeyen et al. 2016). Neuroscience knew little about the brain circuits behind *active* defensive responses to pain. Most animal work had studied *freezing* to foot shock. The midbrain periaqueductal gray (PAG) coordinates defence: its dorsolateral/lateral columns (dl/lPAG) drive active responses such as running and jumping, and its ventrolateral column drives freezing and pain suppression. The ACC is a hub for pain affect and is altered in chronic pain. The authors asked what the ACC's downstream circuits do in pain, especially its input to the PAG. They combined behaviour with optogenetics and whole-brain fMRI at 15.2 tesla in mice.

#### Key Findings

1. **ACC matters for persistent, not acute, pain sensitivity.** Silencing the ACC left normal heat withdrawal latency unchanged and did not block acute capsaicin pain licking. It did reverse *maintained* heat hypersensitivity after capsaicin or chronic inflammation.
2. **Chronic pain strengthens the ACC network.** In mice with weeks of inflammatory pain, silencing the ACC produced larger brain-wide signal drops and stronger connectivity among its targets. The authors read this as higher baseline ACC output.
3. **ACC targets are sensorimotor rather than sensory.** During a noxious whisker-pad shock, silencing the ACC reduced responses in PAG and motor regions but not in the main somatosensory relay areas. Tracing showed dense ACC projections to the dl/lPAG and the motor superior colliculus. The prelimbic cortex instead projects mainly to the vlPAG.
4. **The ACC→dl/lPAG pathway changes reflexes and active avoidance.**
   - *Activation* lowered heat withdrawal latency (more sensitive); ketamine partly reversed this.
   - *Inhibition* raised withdrawal latency and suppressed chronic inflammatory hypersensitivity.
   - *Activation* increased movement speed without changing anxiety-like centre avoidance. It moved mice *toward* a predator odour, and it made mice keep a greater distance from a shock zone they had already learned to avoid.

#### Initial Takeaway

In mice, the ACC's projection to the active-defence columns of the PAG can push behaviour toward active defence. It increases reflexive heat sensitivity and moves animals further from a learned shock zone. Chronic inflammatory pain appears to strengthen this pathway. The authors propose that increased ACC→PAG signalling might contribute to excessive fear-avoidance in chronic pain. The paper tests *activation* of the pathway in the avoidance task, not whether avoidance *requires* it.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Framing (p. 2834).**
- Pain has sensory-discriminative and affective-motivational dimensions (Melzack & Casey 1968), with the latter establishing "the unpleasantness and aversive experiences of pain".
- The fear-avoidance model (Vlaeyen et al. 2016) is the clinical motivation.
- The defence-cascade model (Kozlowska et al. 2015) distinguishes active fight/flight from passive freezing.
- PAG column functions: dl/lPAG active defence, vlPAG analgesia and passive defence.

The ACC is introduced as a pain hub whose increased activity "engages in descending pain facilitation and fear memory formation" (citing, among others, Johansen & Fields 2004) and which is "known to generate a teaching signal for the sources of danger and predict future dangers" (citing Ortiz et al. 2019, Bian et al. 2019, Steenland et al. 2012, Han et al. 2003) (p. 2835).

**Subjects and tools (pp. e1–e3).**
- Adult male C57BL/6 mice (n = 42) for viral experiments.
- VGAT-ChR2-eYFP mice (5 male, 15 female) plus 4 female negative littermates. Sexes pooled because "behavior differences between genders were not observed" (p. e2).
- Injections and fibres were **unilateral, left hemisphere**: ACC at AP +1.0, ML 0.3, DV 1 mm; PrL at AP +2.5. The PAG fibre was at AP −4.0, ML 0.5, DV 1.9 mm.
- Pain models were in the right hind paw: capsaicin 20 µl (acute), and CFA 20 µl injected twice 7 days apart (persistent, ≥ 3 weeks).

**Design overview.**

| Experiment (figure) | Manipulation | Measure | n (as in legends) |
|---|---|---|---|
| ACC silencing on pain (Fig. 1) | VGAT-ChR2 activation (473 nm, 20 Hz, 10 ms, 3–5 mW) or CaMKII-eArch inhibition (532 nm) of ACC | Hargreaves heat withdrawal latency; capsaicin licking time; CAP/CFA hypersensitivity | VGAT-ChR2 6–7, littermates 4; eArch 5–7, eYFP 4 |
| Anaesthetic choice (Fig. 2A) | Ketamine vs. dexmedetomidine (DEX) | threshold, capsaicin behaviour, hypersensitivity | vehicle 10, KET 5–6, DEX 7 |
| Silencing ofMRI (Fig. 2) | VGAT-ChR2 ACC silencing under DEX/isoflurane, naive vs. CFA | BOLD area under curve (AUC) per ROI; 40-ROI functional connectivity; network-based statistic | naive 7, CFA 7 (after exclusion from 9, 8) |
| Noxious stimulation ofMRI (Fig. 3) | Whisker-pad electrical stimulation (0.4 mA, 4 Hz) with and without ACC silencing | BOLD AUC; module detection | 7–8 |
| Tracing and activation ofMRI (Fig. 4) | AAV5-CaMKII-eYFP anterograde tracing; ACC-CaMKII ChR2 activation ofMRI; ACC vs. PrL projections to PAG columns | fluorescence; BOLD AUC | activation 6 |
| ACC→dl/lPAG terminals on pain (Fig. 5) | ChR2 activation or eArch inhibition of ACC axon terminals in left PAG; ketamine | Hargreaves latency; CFA hypersensitivity | ChR2 7, eYFP 6; eArch 5–7, eYFP 4; KET 7 |
| Anxiety (Fig. 6A–B, S5A) | Terminal activation (473 nm, 20 Hz, 10 ms; 1 min on/off × 3) or inhibition | Open field: speed, centre/border time | 9 |
| Innate fear (Fig. 6C–D, S5B) | Same, with fox urine in an inescapable box | speed; time in zone near odour (1) vs. away (2) | 9 |
| Active place avoidance (Fig. 6E–H, S6) | **Activation only**, day 2 after day-1 training | shock-zone entries; angular distance from shock zone (ON1 − OFF1, with OFF1 − OFF2 as baseline) | 9–10 |

In the active place avoidance task (APAT) (p. e3), mice sit on a rotating arena (radius 17 cm; 3 then 2 rpm). A 60° sector is a shock zone (0.2 mA, 60 Hz, 500 ms, repeated every 1.5 s until exit), located by wall cues. Day 1 is training; day 2 repeats it with 5-min on/off light blocks.

#### Key results (as reported; statistics mostly as figure significance markers)

**ACC silencing (Fig. 1, p. 2837).**
- No change in naive heat threshold under either silencing method.
- Silencing for 10 min after capsaicin "failed to block the CAP-induced spontaneous pain behavior and the induction of pain hypersensitivity".
- It "reversed the maintenance of CAP- or CFA-induced pain hypersensitivity".
- Conclusion: "the ACC is engaged in the maintenance of pain hypersensitivity rather than nociception" (p. 2837).

**Chronic network change (Fig. 2, p. 2837).**
- DEX was chosen for scanning because it suppressed nociception but not hypersensitivity (ketamine did the reverse).
- ACC silencing produced larger negative BOLD responses in the ACC and downstream regions in CFA mice, with stronger connectivity among responsive ROIs.
- Regions named: S1HL (lateral/sensory pathway), ACC and MD thalamus (medial/affective pathway), PAG (descending), M1hl, M2 and VAL (motor).
- The authors interpret negative BOLD amplitude as baseline spontaneous activity, while noting "the controversy regarding the origin of negative BOLD responses" (p. 2837).
- BNST, lateral OFC and anteromedial thalamus were also enhanced (p. 2843).

**Sensorimotor vs. sensory (Fig. 3, p. 2837).**
- Three modules emerged with silencing:
  - *WP-dominant*: S1 barrel field, VP thalamus. Not modulated by ACC silencing.
  - *ACC-dominant*: negative response only.
  - *ACC-modulated*: dl/lPAG, vlPAG, M2, M1, SCm. Noxious responses significantly reduced.
- Conclusion: ACC targets are "closely related to sensorimotor integration and movement generation rather than sensory discrimination in pain processing" (p. 2837).

**Projections (Fig. 4, pp. 2837–2838).**
- Dense ACC projections to PAG and SCm; less to S1, S2 and VP.
- ACC activation BOLD was higher in dl/lPAG than in S1; dl/lPAG was "although not significant" higher than vlPAG and dmPAG (p. 2838).
- "The vlPAG received dense input from the PrL rather than the ACC, whereas the dl/lPAG received dominant inputs from the ACC" (p. 2838).

**ACC→dl/lPAG and pain thresholds (Fig. 5, pp. 2839–2840).**
- Activation "decreased the thermal pain threshold". Inhibition "increased the thermal pain threshold in naive mice and suppressed CFA-induced pain hypersensitivity" (p. 2839).
- Ketamine "partially blocked" activation-induced hypersensitivity, which the authors read as "indicating glutamatergic synaptic neurotransmission" (p. 2840).

**Anxiety and innate fear (Fig. 6A–D, S5; p. 2840).**
- Open field: activation increased speed "without abnormal motor behavior" with centre time unchanged. Inhibition decreased centre time. The authors conclude the circuit "is unlikely to cause pain hypersensitivity by increasing the anxiety levels".
- Fox urine: activation increased speed, and activated mice "preferred to be in zone 1" (near the odour). Inhibition slightly decreased speed.
- The authors' reading: "in an uncertain threat, the increased input from the ACC to PAG induces active movement related to exploratory behavior toward the threat environment" (p. 2840).

**Active avoidance (Fig. 6E–H, S6; pp. 2840–2841).**
- On day 2, shock-zone entries were "close to zero and independent of the optogenetic activation". One mouse with many day-1 shocks received fewer shocks under activation (S6).
- Activation "increased the angle from the shock zone".
- Conclusion: "increased inputs from the ACC to PAG contribute to active avoidance behavior to noxious stimuli" (p. 2841).

#### Inferential Step — from result to claim

**Summary claims (p. 2834).**
- "the ACC … and its downstream circuits are closely related to modulating sensorimotor integration and generating active movement rather than carrying sensory information".
- "The projection from the ACC to the … dl/lPAG especially enhances both reflexive and active avoidance behavior toward pain".
- "increased signals from the ACC to the dl/lPAG might be critical for excessive fear avoidance in chronic pain disability".

**Reconstruction.**
- **P1.** Chronic inflammatory pain increases ACC baseline output and downstream network strength (silencing ofMRI).
- **P2.** ACC silencing reduces noxious-evoked activity in PAG and motor regions, not somatosensory relays (WP ofMRI), and the ACC projects densely to dl/lPAG and SCm (tracing).
- **P3.** Stimulating ACC→dl/lPAG terminals raises reflexive heat sensitivity and increases the distance kept from a learned shock zone; inhibiting them lowers heat sensitivity and CFA hypersensitivity.
- **C1.** The ACC's downstream role is sensorimotor/defensive-action rather than sensory transmission.
- **C2.** ACC→dl/lPAG "enhances" reflexive and active avoidance.
- **C3 (speculative, marked "might").** Increased ACC→dl/lPAG signalling in chronic pain could underlie excessive fear-avoidance.

**Where the authors place affect.**
- "The ACC receives direct nociceptive inputs and encodes the unpleasantness of pain" (p. 2842, citing Bliss et al. 2016).
- "The artificial activation of the ACC also induces fear experience even without aversive stimuli" (p. 2842, citing Johansen & Fields 2004 and Tang et al. 2005). This supports the view that "the functional plasticity of the ACC generates a teaching signal for aversive experiences" (p. 2842).
- On locomotion: "the effect of the ACC-PAG circuit on locomotion seems to be associated with the affective aspect rather than the direct activation of the motor system" (p. 2843).
- Other discussion points:
  - Proposed homology: rodent ACC (area 24) ≈ human dACC/aMCC; rodent PrL (area 32) ≈ human pgACC (p. 2842).
  - Human fMRI links dACC–PAG to imminent-threat active avoidance (Mobbs et al. 2009) and aMCC/PAG to aversive prediction errors (Roy et al. 2014) (pp. 2842–2843).
  - The hypothesis "dACC-dl/lPAG versus pgACC-vlPAG" is offered for future human fMRI (p. 2843).
  - The ACC–superior colliculus and nigro-striatal-thalamocortical networks are candidate motor-output routes; BNST, OFCl and AM are candidate targets (p. 2843).

#### Reviewer notes (for the field history)

- **Necessity for avoidance was not tested.** In the active avoidance task only *activation* was applied (Fig. 6 legend: "The effect of the optogenetic activation of ACC-PAG"). *Inhibition* was tested only on heat thresholds, CFA hypersensitivity, open field and fox urine (Fig. 5D, S5). Whether ACC→PAG input is *required* for pain avoidance is not addressed.
- **Reflex and avoidance moved together.** Unlike Johansen et al. (2001) and Corder et al. (2019), where the manipulation changed avoidance but not reflexive responding, here the same pathway manipulation shifted reflexive heat withdrawal latency *and* active avoidance in the same direction. The paper does not report a reflex/affect dissociation for this pathway.
- **The avoided stimulus was foot shock in a learned spatial task,** framed by the authors as a "learned fear response to noxious stimuli" (p. 2840). No place-conditioning or other affect-specific pain readout was used for the pathway.
- **The key contrast is "sensorimotor integration" vs. "sensory transmission/discrimination"** (pp. 2834, 2837), not "command" vs. "evaluation". The authors elsewhere attribute unpleasantness encoding to the ACC and tie the locomotor effect to "the affective aspect".
- **Unilateral manipulation, and a different "ACC".** Manipulations were unilateral, and the mouse ACC target (AP +1.0) is area 24, not the rat rostral/perigenual ACC (area 32 / perigenual 24b, AP +2.6) of the Johansen papers.
- **Statistics are thin in the text.** Most group results are figure stars; AUC comparisons used one-tailed Mann–Whitney/Wilcoxon tests (p. e4).

### Appendix: Section-by-Section Backbone

**Graphical abstract, highlights, In brief (p. 2834, PDF front page).** ACC is involved in maintaining chronic pain hypersensitivity; ofMRI shows increased ACC network strength in chronic pain; ACC contributes to sensorimotor integration; the ACC-dl/lPAG circuit induces active defensive behaviours against threat signals.

**Summary (p. 2834).** Pain-related fear drives chronic pain disability; ACC downstream circuits for fear avoidance unknown. ofMRI at 15.2 T: ACC is part of abnormal chronic-pain circuitry; downstream circuits relate to sensorimotor integration and active movement rather than sensory information; ACC→dl/lPAG enhances reflexive and active avoidance; increased ACC→dl/lPAG signals might be critical for excessive fear avoidance.

**Introduction (pp. 2834–2835).** Sensory-discriminative vs. affective-motivational dimensions; fear-avoidance model; defence cascade (active vs. passive); PAG columns; limits of human correlational fMRI; ofMRI as a causal systems tool; ACC as pain hub, chronic-pain plasticity, descending facilitation, fear memory, teaching signal; preview of results.

**Results — ACC in pain-induced plasticity (pp. 2835–2837; Fig. 1).** Two silencing methods; capsaicin and double-CFA models; silencing spares nociception and acute capsaicin behaviour but reverses maintained hypersensitivity.

**Results — ACC and downstream circuit in chronic pain (p. 2837; Fig. 2, S1–S2).** Choice of DEX; silencing ofMRI; larger negative BOLD and connectivity in CFA mice across sensory, affective, descending and motor regions.

**Results — ACC in sensorimotor integration (pp. 2837–2839; Figs. 3–4, S3–S4).** WP noxious stimulation with/without silencing; modules; ACC-modulated PAG/motor regions; anterograde tracing; activation ofMRI; ACC→dl/lPAG vs. PrL→vlPAG.

**Results — ACC projection to PAG contributes to pain behaviour (pp. 2839–2840; Fig. 5).** Terminal activation lowers heat threshold (ketamine-sensitive); inhibition raises threshold and suppresses CFA hypersensitivity.

**Results — anxiety (p. 2840; Fig. 6A–B, S5A).** Open field: activation raises speed, centre time unchanged; inhibition lowers centre time; anxiety not the mechanism.

**Results — ACC projection to PAG contributes to fear response (pp. 2840–2841; Fig. 6C–H, S5B, S6).** Fox urine: activation increases speed and approach to odour zone. APAT: activation leaves near-zero shock entries unchanged but increases angular distance from shock zone.

**Discussion (pp. 2842–2843).** Role of ACC in chronification and fear formation (baseline hyperactivity; pro-nociceptive and aversive effects of ACC activation; teaching signal). Frontal projections to PAG (descending facilitation; glutamatergic ACC→PAG; active response under persistent threat; PrL→vlPAG opposing action). Relevance to human fMRI (area homologies; dACC–PAG and active avoidance; prediction errors; attentional analgesia; proposed dACC–dl/lPAG vs. pgACC–vlPAG hypothesis). ACC in motor output (SCm; nigro-striatal-thalamocortical network; no abnormal motor behaviour, so locomotion is tied to affect). Potential targets (NAc, BNST, OFCl, AM). Conclusion: insight into the neural mechanism of fear-avoidance responses to pain; ofMRI as a systems tool.

**STAR Methods (pp. e1–e5).** Animals; stereotaxic surgery and coordinates; optogenetic parameters; Hargreaves test; capsaicin and CFA models; open field; fox urine; APAT; 15.2 T MRI under DEX/isoflurane; EPI parameters; block design; preprocessing; viral tracing; ROI list; statistics (paired/unpaired t, ANOVA with Bonferroni; GLM maps with cluster correction; AUC with IQR exclusion and one-tailed nonparametric tests; 40×40 Pearson connectivity, Newman spectral modules, NBS).

**Field-history record**
- Year · community: 2022 · animal-circuits
- Question it asked: What do the ACC's downstream circuits, and in particular its projection to the periaqueductal gray, contribute to pain processing and to active defensive/avoidance behaviour in acute and chronic pain?
- Position / finding in one line: In mice, the ACC's downstream targets during noxious stimulation are sensorimotor rather than sensory-relay regions, chronic inflammatory pain strengthens the ACC network, and optogenetic activation of ACC→dl/lPAG terminals increases both reflexive heat sensitivity and the distance kept from a learned shock zone (inhibition reduces heat sensitivity and CFA hypersensitivity).
- Responds to / builds on: Melzack & Casey 1968; Vlaeyen, Crombez & Linton 2016; Kozlowska et al. 2015; Johansen & Fields 2004; Tang et al. 2005; Calejesan et al. 2000; Bliss et al. 2016; Kang et al. 2015; Jhang et al. 2018; de Lima et al. 2022; Huang et al. 2019; Drake et al. 2021; Mobbs et al. 2009; Roy et al. 2014; Kragel et al. 2018; Coghill 2020
- Measures (empirical only): intensity rating no (mice; proxy = Hargreaves heat withdrawal latency) · unpleasantness rating no · avoidance/escape behaviour yes (active place avoidance of foot shock; fox-urine zone preference) · desire/urge rating no · neural optogenetic silencing/activation (cell-type and projection-specific), optogenetic fMRI at 15.2 T, anterograde viral tracing
- Dissociation reported (empirical only): ACC silencing → naive heat threshold and acute capsaicin licking unchanged, maintained CAP/CFA hypersensitivity reversed. ACC→dl/lPAG activation → heat threshold lowered and shock-zone distance increased (reflex and avoidance move together), open-field centre time unchanged. ACC→dl/lPAG inhibition → threshold raised, CFA hypersensitivity suppressed, centre time decreased. Noxious-evoked BOLD reduced in PAG/motor regions but not S1BF/VP under ACC silencing
- Survey claim check: partly — 'ACC->PAG projections are required for pain avoidance - a descending command line, not an evaluative one' → the paper links the projection to avoidance ("increased inputs from the ACC to PAG contribute to active avoidance behavior to noxious stimuli", p. 2841), but the load-bearing qualifiers are not supported. (a) *Required* was not tested: only activation was used in the avoidance task, and shock-zone entries were unchanged (p. 2841). (b) *Command, not evaluative* is not the paper's contrast. The paper contrasts "sensorimotor integration and movement generation" with "sensory discrimination" (p. 2837), states that the ACC "encodes the unpleasantness of pain" (p. 2842), and ties the locomotor effect to "the affective aspect" (p. 2843).
- PDF version: published

---

## 5. Batch notes for the synthesis

These notes describe relations among the four papers as their own texts state them. They take no side on theories of pain affect.

1. **A citation chain inside the batch.** Johansen & Fields (2004) explicitly extends Johansen et al. (2001) (acquisition vs. expression; sufficiency). Lee et al. (2022) cites Johansen & Fields (2004) for ACC activity in fear-memory formation and for artificial ACC activation inducing "fear experience even without aversive stimuli", and from that literature concludes that ACC plasticity "generates a teaching signal for aversive experiences" (p. 2842). Corder et al. (2019) does not cite the Johansen papers; its lineage is amygdala valence coding and clinical BLA-lesion reports.
2. **How "unpleasantness" was operationalised in animals changed over time.**
   - 2001/2004: *learned place avoidance* after conditioning. Affect is inferred from what the animal learns.
   - 2019: *attending and escape* during stimulation, plus operant thermal avoidance. Affect is inferred from ongoing protective behaviour.
   - 2022: *active avoidance of a learned shock zone* and *approach to a predator odour*, framed as fear-avoidance and active defence rather than unpleasantness.
   - No paper measures anything the authors call unpleasantness *independently* of avoidance or protective behaviour.
3. **The reflex/affect dissociation is not uniform across circuits.**
   - Rostral ACC lesions (2001), ACC glutamate blockade (2004) and BLA ensemble silencing (2019): affective-motivational measures changed while reflex-like measures did not.
   - ACC→dl/lPAG manipulation (2022): reflexive heat withdrawal *and* avoidance shifted together.
   - ACC silencing (2022): maintained hypersensitivity, a reflex measure, reversed, while naive thresholds were spared.
   - A synthesis that reads "ACC = affect, not sensation" would need to reconcile these.
4. **"Teaching signal" vs. "evaluation" vs. "active defence".** The papers use three families of vocabulary for what these circuits do:
   - *learning-theoretic*: the teaching signal (2004);
   - *valence/evaluation*: "an evaluation of nociceptive information" that "intrinsically motivates protective behaviors" (2019), using both evaluative and motivational terms in one sentence;
   - *action selection / active defence*: "sensorimotor integration and movement generation" (2022).

   These are the authors' framings, not tests between theories of affect.
5. **"ACC" is not one region across the batch.** The rat rostral ACC of 2001/2004 (perigenual 24b, part of 24a, dorsal 32; AP +2.6) is not the mouse ACC target of 2022 (area 24; AP +1.0). Lee et al. map rodent area 24 to human dACC/aMCC and rodent area 32 to human pgACC (p. 2842). In 2001, caudal (postgenual) ACC lesions had no effect on formalin avoidance.
6. **Acute vs. chronic.** Corder et al. and Lee et al. both link their circuits to chronic pain (neuropathic allodynia; inflammatory hypersensitivity and fear-avoidance). The Johansen papers study acute/tonic formalin pain only.

## 6. Survey-claim audit (summary)

| Paper | Survey claim (quoted from assignment) | Verdict | Key discrepancy |
|---|---|---|---|
| Johansen et al. 2001 | 'ACC lesions abolish pain-conditioned place avoidance without changing nociceptive thresholds' | partly | Rostral ACC only; no thresholds were measured (acute formalin behaviours instead, one bin higher in lesioned rats) |
| Johansen & Fields 2004 | 'ACC activation is itself an aversive teaching signal' | yes | Authors call the evidence "not conclusive" (p. 401); rat rostral ACC, chemical activation, place-avoidance paradigm only |
| Corder et al. 2019 | 'A BLA ensemble encodes unpleasantness; silencing it removes affective-motivational behavior but not withdrawal reflexes' | yes | "Removes" overstates the acute result ("significantly reduced", p. 278) |
| Lee et al. 2022 | 'ACC->PAG projections are required for pain avoidance - a descending command line, not an evaluative one' | partly | Necessity never tested (activation only in avoidance task); the "command vs. evaluative" contrast is the survey's, not the paper's; the paper says the ACC encodes unpleasantness |

## Not reviewed (no PDF)

None. All four assigned PDFs were present in `sources/` and reviewed from the PDF.
