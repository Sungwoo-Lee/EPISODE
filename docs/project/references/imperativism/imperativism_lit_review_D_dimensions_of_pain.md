# Imperativism Field History — Part D: How Pain Was Split into Dimensions

**Topic folder:** `docs/project/references/imperativism/`
**Part of:** a multi-file review of how ideas about pain's non-sensory side developed, from the 1960s to 2025. Part A is [[imperativism_lit_review_A_imperative_theories]] (the philosophical debate over whether pain is a command or a perception of value).
**This part:** 4 papers, reviewed one at a time in chronological order, 2026-09-17. 5 more are named but not reviewed because no PDF was available.
**Reviewer:** literature-reviewer

## What this part is about (plain-language entry point)

**The question.** Is pain one experience, or several bundled together? Today most pain researchers ask volunteers for two separate ratings: how *intense* the pain is, and how *unpleasant* it is. That habit rests on a history. This part follows it.

**The story the four papers tell.**
- **1965: the opening.** Melzack and Wall attacked the idea of a single wired "pain line" running from skin to a "pain centre" in the brain. They proposed a spinal *gate* that the brain can open or close. The paper's own phrases point ahead: pain has "sensory and affective components", and the input reaches brain systems "involved in affective as well as sensory activities". It does **not** yet propose separate dimensions. That came three years later (Melzack & Casey 1968, not held here).
- **2000: the consolidation.** Price's review in *Science* gave a layered model. Felt intensity comes first. It *causes* unpleasantness. Unpleasantness then feeds a slower "secondary" suffering about what the pain means for the future. He tied the layers to brain pathways, with the anterior cingulate cortex (ACC, a frontal midline region) as the hub for unpleasantness.
- **2008: the reward link.** Leknes and Tracey placed pain beside pleasure. The brain's opioid and dopamine chemistry serves both. They also noted that feeling bad (the *hedonic* side) and being driven to avoid (the *motivational* side) are hard to tell apart in the brain.
- **2019: the critique.** Talbot, Madden, Jones and Moseley ran a systematic review. They asked whether the two ratings can really be moved separately by psychological manipulations such as hypnosis, meditation or pleasant pictures. Their answer: the evidence is weak. Intensity could not be moved on its own. Unpleasantness *might* be, but only slightly, and only in studies at high risk of bias.

**Why it matters for the field's history.** Whether "unpleasantness" is the same thing as "the urge to avoid" is the fault line that later theories argue over, imperativism included. These papers show when the two were joined, when the join was questioned, and how loosely the words were used along the way.

**A caution for the synthesis.** Checked against the PDFs, the unverified survey that seeded this corpus puts two claims on the wrong papers. Details are in the reading conventions below and in each entry's final block.

## Table of Contents

