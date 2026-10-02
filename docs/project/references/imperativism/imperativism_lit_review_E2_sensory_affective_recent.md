# Separating How Strong Pain Is from How Bad It Feels — Recent Human and Animal Evidence (2017–2024) — Reference Review, Batch E2

**Topic folder:** `docs/project/references/imperativism/`
**Corpus:** 4 empirical papers, all `[tier: full]`, reviewed one at a time in the assigned order, 2026-09-17. One further paper is named but not reviewed (no PDF; see [Not reviewed (no PDF)](#not-reviewed-no-pdf)).
**Reviewer:** literature-reviewer
**Companion files:** Part A, the philosophical debate: `imperativism_lit_review_A_imperative_theories.md`. Other batches of this field-history review sit alongside it at the topic root.

## What this batch is about (plain-language entry point)

**The question.** Since the late 1960s, pain researchers have said pain has at least two sides: **how strong it is** (intensity) and **how bad it feels** (unpleasantness). Melzack and Casey (1968) proposed separate brain systems for the two. Imaging studies in the 1990s then tried to show that one side can change while the other stays put, for example by changing unpleasantness under hypnosis. The question matters to the field's history because some theories treat pain's badness as more than a sensation, including the imperative theories in Part A. Evidence that the two sides come apart is often cited in support of such theories.

**What this batch covers.** Four recent studies test the split with newer tools:
- **Opioid drug study (Hayen 2017).** An opioid made **breathlessness**, not pain, less unpleasant without making it significantly less intense.
- **Rat circuit study (Singh 2020).** A direct connection runs from the body-sensation cortex (S1) to the anterior cingulate cortex (ACC), a region linked to pain affect. Switching this connection on made rats avoid a place linked to a pinprick more strongly; switching it off weakened that avoidance.
- **Ultra-high-field brain scan (Stankewitz 2023).** Brain signals followed unpleasantness ratings of the same cold pain slightly more closely than intensity ratings.
- **EEG study (Zidda 2024).** Brief emotional pictures changed how unpleasant a shock felt but not, significantly, how intense it felt.

**Survey check.** The survey behind this corpus got two studies wrong. Hayen 2017 is about breathlessness, not pain, and Singh 2020 used rats, not mice. It also calls the ultra-high-field study an EEG result, but that study recorded no EEG. [§5](#5-cross-paper-notes-for-the-synthesis) lists what the later synthesis needs to know.

## Table of Contents

- [What this batch is about (plain-language entry point)](#what-this-batch-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Hayen et al. (2017) — Opioid suppression of conditioned anticipatory brain responses to breathlessness [tier: full]](#1-hayen-et-al-2017--opioid-suppression-of-conditioned-anticipatory-brain-responses-to-breathlessness-tier-full)
  - [Phase 1](#phase-1-foundational-overview) · [Phase 2](#phase-2-graduate-level-deep-dive) · [Backbone](#appendix-section-by-section-backbone)
- [2. Singh et al. (2020) — Mapping cortical integration of sensory and affective pain pathways [tier: full]](#2-singh-et-al-2020--mapping-cortical-integration-of-sensory-and-affective-pain-pathways-tier-full)
  - [Phase 1](#phase-1-foundational-overview-1) · [Phase 2](#phase-2-graduate-level-deep-dive-1) · [Backbone](#appendix-section-by-section-backbone-1)
- [3. Stankewitz et al. (2023) — Pain and the emotional brain: pain-related cortical processes are better reflected by affective evaluation than by cognitive evaluation [tier: full]](#3-stankewitz-et-al-2023--pain-and-the-emotional-brain-pain-related-cortical-processes-are-better-reflected-by-affective-evaluation-than-by-cognitive-evaluation-tier-full)
  - [Phase 1](#phase-1-foundational-overview-2) · [Phase 2](#phase-2-graduate-level-deep-dive-2) · [Backbone](#appendix-section-by-section-backbone-2)
- [4. Zidda et al. (2024) — Neural dynamics of pain modulation by emotional valence [tier: full]](#4-zidda-et-al-2024--neural-dynamics-of-pain-modulation-by-emotional-valence-tier-full)
  - [Phase 1](#phase-1-foundational-overview-3) · [Phase 2](#phase-2-graduate-level-deep-dive-3) · [Backbone](#appendix-section-by-section-backbone-3)
- [5. Cross-paper notes for the synthesis](#5-cross-paper-notes-for-the-synthesis)
- [Not reviewed (no PDF)](#not-reviewed-no-pdf)

(Sub-entry anchors follow GitHub's duplicate-heading numbering: `-1`, `-2`, … in paper order.)

---

## Reading conventions

- **Page citations** use the journal pagination printed on each PDF:
  - *Hayen 2017*: pp. 383–394. The PDF has two repository cover pages before p. 383.
  - *Singh 2020*: pp. 1703–1715, then STAR Methods pp. e1–e5.
  - *Stankewitz 2023*: article 8273, pp. 1–9.
  - *Zidda 2024*: article bhae358, pp. 1–10 plus references.
- **Statistics** are copied as the papers report them, including apparent typos, which are flagged and not corrected.
- **Reviewer observations** that are not claims made by the authors are marked **(reviewer)**.
- **No invented mathematics.** Display equations are the papers' own: Singh's firing-rate z-score and SVM decision function, Stankewitz's mixed-model formula, and Zidda's difference indices and hierarchical regression. Where the reviewer expands a formula or checks reported numbers against each other, the step is labelled as the reviewer's. Hayen 2017 reports ANOVAs and t-tests only, so it has no equations.
- **Vocabulary.**
  - *Intensity*: how strong a sensation is. *Unpleasantness*: how bad it feels.
  - *CPA / CPP*: conditioned place aversion / preference. An animal's learned avoidance of, or preference for, a chamber paired with a treatment. It is the standard rodent measure of the "affective" side of pain.
  - *BOLD*: the blood-oxygen fMRI signal.
  - *ERP*: event-related potential, an EEG wave time-locked to a stimulus.
  - *S1*: primary somatosensory cortex. *ACC*: anterior cingulate cortex.
- **Project vocabulary.** "Pain" is used for the human and animal phenomenon studied here. The internal damage signal of this project's artificial agents is **nociception**, never "pain". No experiments are proposed.

---

## 1. Hayen et al. (2017) — Opioid suppression of conditioned anticipatory brain responses to breathlessness [tier: full]

**Citation:** Anja Hayen, Vishvarani Wanigasekera, Olivia K. Faull, Stewart F. Campbell, Payashi S. Garry, Simon J. M. Raby, Josephine Robertson, Ruth Webster, Richard G. Wise, Mari Herigstad, Kyle T. S. Pattinson, "Opioid suppression of conditioned anticipatory brain responses to breathlessness," *NeuroImage* 150: 383–394, 2017. DOI 10.1016/j.neuroimage.2017.01.005.
**PDF:** `docs/project/references/imperativism/sources/Hayen et al. 2017 - Opioid suppression of conditioned anticipatory brain responses to breathlessness.pdf`. This is the publisher's open-access (CC-BY) version, deposited in the University of Reading repository (CentAUR) with two cover pages. Supplementary figures and material are not included.

> **Scope warning for the synthesis.** This is a study of **experimentally induced breathlessness** (dyspnoea), produced by making it hard to breathe in. It is **not a pain study**. Pain enters only as precedent and analogy (pp. 384, 391).

### Phase 1: Foundational Overview

#### Introduction

People with chronic heart, lung or neuromuscular disease often suffer from breathlessness, and low-dose opioids are increasingly used to relieve it. How opioids do this is unclear, and they carry a risk of fatal respiratory depression. The authors start from a learning account. After repeated episodes of breathlessness, neutral cues such as a flight of stairs come to predict it. The prediction itself can worsen breathlessness and lead people to avoid activity, which starts a spiral of deconditioning. Opioids are known to affect fear learning, and the amygdala and hippocampus are rich in opioid receptors. The authors therefore asked whether an opioid dampens the brain's learned anticipation of breathlessness. They also asked whether it changes how **unpleasant** breathlessness feels, separately from how **intense** it feels. That second question follows an earlier finding for pain (Price et al. 1985).

#### Key Findings

1. **Unpleasantness fell and intensity did not change significantly.** The drug was remifentanil, a fast-acting opioid given by controlled infusion. On it, strong breathlessness was rated less unpleasant than on saline (about 61 → 49 on a 0–100 scale, p = 0.03). Intensity barely moved (about 71 → 68, p = 0.21).
2. **Anticipation network.** On saline, a cue predicting breathlessness activated the right anterior insula and the neighbouring operculum, plus motor-planning and frontal areas.
3. **Learning regions tracked individual relief.** Remifentanil did not change average anticipatory activity. However, people whose amygdala and hippocampus responses to the cue dropped more also reported larger drops in unpleasantness.
4. **During breathlessness itself**, remifentanil reduced activity in the insula, ACC, sensorimotor cortex, thalamus and pons. Larger reductions in unpleasantness went with *increases* in the rostral ACC and nucleus accumbens. The authors describe these as parts of the brain's own opioid system.

#### Initial Takeaway

The split between intensity and unpleasantness, long reported for opioids and pain, also appears for a different aversive bodily sensation: air hunger from resistive breathing. For a history of the field, this suggests the two-dimensional description is not unique to pain. It is also a caution: this paper is evidence about breathlessness, and counting it as direct pain evidence misreports it.

### Phase 2: Graduate-Level Deep Dive

#### Design, sample and manipulation

- **Design.** Double-blind, randomised, placebo-controlled crossover over three consecutive days at the same time of day. Day 1: conditioning session. Days 2 and 3: fMRI with remifentanil or saline, order counterbalanced (p. 384).
- **Sample.** 29 healthy volunteers enrolled; **N = 19** analysed (10 female, age 24 ± 7). Of the 10 exclusions: 2 fainted during cannulation, 1 did not follow instructions, **4 did not learn the cue–load association**, and 3 were lost to MRI technical problems (p. 384).
- **Stimulus (the unconditioned stimulus).** Inspiratory resistive loading for 30–60 s through a scanner-compatible breathing circuit:
  - strong load ≈ −12 cmH₂O ("breathlessness");
  - mild load ≈ −3 cmH₂O;
  - no load.

  Four strong, four mild and eight unloaded periods were given per session. End-tidal CO₂ was held constant at +0.3 kPa above baseline and end-tidal O₂ at 20 kPa (pp. 384–385).
- **Cues (the conditioned stimuli).** A white square, star or triangle on black. Each shape predicted one load level, counterbalanced across participants and kept fixed over all three sessions. The cue appeared 8 s before the load (the "anticipation period") and stayed on during it. Participants had to confirm the association in writing (pp. 384–385).
- **Drug.** Remifentanil, a μ-opioid agonist with a context-sensitive half-life of 3–4 min. It was given by target-controlled infusion to an effect-site concentration of 0.7 ng/ml for 45 min (10-min ramp). The authors estimate this equals about 4–7 mg oral morphine and call it "at the lower end of efficacy for the treatment of acute pain" (p. 385). Saline placebo was given the same way.

#### Measures

- **Ratings.** After each stimulus, a visual analogue scale (VAS) for breathing **intensity** ("no breathlessness" to "severe breathlessness") and **unpleasantness** ("not unpleasant" to "extremely unpleasant"). The paper does not state the rating order (p. 385).
- **Mood.** Bond–Lader scales for alertness–sedation, relaxation–tension and contentment–discontentment. Anxiety (STAI trait) and depression (CES-D) screening.
- **Physiology.** Mouth-pressure amplitude (breathing effort), end-tidal CO₂ and O₂, pulse oximetry and heart rate, blood pressure.
- **Imaging.**
  - 3 T BOLD fMRI: TR 3 s, 3 mm voxels, 380 volumes.
  - Multi-inversion-time pseudo-continuous arterial spin labelling (ASL) to measure cerebral blood flow (CBF), plus phase-contrast carotid flow. Opioids raise CBF, which could distort BOLD.

#### Analysis

- **Behaviour.** Separate 2 × 2 repeated-measures ANOVAs (drug × loaded/unloaded) for intensity and unpleasantness. Saline-vs-remifentanil differences were tested with **one-tailed** paired t-tests, justified "based on the extensive literature surrounding the analgesic actions of acutely administered opioids" (pp. 385–386). Mood ANOVAs used a Bonferroni threshold of 0.05/4 = 0.0125.
- **fMRI** (FSL FEAT).
  - Noise removal: ICA denoising combined with RETROICOR physiological-noise regressors, applied in a stepwise way so noise is not reintroduced.
  - Haemodynamic response: modelled with the FLOBS basis set.
  - End-tidal CO₂ entered as a regressor.
  - Group level: FLAME 1+2, cluster Z > 2.3, corrected p < 0.05.
  - Drug contrast covariates: sedation score, drug order, the subject's mean unpleasantness difference, and voxel-wise CBF.
  - Region-of-interest test: a bilateral amygdala + hippocampus mask with non-parametric Randomise, asking whether anticipatory activity correlated with the drug-induced change in unpleasantness (pp. 386–387).
- **Mild load dropped.** "Some subjects found it aversive … whereas for others it was imperceptible", so anticipation of the mild load is not reported (p. 387).

#### Key results as reported (pp. 387–388, Table 1, Fig. 2)

| Measure (0–100 %VAS, mean ± SD) | Saline | Remifentanil | p (one-tailed) |
|---|---|---|---|
| Unpleasantness, strong load | 61.2 ± 31.6 | 48.7 ± 26.2 | 0.03 |
| Intensity, strong load | 70.5 ± 19.5 | 67.5 ± 20.2 | 0.21 |
| Unpleasantness, unloaded | 10.4 ± 17.9 | 6.6 ± 11.0 | 0.13 |
| Intensity, unloaded | 11.9 ± 16.1 | 10.8 ± 14.0 | 0.22 |

- **Mood (drug × time interactions).** More sedation (F = 19.799, p < 0.0001), less tension (F = 15.732, p = 0.001), less discontentment (F = 7.748, p = 0.012).
- **Link between intensity and unpleasantness changes.** "The difference in perceived intensities between the saline and remifentanil conditions positively correlated with perceived unpleasantness (r = 0.589, p = 0.008), but did not correlate with changes in sedation (r = −0.086), tension (r = 0.511, p = 0.026) or discontentment (r = 0.319)", all Bonferroni corrected (pp. 387–388).
- **Physiology.**
  - Anticipatory mouth pressure rose above the unloaded-cue level under both saline (3.5 vs 2.7 cmH₂O) and remifentanil (2.8 vs 2.2), i.e. a learned ventilatory response.
  - Remifentanil raised end-tidal CO₂ to about 6.0 kPa (mild respiratory depression).
  - Blood pressure, heart rate and oxygen saturation were unchanged.
  - Grey-matter CBF rose about 10 % (40.7 → 44.8 ml/100 g/min, p = 0.003).
- **Anticipation fMRI.**
  - Saline: activation in the right anterior insula/operculum, supplementary motor cortex, superior frontal gyrus and left cerebellum; deactivation in the right hippocampus, precuneus/PCC and M1/S1.
  - Remifentanil vs saline: **no significant mean change**.
  - ROI analysis: bilateral anterior hippocampus and right amygdala activity correlated with the remifentanil-induced change in unpleasantness (Fig. 4).
- **Breathlessness fMRI.**
  - Saline: a broad network including dlPFC, insula, operculum, ACC, SMA, M1/S1, amygdala, thalamus, caudate, periaqueductal gray, pons and cerebellum.
  - Remifentanil: decreases in insula, operculum, ACC, SMA, M1/S1, supramarginal gyrus, thalamus, pons and cerebellum. No increases.
  - Across subjects, larger unpleasantness decreases went with larger BOLD **increases** in rostral ACC, nucleus accumbens, vmPFC, precuneus, PCC, supramarginal gyrus and cerebellum.

#### Inferential step from result to claim

1. **Behavioural claim.** A significant unpleasantness drop plus a non-significant intensity drop → "Remifentanil significantly reduced the unpleasantness but not the intensity of breathlessness, indicating the ability of low-dose opioids to dissociate breathlessness intensity from unpleasantness" (p. 388).
2. **Mechanistic claim.** The between-subject correlation of amygdala/hippocampus anticipatory activity with unpleasantness relief, together with opioid effects on aversive learning reported elsewhere → "it is conceivable that opioid relief of chronic breathlessness stems (at least in part) from functional interference of neural activity in brain areas that regulate emotional and memory functions" (p. 390).
3. **Link to pain, by analogy only.** Rostral ACC and nucleus accumbens are "structures of the endogenous opioid system that have been shown to modulate the unpleasantness of other aversive stimuli, such as pain" (p. 391).

#### Critical assessment (reviewer)

- **The dissociation is a significant vs. non-significant contrast.** No drug × rating-type interaction test is reported, the tests are one-tailed, and N = 19. The intensity null (3-point drop, p = 0.21) is an absence of evidence, not a demonstrated equivalence.
- **The two dimensions are not independent across people.** Individual intensity changes correlated r = 0.589 with unpleasantness changes (pp. 387–388).
- **The drug shifted mood as well** (sedation, less tension, less discontentment). The authors handle this with covariates in the fMRI analysis (p. 391). The behavioural dissociation itself was not adjusted for mood.
- **The anticipation effect is correlational.** There was no mean remifentanil effect on anticipatory BOLD; the amygdala/hippocampus result is a within-ROI, across-subject correlation.
- **Selection.** Four people who did not learn the association were excluded, so the sample is limited to those who formed the cue–load association.
- **Domain.** Breathlessness, not pain. For a history of the pain literature this is a parallel case. Its closest pain precedent is Price et al. (1985), which is not held in this batch.

### Appendix: Section-by-Section Backbone

**Abstract (p. 383).** Opioids help chronic breathlessness but carry fatal side effects. The learned cue–breathlessness association may worsen symptoms. Hypothesis: opioids interfere with conditioned anticipatory responses in amygdala and hippocampus. Design summary and key results as above.

**Introduction (pp. 383–384).**
- Breathlessness is multidimensional (sensory "work of breathing", affective, psychological) and correlates poorly with disease severity.
- Low-dose opioids are used, but their mechanism is unknown. They act on brainstem respiratory centres and higher centres. Low-dose opioids act differently on unpleasantness than on intensity of aversive stimuli (Price et al. 1985).
- Conditioning account: stairs (conditioned stimulus) predict breathlessness (unconditioned stimulus), and learned anticipation worsens breathlessness and drives avoidance.
- Opioids affect aversive learning (Fanselow 1998; McNally 2004) via amygdala and hippocampus (Phelps 2004). Hypothesis stated.

**Methods — data acquisition (pp. 384–385).**
- *Participants*: 29 enrolled, 19 analysed, exclusions as listed.
- *Initial session*: CES-D, STAI.
- *Breathlessness stimulus*: three-route hydraulic valves; delay conditioning with shapes; 4 strong, 4 mild and 8 unloaded periods; VAS ratings; Bond–Lader; written confirmation of the association; a 20-min test infusion for safety; isocapnia.
- *Physiological recordings*: as above.
- *fMRI sessions*: two, counterbalanced.
- *Drug infusion*: TCI to 0.7 ng/ml, 45 min, double-blind; rationale for remifentanil; estimated morphine equivalence.
- *MRI*: 3 T Trio; EPI; field maps; MPRAGE; multi-TI PCASL; phase-contrast carotid flow.

**Methods — data analysis (pp. 385–387).**
- *Behavioural*: SPSS repeated-measures ANOVAs; one-tailed paired t-tests; Bonferroni-corrected correlations.
- *Physiological*: MATLAB.
- *Pre-processing*: MCFLIRT, BET, 5 mm smoothing, 150 s high-pass, BBR and FNIRT registration.
- *Physiological noise*: a three-step ICA + PNM procedure.
- *First level*: separate regressors for anticipation, loading and unloaded periods; rating periods and 5-s recovery periods as regressors of no interest; end-tidal CO₂ regressor; FLOBS.
- *Saline group analysis*, then *remifentanil − saline* via second-level fixed effects and third-level mixed effects with covariates.
- *ROI Randomise* test.
- *Mild load excluded.*
- *ASL*: carotid flow up 20 % on remifentanil, used as a correction; RETROICOR on multi-TI data; BASIL CBF maps as a voxel-wise covariate.

**Results (pp. 387–388).**
- *Behavioural/physiological*: Table 1; conditioning confirmed by raised anticipatory mouth pressure; ratings and mood as above.
- *Questionnaires*: all within normal range. **(reviewer)** The printed values look transposed: STAI-T "mean: 7 … range (23–57)" and CES-D "mean: 34 … range (0–23)" (p. 388).
- *fMRI anticipation*: saline map; no mean drug effect; ROI correlation.
- *fMRI breathlessness*: saline map; drug decreases; unpleasantness-linked increases.
- *ASL*: grey-matter CBF up about 10 %.

**Discussion (pp. 388–391).**
- *Key findings* restated.
- *Anticipation*: anterior insula as a salience/anticipation hub (Craig 2009; Ploner 2010).
- *Opioid effects on anticipation*: amygdala–hippocampus role in aversive learning; opioid agonists attenuate and antagonists facilitate such learning (Eippert 2008).
- *Activations during breathlessness*: sensory, cognitive and affective domains; pons.
- *rACC/NAcc*: the endogenous opioid system; Zubieta et al. 2001 PET; analogy to pain.
- *Respiration*: mild depression, but the conditioned ventilatory response was preserved. The authors speculate that low-dose opioids "dissociate respiratory and emotional effects".
- *Emotional state*: opioids shift affect positively (Leknes & Tracey 2008); handled by covariates.
- *Clinical relevance*: parallels with COPD word-cue fMRI; targeting associative learning; maladaptive learning in chronic pain (Zaman et al. 2015) mentioned as a parallel.
- *Discussion of methods*: end-tidal gas control (mild hypercapnia/hyperoxia is conservative); ASL linearity assumption; FLOBS may slightly underestimate effects; noise-correction caveats.

**Conclusions (pp. 391–392).** Anticipation engages the anterior insula and operculum. Remifentanil suppresses anticipatory amygdala/hippocampus activity, "which was expressed as reductions in unpleasantness". rACC/NAcc increases accompany relief. Opioids palliate breathlessness "through an interplay of altered associative learning mechanisms, independent of or in addition to effects on brainstem respiratory control" (p. 392).

**Field-history record**
- Year · community: 2017 · human-neuroscience
- Question it asked: Does a low-dose opioid relieve breathlessness partly by suppressing learned anticipatory brain responses, and does it change breathlessness unpleasantness separately from breathlessness intensity?
- Position / finding in one line: Remifentanil lowered the unpleasantness but not, significantly, the intensity of resistive-load breathlessness. Individual relief tracked reduced anticipatory amygdala/hippocampus activity and increased rostral ACC / nucleus accumbens activity.
- Responds to / builds on: Price et al. 1985; Zubieta et al. 2001; Leknes & Tracey 2008; Fanselow 1998; McNally et al. 2004; Phelps 2004; Eippert et al. 2008, 2009; De Peuter et al. 2004, 2005; Herigstad et al. 2011, 2015/2016; Craig 2009
- Measures (empirical only): intensity rating [yes — of breathlessness] · unpleasantness rating [yes — of breathlessness] · avoidance/escape behaviour [no] · desire/urge rating [no] · neural [3 T BOLD fMRI + arterial spin labelling]
- Dissociation reported (empirical only): Remifentanil vs saline during strong loading: breathlessness unpleasantness fell (61.2 → 48.7, p = 0.03, one-tailed) while intensity did not change significantly (70.5 → 67.5, p = 0.21). No interaction test was reported, individual changes in the two ratings correlated (r = 0.589), and the sensation was breathlessness, not pain.
- Survey claim check: partly — 'Opioids: unpleasantness down, intensity flat (Hayen 2017)', cited as pain evidence → the direction is correct, but the sensation was experimentally induced breathlessness (inspiratory resistive loading), not pain: "Remifentanil significantly reduced the unpleasantness but not the intensity of breathlessness" (p. 388). Pain appears only as an analogy, "other aversive stimuli, such as pain" (p. 391).
- PDF version: published (publisher's CC-BY version of record, deposited in a university repository with cover sheet)

---

## 2. Singh et al. (2020) — Mapping cortical integration of sensory and affective pain pathways [tier: full]

**Citation:** Amrita Singh, Divya Patel, Anna Li, Lizbeth Hu, Qiaosheng Zhang, Yaling Liu, Xinling Guo, Eric Robinson, Erik Martinez, Lisa Doan, Bernardo Rudy, Zhe S. Chen, Jing Wang, "Mapping Cortical Integration of Sensory and Affective Pain Pathways," *Current Biology* 30: 1703–1715.e5, 2020. DOI 10.1016/j.cub.2020.02.091.
**PDF:** `docs/project/references/imperativism/sources/Singh et al. 2020 - Mapping cortical integration of sensory and affective pain pathways.pdf`. This is the publisher's typeset version of record, including the graphical-abstract page and STAR Methods. **Supplementary Figures S1–S5 are not included.** Several claims rest on them: the tracing anatomy, that non-noxious touch produced no place aversion, the YFP light controls, and that activation alone was not aversive in naive rats. They are reported below as the main text states them.

> **Species note for the synthesis.** The animals were **male Sprague-Dawley rats** (p. e1), **not mice**.

### Phase 1: Foundational Overview

#### Introduction

A standard picture of pain in the brain has two ascending routes. One ends in S1, which handles *what and where and how strong*. The other ends in the ACC, which handles *how aversive*. This picture goes back to Melzack & Casey (1968) and to imaging work such as Rainville et al. (1997). If the routes were fully separate, it would be unclear how a pain's location and strength come to shape how much an animal wants to avoid it. Singh and colleagues asked whether S1 talks to the ACC directly, and whether that link matters for pain-driven avoidance, both normally and in chronic pain.

#### Key Findings

1. **There is a direct S1 → ACC projection.** It runs from the hindlimb region of S1 to the ACC, confirming older tracing studies.
2. **Few ACC neurons receive it, but they are pain-tuned.** Only 54 of 623 recorded ACC neurons (8.7 %) responded to S1 input. Of these, 37 % responded to a noxious pinprick, versus 14 % of the other neurons.
3. **S1 input selectively amplifies noxious responses in ACC.** Light activation of S1 axon terminals inside the ACC raised ACC firing to a pinprick but not to a gentle von Frey filament touch. It also recruited more pain-responsive neurons (98 → 131) and made the neuron population better at telling pinprick from touch.
4. **The pathway regulates pain avoidance.** Activating the pathway while pinpricks were given made rats avoid that chamber more (conditioned place aversion). Silencing it made them prefer the chamber. Activation without any pinprick was not aversive in normal rats (supplementary data).
5. **Chronic pain strengthens the pathway.** After inflammation (CFA injection) or nerve injury (spared nerve injury, SNI):
   - more ACC neurons received S1 input;
   - activating the pathway *on its own*, with no peripheral stimulus, became aversive;
   - silencing it was preferred, which the authors read as relief of ongoing ("tonic") pain.

#### Initial Takeaway

The study offers a concrete route by which the "sensory" cortex feeds the "affective" cortex. It argues for **integration** of the two streams while keeping the traditional roles of S1 (sensory) and ACC (affective). In the history of the field it belongs to the rodent optogenetic circuit era. Here "pain affect" is operationalised as learned place avoidance, not as a rating of unpleasantness.

### Phase 2: Graduate-Level Deep Dive

#### Subjects, manipulations and stimuli

- **Animals.** Male Sprague-Dawley rats, 7 weeks old on arrival (p. e1).
  - Electrophysiology: n = 5 rats (623 ACC units) in the naive state; n = 3 rats (294 units) after CFA (Fig. 1F, 3D legends).
  - Behavioural groups: n = 6–19 per group, stated per panel.
- **Viral tools.** AAV1-CaMKII injected unilaterally into S1 hindlimb (AP 1.5, ML ±3.0, DV 1.5 mm):
  - channelrhodopsin (ChR2; 473 nm, 20 Hz) to activate;
  - halorhodopsin (NpHR; 589 nm) to inhibit;
  - eYFP-only as control.

  Optic fibres went bilaterally into ACC for behaviour. For recording, an optrode (tetrodes plus fibre) went unilaterally into ACC (p. e2).
- **Peripheral stimuli.** Noxious: pinprick (PP) with a 30-gauge needle to the hind paw, ended by paw withdrawal. Non-noxious: 2 g von Frey filament (vF) for 3 s or until withdrawal. Stimuli were applied contralateral to the recording site, with about 60 s between trials (pp. e2–e3).
- **Chronic pain models.**
  - CFA: 0.1 ml into the paw **opposite** the stimulated paw, "to avoid confounding spinal and peripheral hypersensitivity" (p. 1707); tested on day 7.
  - SNI: common peroneal and tibial nerves ligated and cut; tested on day 14 (p. e2).

#### Measures and their equations

**Classifying a neuron as responsive** (p. e4). Peri-stimulus time histograms used 100 ms bins over ±5 s. For each post-stimulus bin, the firing rate was converted to a z-score against the pre-stimulus baseline bins:

$$
Z = \frac{FR - \mathrm{mean}(FR_b)}{\mathrm{SD}(FR_b)}
$$

A neuron counted as responsive if, within 3 s of the stimulus, (1) one bin had |Z| ≥ 2.5 and (2) at least the next two bins had Z > 1.645. The same rule was applied to optogenetic onset to classify "receives S1 input". The few neurons that decreased firing were counted as non-responders. **(reviewer)** 1.645 is the one-sided 5 % standard-normal quantile.

**Population decoding** (pp. e4–e5). Spikes were binned at 50 ms and accumulated from stimulus onset to 3 s, giving an input dimension from C to 60C for C simultaneously recorded neurons. A nonlinear support vector machine with a polynomial kernel classified pinprick vs von Frey trials:

$$
y = \sum_{i=1}^{N} a_i \, K(x, x_i) + b
$$

Here `x_i` are training samples (those with non-zero `a_i` are the support vectors), `K` is the kernel and `b` the bias. The model was trained by sequential minimal optimisation (MATLAB `fitcsvm`). Accuracy came from 2-fold cross-validation over 50 Monte Carlo repetitions, using only sessions with at least 5 simultaneously recorded units.

**Conditioned place aversion** (pp. e3–e4). Two-chamber apparatus in three phases:
- *Preconditioning*: 10 min of free access. Rats spending > 500 s or < 100 s in either chamber were excluded.
- *Conditioning*: 10 min with a peripheral stimulus every 10 s, or 60 min (30 min per chamber) for tonic-pain tests without peripheral stimulation. Order and chamber pairings were counterbalanced.
- *Test*: 10 min, no treatment.

The paper defines the score as:

$$
\text{CPA score} = T_{\text{pre}}(\text{more noxious chamber}) - T_{\text{test}}(\text{more noxious chamber})
$$

so positive values mean aversion. A place-preference (CPP) score is used analogously for inhibition experiments.

**Mechanical allodynia**: 50 % paw-withdrawal threshold by the up–down method with von Frey filaments. It was used **only to confirm the CFA and SNI models** (Figs. 3B, 5A), not under optogenetic manipulation.

#### Key results as reported

| Result | Statistic (as reported) |
|---|---|
| ACC neurons responding to PP vs vF | ≈16 % vs ≈7 % (p. 1705); SVM peak decoding ≈75 % |
| S1 terminal activation raises ACC firing to PP | n = 623 units / 5 rats, Wilcoxon p < 0.0001 |
| … but not to vF | n = 567, p = 0.3299 |
| Decoding PP vs vF improved with S1 activation | p = 0.0406 |
| Pain-responsive fraction: S1-input vs other neurons | 20/54 vs 78/569, Fisher p < 0.0001 |
| Pain-responsive count with vs without activation | 98 → 131 of 623, Fisher p = 0.0191 |
| Firing of S1-input neurons to PP with activation | +69 %, n = 54, p < 0.0001 |
| CPA to PP (naive) | n = 19, paired t p < 0.0001; none to vF (Fig. S3) |
| Activation + PP chamber vs PP-only chamber | avoided, n = 10, p = 0.0114; score vs YFP p = 0.0415 |
| Inhibition (NpHR) + PP vs PP only | preferred, n = 11, p = 0.0486; score vs YFP p = 0.0495 |
| CFA: ACC firing to PP | increased, Mann–Whitney p < 0.0001 |
| CFA: activation further increases firing | n = 294, p = 0.0083 |
| CFA: fraction receiving S1 input | 15.65 % (46/294) vs 8.67 %, Fisher p = 0.0021 |
| CFA: pain-responsive among S1-input neurons | 52.17 % vs 37 %, p = 0.0487 |
| CFA raises CPA score to PP | n = 9–19, p = 0.0460 |
| Naive + activation vs CFA CPA scores | no difference, p = 0.4746 |
| CFA tonic: avoid activation chamber / prefer inhibition chamber | p = 0.0017 (score p = 0.0021) / p = 0.0128 (score p = 0.0256) |
| SNI: CPA to PP; score vs sham | p < 0.0001; p = 0.0034 |
| Naive + activation vs SNI CPA scores | no difference, p = 0.3012 |
| SNI tonic: avoid activation / prefer inhibition | p < 0.0001 (score p = 0.0009) / p = 0.0111 (score p = 0.0260) |

**(reviewer)** The Fig. 3D legend reads "n = 623 (CFA), n = 294 (+CFA)". The first label is presumably "−CFA".

#### Inferential step from result to claim

The authors list five converging lines (p. 1709): anatomy, pain-tuning of S1-recipient ACC neurons, activation-enhanced firing, improved decoding, and bidirectional control of aversion. From these they conclude that "an S1→ACC projection allows sensory pain information to be transmitted to a higher-order cortical center that regulates the affective experience" (p. 1709). Two further interpretive steps follow:

- Because activation alone was not aversive in naive rats, "it is highly likely that the projection from the S1 assigns sensory-specific value to enrich the aversive response in the ACC" (p. 1710).
- Because the effect of activation on CPA matched that of CFA or SNI, the pathway "could mimic the chronic pain phenotype of enhanced aversion" (p. 1710).

#### Critical assessment (reviewer)

- **The sensory side was never measured under the manipulation.** Withdrawal thresholds were used only to validate the chronic models. The paper therefore does not show that S1 → ACC manipulation leaves sensory discrimination or reflexes unchanged. "Sensory" (S1) and "affective" (ACC) are labels taken from earlier literature, not dissociations tested here.
- **"Affect" is learned place avoidance.** CPA/CPP is the standard rodent affect measure in this lineage (Johansen et al. 2001; King et al. 2009; Navratilova et al. 2012). It indexes avoidance learning, not a report of unpleasantness.
- **Unit statistics use neurons as the sample.** Up to 623 units come from 5 rats, so the neuron-level p-values do not reflect between-animal variability.
- **Several behavioural effects sit close to 0.05** (p = 0.0415, 0.0486, 0.0495), with n = 10–14 per group.
- **Axon-terminal stimulation may also recruit S1 somata or collaterals via back-propagation.** The paper does not discuss this. It is a general caveat of the method, not a finding.
- **Key controls sit in supplementary figures** that are absent from the held PDF.
- The authors themselves note that the S1 → ACC link is "likely one of the many circuit mechanisms", and that an ACC → S1 direction, S1 → spinal cord projections, S2, insula and PFC could all contribute (p. 1710).

### Appendix: Section-by-Section Backbone

**Highlights / In Brief (graphical-abstract page).** ACC receives S1 inputs; activating them increases ACC nociceptive responses; the projection regulates pain-aversive behaviour; chronic pain enhances the connection.

**Summary (p. 1703).** Pain is an integrated sensory and affective experience; cortical integration is poorly defined. Methods: optogenetics, in vivo electrophysiology, machine learning in freely behaving rats. Findings as above.

**Introduction (p. 1703).** Sensory-to-higher-order transmission; acute vs chronic pain as adaptive vs maladaptive. Canonical pathways end in S1 (sensory) and ACC (affective) [refs 4–16, incl. Melzack & Casey 1968; Rainville 1997]. The ACC integrates medial-thalamic input and projects to amygdala and nucleus accumbens. Open question: does ACC receive nociceptive input from sensory cortex? Both areas show plasticity in chronic pain.

**Results — Nociceptive information flow from S1 to ACC (pp. 1703–1705, Fig. 1).** Retrograde beads and anterograde YFP confirm the projection. ACC responds more to PP than vF, and SVM decoding is about 75 %. Optrode terminal activation raises PP-evoked firing but not vF-evoked firing. Fewer than 9 % of neurons receive S1 input, and those that do are over-represented among pain responders. Activation recruits neurons and raises firing by 69 %. "S1 is not a dominant source of nociceptive input to the ACC, it nevertheless makes an important contribution" (p. 1705).

**Results — S1 → ACC projection regulates pain-aversive responses (pp. 1705–1707, Fig. 2).** CPA to PP but not vF. Activation with PP increases aversion; activation alone has no intrinsic aversive value; inhibition with PP produces preference. "This cortico-cortical connection likely confers additional specificity for the affective response to noxious inputs" (p. 1707).

**Results — Enhanced S1 → ACC connection in the chronic pain state (p. 1707, Fig. 3).** CFA (contralateral paw) raises ACC PP responses. Activation raises them further. The S1-input fraction almost doubles, with more than 50 % of those neurons pain-responsive. The authors infer enhancement at both population and single-cell levels.

**Results — Enhanced projection contributes to heightened aversion in chronic pain (pp. 1707–1709, Figs. 4–5).** "Generalized enhancement of pain aversion" (Zhang et al. 2017): CFA rats show higher CPA to PP on the uninjured paw. Naive rats with activation reach similar CPA scores. Tonic-aversion CPA (King et al. 2009 approach): CFA rats avoid the activation chamber and prefer the inhibition chamber. The SNI model replicates all three.

**Discussion (pp. 1709–1710).** ACC ensemble gives a relatively specific pain code, consistent with human fMRI. Five lines of evidence for a direct circuit. Consistent with Eto et al. 2011 and Tan et al. 2019. S1 as a cortical target for pain behaviour beyond the spinal cord (Liu et al. 2018). Activation alone is insufficient for CPA, so S1 "assigns sensory-specific value". Consistent with human work in which "the lateral nociceptive pathway has a modulatory role" (Bushnell 1999; Price 2000). Chronic-pain plasticity at two levels. Limitations: the pathway is one of many (ACC → S1, S1 → spinal, S2, insula, prelimbic PFC). Translation: inhibiting the pathway relieves the aversive component, a proposed target for "non-addictive neuromodulation therapy" (p. 1710).

**STAR Methods (pp. e1–e5).** Key resources; animals; CFA; SNI; AAV constructs; injection and fibre coordinates; optrode construction; recording protocol (about 50 trials, blocks with or without 20 Hz light, counterbalanced); data preprocessing (Open Ephys, 30 kHz, Offline Sorter); histology and exclusion of mis-targeted animals; behaviour timing; CPA protocol; up–down allodynia; statistics (paired t, unpaired two-tailed t, Mann–Whitney, Wilcoxon, Fisher; sample sizes "comparable with previous studies"); responder criterion; SVM; data and code on GitHub.

**Field-history record**
- Year · community: 2020 · animal-circuits
- Question it asked: Does a direct projection from primary somatosensory cortex to anterior cingulate cortex carry nociceptive information into affect-related circuitry and regulate pain aversion, acutely and in chronic pain?
- Position / finding in one line: In rats, S1 → ACC input selectively amplified ACC responses to noxious stimuli. Activating it increased and inhibiting it decreased place aversion to pain, and chronic inflammatory or neuropathic pain strengthened the connection.
- Responds to / builds on: Melzack & Wall 1965; Melzack & Casey 1968; Foltz & White 1968; Turnbull 1972; Rainville et al. 1997; Bushnell et al. 1999; Price 2000; Johansen et al. 2001; Johansen & Fields 2004; LaGraize et al. 2006; King et al. 2009; Qu et al. 2011; Navratilova et al. 2012; Zhang et al. 2017; Zhou et al. 2018; Eto et al. 2011; Tan et al. 2019
- Measures (empirical only): intensity rating [no] · unpleasantness rating [no] · avoidance/escape behaviour [yes — conditioned place aversion/preference; paw-withdrawal thresholds only to validate chronic-pain models] · desire/urge rating [no] · neural [in vivo single-unit electrophysiology with optogenetic axon-terminal activation/inhibition (optrodes), SVM population decoding, tract tracing]
- Dissociation reported (empirical only): S1 → ACC terminal activation increased ACC firing to noxious pinprick but not to non-noxious von Frey touch. Activation increased, and inhibition decreased, pinprick-paired place aversion. Activation alone was not aversive in naive rats (supplementary data) but was aversive in CFA and SNI rats. No sensory or reflex measure was taken under the circuit manipulation, so a sensory-vs-affective behavioural dissociation was not tested.
- Survey claim check: partly — 'In mice, S1->ACC projections carry sensory into affective circuitry' → the content matches the authors' conclusion, "an S1→ACC projection allows sensory pain information to be transmitted to a higher-order cortical center that regulates the affective experience" (p. 1709). The species is wrong: the animals were "Sprague-Dawley male wild-type rats" (p. e1).
- PDF version: published

---

## 3. Stankewitz et al. (2023) — Pain and the emotional brain: pain-related cortical processes are better reflected by affective evaluation than by cognitive evaluation [tier: full]

**Citation:** Anne Stankewitz, Astrid Mayr, Stephanie Irving, Viktor Witkovský, Enrico Schulz, "Pain and the emotional brain: pain-related cortical processes are better reflected by affective evaluation than by cognitive evaluation," *Scientific Reports* 13: 8273, 2023. DOI 10.1038/s41598-023-35294-2.
**PDF:** `docs/project/references/imperativism/sources/Stankewitz et al. 2023 - Pain and the emotional brain - Pain-related cortical processes are better reflected by affective than cognitive evaluation.pdf`. This is the publisher's open-access (CC-BY) version, 9 pages. The supplementary material (a gradient-weighted variant of the model and Supplementary Spreadsheet 1) is not included.

> **Attribution note for the synthesis.** The survey cites this result without naming the paper and calls it a "7T/EEG" result. The study is **7 T fMRI only**; no EEG was recorded.

### Phase 1: Foundational Overview

#### Introduction

When people rate a pain for intensity and for unpleasantness, the two numbers are usually very close, which makes it hard to find brain activity specific to either. Earlier attempts changed one dimension on purpose. The best known is a hypnosis PET study reporting that suggestions changing unpleasantness altered ACC but not S1 activity (Rainville et al. 1997). A follow-up could not cleanly separate the two (Hofbauer et al. 2001). Stankewitz and colleagues took a different route with **no manipulation aimed at either dimension**. Every trial of a long cold pain received both ratings, and the ratings often differed by a few points. They asked which rating the brain signal on that same trial follows more closely.

#### Key Findings

1. **Highly correlated ratings still differed on most trials.** Intensity and unpleasantness correlated r = 0.86 across trials, but 75 % of trials got different numbers on the two scales.
2. **Activity followed unpleasantness more closely.** In regions that switch *on* during pain (insula and frontal operculum, pre- and postcentral gyri, frontal regions), activity rose more steeply with unpleasantness than with intensity. In regions that switch *off* during pain (precuneus, cuneus, occipital and angular regions), activity fell more steeply with unpleasantness.
3. **Connectivity followed unpleasantness more closely.** Prolonged pain reduced connectivity between brain regions compared with rest, and this decoupling was stronger in relation to unpleasantness.
4. **No region went the other way.** The authors report no region more tightly tied to intensity.
5. **The authors call the difference gradual.** They do not claim separate brain processes for the two ratings.

#### Initial Takeaway

The paper contributes a non-interventional way to compare the two dimensions and reports that, for long cold pain, the brain signal sits slightly closer to "how bad" than to "how strong". The authors also interpret unpleasantness as a "more direct and intuitive" evaluation and intensity as a more "minded" one, and predict that unpleasantness is processed faster. That interpretation and prediction go beyond what an fMRI correlation can show. The paper states them as hypotheses.

### Phase 2: Graduate-Level Deep Dive

#### Design, sample and stimulus

- **Data source.** A re-analysis of a dataset first published in Schulz et al. 2019 (*Cortex*) and 2020 (*eLife*), which studied cognitive strategies for reducing pain (p. 2).
- **Sample.** N = 20 healthy adults (16 female / 4 male, 27 ± 5 years), with no history of chronic pain.
- **Blocks.** Four blocks of 12 trials each (48 trials). The unmodulated-pain block always came first. It was followed by counterbalanced blocks of (A) attentional shift, (B) imaginal strategy and (C) non-imaginal reinterpretation. The authors state that the block differences "are not relevant here" because the analysis is within-trial (p. 2).
- **Stimulus.** A thermode (Medoc Pathway II) on the dorsum of the left hand: 10 s rest at 38 °C, then 40 s of **oscillating cold pain**, used "to prevent habituation or sensitisation" (p. 2).
- **Ratings.** After each trial, **intensity first (10 s) and then unpleasantness (10 s)** (Fig. 1). Scale 0–100 in steps of 5, anchored at "no pain" (0) and "the maximum pain the subjects were willing to tolerate" (100).
- **Imaging.** 7 T Siemens with GRAPPA 2. 1768 EPI volumes, 34 slices of 2 mm with a 1 mm gap, 2 × 2 mm in-plane, TR 1.96 s, TE 25 ms. A 1 mm T1 for registration (p. 2).

#### Analysis pipeline

1. **Preprocessing.** FSL: brain extraction, 1/90 Hz high-pass, motion correction, MNI normalisation, 6 mm FWHM smoothing, MELODIC artefact cleaning. Single-trial beta coefficients were estimated in FEAT (p. 3).
2. **Regions of interest.** Data were projected to the cortical surface with the Glasser parcellation (180 regions per hemisphere), plus six subcortical regions from the Oxford atlas (e.g., PAG, thalamus, amygdala): 371 ROIs.
3. **Single-trial connectivity.**
   - Per ROI and subject, the first principal component of the voxel time courses was taken.
   - The plateau phase, the last ~30 s of each trial (15 volumes), was kept.
   - Outliers were removed with Grubbs' test.
   - Kendall's τ was computed between each ROI and the 370 others, per trial, then Fisher z-transformed.
4. **Mixed-effects model** (p. 3, Eq. 1, Wilkinson notation):

$$
\text{rating} \sim \text{fmri} + \text{rating\_type} : \text{fmri} + (1 \mid \text{subject})
$$

Here `rating` stacks each trial's intensity and unpleasantness ratings, `fmri` is that trial's brain value (identical for both rows), `rating_type` is coded −1 / +1, and `(1 | subject)` is a random intercept per subject.

**Expansion (reviewer).** For subject `j`, trial `t` and descriptor `k`, with code `c_k ∈ {−1, +1}`, the formula corresponds to:

$$
r_{jtk} = \beta_0 + \beta_1 f_{jt} + \beta_2 \, c_k \, f_{jt} + u_j + \varepsilon_{jtk}
$$

The slope of the rating on the brain value is therefore `β₁ + β₂` for the descriptor coded +1 and `β₁ − β₂` for the one coded −1. The two slopes differ by `2β₂`, so testing the interaction term `β₂` asks whether intensity and unpleasantness have different slopes against the *same* brain measurement. The formula as printed has no main effect of `rating_type`, so both descriptors share one intercept. The paper does not say which descriptor is coded +1.

5. **Masking and sign interpretation.** A relative slope difference cannot by itself say whether one slope is "more positive" or the other "more negative". The analysis was therefore restricted to voxels significant in a pain-vs-baseline FEAT contrast (cluster-corrected p < 0.05). Direction was read against that map, which "closely resembles" Wager et al.'s (2013) neurologic pain signature: a stronger positive slope in activated voxels, a stronger negative slope in deactivated voxels, and stronger decoupling where connectivity drops (pp. 3–4). An |t| > 2 overlay was used for display.
6. **Multiple comparisons.** Behavioural data were shuffled 5000 times, the maximum |t| was taken per permutation, and p-values came from PALM's `palm_datapval` (p. 3). The supplement contains a gradient-weighted variant that gives more weight to trials with larger rating differences; it is not in the PDF.

#### Key results as reported (pp. 4–5, Table 1, Figs. 2–4)

- **Behaviour.** Intensity 34 ± 14 and unpleasantness 31 ± 17. "we did not find any systematic rating difference between both descriptors (paired t-test, p < 0.05, …)" (p. 4). **(reviewer)** The reported "p < 0.05" contradicts "no systematic difference"; it is probably a typo for p > 0.05, but the PDF does not resolve this. Correlation r = 0.86, p < 0.01. 75 % of trials were rated differently and 25 % identically.
- **Positive BOLD effects** (stronger positive relation to unpleasantness) in bilateral insula/frontal operculum, pre- and postcentral regions and frontal regions, all inside pain-activated territory.
- **Negative BOLD effects** ("a more positive relationship for pain intensity") in cuneal/precuneal, occipital, angular and frontal regions, all inside pain-deactivated territory. These are therefore read as "a stronger negative relationship … for unpleasantness" (p. 4).
- **Connectivity.** Pain periods showed only *lower* connectivity than baseline, so no positive effects were possible. Across connections, "a more positive relationship for pain intensity and connectivity", interpreted as "a stronger disconnection effect for unpleasantness" (p. 4).
- **Table 1 peak t-values** (PALM-corrected p < 0.05): precentral gyrus 6.23; paracingulate gyrus 5.98; frontal operculum/insula 5.16; frontal pole 4.78 and 4.70; postcentral gyrus 4.44; precentral gyrus 4.50; precuneus −4.59 and −3.53; lateral occipital −4.21; cuneus −4.18; occipital pole −3.87; angular gyrus −3.85; superior frontal gyrus −3.55.

#### Inferential step from result to claim

- **Main claim.** Because every significant effect, once read through the activation/deactivation sign rule, favours unpleasantness → "pain unpleasantness is more tightly related to cortical processing than the cognitive evaluation of pain intensity" (p. 7), and "No brain region showed a stronger relationship to pain intensity" (p. 5).
- **The authors' own limit.** "the differences are in a gradual fashion; due to the fact that both aspects of pain evaluation are highly correlated, we can not assume distinct processes for intensity and unpleasantness" (p. 5).
- **Interpretive extension, stated as a hypothesis.** Unpleasantness "may reflect the more direct and intuitive processing of emotions … rather than the more complex and 'minded' evaluation of pain intensity" (p. 7), and "the cortical processes of pain unpleasantness evaluation are processed faster" (p. 7). This is supported by citation (e.g., Kong et al. 2006; Wiech & Tracey 2013), not by the present data.

#### Critical assessment (reviewer)

- **Correlational and within-trial.** Nothing was manipulated to separate the dimensions, so the result speaks to which rating co-varies more with the signal, not to separable mechanisms. The authors say as much.
- **Fixed rating order.** Intensity was always rated first and unpleasantness second (Fig. 1). Any effect of rating order, such as delay, memory or anchoring on the first answer, is confounded with the descriptor. The paper does not discuss this.
- **"No region favoured intensity" depends on the sign rule.** Raw effects in deactivated regions are "more positive for intensity" and are recoded as stronger negative relations for unpleasantness.
- **Pooling across conditions.** Trials from four cognitive-modulation conditions are pooled. The authors acknowledge that condition-specific encoding differences cannot be ruled out (p. 7).
- **Generalisation.** The stimulus was prolonged, oscillating cold pain. The authors note the global decoupling may not generalise to brief heat pain, where connectivity *increases* have been reported (p. 7).
- **Behavioural typo.** The p-value sentence on p. 4 should be checked against the data (available on OSF, `osf.io/tbc2u`) before the mean-rating comparison is quoted.
- **Framing.** The title labels intensity evaluation "cognitive" and unpleasantness "affective". This framing is the authors' and is not established by the analysis.

### Appendix: Section-by-Section Backbone

**Abstract (p. 1).** Pain has sensory-discriminative and affective-motivational aspects. Participants rated cold pain for both. Most trials differed. 7 T fMRI showed a stronger relationship with unpleasantness, which the authors read as reflecting pain's harm-preventing function.

**Introduction (pp. 1–2).** The two descriptors share core variance and are highly correlated, yet diverge by pain type (Price, Harkins & Baker 1987; Rainville et al. 1992). Unpleasantness is linked to well-being and catastrophising. Imaging studies of unpleasantness are "scarce and non-specific". Hypnosis PET: Rainville et al. 1997 reported an ACC-specific effect; Hofbauer et al. 2001 could not separate the dimensions. Questions remain because the ACC location shifted between studies and one study did not report its sample size. Proposal: a within-subject, single-trial dissociation without "potentially unreliable modulatory intervention".

**Materials and methods (pp. 2–4).**
- *Subjects*: N = 20; dataset reused from Schulz 2019/2020; four blocks; cold pain; rating scales; oscillating stimulation.
- *Data acquisition*: 7 T parameters.
- *Preprocessing*: FSL steps; single-trial betas.
- *ROI extraction*: Glasser plus subcortical, 371 ROIs.
- *Single-trial connectivity*: PCA, plateau, Grubbs, Kendall τ, Fisher z.
- *Comparison between intensity and unpleasantness*: differences on 75 % of trials; LME Eq. 1; gradient-weighted variant in the supplement. A separate encoding map per descriptor is "not possible" because both refer to the same trials and would be confounded by the attenuation conditions. Masking by the pain map; 5000-permutation correction.
- *Mapping of pain processing*: pain vs baseline for BOLD and connectivity. 97 % of pain trials and 98 % of baseline periods had positive τ.
- *Ethics*: Oxford MSD-IDREC.

**Results (pp. 4–5).** *Behavioural data*, *positive BOLD*, *negative BOLD*, *positive connectivity* (none, due to decoupling) and *negative connectivity*, as above. Summary: "for all brain regions and cortical connections, cortical processes are always tighter connected to unpleasantness ratings", with the gradual-difference caveat (p. 5).

**Discussion (pp. 5–7).**
- The affective aspect is "more deeply rooted in the human brain".
- Long-lasting pain is represented through disrupted connectivity (Mayr et al. 2022).
- Direct/intuitive vs "minded" evaluation.
- Not comparable with earlier imaging studies because of their methodological weaknesses; consistent with preferential processing of pain emotion (Baliki 2006; Zhou 2020).
- Unpleasantness may precede conscious cognitive evaluation (Kong 2006) and fits the protective function of pain (Wiech & Tracey 2013).
- Autonomic responses track affect (Geuter 2014; Loggia 2011; Nickel et al. 2017, *Pain*).
- Meditation hubs: orbitofrontal cortex for unpleasantness and anterior insula for intensity (Zeidan 2011).

**Limitations (p. 7).** Prolonged cold pain may not generalise. Condition-specific encoding differences cannot be ruled out.

**Conclusions (p. 7).** Unpleasantness is more tightly related to cortical processing across activated and deactivated regions. Intensity ratings remain useful because they are more sensitive to change in some conditions (Price 1987; Rainville 1992; Wade 1996). Hypothesis: unpleasantness evaluation is processed faster than intensity evaluation. Data on OSF.

**Field-history record**
- Year · community: 2023 · human-neuroscience
- Question it asked: When the same painful trial receives both an intensity and an unpleasantness rating, which rating does trial-by-trial cortical activity and connectivity follow more closely?
- Position / finding in one line: Across pain-activated and pain-deactivated regions and across decoupled connections, 7 T fMRI signals related more strongly to unpleasantness than to intensity ratings. The authors describe this as a graded difference between highly correlated ratings, not evidence for distinct processes.
- Responds to / builds on: Melzack & Casey 1968; Price, Harkins & Baker 1987; Rainville et al. 1992, 1997, 1999; Coghill et al. 1999; Hofbauer et al. 2001; Schreckenberger et al. 2005; Kong et al. 2006; Baliki et al. 2006; Zeidan et al. 2011; Wager et al. 2013; Wiech & Tracey 2013; Schulz et al. 2019, 2020
- Measures (empirical only): intensity rating [yes] · unpleasantness rating [yes] · avoidance/escape behaviour [no] · desire/urge rating [no] · neural [7 T BOLD fMRI — single-trial activity and ROI-to-ROI connectivity]
- Dissociation reported (empirical only): none experimentally induced. No manipulation targeted either dimension; ratings of the same trial differed on 75 % of trials (r = 0.86), and brain activity and connectivity tracked unpleasantness more closely than intensity.
- Survey claim check: partly — 'cortical pain responses relate more strongly to unpleasantness than intensity ratings' (cited without author name as a 7T/EEG result) → the direction matches, but the study is 7 T fMRI only, with no EEG. The authors also call the difference gradual: "we can not assume distinct processes for intensity and unpleasantness" (p. 5).
- PDF version: published

---

## 4. Zidda et al. (2024) — Neural dynamics of pain modulation by emotional valence [tier: full]

**Citation:** Francesca Zidda, Yuanyuan Lyu, Frauke Nees, Stefan T. Radev, Carolina Sitges, Pedro Montoya, Herta Flor, Jamila Andoh, "Neural dynamics of pain modulation by emotional valence," *Cerebral Cortex* 34(9): bhae358, 2024. DOI 10.1093/cercor/bhae358.
**PDF:** `docs/project/references/imperativism/sources/Zidda et al. 2024 - Neural dynamics of pain modulation by emotional valence.pdf`. This is the publisher's (Oxford University Press) typeset version of record, downloaded through an institutional library (download stamp on each page). No supplementary material is referenced.

### Phase 1: Foundational Overview

#### Introduction

Emotions change pain: people feel more pain in a bad mood and less in a good one. It is contested whether emotion changes how strong pain feels, how unpleasant it feels, or both. Some studies collected only one pain rating and so could not tell (Godinho et al. 2006). The authors flashed an emotional picture (negative, neutral or positive) for a fifth of a second just before a painful electric shock, then asked for both ratings. They recorded EEG throughout to see which brain waves track the change.

#### Key Findings

1. **Unpleasantness followed picture valence; intensity did not significantly.** Shocks after negative pictures were rated most unpleasant, after positive pictures least, and after neutral pictures in between. Intensity showed no significant main effect of picture type.
2. **Two pain-evoked brain waves changed, in different patterns.**
   - The early negative wave, N2 (~100–150 ms after the shock), was *larger after neutral* pictures than after either emotional kind.
   - The later positive wave, P2 (~200–300 ms), was *larger after negative* pictures.
3. **Only P2 predicted unpleasantness.** People whose P2 changed more between picture types also showed larger changes in unpleasantness. Adding N2 did not improve the prediction.
4. **Sources.** Source clustering pointed to the ACC (for P2) and the thalamus (for N2) as the regions that distinguished picture valence.
5. **Controls.** Accounting for how arousing the pictures were did not change the results. A re-analysis of an older dataset with *non-painful* touch found no valence effect on N2 or P2.

#### Initial Takeaway

This is a recent example of a long line of work in which emotional context shifts pain affect more reliably than pain intensity (e.g., Kenntner-Mabiala et al. 2008; Kamping et al. 2013; Rainville et al. 2005). It adds a candidate EEG marker, the P2, for the unpleasantness shift. The study is small (19 analysed), and the intensity null is not a clean zero.

### Phase 2: Graduate-Level Deep Dive

#### Design, sample, stimuli

- **Sample.** 21 healthy right-handed volunteers (11 female, 23.53 ± 2.55 years). Two were excluded from EEG analysis for having fewer than 75 % artifact-free epochs, leaving **N = 19** (p. 3). The ANOVA degrees of freedom (F(2,36)) and regression degrees of freedom (F(4,14)) are consistent with 19 people in all analyses (see the check below).
- **Primes.** 40 negative, 40 neutral and 40 positive pictures from the International Affective Picture System (IAPS). Normative valence: 2.16 / 5.19 / 7.58. Normative arousal: 5.77 / 4.10 / 4.85; arousal differed across categories, F(2,117) = 58.04, p < 0.001 (pp. 3, 5).
- **Pain.** Constant-current electric stimulation (Digitimer DS7A) through a bar electrode on the left forearm.
  - Threshold and tolerance were measured three times, averaging the last two.
  - Stimulus intensity was set **80 % of the way between pain threshold and tolerance**.
  - It was then checked with 10 stimuli and raised if needed until intensity ratings reached 7–8 of 10 (p. 3).
- **Trial.** Fixation 1,200–2,400 ms → picture **200 ms** → fixation 1,200 ms. The shock came 200 ms into this second fixation, i.e. **400 ms after picture onset** (Fig. 2 caption). Two numerical analogue scales followed: **intensity** ("How strong was the stimulus?", 0 = no pain to 10 = strongest pain imaginable), then **unpleasantness** ("How unpleasant was the stimulus?", 0 = not at all to 10 = most unpleasant) (pp. 3–4).
- **Instruction.** Participants were "explicitly made conscious of the conceptual distinction between the sensory and the affective dimension of pain" using Price et al.'s (1983) radio analogy (p. 3).
- **Trial count.** Picture order was pseudo-randomised, with 3-min breaks every 30 trials. The total per participant is not stated explicitly. **(reviewer)** 120 pictures and breaks every 30 trials suggest 120 trials.

#### EEG acquisition and processing

- **Recording.** 64 active Ag/AgCl electrodes (BrainProducts actiCap, 10–10 system), FCz reference, 1000 Hz, impedances < 20 kΩ, EOG recorded.
- **Processing** (EEGLAB).
  - 0.1–30 Hz filter; resampled to 250 Hz.
  - Epochs from −200 to 900 ms **time-locked to picture onset**; average reference.
  - ICA (matrix computed on longer 1–30 Hz epochs) with SASICA for artifact rejection.
  - Baseline: 200 ms before the picture.
  - Averages per valence condition (pp. 3–4).
- **Sources.** DIPFIT 2.2 equivalent-dipole models with a standard boundary-element model. Components with < 15 % residual variance were kept and grouped by k-means on dipole location, power, ERP, ERSP and inter-trial coherence (p. 4).
- **Component windows** (p. 4).
  - N2: 100–150 ms after pain onset, at Cz, C2, C4 and "CF2".
  - P2: 200–300 ms, at Cz, C1, C2, CPz, CP1 and CP2.
  - **(reviewer)** These are not fully consistent with the Fig. 2 caption (N2 topography window "20–120 ms", sites Cz, C2, C4, FC2, FC4) or the Results text (P2 "between 220 and 350 ms", N2 peaking at FC2).

#### Statistical model and equations

- **Transforms.** Non-normal data were log₁₀-transformed. ERP values were made positive by absolute value, then log₁₀-transformed.
- **Tests.**
  - MANOVA with valence (3 levels) on N2, P2, intensity and unpleasantness, with FDR-corrected post-hoc tests.
  - Two-way repeated-measures ANOVA, valence × rating type.
  - Pearson correlations between N2 and P2 changes.
  - Arousal added as a covariate to all analyses (pp. 4–5).

**Difference indices** (p. 5). Only unpleasantness, the rating that differed across valence, was modelled:

$$
\mathrm{UNP}_{\text{neg}-\text{neu}} = U_{\text{neg}} - U_{\text{neu}}, \qquad \mathrm{UNP}_{\text{neg}-\text{pos}} = U_{\text{neg}} - U_{\text{pos}}
$$

ERP predictors were formed "by subtracting ERP amplitudes between valence of interest", with amplitudes already in the log domain. **(reviewer)** A difference of logs is the log of a ratio, which is why the Discussion calls them "amplitude ratios" (p. 9):

$$
\mathrm{P2}_{\text{neg}-\text{pos}} = \log_{10}\lvert \mathrm{P2}_{\text{neg}} \rvert - \log_{10}\lvert \mathrm{P2}_{\text{pos}} \rvert = \log_{10}\frac{\lvert \mathrm{P2}_{\text{neg}} \rvert}{\lvert \mathrm{P2}_{\text{pos}} \rvert}
$$

**Hierarchical regression** (p. 5, Table 1), run separately for each unpleasantness index:

$$
\text{Model 1:}\quad \mathrm{UNP} = b_0 + b_1\,\mathrm{P2}_{\text{neg}-\text{pos}} + b_2\,\mathrm{P2}_{\text{neg}-\text{neu}} + \varepsilon
$$

$$
\text{Model 2:}\quad \mathrm{UNP} = b_0 + b_1\,\mathrm{P2}_{\text{neg}-\text{pos}} + b_2\,\mathrm{P2}_{\text{neg}-\text{neu}} + b_3\,\mathrm{N2}_{\text{neu}-\text{pos}} + b_4\,\mathrm{N2}_{\text{neu}-\text{neg}} + \varepsilon
$$

The contribution of N2 is judged by the R² change, tested with the standard F-change statistic:

$$
F_{\Delta} = \frac{\Delta R^2 / \Delta k}{\left(1 - R^2_{\text{full}}\right) / \left(n - k_{\text{full}} - 1\right)}
$$

**Consistency check (reviewer).** With `n = 19`, `k_full = 4` and `Δk = 2`, the denominator df is 14, matching the reported F(4,14). For `UNP_neg−pos`:
- F-change: `ΔR² = 0.118` and `R²_full = 0.502` give `(0.118/2) / (0.498/14) = 0.0590 / 0.03557 ≈ 1.66`. Reported: 1.655.
- Full model: `(0.502/4) / (0.498/14) ≈ 3.53`. Reported: 3.525.

For `UNP_neg−neu`: `(0.119/2) / (0.519/14) ≈ 1.61`, matching the reported 1.610. The regressions therefore used all 19 participants.

**Effect-size check (reviewer).** Partial η² for a one-effect F test is:

$$
\eta^2_p = \frac{F \cdot df_1}{F \cdot df_1 + df_2}
$$

- Unpleasantness: `F(2,36) = 12.766` gives `25.53 / 61.53 = 0.415`, as reported.
- Intensity: `F(2,36) = 2.532` gives `5.064 / 41.064 = 0.123`, as reported.

So the non-significant intensity effect is not negligible in size; it is about 30 % of the unpleasantness effect in partial η² terms.

#### Key results as reported (pp. 5–7, Fig. 2, Tables 1–2)

| Result | Statistic (as reported) |
|---|---|
| Multivariate effect of valence (ratings + ERPs) | F(8,11) = 3.440, p = 0.031; Wilks' Λ = 0.286; partial η² = 0.714 |
| Unpleasantness by valence | F(2,36) = 12.766, p < 0.001, partial η² = 0.415 |
| Post-hoc unpleasantness | neg > pos p < 0.001; neg > neu p < 0.002; neu > pos p < 0.021 |
| Linear trend, unpleasantness | F(1,18) = 13.611, p = 0.002 |
| Intensity by valence | F(2,36) = 2.532, "p = n.s.", partial η² = 0.123 |
| Quadratic trend, intensity | F(1,18) = 4.88, p = 0.040 (neg < neu > pos, p. 8) |
| Valence × rating type | F(2,19) = 5.468, p < 0.01, partial η² = 0.365 |
| N2 by valence | F(2,36) = 8.314, p = 0.001, η² = 0.316; neutral more negative than positive (p = 0.002) and negative (p = 0.027); quadratic F(1,18) = 18.193, p < 0.001 |
| P2 by valence | F(2,36) = 5.939, p = 0.006, η² = 0.248; negative > positive (p = 0.005), negative > neutral (p = 0.027); linear F(1,18) = 12.498, p = 0.002 |
| N2–P2 change correlation | r(19) = −0.123, p = 0.617 |
| Regression, `UNP_neg−pos` | Model 1 R² = 0.384, F = 4.987*; +N2 ΔR² = 0.118, F = 1.655 n.s.; full R² = 0.502, adj. 0.359 |
| Regression, `UNP_neg−neu` | Model 1 R² = 0.361, F = 4.529*; +N2 ΔR² = 0.119, F = 1.610 n.s.; full R² = 0.481, adj. 0.333 |
| Arousal as covariate | significance unchanged for all effects |
| IC clusters, 400–800 ms after picture (0–400 ms after shock) | 8 clusters, 99.8 % variance: thalamus 27.7 %, PCC 23.3 %, ACC 22.1 %, angular 11.2 %, right occipital 6.4 %, right parietal 4.2 %, orbitofrontal 2.8 %, medial occipital 2.1 % |
| Tactile re-analysis (Montoya & Sitges 2006; 33 women, non-noxious touch during IAPS) | P2 pleasant vs unpleasant P > 0.46; N2 P > 0.14 |

**(reviewer)** Three reporting details to note:
- The results text says eight clusters were found, but Table 2's cluster names (thalamus, PCC, ACC, …) differ from the list in the text ("visual cortices, the right somatosensory cortex, the posterior parietal cortex, the angular gyrus, the thalamus, the ACC and the PFC").
- The claim that "only cortical sources in the ACC and the thalamus seem to differentiate between picture valence" (p. 5) comes without a reported statistic.
- The interaction's df, F(2,19), differ from the F(2,36) of the other within-subject tests. It is reported here as printed.

#### Inferential step from result to claim

- **Separation claim.** From a significant valence effect on unpleasantness, a non-significant main effect on intensity, and a significant valence × rating-type interaction → "These findings provide evidence for a separation of the sensory and affective dimensions of pain" (p. 1).
- **Marker claim.** From P2 differences predicting unpleasantness differences, with no gain from adding N2 → "the P2 component may be a neural marker for perceived pain unpleasantness" (p. 9).
- **Mechanism, offered as interpretation.**
  - N2 changes are read as automatic attention to arousing pictures (p. 8).
  - P2 changes are read as congruent-valence expectation: "The display of negative pictures may have generated a negative state, priming the participant to react more negatively to painful stimuli" (p. 8).
  - In the Conclusions, "uncertainty and expectation" are named as the candidate mechanisms (p. 10).

#### Critical assessment (reviewer)

- **The intensity null is partial.** The main effect was non-significant, but the quadratic trend was significant (p = 0.040) and partial η² was 0.123. The paper's "not pain intensity" means no significant main effect.
- **Both ERP components moved.** The authors predicted no N2 change across valence (p. 2), yet N2 changed significantly. The "distinct" roles of the components rest on different change patterns and on only P2 predicting unpleasantness.
- **Overlap of picture and pain responses.** Epochs were time-locked to the picture, the baseline preceded the picture, and the shock came 400 ms after picture onset. Pain-evoked N2/P2 therefore overlap late visual responses to the picture, which are themselves sensitive to valence and arousal. The authors' tactile re-analysis is from a different study, sample and timing; they call it "not a direct control" (p. 9).
- **Fixed rating order.** Intensity was always rated before unpleasantness. This is not discussed.
- **Small sample and double subtraction.** N = 19. The regressions use difference scores of difference scores with four predictors, so the adjusted R² values (0.33–0.36) matter more than the raw ones.
- **Inconsistencies** in the reported windows, electrode sites and source-cluster naming (noted above).

### Appendix: Section-by-Section Backbone

**Abstract (p. 1).** The IASP definition implies separable affective and sensory dimensions. EEG study of emotional pain modulation with negative, neutral and positive primes before painful electric stimuli and both ratings. Unpleasantness but not intensity increased after negative primes. N2 was higher after neutral; P2 was higher after negative. P2 alone predicted perception. ACC and thalamus were the main source clusters. The authors take this as evidence for separation.

**Introduction (pp. 1–2).**
- Pain as a threat signal; the IASP 2020 definition; sensory, affective and cognitive dimensions (Melzack & Casey 1968; Fernandez & Turk 1992).
- Emotion modulates pain; valence and arousal (Russell 1980); Lang's (1995) motivational priming hypothesis.
- Dissociations in chronic pain (Kamping 2013) and in cancer vs labour pain (Price 1987). The dissociation is still debated (Chapman 2001; Horn 2012; Talbot 2019 review).
- Design factors: single-rating studies (Godinho 2006); prime modality (pictures are strongest); prime duration (short primes recruit automatic processing, stronger effects < 500 ms).
- ERP background: the N1/N2 debate over sensory vs salience (Iannetti 2005, 2008; Mouraux & Iannetti 2009); P2 sources in ACC or thalamus.
- Hypotheses: unpleasantness shifts with valence while intensity stays constant; N2 unchanged; P2 highest for negative; sources in thalamus, S1, ACC and PFC.

**Materials and methods (pp. 3–5).** *Participants*; *Visual stimuli* (IAPS numbers listed in a footnote); *Painful stimuli* (calibration); *Experimental procedure* (trial timing, radio-analogy instruction, pseudo-randomisation, breaks); *EEG acquisition*; *EEG analysis*; *Source analysis*; *Statistical analysis* (windows, transforms, MANOVA, FDR, two-way ANOVA, correlations, hierarchical regression indices, arousal covariate).

**Results (pp. 5–7).** *MANOVA*; *Perceptual results*; *Scalp ERP results (N2, P2)*; *Hierarchical multiple regression* (intensity not modelled "because the intensity ratings did not differ significantly"); arousal covariate; *Brain sources*: eight clusters, with ACC and thalamus as the valence-differentiating ones.

**Discussion (pp. 7–10).**
- *Summary*: different mechanisms for regulating intensity vs unpleasantness.
- *Pain ratings*: consistent with Rainville et al. 2005; a stronger effect than earlier studies, attributed to short primes preceding the pain rather than long pictures during it. Congruent-valence expectation (Tu 2021; Atlas & Wager 2012). The intensity quadratic trend contrasts with Godinho 2006, attributed to that study's single rating. Untrained participants struggle to separate dimensions (Fernandez & Turk 1994; Chapman 2001). Clinical relevance (Taenzer 1986; Wade 1990).
- *EEG results*: inconsistent N2 directions across studies (Kenntner-Mabiala; Ring 2013; de Tommaso 2009). N2 read as attention to arousing stimuli, possibly prepulse inhibition (Tiemann 2018). P2 read as congruent expectation, argued not to be arousal- or attention-driven. Priming design reduces cognitive competition. The regression marks P2 as a candidate marker. Only N2/P2 studied. Individually calibrated intensity. Tactile re-analysis with Montoya & Sitges data. Sources: ACC for affective processing (Price 2000); thalamus for arousal; thalamus–S1 vs ACC tracts (Treede 1999; Hofbauer 2001); occipital activity reflects picture viewing. Future work on picture features and appraisal.

**Conclusions (p. 10).** Emotions modulate pain-related neural dynamics, associated with ratings. Uncertainty and expectation are the candidate mechanisms. Individual differences in perceptual modulation relate to neural emotional discrimination. Relevance to chronic pain with deficient emotional modulation (Klossika 2006; Kamping 2013).

**Field-history record**
- Year · community: 2024 · human-neuroscience
- Question it asked: Do brief emotional picture primes change pain unpleasantness and pain intensity differently, and which pain-evoked EEG components track that change?
- Position / finding in one line: Negative primes raised and positive primes lowered pain unpleasantness with no significant main effect on intensity. Individual changes in the P2 potential, but not N2, predicted the unpleasantness change.
- Responds to / builds on: Melzack & Casey 1968; Price et al. 1983, 1987; Fernandez & Turk 1992, 1994; Lang 1995; Price 2000; Chapman et al. 2001; Hofbauer et al. 2001; Iannetti et al. 2005, 2008; Rainville et al. 2005; Kenntner-Mabiala & Pauli 2005; Godinho et al. 2006; Montoya & Sitges 2006; Kenntner-Mabiala et al. 2008; de Tommaso et al. 2009; Horn et al. 2012; Kamping et al. 2013; Ring et al. 2013; Talbot et al. 2019
- Measures (empirical only): intensity rating [yes] · unpleasantness rating [yes] · avoidance/escape behaviour [no] · desire/urge rating [no] · neural [64-channel EEG — pain-evoked N2/P2 ERPs, ICA dipole source clustering]
- Dissociation reported (empirical only): Picture valence moved unpleasantness (F(2,36) = 12.77, p < 0.001; negative > neutral > positive) but not intensity as a main effect (F(2,36) = 2.53, n.s.; partial η² = 0.123; quadratic trend p = 0.040). Valence × rating-type interaction p < 0.01. N2 and P2 amplitudes both changed with valence; only P2 changes predicted unpleasantness changes.
- Survey claim check: yes — 'emotional priming moves unpleasantness but not intensity with distinct ERP components' → matches the authors' main result, "pain unpleasantness but not pain intensity ratings were increased when pain was preceded by negative compared to neutral or positive pictures" (p. 1). Two qualifications: intensity showed a significant quadratic trend (F(1,18) = 4.88, p = 0.040; p. 5), and both N2 and P2 changed with valence, with only P2 predicting unpleasantness (pp. 5–6).
- PDF version: published

---

## 5. Cross-paper notes for the synthesis

These notes are for the later cross-paper synthesis. They record what these four entries do and do not support; they take no position on any theory.

1. **Four different kinds of evidence.**
   - *Pharmacological* (Hayen 2017): a drug lowers one rating more than the other, but for **breathlessness**.
   - *Correlational, within-trial* (Stankewitz 2023): no manipulation; which rating the brain signal follows.
   - *Contextual priming* (Zidda 2024): emotional pictures shift one rating.
   - *Animal circuit* (Singh 2020): the labels "sensory" (S1) and "affective" (ACC) are **assumed from earlier literature** and not tested behaviourally. The only behavioural measure is learned place avoidance.
2. **The human dissociations are one-directional and graded.** Every human result here shows unpleasantness moving significantly while intensity moves non-significantly or less. None reports a manipulation that changes intensity while leaving unpleasantness fixed. In every case the intensity "null" is a non-significant difference, not an equivalence result: Hayen p = 0.21; Zidda partial η² = 0.123 with a significant quadratic trend; Stankewitz a graded slope difference.
3. **The two ratings are strongly linked wherever this was measured.** Hayen: individual drug-induced changes correlated r = 0.589. Stankewitz: trial ratings correlated r = 0.86, and the authors decline to infer distinct processes.
4. **Fixed rating order.** In Stankewitz 2023 and Zidda 2024, intensity was always rated before unpleasantness. Hayen 2017 does not state the order. None of the three discusses order effects.
5. **Survey errors to carry forward.**
   - Hayen 2017 is a breathlessness study; using it as pain evidence misattributes the domain.
   - Singh 2020 used rats, not mice.
   - The unnamed "7T/EEG" result is Stankewitz 2023, which is 7 T fMRI only.
6. **Name collision.** Stankewitz 2023 cites "Nickel et al. 2017" (ref. 36), but that is *Autonomic responses to tonic pain are more closely related to stimulus intensity than to pain intensity* (*Pain* 158). It is **not** the named-only NeuroImage oscillations paper listed below. The two should not be merged in the synthesis.
7. **Shared lineage.** All four cite, directly or via Price/Rainville, the Melzack & Casey (1968) two-dimension model. Hayen, Singh and Stankewitz cite Price's or Rainville's intensity/unpleasantness dissociation work as their point of departure.

---

## Not reviewed (no PDF)

- **Nickel et al. 2017** — *Brain oscillations differentially encode noxious stimulus intensity and pain intensity*, *NeuroImage* (DOI 10.1016/j.neuroimage.2017.01.011). Not reviewed: PDF not obtainable. Nothing about its content is asserted in this batch.
