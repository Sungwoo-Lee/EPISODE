# The Non-Sensory Side of Pain, 1962–2026 — A Field-History Synthesis

**Topic folder:** `docs/project/references/imperativism/`
**Built from:** the per-paper reviews in Parts A–I (65 papers reviewed from PDF, 24 more known only by name), 2026-09-17.
**Curator:** literature-curator
**Master index:** [[imperativism_lit_review_INDEX]] · **Data for diagrams:** `field_history_data/` (8 CSV files; see [§9](#9-data-files-for-diagrams))

## What this document is about (plain-language entry point)

**The field.** Pain is more than a sensation of where and how strongly something hurts. It also *feels bad*, and it *pushes* you to do something, such as pull away, protect the injury, or take a painkiller. This synthesis traces how six research communities have studied that second side of pain since 1962: philosophers, brain-imaging researchers, animal circuit neuroscientists, clinical psychologists, neurologists and computational modellers.

**Why it exists.** These communities ask versions of the same questions but rarely read each other. This document puts their work on one timeline, names the debates that cut across them, and records what each side's evidence can and cannot show. It is a history of a field, not an argument for any theory.

**Where things stand in 2026.** Most debates are still open.
- Philosophers still disagree whether pain's badness is a *command* ("less of this!") or a *perception of value* ("this is bad for me").
- Human experiments can shift how unpleasant pain feels more easily than how strong it feels, but the two ratings stay tightly linked.
- Several studies change avoidance behaviour without changing ratings.
- **No reviewed study measured how unpleasant a person's own pain felt and how much they avoided it on the same trials.**

For this project's artificial agents, the damage signal is called **nociception**, never pain.

## Table of Contents

- [What this document is about (plain-language entry point)](#what-this-document-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Vocabulary](#1-vocabulary)
- [2. Eras](#2-eras)
- [3. Debates](#3-debates)
- [4. How the communities relate](#4-how-the-communities-relate)
- [5. What the evidence does and does not show](#5-what-the-evidence-does-and-does-not-show)
- [6. Corrections to the seed survey](#6-corrections-to-the-seed-survey)
- [7. Current status in one page](#7-current-status-in-one-page)
- [8. Relevance to this project (interpretive)](#8-relevance-to-this-project-interpretive)
- [9. Data files for diagrams](#9-data-files-for-diagrams)
- [10. Scope and provenance](#10-scope-and-provenance)

---

## Reading conventions

- **Citations.** Each claim carries the paper's manifest key and the review section it comes from, written as (`key`; Part §n). Example: (`price2000`; D §2) means the Price 2000 entry, which is entry 2 of Part D. Part files:

  | Part | File | Theme |
  |---|---|---|
  | A | [[imperativism_lit_review_A_imperative_theories]] | Imperative vs evaluative theories (5 papers) |
  | B1 | [[imperativism_lit_review_B1_imperativism_evaluativism_origins]] | Philosophy 2008–2013 |
  | B2 | [[imperativism_lit_review_B2_imperativism_evaluativism_maturity]] | Philosophy 2015–2019 |
  | B3 | [[imperativism_lit_review_B3_valence_debate_current]] | Philosophy, 2020s |
  | C | [[imperativism_lit_review_C_asymbolia_and_lesions]] | Pain asymbolia |
  | D | [[imperativism_lit_review_D_dimensions_of_pain]] | How pain was split into dimensions |
  | E1 | [[imperativism_lit_review_E1_sensory_affective_neuroimaging]] | Human imaging, 1997–2014 |
  | E2 | [[imperativism_lit_review_E2_sensory_affective_recent]] | Human and animal dissociations, 2017–2024 |
  | F | [[imperativism_lit_review_F_motivation_fear_avoidance]] | Fear-avoidance and homeostatic emotion |
  | G1 | [[imperativism_lit_review_G1_avoidance_circuits]] | Animal circuits |
  | G2 | [[imperativism_lit_review_G2_computational_avoidance]] | Pain as a learning and decision signal |
  | H | [[imperativism_lit_review_H_valence_avoidance_dissociation]] | Measuring unpleasantness, avoidance and valence separately |
  | I | [[imperativism_lit_review_I_pain_and_action_cortex]] | Where pain meets action in cortex |

  Unnumbered cross-paper sections are cited by name, e.g. "E1 batch notes", "F connections", "G2 §8".
- **Years.** A paper is placed on the timeline by its first public (online) year where the reviews record that it differs from the print year. The label keeps the familiar citation year. Examples: Carruthers 2018 appeared online in 2017; Bain 2019 in 2017; Misra & Coombes 2015 and Procyk 2016 in 2014.
- **Named-only works** (24 keys, no PDF) are mentioned only as "cited by X", and never carry a claim on their own.
- **"Not found"** means not found in the 65 reviewed papers. It is never a claim about the wider literature.
- **Neutrality.** Positions are stated at their strongest as the reviews record them. A debate is called "leaning" only when the reviewed papers on it converge; that is a description of the corpus, not a verdict.

---

## 1. Vocabulary

| Term | One-line meaning (as used in the reviews) |
|---|---|
| Sensory-discriminative | Where the pain is, what it is like, and how strong it is; in practice usually an intensity rating (D reading conventions). |
| Affective | How bad or unpleasant the pain feels; in practice usually an unpleasantness rating (D reading conventions). |
| Motivational | The drive to act: escape, avoid, protect (D reading conventions). |
| Affective-motivational | A compound label fusing the two previous terms; traced to Melzack & Casey 1968 (not held), made explicit as "unpleasantness … the motivational aspect" in `talbot2019` (D §4). |
| Intensity vs unpleasantness | Two ratings of the same pain: how strong it is vs how bad it feels (E1 entry point). |
| Secondary affect | Price's term for longer-term suffering, worry and depression about having pain (`price2000`; D §2). |
| Valence | The good-or-bad quality shared by pains, pleasures, emotions and moods (A reading conventions). Lee et al. 2024 use it for the *signed* pleasant/unpleasant rating (H §1). |
| Affective intensity | In `lee2024`, the *unsigned* strength of a pleasant or unpleasant feeling; not sensory pain intensity (H §1). |
| Indicative content | A state that describes; true or false ("the ankle is damaged") (A reading conventions). |
| Imperative content | A state that commands; satisfied or not ("don't put weight on that ankle!") (A reading conventions). |
| Imperativism | The view that pain's felt badness (or pain itself) is imperative content. Variants: body-directed (`klein2007`), bodily-state (`martinez2011`), reflexive "less of me!" (`bh2019`), relational (`kauppinen2021`) (B3 reading conventions). |
| Evaluativism | The view that pain's unpleasantness is a representation of something as bad for the subject; label introduced by `bain2013` (B1 §3). |
| Pushmi-pullyu | Millikan's term for a state that is indicative and imperative at once (A §5; B3 §2). |
| Pain asymbolia | A rare lesion condition in which patients report pain but show no concern or withdrawal (C entry point). |
| Avoidance vs escape vs reflex | Avoidance prevents an aversive event; escape ends one under way (F, G2 reading conventions); a reflex is a fast withdrawal such as paw flick, used in animal work as the "sensory" contrast (G1 reading conventions). |
| Conditioned place avoidance (CPA) | An animal learns to avoid a chamber where it was hurt; the standard rodent readout of pain's affective side (G1, E2 reading conventions). |
| ACC / aMCC / MCC / pACC | Anterior cingulate cortex; anterior midcingulate; midcingulate; perigenual ACC. The same labels cover different subregions across papers (I reading conventions; E1 batch note 4). |
| S1 | Primary somatosensory cortex, the body-map region (E1 reading conventions). |
| Insula | Cortex linked to bodily state; anterior insula often responds to pain regardless of action (`perini2013`; I §2). |
| PAG | Periaqueductal gray, a midbrain defence and pain-modulation hub (G1 reading conventions). |
| Teaching signal | A neural signal necessary and sufficient to produce a learned response (`johansen2004`; G1 §2). |
| Prediction error / learning rate | Outcome minus expectation; how far one error moves the expectation (G2 reading conventions). |
| Fear-avoidance model | Clinical model in which catastrophic interpretation of pain leads to fear, avoidance and disability (`vlaeyen2000`; F §1). |

---

## 2. Eras

The corpus supports five eras. Boundaries fall where the questions being asked changed, and are approximate. Era membership of every work is in `field_history_data/works.csv`.

| Era | Years | Reviewed works | Named-only works |
|---|---|---|---|
| Clinical dissociations and the gate | 1962–1989 | 1 | 5 |
| Mapping the dimensions | 1990–2006 | 10 | 9 |
| Pain's badness as a philosophical and motivational problem | 2007–2013 | 10 | 8 |
| Elaboration, formal models and the turn to valence | 2014–2019 | 25 | 1 |
| Valence across all affect and contested dissociations | 2020–2026 | 19 | 1 |

The first era is thin because only one of its works is held. Its content is known mostly through later citations.

### 2.1 Clinical dissociations and the gate (1962–1989)

**Live questions.** Is pain a fixed line from "pain receptor" to "pain centre"? Why do some surgical patients still report pain but say it no longer bothers them?

**Who asked.** Neurosurgeons and neurologists reporting cases; physiologists and psychologists building pain theory.

**Key works.**
- **Melzack & Wall 1965** (`melzackwall1965`; D §1) replaced the single-channel picture with a spinal *gate* modulated by descending brain control. It speaks of pain's "sensory and affective components" without proposing dimensions. It records lobotomised patients who "still have pain but it does not bother them". It quotes Sherrington's description of pain as the adjunct of "an imperative protective reflex", only to reject a reflex-only view. This is the earliest documented use of command vocabulary in the corpus.
- **Named-only anchors, known through citing papers:**
  - Foltz & White 1962 on cingulumotomy, cited as background by `rainville1997` (E1 §1) and `johansen2001` (G1 §1). No reviewed asymbolia paper discusses it (C, not reviewed).
  - Melzack & Casey 1968, cited throughout as the origin of the sensory-discriminative / motivational-affective / cognitive-evaluative split (D §1; G2 §4).
  - Wall 1979, cited for short-term avoidance being adaptive (F §1, §3).
  - Berthier et al. 1988, the asymbolia case series described by `price2000` (D §2) and the Part C papers.

**What changed by the end.** Pain was treated as modulated and multi-component. Clinical dissociations (surgery, lesions) became the template for evidence that its parts come apart.

### 2.2 Mapping the dimensions (1990–2006)

**Live questions.** Which brain systems track how strong pain is versus how bad it feels? Can the bad-feeling side be measured in animals? What turns acute back pain into chronic disability?

**Who asked.** Human neuroimaging, animal circuit neuroscience, clinical psychology.

**Key works.**
- **Human imaging.**
  - `rainville1997` (E1 §1): hypnotic suggestion changed unpleasantness while intensity changed non-significantly. ACC activity followed; S1 did not (N = 8).
  - `hofbauer2001` (E1 §2): the reverse suggestion moved S1, not ACC, but also moved unpleasantness (r = 0.81). The authors rejected "a simple dichotomous description".
  - `zubieta2001` (E1 §3): opioid release in different regions correlated with sensory vs affective questionnaire scores across people.
  - `kulkarni2005` (E1 §4): attending to location vs unpleasantness engaged lateral vs medial regions, without hypnosis.
- **Synthesis.** `price2000` (D §2) turned this into a serial model (intensity → unpleasantness → secondary affect) converging on the ACC. Motivation got no dimension of its own: escape desires "accompany" pain, and "motivation" appears once, in the ACC's "response priorities".
- **Animals.** `johansen2001` (G1 §1) made pain affect measurable in rats as learned place avoidance. Rostral ACC lesions abolished it while acute paw behaviours were not reduced. `johansen2004` (G1 §2) showed ACC glutamate activity was necessary and sufficient for that learning and called it an "aversive teaching signal".
- **Neuroanatomy.** `craig2003` (F §2) recast pain as a homeostatic emotion, like hunger or thermal discomfort: a sensation in insula and a motivational drive in ACC.
- **Clinical psychology.** `vlaeyen2000` (F §1) consolidated the fear-avoidance model: fear, not pain intensity, predicts disability. `leeuw2006` (F §3) audited it: intense pain is itself threatening, disuse is weakly supported, and the causal claims had not been tested by manipulation.

**What changed by the end.** "ACC encodes unpleasantness" became the standard citation, although its authors hedged it. "Affect" meant a rating in humans and avoidance in animals. Fear-avoidance was the clinical default, with causal tests still missing.

### 2.3 Pain's badness as a philosophical and motivational problem (2007–2013)

**Live questions.** What does pain's badness *represent*, if anything? Is pain a command or an evaluation? How can pain give reasons to act, and why is taking a painkiller rational? In neuroscience: is pain a motivator, and is the cingulate about feeling or about action?

**Who asked.** Philosophers of mind, for the first time in this corpus; human neuroscience; clinical psychology.

**Key works.**
- **Philosophy founds the two camps.**
  - `klein2007` (A §1): pain is a *negative command* against using a body part; intensity is command strength; morphine pain is "a stop sign in a ghost town".
  - `martinez2011` (B1 §1), developed independently: unpleasantness commands that a *bodily disturbance* not exist. He argues against Klein's action commands and against reading pain as represented harm.
  - `cuttertye2011` (B1 §2): pain represents damage as bad for the subject *to a degree*; imperatives cannot capture intensity or why pain is negative and pleasure positive.
  - `bain2013` (B1 §3) names *evaluativism*. Commands are not reasons, and imperativism cannot explain painkillers.
  - `jacobson2013` (B1 §4) turns the painkiller point on evaluativism: removing a report of bodily badness without fixing the body is "killing the messenger".
  - Named-only: Hall 2008 (itch as "scratch here!") is cited by all three B1 critics (B1 not reviewed). Tumulty 2009 and Klein 2010 are listed as an early exchange but were not reviewed.
- **Neuroscience reframes pain as motivation.**
  - `leknestracey2008` (D §3) puts pain beside pleasure, with shared opioid and dopamine systems. It names "hedonic (suffering)" and "motivational (avoidance)" aspects separately but says they are hard to disentangle.
  - `shackman2011` (I §1) finds pain, negative affect and cognitive control converging on one aMCC region (adaptive control hypothesis).
  - `perini2013` (I §2) finds midcingulate responses to pain only when a button press is made.
  - `wiech2013` (G2 §1) calls the pain–motivation relation "clearly bidirectional" and names reinforcement-learning tools as the next step.
- **Clinical psychology turns to goals.** `crombez2012` (F §4) recasts fear-avoidance as competition between avoiding pain and other valued goals, and says the model "underplayed" pain intensity.

**What changed by the end.** Two philosophical camps and their open threads were in place: intensity, reasons, painkillers, asymbolia (B1 §5). In neuroscience and clinical work, *motivation* had become a separate object of study rather than a synonym for affect.

### 2.4 Elaboration, formal models and the turn to valence (2014–2019)

**Live questions.** Can imperativism handle intensity and reasons? What motivates relief-seeking? Does asymbolia refute the idea that pain intrinsically motivates? Is valence one kind of thing across all feelings? Is pain a reinforcement signal? Can behaviour be moved without moving ratings? Do the two ratings separate at all?

**Who asked.** All six communities. This is the densest era: 25 reviewed works.

**Key works.**
- **Imperativism elaborated.**
  - `martinez2015` (B2 §1): pains are "benevolent-dictator" commands; relief-seeking is extrinsic avoidance of "spammy" requests.
  - `klein2015` (B2 §2): a book-length defence (only a 12-page preview held) about *pain per se*, with unpleasantness treated separately.
  - `mk2016` (B2 §3): a signalling-game model in which pain messages carry more information about protective acts than about world states. The surplus is at most about 1 bit, so "predominantly" is modest.
  - `km2018` (B2 §6): intensity as a ranking over possible worlds (written c. 2014).
- **Evaluativism restated.**
  - `bain2017` (B2 §4): a handbook statement.
  - `bainreview2017` (B2 §5): a critical review of Klein's book.
  - `bain2019` (B2 §7): unpleasantness is bad in itself, and relief-seeking comes from *separate* desires.
- **Asymbolia reinterpreted.** `klein2015asym` (C §1): asymbolics have lost a general capacity to care about bodily integrity; the command persists but is not treated as binding.
- **Debate widens to all affect.**
  - `carruthers2018` (A §2): valence is a nonconceptual representation of value, for all feelings.
  - `bh2019` (A §3) and `loopy2019` (B2 §8): reflexive imperativism, in which an unpleasant experience commands "less of me!". Loopy uses rat liking/wanting dissociations as evidence, the point B2 identifies as where the dispute began to lean on affective neuroscience.
- **Pain as a learning and control signal.**
  - `wang2018` (G2 §2): planning vs habit arbitration applied to pain avoidance.
  - `seymour2019` (G2 §4): pain is a reinforcement signal in a hierarchy of controllers, and "control behavior should serve as the ultimate measure of pain".
- **Dissociations tested and audited.**
  - `tiemann2014` (E1 §5): dopamine depletion raised unpleasantness only.
  - `hayen2017` (E2 §1): an opioid lowered the unpleasantness of *breathlessness* only.
  - `claes2015` (F §5): reward changed avoidance choices while ratings did not change.
  - `corder2019` (G1 §3): silencing an amygdala ensemble reduced tending and escape, not reflexes.
  - `talbot2019` (D §4): a systematic review found intensity not selectively modifiable and unpleasantness only tentatively and slightly so, and leans toward pain as unitary.
- **Cingulate and action.** `misra2014`, `budell2015`, `procyk2014`, `tolomeo2016`, `han2017` (I §3–§7).

**What changed by the end.** The philosophical question became one about *valence in general*. Relief-seeking became a named test. Pain as a learning signal got a formal architecture. The main human evidence for separable dimensions got its first systematic, and sceptical, audit.

### 2.5 Valence across all affect and contested dissociations (2020–2026)

**Live questions.** Which theory best interprets learning and decision neuroscience? Is asymbolia pain at all? How graded are dissociations measured without heavy manipulation? Do people learn more from pain received or pain avoided? Is midcingulate "pain" activity about action?

**Who asked.** Philosophy, human neuroscience, animal circuits, computational modelling, clinical psychology.

**Key works.**
- **Philosophy.**
  - `barlassina2020` (A §4) tests reflexive imperativism against Carruthers's own standards.
  - The essay `barlassina_reflection` (B3 §3) concedes the evolutionary function of valence is unexplained.
  - `kauppinen2021` (B3 §1) proposes relational imperativism and denies that feelings intrinsically motivate getting rid of themselves.
  - `carruthers2023` (A §5) argues valence represents adaptive value and that commands are idle in the science.
  - `mb2026` (B3 §2) replies with an information-based test: valence informs more about behaviour than about the world.
- **Asymbolia.** `griffithkind2023` (C §2) argues the clinical record does not show asymbolia is pain. `duvalklein2025` (C §3) replies that the real question is taxonomic.
- **Human and animal dissociations.**
  - `singh2020` (E2 §2): a rat S1→ACC pathway regulates place aversion.
  - `stankewitz2023` (E2 §3): cortex tracks unpleasantness slightly more than intensity, as a graded difference.
  - `zidda2024` (E2 §4): emotional primes shift unpleasantness.
  - `lee2024` (H §1): signed valence and unsigned affective intensity, decoded for pain and pleasure.
  - `flury2025` (H §2): reward improves avoidance without changing ratings, with the authors declining a differential claim.
- **Computational and avoidance.** `gandhi2021` (G2 §5), `jepma2022` (G2 §6) and `le2024` (G2 §7). Jepma and Le disagree on the direction of learning asymmetry.
- **Circuits and action cortex.**
  - `lee2022` (G1 §4): an ACC→PAG pathway shifts reflex and avoidance together.
  - `perini2020` (I §8) and `koppel2022` (I §9) extend the action-dependence line.
  - `gordon2023` (I §10) redraws the motor map, with a pain link by citation only.

**Where the era stands.** Philosophers argue over how to read reward, decision and learning models. Neuroscientists report graded rather than clean dissociations. The asymbolia exchange moved to classification. No reviewed paper yet combines ratings of one's own unpleasantness with avoidance on the same trials.

---

## 3. Debates

Statuses use a fixed scale: settled / leaning / open / stalled / not yet tested. The full position lists with keys are in `positions.csv`.

### 3.1 How many components does pain have, and can they be moved separately? — **open**

**In plain words.** Are "how strong" and "how bad" two separate parts of pain, or two descriptions of one experience?

**Positions.**
- *Separable and serial.* Intensity causes unpleasantness, which feeds secondary suffering; the ACC tracks unpleasantness (`price2000`, D §2; `rainville1997`, E1 §1).
- *Distinct lateral and medial systems.* `kulkarni2005` (E1 §4) and `zidda2024` (E2 §4) claim a separation. `tiemann2014` (E1 §5) finds affect-only effects. `craig2003` (F §2) assigns sensation to insula and drive to ACC.
- *Relative specialisation or graded difference.*
  - `hofbauer2001` (E1 §2): against a simple dichotomy.
  - `zubieta2001` (E1 §3): regions overlap.
  - `stankewitz2023` (E2 §3): "we can not assume distinct processes".
  - `singh2020` (E2 §2): the streams integrate.
- *Unitary lean.* `talbot2019` (D §4): "pain is a unitary unpleasant and sensory experience".
- *Recast axis.* Pain shares signed valence and unsigned intensity codes with pleasure (`lee2024`, H §1; `leknestracey2008`, D §3).

**Key exchanges, in order.**
1. Rainville 1997 moves unpleasantness.
2. Hofbauer 2001 attempts the mirror image and finds unpleasantness moves with intensity.
3. Price 2000 reads the asymmetry as seriality.
4. Kulkarni 2005 criticises hypnosis as a tool and uses attention instead.
5. Talbot 2019 reads the same kind of asymmetry as the sensory rating being non-modifiable, adding bias and demand caveats (D cross-paper note 2).
6. Stankewitz 2023 avoids manipulation altogether and reports a graded difference.

**Evidence each side leans on.** Separation: rating dissociations plus region-specific neural changes (E1 batch note 2), lesion and asymbolia cases (D §2). Unitary lean: the risk of bias across all 12 reviewed studies, small effects (3–4.4 points per 100 for external stimuli), and untrained raters not separating the dimensions (D §4).

**Status now: open.** The same one-directional pattern (unpleasantness moves, intensity does not significantly move) is read as seriality by `price2000` and as near-unitary by `talbot2019`. The 2023–2024 studies describe graded differences. No primary study reviewed in E1–E2 moves intensity while leaving unpleasantness fixed (E2 §5); in Talbot's review only two very-high-bias studies claimed to (D §4).

### 3.2 What is the non-sensory component: evaluation, command, desire, or something else? — **open**

**In plain words.** When pain feels bad, is that feeling a *command* ("stop this", "less of me"), a *perception that something is bad*, a *desire*, or something else?

**Positions.**
- *Body-protection imperativism.* `klein2007` (A §1), `klein2015` (B2 §2), `mk2016` (B2 §3), `km2018` (B2 §6).
- *Imperativism about a bodily state.* `martinez2011` (B1 §1), `martinez2015` (B2 §1).
- *Reflexive imperativism, "less of me!".* `bh2019` (A §3), `loopy2019` (B2 §8), `barlassina2020` (A §4), `barlassina_reflection` (B3 §3).
- *Relational imperativism.* `kauppinen2021` (B3 §1).
- *Any imperativism beats evaluativism.* `mb2026` (B3 §2) is deliberately neutral between the imperativist variants.
- *Evaluativism about bodily badness.* `cuttertye2011` (B1 §2), `bain2013` (B1 §3), `bain2017` (B2 §4), `bain2019` (B2 §7).
- *Evaluativism about adaptive value, for all affect.* `carruthers2018` (A §2), `carruthers2023` (A §5).
- *Evaluative representation cannot be the whole story.* `jacobson2013` (B1 §4) hints at a desire-like view. Desire theories themselves are held by authors outside the corpus and are known here only through `bain2013` and `bain2019`.

**Key exchanges, in order.**
1. Martínez 2011 against Klein 2007's action commands (B1 §1).
2. Cutter & Tye 2011 against both on intensity and polarity (B1 §2), answered by Klein & Martínez 2018 (B2 §6) and later by Kauppinen 2021's opportunity-cost account (B3 §1).
3. Bain 2013 on reasons (B1 §3), answered by Martínez 2015 (B2 §1).
4. Martínez & Klein 2016 against evaluativism as "guise of the good" (B2 §3).
5. Barlassina & Hayward 2019 against first-order and higher-order imperativism, and first-order evaluativism (A §3).
6. Barlassina 2020 against Carruthers 2018 (A §4).
7. Carruthers 2023's reply (A §5). Several of Barlassina 2020's points go unanswered there: identity fusion, evolution as a tinkerer, projection bias, the exclusion problem (A §6 reply ledger).
8. Martínez & Barlassina 2026's reply, which in turn leaves Carruthers's attention argument, hedonism charge and multiple-appraisal replies unaddressed (B3 §2).

**Evidence each side leans on.**
- *Imperativists.* Objectless moods; desensitised experts; rat liking/wanting dissociations (B2 §8); the Ploner lesion patient (A §3); thermal pleasantness that depends on body state (B3 §2).
- *Evaluativists.* Value networks, prediction-error learning and neuroeconomic models; the claim that valence sits in value areas rather than motor areas; attention being drawn toward horrible scenes (A §5).
- **Shared ground.** All of this evidence is cited second-hand. None of these papers collects data (B2 cross-paper notes).

**Status now: open.** The latest exchange (`mb2026` replying to `carruthers2023`) has no counter-reply in the corpus. The imperativists are divided among themselves on whether the command targets the world or the experience (B3 §4).

### 3.3 Why take painkillers? The direction of pain's motivation — **open**

**In plain words.** A painkiller removes the feeling but not the injury. Does pain's badness itself push us to get rid of the *feeling*, or only to protect the *body*?

**Positions.**
- *Commands cannot explain it* (`bain2013`; B1 §3).
- *Evaluations cannot explain it*, "killing the messenger" (`jacobson2013`; B1 §4).
- *Extrinsic spam avoidance* (`martinez2015`; B2 §1).
- *Two routes.* The experience motivates body care, and separate desires motivate relief (`bain2017`, B2 §4; `bain2019`, B2 §7).
- *Relief-seeking is intrinsic*, and body care is derived from it (`loopy2019`, B2 §8; `bh2019`, A §3; `barlassina_reflection`, B3 §3).
- *No reflexive motivation.* A separate displeasure explains painkillers (`kauppinen2021`; B3 §1).
- *Hedonism charge.* Experience-directed views would make every choice aim at one's own experiences (`carruthers2023`, A §5; building on `carruthers2018`, A §2).

**Key exchanges, in order.** Bain 2013 → Jacobson 2013 (same year, independent; Jacobson does not cite Bain; B1 §4) → Martínez 2015 → Bain 2019 → Loopy Regulations 2019, which calls the spam account "utterly unbelievable" (B2 §8) → Kauppinen 2021 → Carruthers 2023.

**Evidence each side leans on.** Mostly cases and thought experiments: phantom-limb pain, allodynia, morphine and lobotomy reports, habanero peppers, alarm fatigue (B1 §3–§4; B2 §1, §7, §8).

**Status now: open.** Four rival accounts persist and `carruthers2023` presses a hedonism charge against the experience-directed one. No side concedes in the corpus.

### 3.4 Is asymbolic pain pain, and what does it show? — **stalled**

**In plain words.** Some brain-lesion patients say a pinprick hurts yet smile and offer another hand. Are they in pain without the bad part, and does that prove pain has separable parts?

**Positions.**
- *Pain without painfulness.* The standard reading comes from Grahek 2007 (not in corpus). Within the corpus it is assumed by `bain2013` (B1 §3), used as lesion evidence by `price2000` (D §2), and modelled as sensation-without-command by `bh2019` (A §3).
- *Lost capacity to care about the body* (`klein2015asym`; C §1).
- *Command or evaluation without authority.* Without concern for the body, pain is not unpleasant (`kauppinen2021`, B3 §1; `bain2017`, B2 §4).
- *Not shown to be pain; set aside* (`griffithkind2023`; C §2).
- *Probably still pain; how to classify it is the real question* (`duvalklein2025`; C §3).

**Key exchanges, in order.**
1. Klein 2015 against Grahek's reading (C §1), revising his own 2007 negative commands into protective commands (C §1 fn. 12).
2. Griffith & Kind 2023 against the standard reading and against Klein, arguing it is incoherent under essentialism (C §2).
3. Duval & Klein 2025 in reply, treating pain as a cluster kind and moving the dispute to taxonomy (C §3).

**Evidence each side leans on.** The same handful of case reports from 1928–1988, all cited second-hand. The Berthier 1988 threshold data are read as normal by the standard reading and as 25% higher by Griffith & Kind (C §2). All three papers agree the "affect without sensation" half (Ploner 1999) is weak (C §4).

**Status now: stalled.** The philosophical exchange was active in 2023–2025, but all three papers agree the clinical record is small, old and confounded by aphasia (C §4), and no clinical data newer than Ploner 1999 enter the corpus.

### 3.5 Is felt unpleasantness separable from avoidance and motivation? — **open**

**In plain words.** Is how bad pain feels the same thing as the urge to get away from it? Can you change one without the other?

**Positions.**
- *Escape desire accompanies unpleasantness, with no separate dimension* (`price2000`, D §2). `talbot2019` explicitly equates unpleasantness with "the aspect that makes us want to take protective action" (D §4).
- *Avoidance is the readout of affect.* Animal work infers unpleasantness from avoidance and never measures it independently (`johansen2001`, `johansen2004`, `corder2019`, G1 §5 note 2; `singh2020`, E2 §2).
- *Hard to disentangle.* `leknestracey2008` (D §3). In `cuttertye2011`, represented badness is carried by a state defined by its avoidance role (B1 §2).
- *Behaviour moves while ratings do not* (`claes2015`, F §5; `flury2025`, H §2; `becker2018`, G2 §3).
- *Behaviour, not report, is the ultimate measure* (`seymour2019`; G2 §4).
- *Liking and wanting come apart.* Both philosophical camps accept these dissociations and disagree on what they show (`loopy2019`, B2 §8; `barlassina_reflection`, B3 §3; `carruthers2023`, A §5).
- *The urge to withdraw tracks insula–cingulate coupling* (`perini2013`, I §2; `perini2020`, I §8).

**Key exchanges, in order.**
1. Johansen 2001 already allows that unpleasantness and aversion learning may "not [be] separable at the neural level" (G1 §1).
2. Leknes & Tracey 2008 name the problem (D §3).
3. Claes 2015 separates choice from ratings (F §5).
4. Carruthers 2023 and Loopy 2019 read liking/wanting dissociations in opposite theoretical directions (A §5; B2 §8).
5. Lee 2022's pathway manipulation moves reflex *and* avoidance together, unlike 2001–2019 (G1 §5 note 3).
6. Flury 2025 replicates behaviour-without-ratings but declines a differential conclusion (H §2).

**Evidence each side leans on.**
- *Fused.* Correlated ratings and correlated measures. For example, urge and intensity slopes correlate at r = 0.53–0.83 (I §2).
- *Separable.* Choice rose with a reward effect size of η²_G = .557 while ratings did not change (F §5). Rodent manipulations spared reflexes (G1 §5).

**Status now: open.** Behaviour moved without ratings in `claes2015` and `flury2025`, but the ratings came from different phases or sparse probe trials on mild stimuli. No reviewed study rates a person's own unpleasantness and their avoidance on the same trials (§5).

### 3.6 Where does pain meet action in cortex? — **open**

**In plain words.** When pain lights up the cingulate cortex, is that the feeling of badness, general self-control, or the brain getting ready to move?

**Positions.**
- *Seat of unpleasantness or drive.* `rainville1997` (E1 §1), `price2000` (D §2), `johansen2001` (G1 §1), `craig2003` (F §2).
- *Adaptive-control integration.* `shackman2011` (I §1), `misra2014` (I §3), `tolomeo2016` (I §6).
- *Action dependence.*
  - `perini2013` and `perini2020` (I §2, §8).
  - `koppel2022` (I §9).
  - `lee2022` (G1 §4): the ACC's downstream targets relate to sensorimotor integration rather than sensory discrimination, although the paper also says the ACC "encodes the unpleasantness of pain".
- *Observed pain: meaning and vigour* (`budell2015`, I §4; `han2017`, I §7).
- *Effector-specific action maps, not pain studies* (`procyk2014`, I §5; `gordon2023`, I §10).

**Key exchanges, in order.** Shackman 2011 is cited by seven of the other nine Part I papers (I batch note 1). Perini 2013 introduces action dependence. Perini 2020 extends it to people with fewer pain fibres. Koppel 2022's preregistered action tests were null, and its support for action dependence comes from exploratory contrasts (I §9).

**Evidence each side leans on.** Co-activation and meta-analysis for integration; press/no-press designs for action dependence; lesions for affect (`johansen2001`, rats). In humans the only lesion study did not measure pain (`tolomeo2016`).

**Status now: open.** Batch I reports that the integration and action-dependence readings "are not mutually exclusive, and no paper here adjudicates" (I batch note 2). Causal human evidence on pain is absent from the batch (I batch note 5). "ACC" also names different subregions across studies (§5).

### 3.7 Is pain a learning signal, and how is learning from pain structured? — **leaning** (on whether), **open** (on how)

**In plain words.** Does pain work mainly to teach you what to avoid next time? And do people learn more from pain that happened or pain they escaped?

**Positions.**
- *ACC aversive teaching signal* (`johansen2004`; G1 §2).
- *Pain as reinforcement and control signal* (`seymour2019`, G2 §4; `wiech2013`, G2 §1).
- *Planning and habit arbitration* (`wang2018`; G2 §2).
- *Learn more from received pain* (`jepma2022`; G2 §6).
- *Learn more from avoided pain* (`le2024`; G2 §7).
- *Learning is describable as value updating* (`carruthers2023`; A §5).
- *Learning supports a command reading.* The evolutionary function of affect is reward and punishment for trial-and-error learning (`bh2019`, A §3), and learning models favour imperative content (`mb2026`, B3 §2).
- *Avoidance vigour adapts to failure* (`gandhi2021`; G2 §5).

**Key exchanges, in order.**
1. Wiech & Tracey 2013 names RL tools as the way forward (G2 §1).
2. Seymour 2019 cites Wang 2018 for hand-off between controllers (G2 §4).
3. Carruthers 2023 argues learning needs no commands, and Martínez & Barlassina 2026 read the same learning models as imperatival (B3 §2).
4. Le 2024 cites Jepma 2022 only for midcingulate involvement and does not discuss the opposite asymmetry (G2 §7).

**Status now.** *Leaning*, on whether: every reviewed paper that addresses the question treats pain as a teaching signal, across animal, computational and philosophical communities. *Open*, on how: learning asymmetry conflicts between `jepma2022` and `le2024` (G2 §8 note 2), and whether the learning signal is best described as value or as command is disputed (A §5; B3 §2).

### 3.8 What drives pain-related avoidance and disability: fear, pain itself, or competing goals? — **leaning**

**In plain words.** Do people with chronic pain avoid activity because they are afraid, because pain itself is threatening, or because avoiding pain crowds out their other goals?

**Positions.**
- *Fear* (`vlaeyen2000`; F §1).
- *Intense pain is itself threatening* (`leeuw2006`; F §3).
- *Goal competition* (`crombez2012`, F §4; `claes2015`, F §5; `vlaeyen2016`, F §6; `becker2018`, G2 §3).
- *Homeostatic drive* (`craig2003`; F §2).
- *Learned decision.* `seymour2019` and `wiech2013` (G2 §4, §1); `gandhi2021` finds avoidance vigour falls after failure and helplessness (G2 §5).
- *Active-defence circuit, stated as speculation* (`lee2022`; G1 §4).

**Key exchanges, in order.** Vlaeyen & Linton 2000 → Leeuw 2006 (intensity matters; causality untested) → Crombez 2012 (goals) → Claes 2015 (lab test) → Vlaeyen 2016 (goal-priority fork in the model's diagram). F connections describe this as one research programme with changing diagrams.

**Status now: leaning.** The model's own originators moved from a fear-driven to a goal-competition framing (`crombez2012`, `vlaeyen2016`). Causal tests remain few: `leeuw2006` notes components had not been manipulated, and `claes2015` is one healthy-student experiment with self-selected goal groups.

---

## 4. How the communities relate

Citation links below come only from what the reviews record (`edges.csv`, 182 documented engagements). A missing link means none was recorded among the 65 reviewed papers. It does not mean none exists in the wider literature.

**Dense within, thin between.** Of the 182 recorded engagements, 69 are philosophy citing philosophy and 36 are human neuroscience citing human neuroscience. Philosophy is the most self-contained community: its outgoing engagements with other communities are 8 to named-only clinical case reports (Ploner 1999, Berthier 1988), 1 to `craig2003` and 1 to `price2000`, both from `klein2015asym` (C §1). **No engagement from any non-philosophy paper to a philosophy paper is recorded.** The nearest things are indirect:
- Corder 2019 cites Grahek's 2007 philosophy book, which is not in the corpus (G1 §3).
- Wiech & Tracey 2013 call pain "imperative" in passing, with no reference to philosophical imperativism (G2 §1, §8 note 7).
- Perini 2013 describes the action component as "an imperative desire to escape", also without a philosophical citation (I §2).

**Computational modelling and philosophy do not meet.** "No G2 paper engages that literature" (G2 §8 note 7). Going the other way, the philosophy papers argue about learning and decision science through models outside the corpus (Schultz; Juechems & Summerfield; Rangel; B3 §2; A §5). They cite none of `wang2018`, `seymour2019`, `jepma2022` or `le2024`.

**Craig 2003 sits apart from fear-avoidance.** Craig cites none of the fear-avoidance literature, and none of the five fear-avoidance papers cites him (F connections). He is picked up instead by `leknestracey2008` (D §3), `seymour2019` (G2 §4) and `klein2015asym` (C §1).

**Bridges that do exist.**
- *Clinical psychology → animal circuits.* `lee2022` motivates its mouse work with the fear-avoidance model (`vlaeyen2016`; G1 §4).
- *Clinical psychology ↔ computational.* `seymour2019` cites `vlaeyen2000`, `wiech2013` cites `vlaeyen2000`, and `flury2025` cites `seymour2019`.
- *Animal and human work in one review.* `becker2018` joins goal-regulation models with rodent relief-reward studies (G2 §3).
- *Human imaging → animal circuits.* `rainville1997` is the shared anchor: Johansen 2001/2004, Singh 2020 and Han 2017 all cite it.

**Internal chains worth knowing.**
- The Montreal hypnosis studies (`rainville1997` → `hofbauer2001`) are critiqued by `kulkarni2005` and `stankewitz2023`, and used as evidence by `price2000` and `talbot2019`.
- In animal circuits, Johansen 2001 → Johansen & Fields 2004 → Lee 2022. `corder2019` cites neither Johansen paper; its lineage is amygdala valence coding (G1 §5 note 1).
- In action cortex, `shackman2011` is the hub.
- In philosophy, the exchange is not a clean chain. `carruthers2018` does not mention imperativism, and `bh2019` attacks Martínez and Klein 2015 rather than Klein 2007 (A §6).

**What is corpus-limited.**
1. The corpus was seeded from one survey. Its 89 references are a selection, not a census.
2. 24 of them are named-only, so their own citations are invisible.
3. Engagement is recorded only where a reviewer noted it. For short-tier entries this is mostly the "responds to / builds on" list.
4. `gordon2023`, `gandhi2021`, `tumulty2009`, `vogt1992`, `bolles1980`, `vase2003`, `vase2005`, `raja2020` and `nickel2017` have no recorded engagement with other manifest works. That is a gap in the corpus, not evidence of isolation.

---

## 5. What the evidence does and does not show

### 5.1 Consistent findings

| Finding | Where it recurs | Qualification |
|---|---|---|
| Manipulations shift unpleasantness more readily than intensity | Hypnotic suggestion (`rainville1997`, E1 §1); dopamine depletion (`tiemann2014`, E1 §5); emotional primes (`zidda2024`, E2 §4); 4 of 5 hypnosis studies (`talbot2019`, D §4); opioid in breathlessness (`hayen2017`, E2 §1) | Intensity nulls are non-significant, not shown to be equivalent. Talbot rates every included study at high or unclear risk of bias (D §4; E2 §5 note 2) |
| No primary study in E1–E2 moves intensity alone | Intensity suggestions also moved unpleasantness (`hofbauer2001`, E1 §2); `talbot2019` concludes intensity "cannot be selectively modulated" (D §4) | In Talbot's 12 studies, two at very high risk of bias (Dahlgren 1995, Kunz 2012) did claim selective intensity change (D §4) |
| The two ratings are tightly coupled | r = 0.81 (`hofbauer2001`); r = 0.59 for drug-induced changes (`hayen2017`); r = 0.86 across trials (`stankewitz2023`) | Coupling measured in different ways |
| Rodent manipulations reduce learned or ongoing avoidance while sparing reflex-like measures | `johansen2001`, `johansen2004`, `corder2019` (G1 §5 note 3) | Not uniform: `lee2022`'s pathway moved reflex and avoidance together |
| Behaviour can change without ratings changing | Reward raised choice of a painful movement (`claes2015`, F §5) and avoidance performance (`flury2025`, H §2) | Cross-phase and probe-trial ratings; mild stimuli; task-compliance confound |
| Midcingulate "pain" responses depend on action | `perini2013`, `perini2020`, exploratory `koppel2022` (I §2, §8, §9) | Correlational fMRI; Koppel's preregistered action tests were null |
| Pain-avoidance choices fit reinforcement-learning models | `wang2018`, `jepma2022`, `le2024` (G2) | Direction of learning asymmetry conflicts |

### 5.2 Findings that rest on weaker ground

- **One-directional.** Every human dissociation in E1–E2 moves unpleasantness, never intensity alone (E2 §5 note 2).
- **Small samples.**
  - `rainville1997`: N = 8, selected for suggestibility *and* for already showing the effect.
  - `hofbauer2001`: N = 10.
  - `wang2018`: N = 15, compared against another lab's reward data.
  - `perini2020`: 12 per group, fixed-effects model.
  - `gandhi2021`: helplessness effects rest on n = 15.
  - `tolomeo2016`: 12 and 8 surgical patients.
  - (E1 §1–§2; G2 §2, §5; I §6, §8.)
- **Correlational, not manipulated.** `zubieta2001` (between-person), `stankewitz2023` (within-trial), `lee2024` (decoding), `le2024` (individual differences). `jepma2022`'s drug effects appear only in model parameters (G2 §6).
- **One rating or one borderline test.** `tiemann2014`'s affect effect is one post-task rating at p = .048 (E1 §5). `kulkarni2005`'s S1 effect is P = 0.05 corrected (E1 §4).
- **Not pain, or not one's own pain.**
  - `hayen2017`: breathlessness.
  - `procyk2014`: juice reward.
  - `tolomeo2016`: facial-emotion recognition and Stroop.
  - `lee2024`: oral capsaicin paired with chocolate.
  - `budell2015` and `han2017`: *observed* pain.
  - The philosophers' empirical anchors: `mb2026` uses thermal pleasantness; `loopy2019` and `barlassina_reflection` use rat salt taste.
- **Manuscript or partial versions.**
  - Accepted or author manuscripts: `gandhi2021`, `le2024`, `claes2015`, `crombez2012`, `vlaeyen2016` (a draft figure), `mk2016`, `km2018` (an early c. 2014 draft), `bain2017`, `bainreview2017`, `bain2019`, `kauppinen2021`, `carruthers2023`, `klein2007`, `barlassina_reflection`.
  - `klein2015` is a 12-page preview.
  - Supplements are absent for `corder2019`, `lee2022`, `singh2020`, `lee2024` and `flury2025`.
- **Reporting inconsistencies flagged by reviewers.**
  - `tiemann2014`: p-values.
  - `kulkarni2005`: hemisphere label and threshold.
  - `claes2015`: t/p mismatch.
  - `tolomeo2016`: r > 1 and a Results/Discussion contradiction.
  - `flury2025`: a confidence interval that excludes its own odds ratio.
  - `zidda2024`: time windows.
  - `talbot2019`: screening counts.
  - `le2024`: sign of the Pavlovian factor.
- **Philosophical empirical claims are second-hand.** None of the philosophy papers collects data (B2 cross-paper notes). The information criteria of `mb2026` are applied qualitatively, with no quantities computed (B3 §2).

### 5.3 Recurring measurement gaps

Each gap below is scoped to the reviewed papers.

| Gap | Scope and grounding |
|---|---|
| No study rates a person's own pain unpleasantness alongside their avoidance on the same trials | Not found in these 65 reviewed papers. Closest: `claes2015` (ratings and choices in different phases), `flury2025` (probe-trial ratings). G2 has no ratings during avoidance (G2 §8 note 4). I has no own-pain unpleasantness (I batch note 4) |
| No rating of desire or urge for relief next to unpleasantness | Not found in these 65 reviewed papers. `perini2013` and `perini2020` rate "urge to move" but not unpleasantness; `han2017`'s "willingness to help" is not an urge to escape. Vase 2003 names desire but was not reviewed (H §3) |
| Intensity always rated before unpleasantness | `stankewitz2023` and `zidda2024`; order not stated in `hayen2017`. None discusses order effects (E2 §5 note 4) |
| No equivalence tests for intensity nulls | None of the E2 papers reports one (E2 §5 note 2) |
| "ACC" names different subregions | Rostral/perigenual rat ACC vs mouse area 24 (G1 §5 note 5); pACC vs aMCC vs pMCC across human studies (E1 batch note 4); the concordance table in I |
| Animal "unpleasantness" is never measured independently of avoidance or protective behaviour | Across the four G1 papers (G1 §5 note 2) and `singh2020` (E2 §2) |
| Sensory side not measured under the circuit manipulation | `singh2020` (E2 §2); `johansen2001` measured no thresholds (G1 §1) |
| No new clinical asymbolia data | The three Part C papers rely on 1928–1988 case reports (C §4) |
| Pain rated on one merged "painful/unpleasant" scale | `gandhi2021` (G2 §5) |

---

## 6. Corrections to the seed survey

The corpus was seeded by a survey written in another session for a specific study design. It is not a source. Reviewers checked each survey claim against the paper. The full table (47 rows) is `survey_corrections.csv`. Counts: holds 22, partly 19, does-not-hold 3, misattributed 2, not applicable 1.

The rows below are the ones that change how a paper should be cited.

| Paper | Survey claim | What the reviewed paper shows | Verdict |
|---|---|---|---|
| `bainreview2017` (B2 §5) | Evaluativism predicts a valenced judgement that causes motivation but is not itself motivational | The review never discusses evaluativism. Bain's 2017 chapter says the unpleasant experience is "itself motivational" (B2 §4) | does-not-hold |
| `gandhi2021` (G2 §5) | Human pain-avoidance behaviour has neural correlates distinct from pain report | No comparison with pain report; pain rated only for calibration. The actual claim is parietal rather than PAG involvement | does-not-hold |
| `budell2015` (I §4) | Facial pain expressions drive motor mirroring in MCC | Reverses the paper's conclusion: pain responses appeared with attention to meaning, and affective-meaning networks are favoured | does-not-hold |
| `hayen2017` (E2 §1) | Opioids lower unpleasantness, not intensity (as pain evidence) | The sensation was experimentally induced breathlessness | misattributed |
| `tolomeo2016` (I §6) | Causal cingulotomy evidence (for pain and action) | Lesions predicted facial-emotion and Stroop errors in depression; pain never measured | misattributed |
| `lee2022` (G1 §4) | ACC→PAG projections are *required* for pain avoidance; a command line, not evaluative | Only activation was tested in the avoidance task. The command/evaluation contrast is not the paper's, and it says the ACC encodes unpleasantness | partly |
| `flury2025` (H §2) | Cleanest demonstration that avoidance is separate from both ratings (N = 62) | 58 analysed. The authors say the pattern "does not allow us to conclude" differential modulation, and note a task-compliance confound | partly |
| `price2000` (D §2) | Affective and motivational used interchangeably | "Motivational" never appears. The explicit fusion is in `talbot2019`, which attributes the label to Price (D §4) | partly |
| `talbot2019` (D §4) | Not independently modifiable; dissociations mostly attention effects | Verdict is asymmetric (unpleasantness might be modifiable). The explanations offered are demand, wording and bias, not attention | partly |
| `seymour2019` (G2 §4) | Pain is a *precision-weighted* RL control signal | "Precision" means precise and objectifiable; "precision-weighted" never appears | partly |
| `singh2020` (E2 §2) | In mice, S1→ACC … | Rats | partly |
| `stankewitz2023` (E2 §3) | Unnamed "7T/EEG" result | 7T fMRI only; the authors call the difference gradual | partly |
| `hofbauer2001` (E1 §2) | The reverse suggestion moves S1 | S1 moved, but unpleasantness moved too, and the authors reject a simple dichotomy | partly |
| `johansen2001` (G1 §1) | ACC lesions abolish avoidance without changing thresholds | Rostral ACC only; thresholds not measured | partly |
| `perini2013` (I §2) | Midcingulate activity to pain scales with action | Action *dependence*, not graded scaling | partly |
| `griffithkind2023` (C §2) | Asymbolia isn't pain at all | Title claim; the body argues only that the evidence fails to show it is pain | partly |
| `martinez2015` (B2 §1) | Command "protect this body part / stop this" | Command targets bodily damage, not the pain; "protect this body part" is Klein's wording | partly |
| Fear-avoidance papers (F §1, §3, §4, §6) | "Four iterations" of the model | None of the papers counts iterations; it is one programme with changing diagrams | partly |

**Attribution slips inside the reviewed papers themselves.** These are provenance, not survey errors.
- `carruthers2023` credits four points to "Loopy Regulations". Three are there. The affective-forecasting point is in `bh2019` and `barlassina2020` (B2 §8 attribution check).
- `talbot2019` attributes the "affective-motivational" label to `price2000`. It also cites a 1992 psychophysics paper for the 1997 ACC hypnosis finding (D §4).
- `griffithkind2023` likely attributes Klein's book schema "Keep B from E (with priority P)!" to the *Mind* paper (C §2, unverified).
- `duvalklein2025` cites Berthier et al. as "1998" in text (C §3).
- Bain describes Klein's view of unpleasantness in two different ways in 2017: as an evaluation (chapter) and as a self-command (review) (B2 cross-paper notes).
- The "Nickel et al. 2017" that `stankewitz2023` cites is a different paper from the named-only `nickel2017` (E2 §5 note 6).

---

## 7. Current status in one page

| Debate | Status (2026) | Why, in one line | What the field itself says is open |
|---|---|---|---|
| How many components; can they be moved separately? | open | Same asymmetry read as seriality or near-unitary; recent studies call differences graded | Talbot et al. call for methods that exclude demand effects (D §4); "we can not assume distinct processes" (`stankewitz2023`, E2 §3) |
| Evaluation, command or something else? | open | `mb2026`'s reply to `carruthers2023` unanswered in corpus; imperativists split | Barlassina concedes valence's evolutionary function is unexplained (B3 §3); no metasemantics for evaluative states proposed (`mb2026`, B3 §2) |
| Why take painkillers? | open | Four rival accounts plus a hedonism charge | Martínez calls the spam mechanism "to a large extent an empirical matter" (B2 §1) |
| Is asymbolic pain pain? | stalled | No clinical data newer than 1999 in corpus; dispute moved to taxonomy | Griffith & Kind call for more clinical research (C §2); taxonomy unsettled (C §3) |
| Unpleasantness vs avoidance | open | Behaviour moved without ratings, but never measured on the same trials | Flury et al. note behaviour and self-report often diverge and that the design "did not target generalisation" (H §2) |
| Where pain meets action in cortex | open | Integration and action-dependence readings coexist | Shackman: monitor vs controller unresolved (I §1); Koppel: cingulate not action-selective at whole-brain threshold (I §9) |
| Pain as a learning signal | leaning (whether) / open (how) | Broad agreement it teaches; conflicting asymmetry; value vs command readings | Jepma et al. offer task framing among explanations of their asymmetry (G2 §6); Seymour's Box 1 predictions have mixed or no behavioural support yet (G2 §4) |
| What drives avoidance | leaning | Originators moved to goal competition; few causal tests | Leeuw: causality "can only be established when each construct is experimentally manipulated" (F §3) |

---

## 8. Relevance to this project (interpretive)

> **Interpretive, not a finding.** Nothing in the corpus shows that an artificial agent has pain or valence. The agent's internal damage signal is **nociception**. Experiment ideas are out of scope here and belong to **`research-postdoc`** (triage) and **`professor-pain-modeling`** (whether a construct is valid enough to support "pain-like" claims).

This project trains reinforcement-learning agents with a nociception signal and studies behaviour that looks pain-like, such as hypervigilance after injury. Four points from the field's history bear on how such behaviour can be described.

1. **The field's own measurement gap is the project's interpretive risk.** Humans report feelings and animals only behave, and the corpus shows how often "unpleasantness" in animals is simply avoidance under another name (G1 §5 note 2). An agent resembles the animal case. Behaviour alone cannot separate a command reading, a value reading, or a plain learned avoidance (A §7; A §5 on re-describing learning).
2. **Dissociations are where theories come apart.** The contrasts the literature argues over are signal without concern (asymbolia), lowering the signal rather than repairing the damage (painkillers), avoidance changing without the internal signal changing (`claes2015`, `flury2025`), and reflex vs learned avoidance (G1).
3. **Learning asymmetry is contested in humans** (`jepma2022` vs `le2024`), so no single human benchmark exists for learning from damage received vs damage avoided.
4. **Seymour 2019 argues behaviour should be the measure of pain.** That is itself a position in an open debate, not a settled method.

---

## 9. Data files for diagrams

All in `field_history_data/`, UTF-8 CSV with a header row, using manifest keys throughout. They were generated from one transcription of the reviews and validated against the manifest: all 89 keys present, no extra keys, every debate id and position key cross-checked.

| File | Rows | Contents |
|---|---|---|
| `works.csv` | 89 | Every manifest key: label, plot year, print year, community, era, status, one-line role, debates |
| `eras.csv` | 5 | Era id, label, start and end year, summary |
| `debates.csv` | 8 | Debate id, title, plain question, status, reason, first and latest year of positioned works |
| `positions.csv` | 51 | Positions per debate with keys and one-line summary |
| `edges.csv` | 182 | Documented engagements (builds-on / critiques / replies-to / reinterprets / uses-as-evidence) with review section |
| `dissociation_evidence.csv` | 25 | Empirical reviewed papers measuring two or more outcomes; each outcome coded changed / unchanged / not-measured / correlational |
| `dimension_models.csv` | 23 | How the number and kind of pain components was modelled over time |
| `survey_corrections.csv` | 47 | Survey claim, what the paper shows, verdict |

Notes for the page builder are in [§10](#10-scope-and-provenance).

---

## 10. Scope and provenance

- **Counts** (from `references_manifest.csv`): 89 references. 46 reviewed in full, 19 reviewed as short summaries, 24 named-only.
- **Part A records.** Part A predates the field-history record block. Its five records (year, community, question, position, engagements) were derived here from its entries and its §6 cross-paper map.
- **Ambiguous years.** In each case below, `works.csv` gives the first public year in `year` and the print year in `year_print`.

  | Key | year | year_print | Why |
  |---|---|---|---|
  | `loopy2019` | 2019 | 2020 | Volume dated 2019, printer's stamp 9/30/20 (B2 §8) |
  | `gandhi2021` | 2022 | 2022 | Manifest key and filename say 2021; the accepted-manuscript cover sheet says 2022 (G2 §5). An earlier online date is possible but not recorded |
  | `barlassina_reflection` | 2020 | unknown | Year inferred from the text (B3 §3) |
  | `km2018` | 2018 | 2018 | Written c. 2014 (B2 §6) |
  | `mb2026` | 2026 | 2026 | Accepted 2023 (B3 §2) |
  | `carruthers2018`, `bain2019` | 2017 | print year | Online 2017 |
  | `martinez2011`, `bain2013`, `martinez2015` | online a year before print | print year | |
  | `griffithkind2023`, `duvalklein2025`, `flury2025` | online year | volume year the following year | |
  | `leeuw2006` | 2006 | 2007 | |
  | `misra2014`, `procyk2014` | 2014 | 2015, 2016 | |

- **Communities for named-only works** were assigned only where a citing review describes the work's field. Seven are `unknown`: Wall 1979, Bolles & Fanselow 1980, Fields 2006, Auvray 2010, Raja 2020, Vase 2003, Vase 2005. `tolomeo2016`'s record says "neurosurgery-neurology", normalised here to `neurology-neurosurgery`.
- **Survey verdict recoding.** Verdicts follow the batch reviewers, with three changes. `budell2015` is coded does-not-hold because the survey reverses the paper's conclusion (the reviewer rated it partly). `hayen2017` and `tolomeo2016` are coded misattributed because the finding exists but concerns breathlessness or emotion recognition, not pain.
- **Excluded from `dissociation_evidence.csv`.** Reviews and theory (`price2000`, `talbot2019`, `seymour2019` and others). Papers with fewer than two of the listed outcomes: `wang2018` (avoidance only), `shackman2011`, `procyk2014`, `tolomeo2016`, `gordon2023`.
- **Edges exclude** the Tumulty 2009 / Klein 2010 exchange, because both endpoints are named-only.
