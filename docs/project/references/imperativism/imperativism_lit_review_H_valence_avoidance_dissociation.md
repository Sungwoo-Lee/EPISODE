# Imperativism Field History — Part H: Measuring Unpleasantness, Avoidance and Valence Separately

**Topic folder:** `docs/project/references/imperativism/`
**Batch:** H of the imperativism field-history corpus. There are 2 empirical papers with PDFs: one human fMRI study and one human behavioural conditioning study. Both were reviewed one at a time on 2026-09-17. Two further placebo studies are listed but have no PDF.
**Reviewer:** literature-reviewer
**Companion files:** [[imperativism_lit_review_A_imperative_theories]] (Part A: imperative vs. evaluative theories of valence) · [[imperativism_lit_review_C_asymbolia_and_lesions]] (Part C: pain asymbolia).

## What this part is about (plain-language entry point)

**The question.** Philosophers argue about whether pain's *badness* is a feeling of unpleasantness, a command to act, or a perception of value (Parts A and C). Experimenters face a matching practical question: can we *measure* these things separately in people? Unpleasantness, how strongly something is felt, and the urge to avoid it are candidates. If they can be pulled apart in the lab, one can ask which of them a brain region or a learning process actually tracks.

**Why it matters to the field's history.** The classic 1990s work separated two *self-reports* of pain: how intense it is, and how unpleasant it is. The two papers here push in two newer directions.
- **Lee et al. (2024, PNAS)** scanned 58 people's brains while they tasted a painfully hot capsaicin solution or pleasant chocolate, and rated moment by moment how pleasant or unpleasant it felt. A computer model could read out from brain activity both *which direction* the feeling went (pleasant vs. unpleasant, called "valence") and *how strong* it was regardless of direction (called "affective intensity"). The two readouts rely on mostly different voxels and connect to different brain-wide networks. Caution: here "intensity" means strength of feeling, pleasant or unpleasant, not the sensory intensity of pain. No avoidance or action was measured.
- **Flury et al. (2025/2026, European Journal of Pain)** paid healthy volunteers for successfully dodging a painful heat pulse in a reaction-time game. Payment made them dodge faster and more often. Their ratings of how intense and how unpleasant the heat felt did not change. Paying them for detecting small temperature changes had no specific effect, probably because the task was too easy. The authors are careful to say that this pattern does *not* let them conclude that the two pain components were changed differently.

**Where it stands.** Both studies separate measures that the philosophical debates often run together. Neither measures a felt *urge* or desire to escape, and each authors' conclusions are narrower than a secondary survey summarised them (see each entry's "Survey claim check").

## Table of Contents