- [What this part is about (plain-language entry point)](#what-this-part-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Melzack & Wall (1965) — Pain Mechanisms: A New Theory [tier: short]](#1-melzack--wall-1965--pain-mechanisms-a-new-theory-tier-short)
- [2. Price (2000) — Psychological and Neural Mechanisms of the Affective Dimension of Pain [tier: full]](#2-price-2000--psychological-and-neural-mechanisms-of-the-affective-dimension-of-pain-tier-full)
  - [Phase 1](#phase-1-foundational-overview) · [Phase 2](#phase-2-graduate-level-deep-dive) · [Backbone](#appendix-section-by-section-backbone)
- [3. Leknes & Tracey (2008) — A Common Neurobiology for Pain and Pleasure [tier: short]](#3-leknes--tracey-2008--a-common-neurobiology-for-pain-and-pleasure-tier-short)
- [4. Talbot, Madden, Jones & Moseley (2019) — The Sensory and Affective Components of Pain: Differentially Modifiable or Inseparable? [tier: full]](#4-talbot-madden-jones--moseley-2019--the-sensory-and-affective-components-of-pain-differentially-modifiable-or-inseparable-tier-full)
  - [Phase 1](#phase-1-foundational-overview-1) · [Phase 2](#phase-2-graduate-level-deep-dive-1) · [Backbone](#appendix-section-by-section-backbone-1)
- [Cross-paper notes for the synthesis](#cross-paper-notes-for-the-synthesis)
- [Not reviewed (no PDF)](#not-reviewed-no-pdf)

(Sub-entry anchors follow GitHub's duplicate-heading numbering: `-1` for the second full-tier entry.)

---

## Reading conventions

- **Page citations** use the journal page numbers printed on each PDF. All four PDFs are publisher versions downloaded through institutional access:
  - *Melzack & Wall 1965*: Science 150, pp. 971–978.
  - *Price 2000*: Science 288, pp. 1769–1772.
  - *Leknes & Tracey 2008*: Nat. Rev. Neurosci. 9, pp. 314–320.
  - *Talbot et al. 2019*: Br. J. Anaesth. 123, pp. e263–e272.
- **Tiers.**
  - `[tier: short]` entries were read in full from the PDF but are summarised in a fixed five-part structure: Claim · Method/type · Key result or argument · Place in the field's history · Relevance.
  - `[tier: full]` entries carry Phase 1, Phase 2 and a section-by-section backbone appendix.
- **No invented mathematics.** None of these papers derives equations.
  - Price reports one correlation (R = 0.55). Talbot et al. describe their effect-size estimate in prose. The one display block in §4 is the reviewer's rendering of that prose and is marked as such.
  - For these review papers, Phase 2 "rigor" means reconstructing the argument and tabulating the cited evidence as the paper reports it. The underlying primary studies were not re-checked.
- **Vocabulary.**
  - *Sensory-discriminative dimension*: where the pain is, what quality it has, how intense it is. In practice this is usually an "intensity" rating.
  - *Affective dimension*: how unpleasant or bad it feels. In practice this is usually an "unpleasantness" rating.
  - *Motivational*: the drive to act (escape, avoid, protect).
  - *Affective-motivational*: a compound label that fuses the two previous terms. Which paper uses which label is tracked explicitly below, because the survey's claims turn on it.
  - *Secondary pain affect* (Price): emotions about the longer-term implications of having pain, such as suffering, depression and anxiety.
- **Project vocabulary.** For this project's artificial agents the internal damage signal is **nociception**. "Pain" here refers only to the human and animal phenomenon these papers study.

---

## 1. Melzack & Wall (1965) — Pain Mechanisms: A New Theory [tier: short]

**PDF:** `docs/project/references/imperativism/sources/Melzack and Wall 1965 - Pain mechanisms - A new theory.pdf` — a scan of the published *Science* article (pp. 971–978). PDF page 9 also carries the opening of an unrelated article (Hodgkin's Nobel lecture), and PDF page 10 is the publisher cover sheet.

**Claim.** Pain is not produced by a fixed, direct line from "pain receptors" to a "pain centre".
- A *gate control system* in the spinal cord's substantia gelatinosa modulates incoming nerve signals before they reach the first central transmission (T) cells.
- Large-diameter fibres tend to close the gate; small-diameter fibres tend to open it.
- A fast *central control trigger* lets brain processes such as attention, emotion and past experience act on the gate through descending fibres.
- When T-cell output crosses a critical level, it triggers an *action system* responsible for "response and perception" (p. 974).

**Method / type.** A theoretical synthesis with no new experiment. It rejects the two reigning theories. Specificity theory is faulted for its "psychological assumption" that a receptor that responds to intense stimuli must be a "pain receptor" (p. 971). Pattern theory is faulted for ignoring the receptor specialisation that physiology had already shown (p. 973). The evidence comes from three places:
- **Clinical:** causalgia, phantom limb and the neuralgias, where surgical lesions fail to abolish pain and gentle touch triggers severe pain (p. 971).
- **Psychological:** Beecher's wounded soldiers who "entirely denied pain", and Pavlov's dogs conditioned to treat shocks as food signals (p. 972).
- **Physiological:** only a few fibres respond exclusively to high-intensity stimuli (p. 972).

**Key result or argument.**
- The gate explains three things: hyperalgesia after loss of large fibres, spontaneous pain, and delays of up to 35 s (p. 977).
- It explains why vibration reduces low-intensity pain but enhances high-intensity pain (p. 977).
- It explains why psychological factors act "by acting on the gate control system" (p. 978).

For the history of pain's non-sensory side, four passages matter:
- On lobotomy: lobotomized patients "report that they still have pain but it does not bother them" (p. 972). An early, clinically framed separation of pain from its bothersomeness.
- On the imperative reflex: "Pain is generally considered to be the sensory adjunct of an imperative protective reflex" (p. 976, citing Sherrington). The authors immediately answer that pain "does not consist of a single ring of the appropriate central bell, but is an ongoing process."
- On the action system: its sequence runs from startle and flexion reflex to "patterns of behavior aimed at diminishing the sensory and affective components of the whole experience, such as rubbing the damaged area, avoidance behavior" (p. 976). The input also reaches "neural systems involved in affective as well as sensory activities" (p. 976).
- On the word itself: "pain" is "a linguistic label for a rich variety of experiences and responses" (p. 978).

**Place in the field's history.** This paper replaced the single-channel picture of pain with a *modulated, multi-system* one. That shift made room for pain to have separable components.
- The paper uses the words "sensory" and "affective", but it does **not** set out a dimensional model. The explicit three-way split (sensory-discriminative, motivational-affective, cognitive-evaluative) is Melzack & Casey (1968), which is not held here.
- Its use of Sherrington's "imperative protective reflex" wording is an early appearance of the command vocabulary that later imperativist philosophy took up (see [Part A](imperativism_lit_review_A_imperative_theories.md)). Melzack and Wall cite the phrase only to reject a reflex-only view.

**Relevance.**
- **Anchor point.** It is the standard starting point for "modern pain theory" and the source of the claim that psychological factors change pain itself, not just the report of it.
- **Avoidance placement.** Avoidance behaviour is placed in the *action system*, downstream of the gate, as one response among many. It is not treated as a dimension of the experience.

**Field-history record**
- Year · community: 1965 · human-neuroscience
- Question it asked: Can a single theory reconcile receptor specialisation with the evidence that pain is not a fixed function of stimulus intensity?
- Position / finding in one line: A spinal gate, modulated by large versus small fibre input and by descending brain control, sets what reaches an action system that produces pain experience and response; there is no pain centre.
- Responds to / builds on: von Frey 1894 and Sweet 1959 (specificity theory); Goldscheider 1894, Nafe 1934, Weddell 1955 and Sinclair 1955 (pattern theory); Livingston 1943, Noordenbos 1959 and Hebb 1949 (central summation and input control); Beecher; Pavlov; Sherrington ("imperative protective reflex"); Freeman & Watts 1950 (lobotomy)
- Measures (empirical only): n.a. (theoretical paper; no new data) · intensity rating [no] · unpleasantness rating [no] · avoidance/escape behaviour [no] · desire/urge rating [no] · neural [no]
- Dissociation reported (empirical only): n.a. (no new data). Cited observation: lobotomized patients report pain that "does not bother them" (p. 972).
- Survey claim check: n.a. — no survey claim assigned (history anchor) → n.a.
- PDF version: published

---

## 2. Price (2000) — Psychological and Neural Mechanisms of the Affective Dimension of Pain [tier: full]

**PDF:** `docs/project/references/imperativism/sources/Price 2000 - Psychological and neural mechanisms of the affective dimension of pain.pdf` — the published *Science* review ("Science's Compass" section, pp. 1769–1772) plus the publisher cover sheet.

### Phase 1: Foundational Overview

**Introduction.** Price asks what the *bad-feeling* side of pain is made of, and how the brain produces it. He splits pain affect into two layers:
- **Pain unpleasantness:** the moment-by-moment bad feeling, including emotions about the present or near future such as distress or fear.
- **Secondary pain affect:** emotions about the longer-term implications of having pain, such as suffering, depression and anxiety (p. 1769).

He also notes that pain "is often accompanied by desires to terminate, reduce, or escape its presence" (p. 1769).

**Key findings (as reviewed).**
1. **Two dimensions, not one.** Intensity and unpleasantness ratings follow different curves as heat increases. Their ratio shifts with context: unpleasantness runs lower than intensity for short lab stimuli with reassurance of safety, and matches or exceeds intensity for long ones.
2. **They are in series.** Hypnotic suggestions aimed at unpleasantness changed only unpleasantness. Suggestions aimed at intensity changed both. Price reads this as intensity *causing* unpleasantness, not the reverse.
3. **A third layer.** The personality trait neuroticism barely touched unpleasantness and left intensity unchanged, but strongly shaped secondary affect. A statistical model on 1008 chronic pain patients fit the chain intensity → unpleasantness → secondary affect.
4. **Brain pathways.** Two routes converge on limbic structures, especially the ACC:
   - a direct route from the spinal cord to limbic and medial thalamic areas;
   - a slower route through somatosensory cortex, parietal cortex and insula.

   When hypnosis changed unpleasantness, ACC activity changed but primary somatosensory cortex (S1) did not.
5. **Clinical contrasts.** Insula damage produces *pain asymbolia*: patients detect pain's sensory features but do not withdraw from it. Prefrontal lobotomy patients lose spontaneous worry about their pain but still feel the immediate threat when their attention is drawn to it.

**Initial takeaway.** Price turned the dimensional view into a *layered, causal* model with a brain map attached: first sensation, then immediate unpleasantness, then reflective suffering. In his account, the urge to escape sits beside this chain as an accompaniment and as the ACC's "response priorities". It is not a separately measured dimension.

### Phase 2: Graduate-Level Deep Dive

#### Technical analysis — the argument reconstructed

Price's case is an inference from several evidence lines to one model. Reconstructed:

- **P1 (distinctness).** If two ratings respond differently to stimulus parameters and to psychological factors, they index distinct dimensions. Evidence: ratio effects; selective hypnotic effects (p. 1769).
- **P2 (direction).** If a manipulation aimed at dimension A changes A and B, while a manipulation aimed at B changes only B, then A is upstream of B. Evidence: Rainville et al. 1999 (p. 1769).
- **P3 (third layer).** If a trait changes B only slightly but changes C strongly, and a causal-chain model A → B → C fits large-sample data, then C is a further downstream layer. Evidence: Harkins et al. 1989; Wade et al. 1992, 1996 (p. 1770).
- **P4 (neural mapping).** If activity in a region co-varies with B when A is held constant, the region is "more proximate" to B. Evidence: Rainville 1997 and Tölle 1999 on ACC area 24 (p. 1771).
- **P5 (convergence).** Anatomy shows parallel direct spinal-limbic paths and a serial cortico-limbic path that converge on ACC, insula and amygdala (pp. 1770–1771).
- **C (model).** Pain affect arises from a *parallel-serial* network. Serial cortico-limbic processing carries cognitive evaluation of sensation into unpleasantness. Parallel direct inputs add arousal and autonomic activation. ACC–prefrontal interaction sustains secondary affect (pp. 1771–1772).

**The inferential step to watch.** P2 treats hypnotic suggestion as a clean lever on one rating. The same asymmetry (unpleasantness-targeted suggestion works selectively, intensity-targeted suggestion does not) is read very differently by Talbot et al. 2019 ([§4](#4-talbot-madden-jones--moseley-2019--the-sensory-and-affective-components-of-pain-differentially-modifiable-or-inseparable-tier-full)). Price reads it as evidence of *seriality*. Talbot et al. read it as evidence that *sensory ratings cannot be selectively modulated*, and they add risk-of-bias and demand-effect caveats. Same data, two historical readings.

#### Evidence table (as Price reports it; primary papers not re-checked)

| Evidence line | Design / sample as reported | Manipulation | Measures | Result as reported | Page |
|---|---|---|---|---|---|
| Price, Harkins & Baker 1987 | Human psychophysics | 45–51 °C, 5-s heat | Intensity (sensory) and unpleasantness ratings | Both power functions; unpleasantness/sensory ratio < 1.0 | 1769 |
| Rainville et al. 1992 | Human psychophysics, four pain modalities | Brief (5-s heat, shock) vs long (ischemia, cold pressor) | Both ratings | Ratio < 1.0 for brief stimuli, ≥ 1.0 for long ones | 1769 |
| Rainville et al. 1999 | Two hypnosis experiments; left hand in 47 °C water | Suggestion to raise/lower unpleasantness (Exp. 1) or intensity (Exp. 2) | Both ratings | Exp. 1: only unpleasantness changed. Exp. 2: both changed in parallel | 1769 |
| Harkins et al. 1989 | 105 myofascial pain dysfunction patients; Eysenck inventory | Trait (neuroticism, extraversion) | Sensory, unpleasantness, secondary affect (depression, anxiety) | Neuroticism: no sensory effect; small significant rise in unpleasantness; large effect on secondary affect. Extraversion: none | 1770 |
| Wade et al. 1992 | 205 chronic pain patients | Same traits | Same | Same pattern | 1770 |
| Wade et al. 1996 | 1008 chronic pain patients | — | Ratings of the three dimensions | Structural-equation (LISREL) sequential model fits well on "several indices" | 1770 |
| Coghill et al. 1999 | Human imaging | Graded heat 46/48/50 °C vs 35 °C | Neural activation | Activation magnitude and spread rise with pain in S1, S2, insula, SMA, ACC | 1770 |
| Rainville et al. 1997 | Human PET, hypnosis | High vs low unpleasantness suggestion | Ratings + PET | Unpleasantness higher, sensation unchanged; posterior ACC area 24 higher, S1 unchanged; unpleasantness–ACC regression controlling for sensation R = 0.55, P < 0.001 | 1771 |
| Bushnell et al. 1999 | Human imaging, hypnosis | Intensity suggestion | Ratings + imaging | Changes in S1 | 1771 |
| Tölle et al. 1999 | Human PET, four successive heat trials | Trial order (ratio shifted) | Ratings + PET | "only pain unpleasantness was encoded in ACC area 24" | 1771 |
| Dong et al. 1994 | Monkey area 7b single units | Noxious heat ± aligned visual stimuli | Firing | Visual enhancement, larger for mild (44–45 °C) than strong (47 °C) noxious heat | 1771 |
| Dong et al. 1996 | Monkey S2/7b lesion | Lesion | Escape; detection of stimulus offset | Escape responses absent; offset detection preserved | 1771 |
| Weinstein et al. 1955; Berthier et al. 1988 | Human insula damage | Lesion | Clinical observation | Pain asymbolia: sensory features detected, no withdrawal from noxious or threatening stimuli | 1771 |
| Hardy, Wolff & Goodell 1952 | Prefrontal lobotomy patients | Lesion | Clinical observation | Lost spontaneous concern about pain; immediate threat felt when attention drawn | 1771 |

#### The model in structural form

Price gives no equations. His Fig. 1 schematic can be written as a directed graph, with the direction of each arrow as he states it (pp. 1769–1772):

$$
\text{nociceptive input} \;\rightarrow\; \text{pain sensation intensity} \;\rightarrow\; \text{pain unpleasantness} \;\rightarrow\; \text{secondary pain affect}
$$

Parallel inputs (arousal, autonomic and somatomotor responses) feed directly into unpleasantness. The proposed neural loci are:
- **S1/S2:** sensation.
- **Posterior parietal cortex → insula → ACC:** integration of sensation with context, and unpleasantness.
- **ACC–prefrontal:** secondary affect.

*This display is the reviewer's rendering of the paper's Fig. 1 prose, not an equation from the paper.*

#### Where motivation sits in Price 2000 (terminology audit)

This matters for the survey claim, so it was checked word by word in the extracted text:
- The word **"motivational" does not occur** in the article, and neither does "affective-motivational".
- **"Motivation" occurs once**, describing ACC function: "establishing emotional valence and response priorities. Response priorities would be closely related to premotor functions that are integrally related to motivation and emotions and may be associated with immediate efforts to cope with, escape, or avoid the pain" (p. 1771).
- The **desire** to escape is described as an *accompaniment*: pain "is often accompanied by desires to terminate, reduce, or escape its presence" (p. 1769).
- Price's affective dimension is explicitly **unpleasantness plus secondary affect** (p. 1769).
- No study in the review measures desire, urge or avoidance as its own rating. Avoidance/escape appears only as a *clinical or animal outcome* in the lesion evidence (monkey S2/7b; human asymbolia).

So Price does not treat "affective" and "motivational" as synonyms. What he does is leave motivation without its own dimension or measure. It is folded into the ACC's "response priorities" and into the escape desires that accompany pain.

### Appendix: Section-by-Section Backbone

1. **Abstract (p. 1769).** The affective dimension is unpleasantness plus secondary affect. Serial interactions link sensation intensity, unpleasantness and secondary affect. A central network processes nociceptive information in parallel and in series. Direct spinal-limbic and medial-thalamic inputs converge with a cortico-limbic pathway on ACC and subcortical structures "whose function may be to establish emotional valence and response priorities."
2. **Introduction (untitled, p. 1769).**
   - Unpleasant feelings are integral to pain because of its sensory qualities and threatening contexts.
   - Pain has sensory and affective dimensions and is often accompanied by desires to escape (cites Melzack & Casey 1968; Price 1999).
   - Unpleasantness is "often, although not always, closely linked to the intensity."
   - Secondary affect = long-term implications ("suffering").
3. **Psychological Mechanisms of Pain Affect (pp. 1769–1770).**
   - Sensory attributes (intensity, slow adaptation, summation, spread, quality words) dispose pain to feel "invasive and intrusive."
   - Nociceptive, exteroceptive and interoceptive processes contribute in parallel, in line with Damasio.
   - Psychophysical ratio evidence; hypnosis direction-of-causation experiments.
   - Secondary affect involves reflection on interference with life and the future.
   - Neuroticism studies (105 and 205 patients); sequential model fit in 1008 patients.
4. **Neural Mechanisms of Pain Unpleasantness and Secondary Pain Affect (pp. 1770–1771).**
   - Direct pathways: spinohypothalamic, spinopontoamygdaloid, medial thalamic → ACC/insula.
   - Lateral route: VPL/VPI → S1/S2 → posterior parietal → insula → amygdala, perirhinal cortex, hippocampus. Convergence of the two routes.
   - Graded heat recruits more regions (intensity coding common to all pain functions).
   - Hypnosis PET: ACC 24 tracks unpleasantness, not S1; R = 0.55. Tölle 1999 replication with a different method.
   - Direct spinal inputs drive rudimentary autonomic, escape, orientation and fear responses "somewhat automatically."
   - Posterior parietal and insular integration of context supplies "an overall sense of intrusion and threat."
   - Monkey 7b neurons; monkey S2/7b lesion abolishes escape; human insula lesion yields asymbolia.
   - ACC relates attention and evaluation to "emotional valence and response priorities." Cortical areas for sensory, attentional, premotor and affective functions are "largely in series."
   - Over time, ACC–prefrontal coordination supports secondary affect. Lobotomy vs asymbolia contrast.
5. **A Parallel-Serial Model of Pain Affect (pp. 1771–1772).** Summary model. Direct inputs supply arousal and autonomic/somatomotor aspects. Medial thalamic inputs reach the insula (bodily state) and ACC (attention, response priorities). A serial somatosensory-limbic pathway supplies cognitive evaluation. ACC is "pivotal" and more closely tied to unpleasantness than the structures projecting to it. Secondary affect is sustained by unpleasantness and may depend on ACC–prefrontal interactions.
6. **References and Notes (p. 1772).** 29 notes.

**Deep-dive selection.** Sections 3–4 were expanded above (evidence table, argument reconstruction), because they carry the dimensional claims the later literature inherited and contested.

**Field-history record**
- Year · community: 2000 · human-neuroscience
- Question it asked: What psychological layers make up pain's affective dimension, how are they causally ordered, and which brain pathways implement them?
- Position / finding in one line: Pain affect is a serial chain (intensity → unpleasantness → secondary affect) with parallel arousal inputs, implemented by direct spinal-limbic and cortico-limbic pathways that converge on the ACC, which sets "emotional valence and response priorities."
- Responds to / builds on: Melzack & Casey 1968; Price 1999; Price, Harkins & Baker 1987; Rainville et al. 1992, 1997, 1999; Harkins et al. 1989; Wade et al. 1992, 1996; Coghill et al. 1999; Bushnell et al. 1999; Tölle et al. 1999; Craig 1995; Friedman et al. 1986; Dong et al. 1994, 1996; Weinstein et al. 1955; Berthier et al. 1988; Devinsky et al. 1995; Damasio 1994; Hardy, Wolff & Goodell 1952
- Measures (empirical only): review of cited studies · intensity rating [yes] · unpleasantness rating [yes] · avoidance/escape behaviour [yes — only in cited lesion cases: monkey escape, human asymbolia withdrawal] · desire/urge rating [no] · neural [PET; single-unit (monkey); lesion]
- Dissociation reported (empirical only):
  - Hypnotic suggestion aimed at unpleasantness → unpleasantness and ACC area 24 moved; intensity and S1 did not. Suggestion aimed at intensity → both ratings moved (and S1).
  - Neuroticism → secondary affect moved strongly, unpleasantness slightly, intensity not at all.
  - Insula lesion (asymbolia) → withdrawal lost, sensory detection preserved. Monkey S2/7b lesion → escape lost, offset detection preserved.
  - Lobotomy → spontaneous concern lost, immediate threat preserved.
- Survey claim check: partly — 'Price's Science review kept the fusion - affective and motivational are used interchangeably - and the entire intensity/unpleasantness psychophysics that followed inherited it' →
  - **Not supported: "used interchangeably".** "Motivational" never appears, and "motivation" appears once, as part of the ACC's "response priorities ... integrally related to motivation and emotions" (p. 1771). The affective dimension is defined as unpleasantness plus secondary affect (p. 1769), and escape desires are an accompaniment: pain "is often accompanied by desires to terminate, reduce, or escape its presence" (p. 1769).
  - **Supported: "kept the fusion" in a weak sense.** Price gives motivation no dimension or measure of its own.
  - **Not checkable here: the "inheritance" claim.** It is a claim about later literature. Note that Talbot et al. 2019 attribute the "affective-motivational" label to this paper (their ref. 5), which it does not use; see [§4](#4-talbot-madden-jones--moseley-2019--the-sensory-and-affective-components-of-pain-differentially-modifiable-or-inseparable-tier-full).
- PDF version: published

---

## 3. Leknes & Tracey (2008) — A Common Neurobiology for Pain and Pleasure [tier: short]

**PDF:** `docs/project/references/imperativism/sources/Leknes and Tracey 2008 - A common neurobiology for pain and pleasure.pdf` — the published *Nature Reviews Neuroscience* "Perspectives / Science & Society" article (pp. 314–320). It is an opinion-style perspective, not a systematic review or primary study, and it is only partly about the dimensions of pain.

**Claim.** Pain and pleasure, long studied apart and treated as opposites, share much of their neural circuitry and chemistry. The μ-opioid and dopamine systems in particular are the likely "common currency" that lets the brain compare and trade off competing pleasant and aversive events (pp. 314, 318).

**Method / type.** A narrative perspective drawing on human imaging (fMRI, PET, receptor-ligand PET), rodent pharmacology and lesion work, primate electrophysiology, and genetics. Fig. 2 tabulates regions implicated in both pain and pleasure, with example studies per region (p. 317).

**Key result or argument.**
- **Definitions.** Rewards and punishments are defined behaviourally, as what an animal works to obtain or avoid. "The term 'pain' encompasses both the hedonic (suffering) and motivational (avoidance) aspects of a painful experience" (p. 314).
- **Utility and homeostasis.** Pain is framed as a deviation from homeostasis, following Craig 2003. Greater perceived threat raises unpleasantness (p. 314).
- **Motivation-Decision Model** (Fields). Anything more important for survival than pain should produce antinociception through the brainstem descending system, and pain in turn reduces pleasure (pp. 314–315).
- **Hedonic versus motivational components.** Because avoidance motivation "is generally correlated with the pleasantness or aversiveness of an event ... it is difficult to disentangle the neuroanatomy of the hedonic and motivational components of pain and reward" (p. 315). Yet "the motivation and hedonic subsystems seem to be mediated by different neurotransmitters": opioids for "liking", dopamine for "wanting" (p. 315). That evidence comes mainly from the *reward* side (palatable food).
- **Pain-side dissociations cited.**
  - κ-opioids reduce pain yet induce aversion.
  - A serotonergic knockout separates μ-opioid analgesia from μ-opioid reward.
  - Amphetamine reduces tonic but not phasic pain behaviour.
  - Fibromyalgia patients release less striatal dopamine yet rate deep muscle pain as more painful (pp. 315–316).
- **Overlap and segregation.** Regions overlap at the systems level, but separate sub-populations appear within the pallidum, nucleus accumbens shell (a rostrocaudal "hedonic gradient"), amygdala and orbitofrontal cortex. This "supports the existence of two neural systems for pain and pleasure at the within-region spatial scale" (pp. 317–318).

**Place in the field's history.** The paper marks a turn from the sensory/affective split *within* pain (Price 2000) toward placing pain on a shared **valence and reward axis** with pleasure. It imports Berridge's liking/wanting distinction from reward neuroscience. That brings the *hedonic vs motivational* question into pain research explicitly, while conceding that the two are hard to pull apart for pain itself.

**Relevance.**
- **Hedonic and motivational named separately.** The paper names "hedonic" and "motivational (avoidance)" as distinct aspects of pain, and states that separating them neuroanatomically is difficult. Neither Price 2000 nor Talbot et al. 2019 draws this distinction.
- **Behavioural definition of punishment.** Its definition ("something that an animal will work to ... avoid") ties the aversive side to avoidance behaviour. Later computational and animal-circuit work builds on that tie.

**Field-history record**
- Year · community: 2008 · human-neuroscience
- Question it asked: Do pain and pleasure share neural substrates and chemistry, and how do they inhibit each other?
- Position / finding in one line: Pain and pleasure overlap extensively in circuitry, with opioid ("liking") and dopamine ("wanting") systems as a common currency for comparing them; hedonic and motivational components are hard to separate anatomically but may use different transmitters.
- Responds to / builds on: Fields 2006, 2007 (Motivation-Decision Model); Berridge 2003, 2007 (liking/wanting, incentive salience); Cabanac 1979 (alliesthesia); Craig 2003 (pain as homeostatic emotion); Price, Harkins & Baker 1987; Rainville et al. 1997; Seymour et al. 2005, 2007; Schultz 2007; Smith & Berridge 2007; Scott et al. 2006, 2007; Zubieta et al. 2001, 2003; Wood et al. 2007; Bentham
- Measures (empirical only): n.a. (perspective; no new data). Cited work spans intensity rating [yes] · unpleasantness rating [yes] · avoidance/escape behaviour [yes — rodent place avoidance, suppressed feeding] · desire/urge rating [no] · neural [fMRI; PET incl. dopamine and μ-opioid ligands; rodent pharmacology/lesion; primate electrophysiology]
- Dissociation reported (empirical only): n.a. (no new data). Cited dissociations:
  - Dopamine raises "wanting" but not "liking" of palatable food (reward side).
  - κ-opioids produce analgesia together with aversion.
  - μ-opioid analgesia but not reward depends on central serotonergic neurons.
  - Amphetamine reduces tonic but not phasic pain behaviour.
- Survey claim check: n.a. — no survey claim assigned (history anchor) → n.a.
- PDF version: published

---

## 4. Talbot, Madden, Jones & Moseley (2019) — The Sensory and Affective Components of Pain: Differentially Modifiable or Inseparable? [tier: full]

**PDF:** `docs/project/references/imperativism/sources/Talbot et al. 2019 - The sensory and affective components of pain - Differentially modifiable or inseparable.pdf` — the published *British Journal of Anaesthesia* review article (123(2): e263–e272; Advance Access 1 May 2019). The full title on the PDF is "The sensory and affective components of pain: are they differentially modifiable dimensions or inseparable aspects of a unitary experience? A systematic review". Supplementary Files 1–5 (protocol, search strategy, risk-of-bias tool, extraction form, full data) are **not** in the PDF, and Fig. 2 (forest plots) is an image whose numbers were not extractable.

### Phase 1: Foundational Overview

**Introduction.** Pain researchers routinely treat intensity and unpleasantness as two separable dimensions. Clinicians, philosophers and patients mostly treat pain as one unpleasant bodily experience ("How is your pain?"). The authors note that the evidence for separability "is seldom presented" (p. e263). They asked a narrow, testable version of the question: **can a purely psychological manipulation move one of the two ratings without moving the other?**

**Key findings.**
- **Method.** A PRISMA systematic review with an a priori protocol built on Fernandez & Turk's 1992 recommendations. Five databases were searched up to February 2017, and two independent reviewers screened, extracted data and rated bias.
- **Included studies.** 12 studies qualified, all in healthy adult volunteers; none in clinical pain met the criteria. They used hypnosis with suggestion (5), suggestion alone (1), pleasant or unpleasant odours, pictures or videos (4), and meditation (2).
- **Bias.** Every study was at high risk of bias in at least one area, or gave too little information to judge.
- **Intensity.** 9 of 12 studies could not or did not move intensity selectively. The two studies claiming selective control of *both* ratings were at very high risk of bias.
- **Unpleasantness.** Several studies moved it selectively, mostly with hypnotic suggestion in highly hypnotisable people. The effects of pleasant or unpleasant sights and smells were small, about 3–4.4 points on a 100-point scale.
- **Conclusion.** The authors conclude: "the sensory component cannot be selectively modulated, but the affective component might be", with "only tentative endorsement", and any effect "is likely to be very small". Overall, "the evidence suggests ... that pain is a unitary unpleasant and sensory experience" (p. e270).

**Initial takeaway.** This is the field's first rigorous audit of the experimental basis for treating the two ratings as independent. The verdict is asymmetric. Intensity looked fixed. Unpleasantness looked only slightly movable, and the studies showing it are vulnerable to suggestion wording and demand effects. The authors lean toward pain being a single experience.

### Phase 2: Graduate-Level Deep Dive

#### Technical analysis — design

**Research question (PICO, Table 1, p. e265).**
- **Population:** people with chronic pain and healthy volunteers.
- **Intervention:** cognitive manipulations.
- **Comparison:** none.
- **Outcome:** "the extent to which the affective and sensory dimensions of pain can be selectively and intentionally modulated."

**Eligibility (p. e265).** Studies had to meet all of the following:
- human participants;
- a cognitive technique *aimed* at selectively modulating one dimension;
- an experimental design with a baseline, a control group, or a pre–post comparison;
- *both* dimensions assessed.

Somatosensory interventions (for example TENS) and exogenous drugs were excluded. Languages were unrestricted if the title and abstract were in English; two non-English full texts were translated.

**Risk of bias (p. e265).**
- The authors built a custom tool covering selection, performance/detection, cognitive technique, measurement, statistics and reporting.
- Low risk required a reported manipulation check and blinding efficacy, and outcomes that assessed *pain* rather than the stimulus.
- Purposive or convenience sampling was rated high risk. The authors acknowledge this is "a deliberately conservative decision."

**Effect estimate (p. e265).** For each study, the change in the non-target dimension was subtracted from the change in the target dimension. The result was entered into Review Manager 5.2 using generic inverse-variance weighting with a random-effects model. In symbols (*reviewer's rendering of the paper's prose*):

$$
\widehat{\mathrm{MD}} \;=\; \Delta_{\text{target}} \;-\; \Delta_{\text{non-target}}, \qquad \text{reported with } \mathrm{SE}\!\left(\widehat{\mathrm{MD}}\right)
$$

Here Δ is the change in mean rating under the manipulation. A positive value means the targeted rating moved more than the other one. Raw data were obtainable for only 3 of the 12 studies, and those 3 used different manipulations, so they were shown as forest plots but "prevented pooling" (p. e268).

**Search flow (Fig. 1, p. e266).**

| Stage | Count |
|---|---|
| Records from 5 databases | 8067 (Embase 1975; Cochrane 1994; Scopus 1919; PsycINFO 767; Medline 1412) |
| Duplicates removed | 3373 |
| Added from reference lists / experts | 7 (5 + 2) |
| Titles/abstracts screened | 4708 |
| Excluded at screening | 4476 |
| Full texts assessed | 232 |
| Full texts excluded | 220 (183 no selective manipulation; 36 did not measure both dimensions; 1 design) |
| Included, qualitative synthesis | 12 |
| Included, quantitative display | 3 |

*Internal inconsistencies noted by the reviewer.* The abstract says the search "yielded 4270 articles", but the flowchart says 4708 were screened. The flowchart arithmetic (8067 − 3373 + 7 = 4701) is also off by 7. Neither affects the 12 included studies.

**Included studies (Table 2, p. e267).** Totals: 164 female and 148 male participants (312 across the rows, with the Rainville 1999 experiments counted separately).

| Class | Study | n (F:M) | Target | Scale |
|---|---|---|---|---|
| Hypnosis + suggestion | Dahlgren 1995 | 32 (17:15) | Relaxation or analgesia suggestion | Verbal word lists |
| | Rainville 1997 | 8 (3:5) | Unpleasantness ↑ and ↓ | NRS 0–100 |
| | Rainville 1999 | Exp 1: 17; Exp 2: 20; Exp 3: 22 | Exp 1–2: unpleasantness; Exp 3: intensity ↑↓ | VAS |
| | Hofbauer 2001 | 10 (6:4) | Intensity ↑↓ | Magnitude estimation |
| | Valentini 2013 | 24 (24:0) | Intensity or unpleasantness | VAS 0–101 |
| Meditation | Perlman 2010 | 19 (9:10) | Meditation | NRS |
| | Grant 2009 | 28 (10:18) | Meditation | VAS 0–10 |
| Valence via external stimuli | Kenntner-Mabiala 2007 | 54 (27:27) | Picture valence + attention | VAS |
| | Kenntner-Mabiala 2008 | 30 (15:15) | Picture valence + attention | VAS |
| | Loggia 2008 | 12 (12:0) | Video valence (mood) | NRS |
| | Villemure 2003 | 14 (9:5) | Odour + attention | NRS 0–10 |
| Suggestion alone | Kunz 2012 | 22 (10:12) | Unpleasantness or intensity ↑ | VAS 0–100 |

Selection biases (p. e266):
- All 5 hypnosis studies selected participants by hypnotic susceptibility.
- Both meditation studies compared experts with novices.
- Three studies admitted only people who had already shown successful attentional or emotional modulation of pain.

#### Results by class (as reported, p. e268)

- **Hypnosis with suggestion.**
  - 4 of 5 studies selectively moved affective ratings in the suggested direction.
  - The 3 studies that also targeted the sensory dimension did not achieve selective modulation.
  - Brain activity did follow the target even when ratings did not: sensory-targeted suggestion changed S1/S2, and affective-targeted suggestion changed ACC.
  - Dahlgren 1995 is the exception: "analgesia" suggestion selectively lowered sensory ratings and "relaxation" selectively lowered affective ratings.
  - Highly hypnotisable participants showed greater selectivity.
- **Suggestion alone.** Kunz 2012 reported selective modulation of both dimensions.
- **Valence via external stimuli.**
  - 3 of 4 studies reported selective change in affective ratings, and 1 reported parallel shifts.
  - The paper also states that in both Kenntner-Mabiala studies "only sensory ratings changed". That sits awkwardly with counting Kenntner-Mabiala 2008 among the three affective-selective studies, and the reviewer could not resolve it from the text.
- **Meditation.**
  - Acceptance-based meditation in experts selectively changed unpleasantness in one study but intensity in the other.
  - Focused attention had no effect in one study and raised intensity (in novices only) in the other.

#### Argument reconstruction — from results to conclusion (pp. e269–e270)

1. **Sensory claim.** 9 of 12 studies failed to move intensity selectively. The 2 that succeeded (Dahlgren 1995, Kunz 2012) carry very high bias. **Therefore intensity cannot be selectively modulated by cognitive means.**
2. **Affective claim.** Selective affective effects appear, most consistently under hypnotic *suggestion*. Hypnosis *without* suggestion was ineffective in 3 studies, so the suggestion itself does the work.
3. **Against pure reporting bias (two arguments offered).**
   - The same kind of suggestion failed for intensity, and reporter bias should apply to both dimensions equally.
   - Rainville 1997 showed ACC change only under hypnosis-plus-suggestion, not under wake or hypnotic control conditions.
4. **Caveats that shrink the affective claim.**
   - Only 10–20% of people are highly hypnotisable.
   - External-stimulus effects were 3–4.4 units on a 100-unit scale, below clinical or individual-level meaningfulness.
   - Demand effects cannot be excluded. The one successful intensity manipulation used the word "analgesia", which may carry conceptual weight that "reduce intensity" lacks.
5. **Why unpleasantness might be the more movable of the two (speculative, flagged by the authors with "We suspect").** Lay participants think of pain as "coming from the tissues". They may therefore take the sensory rating to be "pain itself" and treat any attempt to change it as pointless.
6. **The unitary view.**
   - Untrained participants rate the two dimensions alike.
   - In Fernandez & Turk 1994, participants who rated each dimension in a separate week did not rate them differently, but did when rating both at once.
   - Experimental pain is brief, escapable and harmless, so its unpleasantness may be less compelling, and more movable, than clinical pain.
7. **Conclusion.** The evidence for selective modulation is weak. The sensory component cannot be moved on its own; the affective component might be, but tentatively and by very little. "the evidence suggests the alternative view, one that is usually held by people actually in pain—that pain is a unitary unpleasant and sensory experience" (p. e270).

**The inferential step to watch.** The conclusion's title-level wording ("unitary") is stronger than its data-level wording, which is asymmetric: the affective dimension "might be" modifiable. A study that failed to move one rating selectively shows that *this manipulation* did not separate the ratings. It does not show that the ratings are inseparable in principle. The authors acknowledge that their a priori criteria may have missed studies that "inadvertently invoked selective modulation" (p. e270). Non-cognitive dissociations (drugs, lesions) were excluded by design, so the review does not speak to the lesion and asymbolia evidence that Price 2000 relies on.

#### Terminology — where the affective/motivational fusion actually appears

In the introduction (p. e264), Talbot et al. write that pain is "a bidimensional experience consisting of a sensory-discriminative dimension and an affective-motivational dimension", **citing Price 2000 (their ref. 5)**. They continue: "The affective-motivational dimension, often referred to simply as 'unpleasantness' or given the label 'affective', captures how 'bad' or how 'unpleasant' the pain is. That is, it captures the motivational aspect of pain—the aspect that makes us want to take protective action."

This *is* an explicit equation of unpleasantness with motivation. It appears in Talbot et al., not in Price 2000, which never uses "affective-motivational" ([§2](#where-motivation-sits-in-price-2000-terminology-audit)). The compound label historically traces to Melzack & Casey 1968 ("motivational-affective"), which is not held here. The review measures only intensity and unpleasantness ratings, so motivation is never assessed separately.

Two further citation details, for the historian:
- The ACC hypnosis example is cited to ref. 14 (Rainville et al. 1992, a psychophysics paper). The finding described matches Rainville et al. 1997 (their ref. 30). This appears to be a citation slip.
- The pathway assignments come via Treede et al. 1999 and Price 2002: lateral spinothalamic → sensory; spino-parabrachio-amygdaloid/-hypothalamic → affective.

### Appendix: Section-by-Section Backbone

1. **Title, abstract and keywords (p. e263).** Background: pain feels single, but research treats its two dimensions as separable, and the evidence "is seldom presented." Methods: systematic search ("4270 articles"); screening on effectiveness, methodological rigour (a priori intent to modulate one dimension) and theoretical reasoning. Results: 12 articles; "no compelling evidence" of selective, intentional cognitive modulation in humans. Keywords: cognition, hypnosis, imagery, pain measurement, pain perception.
2. **Introduction (untitled, pp. e264).**
   - Pain as a motivator of protective behaviour, "more closely resemble[s] feelings such as hunger or thirst" than vision (citing Moseley).
   - Plato on pain being necessarily perceived.
   - The bidimensional model (citing Price 2000); the IASP 2017 terminology.
   - Definitions of both dimensions, with affective-motivational equated with unpleasantness and protective motivation; the McGill Pain Questionnaire.
   - Clinical threat attribution raises unpleasantness at similar intensity.
   - Imaging: ACC for affect, S1 for sensory. Pathways: lateral spinothalamic (wide-dynamic-range neurones) → sensory; parabrachial-amygdala/hypothalamus → affective.
   - Counter-view: pain as unidimensional, successful separations as demand effects, untrained participants rating the two alike.
   - The split between scientists and clinicians, philosophers and laypeople; the lack of any evidence appraisal.
   - The three requirements from Fernandez & Turk 1992.
3. **Methods (p. e265).**
   - PICO (Table 1); PRISMA; a priori protocol (Suppl. 1).
   - *Information sources*: five databases to February 2017 (Suppl. 2).
   - *Study selection*: two reviewers; inclusion and exclusion criteria; translation.
   - *Risk of bias*: custom tool (Suppl. 3); minimum criteria; convenience sampling rated high risk.
   - *Data collection*: two reviewers, piloted form (Suppl. 4).
   - *Outcome measures*: primary = sensory and affective ratings; secondary = cortical activation, physiological and psychological variables; target-minus-non-target mean difference; RevMan random effects (Suppl. 5).
4. **Results (pp. e265–e268).**
   - *Study selection*: flow counts (Fig. 1).
   - *Study characteristics*: four manipulation classes; limited comparability; healthy adults only; biased eligibility; 164 F / 148 M; two all-female studies (Table 2).
   - *Risk of bias within studies*: all high or unclear (Table 3).
   - *Results of individual studies*: hypnosis, suggestion alone, valence, meditation (detailed above); 3 studies with full data (Fig. 2), not pooled.
5. **Discussion (pp. e269–e270).**
   - Evidence "offers some support to both viewpoints ... far from clear-cut"; the most biased studies showed the largest effects.
   - The sensory dimension is not selectively modifiable; the affective dimension might be.
   - Hypnotic suggestion is the most consistent route; the scripts avoided the word "unpleasantness"; suggestion, not hypnosis alone, does the work; arguments against reporter bias; the neural effect for sensory suggestion did not translate into ratings.
   - Generalisability limited by hypnotisability (10–20%); external-stimulus effects small (4.4 or 3 units per 100).
   - Why affect may be more modifiable: lay beliefs that pain is a tissue marker; mindfulness practice as consistent with this; mechanisms lacking.
   - Demand effects; the "analgesia" wording; expectation effects on remifentanil.
   - The unitary view: untrained raters; Fernandez & Turk 1994; experimental vs clinical pain; volunteer self-selection.
6. **Future directions and limitations (p. e270).** Rigorous methods against demand effects; avoiding ceiling effects and ambiguous anchors; blinding and naïve participants; retaining raw data (only 3 of 12 obtainable, the main limitation); a priori criteria may have missed inadvertent separations; reproducibility.
7. **Conclusion (pp. e270–e271).** Evidence weak; sensory component not selectively modifiable; affective component might be, tentatively and very small; evidence favours a unitary unpleasant and sensory experience; fundamental questions remain.
8. **Back matter (p. e271).** Author contributions; translators; declarations (GLM receives lecture and book royalties on pain and rehabilitation); funding (including NHMRC and Pfizer); 61 references.

**Deep-dive selection.** Methods (the effect estimate and the bias rules), Results and Discussion were expanded above, because the paper's historical weight rests on how the evidence was filtered and how the verdict was worded.

**Field-history record**
- Year · community: 2019 · clinical-psychology
- Question it asked: Can cognitive manipulations selectively and intentionally modulate the sensory (intensity) or affective (unpleasantness) dimension of pain in humans?
- Position / finding in one line: No compelling evidence. Intensity was not selectively modulated; unpleasantness might be, but tentatively, by a very small amount, and in high-bias studies; the authors conclude the evidence favours pain as a unitary unpleasant and sensory experience.
- Responds to / builds on: Fernandez & Turk 1992 (the framework followed), 1994 (demand characteristics); Price 2000, 2002; Melzack & Katz 2001 (McGill Pain Questionnaire); Auvray, Myin & Spence 2010; Treede et al. 1999; Chapman et al. 2001, 2002 and Chapman 1996 (indistinguishable dimensions); Rainville et al. 1992, 1997, 1999; Hofbauer et al. 2001; Dahlgren et al. 1995; Valentini et al. 2013; Kunz et al. 2012; Villemure et al. 2003; Kenntner-Mabiala et al. 2007, 2008; Loggia et al. 2008; Perlman et al. 2010; Grant & Rainville 2009; Moseley & Butler 2015, 2017; IASP 2017
- Measures (empirical only): systematic review of 12 studies · intensity rating [yes] · unpleasantness rating [yes] · avoidance/escape behaviour [no] · desire/urge rating [no] · neural [secondary outcome in some included studies: PET, fMRI, laser-evoked/somatosensory-evoked EEG potentials]
- Dissociation reported (empirical only):
  - Hypnotic suggestion aimed at unpleasantness → unpleasantness moved and intensity did not (4 of 5 hypnosis studies).
  - Suggestion aimed at intensity → no selective rating change (3 of 3), but S1/S2 activity changed selectively.
  - External-valence manipulations → unpleasantness moved selectively in 3 of 4 studies, by about 3–4.4 units per 100.
  - Exceptions at very high bias: Dahlgren 1995 ("analgesia" suggestion → intensity; "relaxation" → unpleasantness) and Kunz 2012 (both dimensions selectively).
  - Avoidance and desire were not measured in any included study.
- Survey claim check: partly — 'argues the sensory and affective components are not independently modifiable dimensions but inseparable aspects of a single experience - the ratings covary too tightly and dissociations are mostly attention effects' →
  - **Supported: the overall lean.** The authors conclude "the evidence suggests the alternative view ... that pain is a unitary unpleasant and sensory experience" (p. e270), and cite work showing untrained raters do not separate the two (p. e270).
  - **Too strong: "not independently modifiable".** The data-level verdict is asymmetric: "the sensory component cannot be selectively modulated, but the affective component might be" (p. e270).
  - **Not supported: "mostly attention effects".** The alternative explanations the paper offers are demand effects, suggestion wording ("analgesia"), selection and risk of bias, and lay beliefs about pain (pp. e269–e270). Attention appears only as a co-manipulation in some valence studies, not as the explanation of dissociations.
- PDF version: published

---

## Cross-paper notes for the synthesis

These are observations about how the four papers relate. They are not a thematic regrouping, which belongs to `literature-curator`.

1. **Who uses which word.**

   | Paper | "sensory"/"affective" | "motivational" | Fused label |
   |---|---|---|---|
   | Melzack & Wall 1965 | "sensory and affective components" (p. 976) | not used | none |
   | Price 2000 | "affective dimension" = unpleasantness + secondary affect | never; "motivation" once, in ACC "response priorities" (p. 1771) | none |
   | Leknes & Tracey 2008 | "hedonic (suffering)" | "motivational (avoidance)", named as a *separate* aspect (p. 314) | none; says the two are hard to disentangle (p. 315) |
   | Talbot et al. 2019 | "sensory-discriminative" vs "affective-motivational" | equated with unpleasantness (p. e264) | yes, and attributed to Price 2000 |

   The survey's "fusion" claim is better supported by Talbot et al. 2019 than by Price 2000. Talbot et al.'s attribution of the fused label to Price 2000 is itself a misattribution; the label's origin is Melzack & Casey 1968, which is not held here.
2. **One asymmetry, two readings.** Suggestion aimed at unpleasantness moves unpleasantness alone, while suggestion aimed at intensity moves both ratings (Price) or neither selectively (Talbot et al.). Price 2000 reads this as *seriality* (sensation causes unpleasantness). Talbot et al. 2019 read it as *non-modifiability of the sensory rating*, plus bias and demand caveats. The underlying primary studies overlap (Rainville 1997 and 1999, Hofbauer 2001).
3. **Where avoidance lives.**
   - Melzack & Wall 1965: in the *action system*, as one of many responses.
   - Price 2000: in ACC "response priorities" and in escape desires that accompany pain; measured only through lesion outcomes (monkey escape, human asymbolia).
   - Leknes & Tracey 2008: as the *motivational* aspect, defined behaviourally.
   - Talbot et al. 2019: equated with unpleasantness and not measured.

   None of the four papers measures an avoidance urge or desire *as a rating* alongside intensity and unpleasantness.
4. **Imperative vocabulary in 1965.** Melzack & Wall quote Sherrington's description of pain as "the sensory adjunct of an imperative protective reflex" (p. 976) and reject the reflex-only reading. This is a documented pre-philosophical use of "imperative" in the pain literature, relevant to [Part A](imperativism_lit_review_A_imperative_theories.md).
5. **Evidence types differ sharply.** Price 2000 relies heavily on lesion and imaging dissociations. Talbot et al. 2019 exclude everything except cognitive manipulations by design. Their disagreement is partly a disagreement about which evidence counts.

---

## Not reviewed (no PDF)

These references are named in the corpus manifest for this batch. No PDF is held, so they were **not** reviewed, and nothing above is drawn from them.

| Reference | DOI | Reason |
|---|---|---|
| Melzack & Casey (1968) — Sensory, motivational and central control determinants of pain | — | PDF not obtainable |
| Fernandez & Turk (1992) — Sensory and affective components of pain: Separation and synthesis | 10.1037/0033-2909.112.2.205 | PDF not obtainable |
| Treede et al. (1999) — The cortical representation of pain | 10.1016/S0304-3959(98)00184-5 | PDF not obtainable |
| Auvray et al. (2010) — The sensory-discriminative and affective-motivational aspects of pain | 10.1016/j.neubiorev.2008.07.008 | PDF not obtainable |
| Raja et al. (2020) — The revised IASP definition of pain | 10.1097/j.pain.0000000000001939 | PDF not obtainable |

(Melzack & Casey 1968, Fernandez & Turk 1992, Treede et al. 1999 and Auvray et al. 2010 are cited *by* the reviewed papers. Where this review mentions what those papers are cited for, it reports only the citing paper's description.)