- [What this part is about (plain-language entry point)](#what-this-part-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Lee et al. (2024) — Brain representations of affective valence and intensity in sustained pleasure and pain [tier: full]](#1-lee-et-al-2024--brain-representations-of-affective-valence-and-intensity-in-sustained-pleasure-and-pain-tier-full)
  - [Phase 1](#phase-1-foundational-overview) · [Phase 2](#phase-2-graduate-level-deep-dive) · [Backbone](#appendix-section-by-section-backbone) · [Field-history record](#field-history-record--lee2024)
- [2. Flury et al. (2025) — Differential operant conditioning of emotional-motivational and sensory-discriminative pain responses [tier: full]](#2-flury-et-al-2025--differential-operant-conditioning-of-emotional-motivational-and-sensory-discriminative-pain-responses-tier-full)
  - [Phase 1](#phase-1-foundational-overview-1) · [Phase 2](#phase-2-graduate-level-deep-dive-1) · [Backbone](#appendix-section-by-section-backbone-1) · [Field-history record](#field-history-record--flury2025)
- [3. What the two studies measure, side by side](#3-what-the-two-studies-measure-side-by-side)
- [Not reviewed (no PDF)](#not-reviewed-no-pdf)

(Sub-entry anchors follow GitHub's duplicate-heading numbering: `-1`, `-2`, … in paper order.)

---

## Reading conventions

- **Page citations.**
  - *Lee et al.* are cited as "p. N", using the PDF's own "N of 10" pagination (PNAS e-article).
  - *Flury et al.* are cited as "p. N", using the "N of 19" pagination (EJP e-article).
  - Neither PDF includes the online supplementary material (Lee: SI Appendix; Flury: Appendix S1). Results that the papers place only in the supplement are marked as not seen.
- **Statistics are copied as printed**, including one internally inconsistent confidence interval in Flury et al. (flagged where it occurs).
- **Vocabulary.**
  - *Valence* (Lee): the signed pleasant-to-unpleasant value of a rating.
  - *Affective intensity* (Lee): the unsigned magnitude of that rating. It is **not** the "pain intensity" of the sensory-vs-affective literature.
  - *Sensory-discriminative / emotional-motivational* (Flury): Melzack & Casey's (1968) components of pain.
  - *Operant conditioning*: changing a behaviour by making a consequence (here money) contingent on it.
  - *Contingent vs. noncontingent*: reward tied to the person's own success vs. reward delivered on another participant's schedule ("yoked").
- **Equations** appear only where the paper has one (Lee's pattern-expression formula). The valence/intensity definitions are displayed as a rendering of the paper's prose and are marked as such.

---

## 1. Lee et al. (2024) — Brain representations of affective valence and intensity in sustained pleasure and pain [tier: full]

**Citation:** Soo Ahn Lee, Jae-Joong Lee, Jisoo Han, Myunghwan Choi, Tor D. Wager, Choong-Wan Woo, "Brain representations of affective valence and intensity in sustained pleasure and pain," *PNAS* 121(25): e2310433121, 2024 (published 10 June 2024). DOI 10.1073/pnas.2310433121.
**PDF:** `docs/project/references/imperativism/sources/Lee et al. 2024 - Brain representations of affective valence and intensity in sustained pleasure and pain.pdf`. This is the published PNAS typeset version (10 pages, CC BY-NC-ND). The SI Appendix is not included.

### Phase 1: Foundational Overview

#### Introduction

Pain and pleasure interact. Pleasant things can dull pain, relief from pain feels pleasant, and people with chronic pain often lose pleasure (anhedonia). This suggests the brain has shared, "modality-general" codes for feeling good or bad. Earlier work mostly studied pain and pleasure in separate experiments, or used non-painful unpleasant stimuli. Lee et al. put sustained pain and sustained pleasure into the same people in one scanner session. They then ask which brain regions carry information about both, and whether those regions separately encode:
- **valence**: which direction the feeling goes;
- **affective intensity**: how strong the feeling is, whatever its direction.

#### Key Findings

1. **Seven regions carry information about both pain and pleasure** (p. 3). These are the amygdala, ventral anterior insula, ventromedial prefrontal cortex (vmPFC), posterior orbitofrontal cortex, and three lateral prefrontal parcels. Several other regions predicted only pain (anterior OFC, anterior midcingulate, frontal pole, pre-SMA) or only pleasure (long insular gyri, dorsal midcingulate, SMA).
2. **Both valence and intensity can be decoded from those seven regions, and the models generalise to a new sample.**
   - Intensity model: within-person prediction–rating correlation r = 0.25 in training and r = 0.16 in the independent test group (n = 62).
   - Valence model: r = 0.11 in training and r = 0.10 in the test group (p. 4).
3. **The informative voxels mostly do not overlap.** The insula is preferentially predictive of intensity and the vmPFC of valence. Within the amygdala, basolateral voxels carry intensity, while centromedial and superficial voxels carry valence (p. 6).
4. **The two readouts are tied to different brain-wide networks.** Measured as functional connectivity in the neutral (water) condition, the intensity model correlates with the ventral attention / salience network (insula, anterior midcingulate). The valence model correlates with the default mode network (vmPFC, posterior cingulate) and the limbic network (OFC, superior temporal gyrus) (p. 7).

#### Initial Takeaway

In the same brain regions, "which way does this feel" and "how much does this feel" are carried by largely different voxel populations, which link to different large-scale systems. The study measures feelings only through a single continuous pleasant–unpleasant rating. It does not measure avoidance, escape, desire for relief, or the sensory intensity of pain as distinct from its unpleasantness. The authors list "salience, cognitive appraisal, and action tendencies" among factors that might contribute to what the models capture (p. 8).

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Design.**

| Element | Detail (as reported) |
|---|---|
| Species / sample | Healthy humans. Study 1 (training) n = 58; Study 2 (independent test) n = 62 (abstract, p. 1). Study 2 procedures are in the SI, not seen. |
| Pain induction | Capsaicin fluid delivered into the mouth via an MR-compatible gustometer, twice for 1.5 min each within a 14.5-min run (p. 2, Fig. 1). |
| Pleasure induction | Chocolate fluid, twice for 3 min each within a 14.5-min run. |
| Control | Water throughout a 14.5-min run. Condition order counterbalanced. |
| Rating | Continuous pleasantness–unpleasantness rating on a modified general Labeled Magnitude Scale (gLMS). Overall pain intensity ratings after the capsaicin runs "reached moderate to strong levels" (SI Fig. S3, not seen; p. 3). |
| Neural measure | fMRI. GLM beta estimates for 34 time bins of 25 s. |
| ROIs | 48 a priori regions: brainstem, subcortical, insular subdivisions, S1/operculum, OFC, 12 medial and 14 lateral PFC parcels (p. 3). |

**Axiomatic logic** (p. 2). The design specifies three criteria in advance:
- Axiom 1: a region encoding pain or pleasure must significantly predict the corresponding ratings.
- Axiom 2: among those regions, an *intensity* region predicts both pain and pleasure ratings "irrespective of the ratings' polarity".
- Axiom 3: a *valence* region predicts both "in relation to the ratings' directional signs".

**Outcome definitions** (reviewer's rendering of the prose on p. 4 and p. 9). Let `r_t` be the signed pleasantness (+) / unpleasantness (−) rating in time bin `t`:

$$
\text{valence}_t = r_t, \qquad \text{intensity}_t = |r_t|
$$

Because capsaicin produced larger magnitudes than chocolate, ratings were **subsampled and converted to ranks** (±1 to ±10) to match the two distributions before modelling (p. 4). A check using the original ratings gave similar performance: intensity r = 0.27, valence r = 0.11 (pp. 4–5).

**Model.** Principal component regression (PCR) was used throughout.
- Region-level mapping used 13 PCs per ROI.
- The seven-region valence and intensity models used 123 PCs, the number explaining 75% of variance (p. 9).
- Performance is the mean within-individual correlation between predicted and actual outcomes under leave-one-subject-out cross-validation (LOSO-CV), with bootstrap tests (10,000 iterations) and Benjamini–Hochberg FDR correction.
- Predictions are "pattern expression" values (p. 9):

$$
\text{Pattern expression} = \vec{w}\cdot\vec{x} = \sum_{i=1}^{n} w_i x_i
$$

where `n` is the number of voxels, `w` the predictive weights and `x` the fMRI data. The step from PCR to voxel weights is a back-projection of the PC regression weights into voxel space (p. 9). No further derivation is given in the main text.

#### Key statistics (as reported)

| Analysis | Result |
|---|---|
| Seven overlapping ROIs predicting pain (p. 3) | mean r = 0.11–0.18, P = 0.00001–0.0045 |
| Seven overlapping ROIs predicting pleasure (p. 3) | mean r = 0.09–0.13, P = 0.0005–0.0105 (FDR q < 0.05) |
| Intensity model, training LOSO-CV (p. 4) | r = 0.25, P = 2.22 × 10⁻¹⁶ (capsaicin r = 0.31; chocolate r = 0.23) |
| Valence model, training LOSO-CV (p. 4) | r = 0.11, P = 0.0017 (capsaicin r = 0.12; chocolate r = 0.08) |
| Intensity model, independent test (Study 2) (p. 4) | r = 0.16, P = 3.82 × 10⁻⁹ |
| Valence model, independent test (Study 2) (p. 4) | r = 0.10, P = 0.0053 |
| Models from the 41 non-overlapping ROIs (p. 5) | intensity r = 0.24 (significant); **valence r = 0.07, P = 0.0869 (n.s.)** |
| Models from voxels outside all 48 ROIs (p. 5) | intensity r = 0.14 (significant); **valence r = 0.06, P = 0.1891 (n.s.)** |
| Capsaicin vs. chocolate classifier from the 7 ROIs (p. 6) | 64% accuracy, P = 0.0479 |

#### From result to claim (inferential steps)

1. **Shared information:** the seven ROIs pass Axiom 1 for both modalities, so they are candidates for modality-general affect.
2. **Two dimensions:** the valence and intensity models trained on those ROIs predict held-out participants and a new sample, so both dimensions are decodable there.
3. **Specificity:** outside the seven regions valence is not decodable while intensity still is. The authors take this to show the seven regions are "crucial" for these codes (p. 6). This asymmetry also means intensity information is more widespread than valence information in these data.
4. **Separable representations:** thresholded weight maps (FDR q < 0.05) are "largely nonoverlapping" (p. 6), so intensity and valence are carried by distinct voxel subpopulations within the same regions.
5. **System-level separation:** in the water condition, seed connectivity from each model's pattern expression maps onto different Yeo networks. The authors' interpretation (p. 8): the ventral attention network detects "important and relevant stimuli", while the limbic and default mode networks carry "modality-general value information" and "subjective affective values". This interpretation draws on prior literature and was not tested directly here.

#### Limitations stated by the authors (pp. 8–9)

- Effect sizes are "small to medium".
- Only activation patterns were modelled, not connectivity patterns.
- Regions predictive of only pain or only pleasure might encode salience, and a salience-matched control is lacking.
- Pain and pleasure were **unbalanced**. The subsampling "tended to exclude the time points with high unpleasantness scores within the pain condition more frequently".
- Meals, satiety and taste preference were not controlled.
- Study 2 ratings were lower than Study 1's.

#### Critical assessment (reviewer)

- **Terminology hazard for the synthesis.** Lee et al.'s "affective intensity" is the unsigned magnitude of a *bipolar affect rating*. It corresponds to arousal/salience-like "valence-general" coding (p. 1 cites affective workspace, unsigned valence, arousal and salience). It is not the sensory "pain intensity" dimension of the classic intensity-vs-unpleasantness dissociation. The study does not separate sensory pain intensity from pain unpleasantness.
- **Oral capsaicin vs. oral chocolate** differ in modality-specific ways beyond valence: chemesthetic burning vs. taste, and different durations (1.5 vs. 3 min). The axiomatic approach and the valence-general target mitigate but do not remove this. The authors also note gustatory contributions to the pleasure-only regions (p. 8).
- **Correlation sizes** are modest (valence r ≈ 0.10 in the test sample). The separation claims rest on thresholded weight maps and connectivity patterns rather than on a formal test of the difference between the two models.

### Appendix: Section-by-Section Backbone

**Significance & Abstract (p. 1).** Pleasure and pain share affective dimensions of valence and intensity. Study with n = 58 plus an independent test set of n = 62. Distinct voxel subpopulations in vmPFC and lateral PFC, OFC, anterior insula and amygdala decode valence vs. intensity. Intensity connects to the ventral attention network; valence to the limbic and default mode networks.

**Introduction (pp. 1–3).**
- Pain and pleasure interact (analgesia by pleasure; relief as pleasant; anhedonia in chronic pain).
- The two are processed by distinct peripheral circuits but should be integrated in core-affect systems. Their overlap regions are rich in opioid receptors.
- Gaps: most prior studies were separate, used non-painful aversive stimuli, or were limited to local animal recordings (amygdala: Corder et al. 2019; ACC).
- Valence vs. valence-general "intensity" (affective workspace, unsigned valence, arousal, salience); both matter for approach/avoidance.
- Three research questions and Axioms 1–3. Overview of the design and results.

**Results — Identifying brain regions containing information of sustained pleasure and pain (pp. 3–4).**
- 48 ROIs; PCR with 13 PCs; LOSO-CV; within-individual r.
- Seven overlapping ROIs, plus pain-only and pleasure-only regions. Brainstem prediction was poor (low temporal SNR).
- Performance was not explained by rating variability, explained variance or voxel count.
- Robustness: searchlight analysis and PC-number variations.

**Results — Parsing affective valence and intensity within the overlapping brain regions (pp. 3–6).**
- Intensity = |rating|, valence = signed rating. Rank subsampling. Models trained across all three conditions.
- Training and test performance. Checks with original ratings and with all 48 ROIs.
- Specificity analyses (41 non-overlapping ROIs; outside-ROI voxels; combined ROIs; binary classifier).
- Largely non-overlapping weight maps: insula for intensity, vmPFC for valence, amygdala subdivisions, medial vs. lateral pOFC, ventral vs. dorsal vmPFC.

**Results — Distinct functional brain networks for affective intensity and valence (pp. 6–7).**
- Pattern-expression seeds in the control condition; positive connectivity only (FDR).
- Intensity → insula and aMCC (ventral attention). Valence → vmPFC and PCC (default mode) plus OFC and STG (limbic).
- Replicated with conventional seed masks and in Study 2's control data (SI).

**Discussion (pp. 7–9).**
- (1) Overlapping pleasure–pain regions match the affective workspace.
- (2) Intensity and valence are encoded there, consistent with valence-specific and valence-general regions (Lindquist et al. 2016). Future pharmacological and contextual tests are proposed. Salience, appraisal and action tendencies may contribute.
- (3) Distinct subregions and networks, offered as a guiding hypothesis for animal circuit work.
- (4) Pain-only regions (aMCC; lateral PFC in the frontoparietal network; overlap with the Neurologic Pain Signature) and pleasure-only regions (gustatory insula).
- Limitations as listed above.

**Materials and Methods (p. 9).** IRB approval at Sungkyunkwan University. Region-level mapping (Harvard-Oxford atlas plus meta-analytic parcellations; PC-number checks at 65–85% variance). Intensity/valence PCR with 123 PCs. Pattern-expression equation. LOSO-CV and bootstrap. Test on Study 2 with no tuning. Whole-brain connectivity on control data with Yeo networks. Data and code on Zenodo (record 11239415); CanlabCore / cocoanCORE.

#### Field-history record — lee2024

**Field-history record**
- Year · community: 2024 · human-neuroscience
- Question it asked: Do brain regions that carry information about both sustained pain and sustained pleasure encode a shared signed valence and a shared unsigned affective intensity, and are these two codes separable?
- Position / finding in one line: Seven prefrontal, insular and amygdala regions predict both pain and pleasure ratings. Within them, largely non-overlapping voxel populations decode valence and affective intensity (both generalising to an independent sample), with intensity linked to the ventral attention network and valence to the limbic and default mode networks.
- Responds to / builds on: Leknes & Tracey 2008; Lindquist et al. 2012, 2016; Barrett & Bliss-Moreau 2009; Russell & Barrett 1999; Wager et al. 2008; Chikazoe et al. 2014; Corder et al. 2019; Berridge 2019; Kahnt et al. 2014; Woo et al. 2017; Roy et al. 2014; Horing et al. 2019; Wager et al. 2013 (NPS); Lee et al. 2021; Yeo et al. 2011
- Measures (empirical only): intensity rating [no — sensory pain intensity is not modelled; overall pain-intensity ratings after capsaicin reported only in SI] · unpleasantness rating [yes — continuous bipolar pleasantness–unpleasantness gLMS] · avoidance/escape behaviour [no] · desire/urge rating [no] · neural [fMRI, multivariate PCR decoding plus functional connectivity]
- Dissociation reported (empirical only): Neural, not behavioural. Valence and affective intensity (signed vs. unsigned value of the same rating) are carried by largely non-overlapping voxels and differently connected networks. Outside the seven shared regions, intensity remains decodable (r = 0.24; r = 0.14) while valence does not (r = 0.07, P = 0.087; r = 0.06, P = 0.19). Manipulation: oral capsaicin vs. chocolate vs. water.
- Survey claim check: yes — "distinct voxel populations and networks, valence to limbic/DMN and intensity to ventral attention. It does not contain an avoidance/action axis." → Accurate. The paper reports "largely nonoverlapping spatial patterns of predictive weights" (p. 6). The intensity model correlated with "the ventral attention network" and the valence model with "the limbic and default mode networks" (p. 8). No avoidance, escape or action measure was collected; "action tendencies" is named only as a possible contributing factor (p. 8). Two nuances: the distinct voxel populations lie *within the same seven regions*, and "intensity" means unsigned affect magnitude, not sensory pain intensity.
- PDF version: published

---

## 2. Flury et al. (2025) — Differential operant conditioning of emotional-motivational and sensory-discriminative pain responses [tier: full]

**Citation:** Melissa L. Flury, Martin Löffler, Shaili Gour, Susanne Becker, "Differential Operant Conditioning of Emotional-Motivational and Sensory-Discriminative Pain Responses," *European Journal of Pain* 30(1): e70162, 2026 (accepted 14 October 2025; © 2025). DOI 10.1002/ejp.70162.
**PDF:** `docs/project/references/imperativism/sources/Flury et al. 2025 - Differential operant conditioning of emotional-motivational and sensory-discriminative pain responses.pdf`. This is the published Wiley typeset version, open access under CC-BY (19 pages). Supplementary Appendix S1, with the simple-model results, is not included.

### Phase 1: Foundational Overview

#### Introduction

Since Melzack & Casey (1968), pain has been described as having a sensory-discriminative side (quality, intensity, location) and an emotional-motivational side (aversiveness, the drive to get away). In the fear-avoidance account of chronic pain, patients show exaggerated emotional-motivational responses and avoidance without a matching change in sensation (Lethem et al. 1983). Flury et al. ask whether ordinary reward learning can boost one side without the other in healthy people. They paid participants for either:
- successfully **avoiding** a heat pulse, as a behavioural stand-in for emotional-motivational pain responses; or
- correctly **detecting** a tiny temperature increase, as a stand-in for sensory-discriminative responses.

They also asked whether any learned change carried over into ratings of pain intensity and unpleasantness.

#### Key Findings

1. **Paying for avoidance improved avoidance.** Compared with the unrewarded baseline, contingent reward made avoidance responses faster (F(1) = 8.89, p = 0.004, partial η² = 0.13) and more often successful (χ²(1) = 32.02, p < 0.001). Yoked, noncontingent reward did not (p. 8).
2. **Paying for discrimination did nothing specific.** Reaction times and accuracy changed from baseline to learning equally under contingent and noncontingent reward (phase × contingency: RT F(1) = 0.13, p = 0.718; correct answers χ²(1) = 0.079, p = 0.778) (p. 10). Accuracy was near ceiling.
3. **Ratings did not move.** In the avoidance task, neither pain-intensity nor unpleasantness ratings changed from baseline to learning, in either reward condition (intensity phase × contingency F(1) = 0.03, p = 0.853; unpleasantness F(1) = 0.15, p = 0.705) (p. 12). The same held in the discrimination task (pp. 12–14). This was **contrary to the authors' hypothesis** that reinforced avoidance would raise unpleasantness (pp. 2, 15).
4. **Pain thresholds and tolerance rose after both tasks** regardless of reward, which the authors read as habituation (p. 14).

#### Initial Takeaway

Reward-based learning can make healthy people better at *avoiding* a painful stimulus without their *reports* of how intense or unpleasant it feels changing. The authors present this as support for the idea that learning can shape motivational pain responses separately from sensation. They are explicit about the limits:
- the discrimination task failed through a ceiling effect;
- the avoidance measure may reflect task compliance rather than pain-avoidance motivation;
- therefore "the present results pattern does not allow us to conclude that emotional-motivational and sensory-discriminative components were modulated differentially by operant conditioning" (p. 16).

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Design.**

| Element | Detail (as reported) |
|---|---|
| Species / sample | Healthy adult humans. **62 recruited** (29 female; mean age 29.98 y). **58 analysed** (27 female) after 1 withdrawal and 3 technical failures (p. 2). |
| Power | A priori G*Power: f = 0.25, α = 0.05, power 0.80, 10% attrition → 62 (p. 2). |
| Registration | Preregistered at ClinicalTrials.gov NCT04280796 (p. 2). |
| Structure | Two sessions about 1 week apart (M = 7.98 d). One task per session, order counterbalanced. Each participant had **contingent** reward in one task and **noncontingent (yoked)** reward in the other, fully balanced across four cells of N = 16/15/16/15 (p. 3). |
| Stimulation | Contact heat (Medoc PATHWAY CHEPS, 30 mm) on the thenar of the non-dominant hand. Baseline 35 °C, max 50 °C, with a skin-burn-risk formula applied (pp. 2–3). |
| Ratings | Intensity VAS 0–200 (100 = pain threshold; 200 = most intense pain tolerable). Un-/pleasantness VAS −100 (extremely unpleasant) to +100 (extremely pleasant) (p. 3). |
| Calibration | Staircase to a moderately painful intensity rating of 130 ± 10 (p. 3). |

**Avoidance task** (a modified monetary incentive delay task; pp. 4–5).
- Each trial starts with a cue announcing difficulty (easy / difficult / control) and heat intensity (high / low). A blue target circle follows 2000–2500 ms later.
- Pressing the space bar while the circle is visible avoids a 3-s heat pulse; pressing late delivers it.
- The target window was 66% of baseline reaction time for easy trials, 33% for difficult, and 4 s for control (a "safe" condition).
- 220 trials. Every 23rd trial delivered both intensities without a response task, for ratings.
- **Technical error:** 44 participants had "low" at the calibrated temperature and "high" at +2 °C; 18 had "high" at the calibrated temperature and "low" at −2 °C (p. 5).
- Outcomes: reaction time and number of successful avoidances.

**Discrimination task** (pp. 4–5).
- Heat rises to the calibrated target. After a cue, it increases by 0.4 °C (easy), 0.2 °C (difficult) or 0 °C (control). The participant answers yes/no to whether it changed.
- The stimulus returns to baseline after the response, so the response also ends the heat.
- 120 trials. Every 13th trial is a 10-s constant stimulus for ratings.

**Operant manipulation** (p. 6).
- In the second half of each task, each success earned CHF 0.20, displayed immediately (contingent).
- In the noncontingent condition, rewards followed the sequence earned by the penultimate participant.

**Analysis** (pp. 7–8).
- Reaction times: linear mixed models (lmerTest). Success: binomial generalised linear mixed models (lme4). Tukey post hocs.
- A simple model (phase × contingency) was fitted first, then additional factors were added by model comparison.
- Outliers were removed by IQR; for example, 1110 of 13,424 avoidance reaction times.
- Questionnaires (PANAS, FPQ-III, FABQ, PCS, NISS, BDI-II, STAI, LOT-R, SHAPS, BIS-15) were correlated with learning effects in exploratory analyses, with Bonferroni correction.

#### Key statistics (as reported)

| Measure | Test | Result |
|---|---|---|
| Avoidance RT, simple model (p. 8) | phase × contingency | F(1) = 8.89, p = 0.004, ηp² = 0.13 (faster with contingent reward) |
| Avoidance success, simple model (p. 8) | phase × contingency | χ²(1) = 32.02, p < 0.001, OR = 1.13 [95% CI: 0.40 to 0.86] *(interval as printed; it does not contain the point estimate)* |
| Avoidance RT, complex model (Table 1, p. 9) | phase × contingency | F = 8.885, p = 0.0041; difficulty F = 97.73; stimulus intensity F = 14.22 (faster for high heat, d = −0.07); no interactions with learning |
| Avoidance success, complex model (Table 2, p. 10) | phase × contingency | χ² = 7.543, p = 0.006; stimulus intensity n.s. (χ² = 2.15, p = 0.142) |
| Discrimination RT (p. 10) | phase × contingency | F(1) = 0.13, p = 0.718 |
| Discrimination correct (p. 10) | phase × contingency | χ²(1) = 0.079, p = 0.778; learning only in 0 °C control trials (p. 11) |
| Intensity ratings, avoidance task (p. 12) | phase; phase × contingency | F(1) = 0.01, p = 0.906; F(1) = 0.03, p = 0.853; stimulus intensity F(1) = 441.65, p < 0.001 |
| Unpleasantness ratings, avoidance task (p. 12) | phase; phase × contingency; contingency | F(1) = 0.596, p = 0.443; F(1) = 0.15, p = 0.705; **contingency main effect F(1) = 5.17, p = 0.027** (group difference present across both phases) |
| Ratings, discrimination task (pp. 12–14) | phase; contingency | all n.s.; unpleasantness phase × contingency F(1) = 4.00, p = 0.050 with no significant Tukey post hocs |
| Threshold / tolerance (p. 14) | time | rose pre→post in both tasks (e.g., avoidance threshold F(1) = 29.11, p < 0.001); no time × contingency |
| Exploratory traits (p. 14) | correlations | BIS-15 impulsivity r = 0.36, p = 0.049 (avoidance RT change); NISS rest avoidance r = −0.36, p = 0.049 (discrimination RT change) |

**Rating levels (Table 5, p. 12).** In the avoidance task, mean intensity ratings for the "low" stimuli were 73.5–84.8, *below* the scale's pain threshold of 100. For "high" stimuli they were 98.3–126.3. Mean un-/pleasantness was on the **pleasant** side for low stimuli (+6.5 to +21.6) and near neutral for high stimuli (−8.1 to +0.8). In the discrimination task, mean intensity was about 108 and mean un-/pleasantness about 0 (Table 8, p. 14).

#### From result to claim (inferential steps and the authors' own hedges)

1. *Contingent reward changed avoidance but not discrimination.* The authors read this as operant conditioning modulating "avoidance-related aspects of pain, while discrimination remained unaffected" (p. 15), in line with earlier findings that pain response channels can be conditioned differentially (Becker et al. 2008, 2011, 2012; Hölzl et al. 2005).
2. *Link to chronic pain.* Learning could raise emotional-motivational responses without sensory change, as in the fear-avoidance model (Lethem et al. 1983; Crombez et al. 2012) and the "negative hedonic shift" (Borsook et al. 2016) (p. 15).
3. *Ratings unchanged.* This contradicts the hypothesis. The authors note that behaviour and self-report often diverge, but also that the design "did not target generalisation" (p. 15).
4. *Hedges that limit steps 1–2* (pp. 15–16):
   - Avoidance behaviour "does not represent emotional aspects directly".
   - The design cannot separate "an intrinsic motivation to avoid pain versus a task compliance motive".
   - The two tasks' reinforcement structures differ: responding in the discrimination task also ended the heat, a form of negative reinforcement in every phase.
   - Discrimination accuracy was at ceiling, possibly because the thermode area was smaller than in Becker et al. 2020.
   - The ±2 °C subgroup error.
   - Conclusion: "The lack of effect in the discrimination task does not allow us to conclude on differential effects of operant conditioning on different pain components" (p. 16).

#### Critical assessment (reviewer)

- **What moved and what did not.** Reward for avoidance changed avoidance *performance* (speed and hit rate in a reaction-time game). It did not change probe-trial ratings of intensity or unpleasantness. Because the reward was monetary and the target was a speeded response, the gain may reflect general incentive-driven speeding. The authors themselves raise task compliance.
- **Stimulus intensity barely drove avoidance.** High heat produced slightly faster reactions (d = −0.07) but no more successful avoidance (p. 9). The authors take this to suggest that "perceived stimulus intensity and unpleasantness did not modulate pain avoidance response" (p. 15). This bears on how tightly "avoidance" here is coupled to pain at all.
- **The rated stimuli were mild.** On average the low stimuli were rated below pain threshold and pleasant; the high stimuli were around threshold and near neutral (Table 5). So "unpleasantness did not change" was measured on stimuli that were, on average, not clearly unpleasant.
- **Sample size to cite is 58 analysed** (62 recruited).
- **Printed statistic inconsistency:** the success-rate OR of 1.13 is reported with a 95% CI of 0.40–0.86 (p. 8).

### Appendix: Section-by-Section Backbone

**Abstract & Significance (p. 1).** Background on the sensory-discriminative vs. emotional-motivational components. 62 healthy participants did an avoidance task and a temperature discrimination task with monetary reinforcement in the second half. Contingent reinforcement selectively enhanced avoidance; discrimination was unchanged, "likely due to a ceiling effect". No generalisation to intensity or unpleasantness ratings. Conclusion: operant conditioning modulates emotional-motivational pain processing. Relevance to chronic pain.

**1 Introduction (p. 2).**
- Tripartite model (Melzack & Casey 1968); the components can dissociate (Auvray et al. 2010; painful massage, chili).
- Operant conditioning dissociates components (Becker et al. 2008, 2011, 2012; Hölzl et al. 2005) and is altered in chronic pain.
- Fear-avoidance model: "exaggerated pain perception" (Lethem et al. 1983). Shift to emotional circuitry (Hashmi et al. 2013). Negative hedonic shift (Borsook et al. 2016).
- Hypotheses: reinforced avoidance → more avoidance and more unpleasantness, with no intensity change; reinforced discrimination → better discrimination and more intensity, with no unpleasantness change.

**2.1 Participants (p. 2).** Sample, power analysis, exclusion criteria, ethics, preregistration, final N = 58.

**2.2 Thermal stimulation (pp. 2–3).** CHEPS thermode, thenar, 35 °C baseline, skin-burn risk formula, 50 °C cap.

**2.3 Rating scales (p. 3).** Intensity VAS 0–200 with 100 = pain threshold; un-/pleasantness VAS −100 to +100.

**2.4 General procedure and design (p. 3).** Two sessions; PANAS and pain assessments before and after; counterbalanced tasks and reinforcement assignment; four balanced cells.

**2.5 Pain assessments (pp. 3–4).** Method-of-limits threshold and tolerance (3 runs each). Ratings of 42–48 °C stimuli. Staircase to VAS 130 ± 10. ±2 °C high/low levels for the avoidance task.

**2.6.1 Discrimination task (pp. 4–5).** +0.4 / +0.2 / +0.0 °C changes; yes/no; 120 trials; rating every 13th trial; outcomes are correct discriminations and reaction time.

**2.6.2 Avoidance task (p. 5).** Modified incentive delay task; cue word pairs; blue-circle target; individual windows (66% / 33% / 4 s); 220 trials; ratings every 23rd trial; the ±2 °C technical error.

**2.6.3 Operant conditioning by monetary rewards (pp. 5–6).** CHF 0.20 per success in the second half; yoked noncontingent control; payouts CHF 15.40–31.20 plus a fixed CHF 20.

**2.7 Questionnaires (pp. 6–7).** PANAS, FPQ-III, FABQ, PCS, NISS, BDI-II, STAI, LOT-R, SHAPS and BIS-15, all exploratory.

**2.8 Data analysis (pp. 7–8).** IQR outlier removal; LMMs for reaction times (skewness checks); GLMMs for success; model selection by ANOVA; LMMs for ratings, threshold and tolerance; Bonferroni-corrected trait correlations; effect-size conventions.

**3.1 Avoidance behaviour (pp. 8–10).** Contingent reinforcement decreased reaction times and increased success. Difficulty and heat intensity had main effects without interacting with learning. Tables 1–2.

**3.1.1 Discrimination behaviour (pp. 10–11).** Reaction times increased and accuracy rose from baseline, with no contingency effect. Learning appeared only in control (0 °C) trials. Tables 3–4.

**3.1.2–3.1.3 VAS ratings (pp. 12–14).** Avoidance task: no phase or phase × contingency effects on intensity or unpleasantness; a stimulus-intensity main effect; a contingency main effect on unpleasantness; the ±2 °C subgroups did not differ in ratings despite a ~2 °C absolute difference. Discrimination task: no effects. Tables 5–8.

**3.2 Threshold and tolerance (p. 14).** Both rose after both tasks, independent of reward (habituation). Discrimination-task tolerance was higher with noncontingent reward (p = 0.049). Table 9.

**3.3 Traits (pp. 14–15).** BIS-15 and NISS correlations (p = 0.049 each); no group differences in these traits.

**4 Discussion (pp. 15–16).**
- Support for operant enhancement of emotional-motivational responses; the discrimination null contrasts with Becker et al. 2020.
- Chronic pain and fear-avoidance interpretation, including an anticipatory-fear mediation idea (Seymour 2019; Seymour & Mancini 2020).
- Heat intensity affected reaction time but not avoidance success.
- Ratings unchanged, against the hypothesis.
- Limits of behavioural surrogates (task compliance), differing reinforcement structures, ceiling effect and thermode size, the ±2 °C error.
- Clinical relevance: exposure-based therapy.
- Conclusion hedged: no firm claim of differential modulation; the stronger effect on motivational components is a hypothesis for future work.

#### Field-history record — flury2025

**Field-history record**
- Year · community: 2025 · clinical-psychology
- Question it asked: Can monetary operant conditioning selectively enhance behavioural surrogates of the emotional-motivational (pain avoidance) versus the sensory-discriminative (heat discrimination) pain component, and do such changes generalise to intensity and unpleasantness ratings?
- Position / finding in one line: Contingent reward enhanced pain-avoidance performance but not heat discrimination (ceiling), and neither intensity nor unpleasantness ratings changed; the authors state this pattern does not license a conclusion of differential modulation of the two components.
- Responds to / builds on: Melzack & Casey 1968; Rainville et al. 1999; Auvray et al. 2010; Becker et al. 2008, 2011, 2012, 2013, 2015, 2017, 2020; Hölzl et al. 2005; Gandhi et al. 2013; Knutson et al. 2001; Lethem et al. 1983; Vlaeyen & Linton 2000; Crombez et al. 2012; Hashmi et al. 2013; Borsook et al. 2016, 2018; Meulders 2019, 2020; Seymour 2019; Seymour & Mancini 2020
- Measures (empirical only): intensity rating [yes] · unpleasantness rating [yes — bipolar un-/pleasantness VAS] · avoidance/escape behaviour [yes — speeded avoidance RT and success] · desire/urge rating [no] · neural [no]
- Dissociation reported (empirical only): Under contingent monetary reward for avoidance, avoidance RT and success improved while intensity and unpleasantness ratings did not change. Under contingent reward for discrimination, nothing changed beyond noncontingent reward (ceiling). Heat thresholds and tolerance rose in all conditions. Heat intensity sped reaction times slightly but did not change avoidance success.
- Survey claim check: partly — "Operant conditioning selectively enhances avoidance without changing intensity or unpleasantness ratings (N=62) - the cleanest recent demonstration that avoidance behavior is a separate variable from both rating dimensions" → The core result is accurate: avoidance improved (RT F(1) = 8.89, p = 0.004; success χ²(1) = 32.02, p < 0.001; p. 8) and "Operantly conditioned changes in pain behaviour did not generalize to self-reported pain intensity and unpleasantness ratings" (p. 1). But N = 62 is the recruited sample; 58 were analysed (p. 2). "Cleanest demonstration" overstates the authors' own reading: "the present results pattern does not allow us to conclude that emotional-motivational and sensory-discriminative components were modulated differentially" (p. 16). They cannot separate pain-avoidance motivation from "a task compliance motive" (p. 16), the ratings were on probe trials with generalisation "not target[ed]" (p. 15), and the rated stimuli averaged near or below pain threshold and near-neutral-to-pleasant (Table 5, p. 12).
- PDF version: published

---

## 3. What the two studies measure, side by side

This is a neutral comparison, to feed the cross-paper synthesis.

| Dimension | Lee et al. 2024 | Flury et al. 2025 |
|---|---|---|
| Community / method | Human neuroscience; fMRI multivariate decoding | Clinical/experimental psychology; behavioural operant conditioning |
| Sample (analysed) | 58 training + 62 independent test | 58 (62 recruited) |
| Aversive stimulus | Oral capsaicin (sustained, minutes) | Contact heat on the hand (3–10 s) |
| Contrast condition | Oral chocolate (pleasure), water | Contingent vs. yoked noncontingent monetary reward |
| Sensory pain intensity rating | Not modelled (SI only) | Yes (VAS 0–200) |
| Unpleasantness rating | Yes (bipolar, continuous) | Yes (bipolar VAS, probe trials) |
| Avoidance / escape behaviour | No | Yes (speeded avoidance) |
| Desire / urge for relief | No | No |
| What separated | Signed valence vs. unsigned affective intensity (voxels, networks) | Avoidance performance vs. intensity and unpleasantness ratings (under reward) |
| Authors' strongest hedge | Small-to-medium effects; unbalanced pain vs. pleasure; salience not controlled | Cannot conclude differential modulation; task-compliance confound; ceiling in discrimination |

**Terminology warning for the synthesis.** "Intensity" means different things in the two papers. In Lee et al. it is the unsigned magnitude of a pleasant/unpleasant rating (affective intensity). In Flury et al. it is the perceived sensory intensity of heat. Neither paper measures a felt urge or desire to escape. The only batch-H item whose title names "desire" is Vase et al. (2003), listed below; it could not be reviewed, so what it measured is not asserted here.

---

## Not reviewed (no PDF)

| Key | Reference | DOI | Reason |
|---|---|---|---|
| vase2003 | Vase et al. 2003 — Suggestion, desire and expectation in placebo effects in IBS patients | 10.1016/s0304-3959(03)00073-3 | PDF not obtainable |
| vase2005 | Vase et al. 2005 — Increased placebo analgesia over time in IBS patients | 10.1016/j.pain.2005.03.014 | PDF not obtainable |

Neither Vase paper is cited in the two reviewed PDFs, and nothing about their content is asserted in this file.
