# The Non-Sensory Side of Pain — A Field-History Synthesis (corpus span 1962–2026)

**Topic folder:** `docs/project/references/imperativism/`
**Built from:** the per-paper reviews in Parts A–I (65 papers reviewed from PDF, 24 more known only by name), 2026-09-17.
**Curator:** literature-curator
**Web page:** [Pain Beyond Sensation](https://claude.ai/artifact/77YdiWcVTAg1iiqRHu9qrB) · **Master index:** [[imperativism_lit_review_INDEX]] · **Data for diagrams:** `field_history_data/` (9 CSV files; see [§9](#9-data-files-for-diagrams))

## What this document is about (plain-language entry point)

**The field.** Pain is more than a sensation of where and how strongly something hurts. It also *feels bad*, and it *pushes* you to act: pull away, protect the injury, take a painkiller. This synthesis traces how six communities have studied that second side of pain, from the corpus's earliest work (1962) onward: philosophers, brain-imaging researchers, animal circuit neuroscientists, clinical psychologists, neurologists and computational modellers.

**Why it exists.** These communities ask versions of the same questions but rarely read each other. This document puts their work on one timeline, names the cross-cutting debates, and records what the evidence can and cannot show. It is a history, not an argument for any theory.

**Where things stand in 2026.** Most debates are still open.
- Philosophers still disagree whether pain's badness is a *command* ("less of this!") or a *perception of value* ("this is bad for me").
- In small human studies, most rated at high or unclear risk of bias by a 2019 systematic review, manipulations shifted how unpleasant pain feels more easily than how strong it feels; the two ratings stay tightly linked.
- Two experiments (Claes 2015, Flury 2025) changed avoidance behaviour without changing pain ratings, though neither rated pain on the avoidance trials themselves.
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
- [10. Known works not held](#10-known-works-not-held)
- [11. Scope and provenance](#11-scope-and-provenance)
- [Feedback from professor-pain-modeling — 2026-09-17](#feedback-from-professor-pain-modeling--2026-09-17)
- [Revision log — literature-curator — 2026-09-17](#revision-log--literature-curator--2026-09-17)

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
- **Neutrality.** Positions are stated at their strongest as the reviews record them. Statuses describe the *reviewed corpus*, not the field; each debate carries a one-line corpus-limit note (`status_scope` in `debates.csv`).
- **Corpus balance.** The corpus was seeded by a survey that argued for one side of the philosophical debate. Among reviewed philosophy works, imperativist authors wrote 14 and evaluativist authors 7, and several evaluativist replies are not held ([§10](#10-known-works-not-held)).
- **Status scale** (used in §3, §7 and `debates.csv`):

  | Status | Meaning here |
  |---|---|
  | settled | Reviewed papers on all sides accept the claim; no live dispute is recorded. |
  | leaning | Reviewed papers converge in a direction that is always named, but dissent or missing causal tests remain. |
  | open | Substantive positions remain in dispute, and new evidence or argument is still entering the record. |
  | stalled | No new evidence has entered the record for a long period; the debate moves only by reinterpreting existing evidence. |
  | not yet tested (`untested`) | The question is posed, but no reviewed study measures what would decide it. |

---

## 1. Vocabulary

| Term | One-line meaning (as used in the reviews) |
|---|---|
| Sensory-discriminative | Where the pain is, what it is like, and how strong it is; in practice usually an intensity rating (D reading conventions). |
| Affective | How bad or unpleasant the pain feels; in practice usually an unpleasantness rating (D reading conventions). |
| Motivational | The drive to act: escape, avoid, protect (D reading conventions). |
| Affective-motivational | A compound label fusing the two previous terms. Melzack & Casey 1968 (not held) used the order "motivational-affective" (D §1); the reversed compound is later usage, made explicit as "unpleasantness … the motivational aspect" in `talbot2019` (D §4). |
| Nociception | The neural encoding of noxious stimuli, which is not the same as pain; the revised IASP definition (`raja2020`, named-only) keeps the two distinct. This project's agents have a nociception channel in this sense. |
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
| Avoidance vs escape | Avoidance prevents an aversive event; escape ends one under way (F, G2 reading conventions). |
| Reflex | A spinally organised withdrawal: paw flick, withdrawal latency, von Frey mechanical threshold. Used in animal work as the "sensory" contrast (G1 reading conventions). |
| Nocifensive behaviour | Supraspinally organised protective behaviour such as licking, guarding or lifting the injured paw. Papers disagree on its side of the line: `johansen2001`/`johansen2004` treat formalin licking and lifting as the spared *sensory-side* measure (G1 §1–§2), while `corder2019` counts attending and licking as *affective-motivational* (G1 §3). |
| Conditioned place avoidance (CPA) | An animal learns to avoid a chamber where it was hurt; the standard rodent readout of pain's affective side (G1, E2 reading conventions). |
| ACC / aMCC / MCC / pgACC | Anterior cingulate cortex; anterior midcingulate; midcingulate; pregenual ACC (Vogt's scheme). "Perigenual" (Kulkarni 2005; the rat rostral ACC of Johansen 2001) is broader, covering pregenual and subgenual cortex. The same labels cover different subregions across papers (I reading conventions; E1 batch note 4). |
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
| Pain's badness and pull on behaviour become explicit problems | 2007–2013 | 10 | 8 |
| Elaboration, formal models and the turn to valence | 2014–2019 | 25 | 1 |
| Revised IASP definition, all-affect valence and graded dissociations | 2020–2026 | 19 | 1 |

The first era is thin because only one of its works is held. Its content is known mostly through later citations.

**How the labels are weighted.** Each label names the era's most distinctive *new* question. Philosophy supplies 23 of the 65 reviewed papers and is new to the corpus in 2007, so the 2007–2013 and 2020–2026 labels lean philosophical even though most papers in those eras come from other communities. The 2020 boundary also coincides with the revised IASP definition of pain (`raja2020`, named-only).

### 2.1 Clinical dissociations and the gate (1962–1989)

**Live questions.** Is pain a fixed line from "pain receptor" to "pain centre"? Why do some surgical patients still report pain but say it no longer bothers them?

**Who asked.** Neurosurgeons and neurologists reporting cases; physiologists and psychologists building pain theory.

**Key works.**
- **Melzack & Wall 1965** (`melzackwall1965`; D §1) replaced the single-channel picture with a spinal *gate* modulated by descending brain control. It speaks of pain's "sensory and affective components" without proposing dimensions. It records lobotomised patients who "still have pain but it does not bother them". It quotes Sherrington's description of pain as the adjunct of "an imperative protective reflex", only to reject a reflex-only view. This is the earliest documented use of command vocabulary in the corpus; no reviewed paper links it to later philosophical imperativism.
- **Named-only anchors, known through citing papers:**
  - Foltz & White 1962 on cingulumotomy, cited as background by `rainville1997` (E1 §1) and `johansen2001` (G1 §1). No reviewed asymbolia paper discusses it (C, not reviewed).
  - Melzack & Casey 1968, cited throughout as the origin of the sensory-discriminative / motivational-affective / cognitive-evaluative split (D §1; G2 §4).
  - Wall 1979, cited for short-term avoidance being adaptive (F §1, §3).
  - Berthier et al. 1988, the asymbolia case series described by `price2000` (D §2) and the Part C papers.

**Before the corpus.** The field's roots predate its earliest held work and sit outside the corpus: Sherrington's "imperative protective reflex" (quoted by `melzackwall1965`), Schilder & Stengel's 1928 asymbolia cases (C reading conventions), and Beecher's wounded-soldier observations of 1956/1959, whose "reaction component" is a direct precursor of the affective dimension (per the professor-pain-modeling feedback below; Beecher cited by `melzackwall1965`, `bain2013`). See `not_held.csv`.

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
- **Animals.** `johansen2001` (G1 §1) made pain affect measurable in rats as learned place avoidance. Rostral ACC lesions abolished it while acute paw behaviours were not reduced. `johansen2004` (G1 §2) reported ACC glutamate activity necessary and sufficient for that learning and called it an "aversive teaching signal" (one agonist dose; the authors call the evidence "not conclusive").
- **Neuroanatomy.** `craig2003` (F §2) recast pain as a homeostatic emotion, like hunger or thermal discomfort: a sensation in insula and a motivational drive in ACC.
- **Clinical psychology.** `vlaeyen2000` (F §1) consolidated the fear-avoidance model: fear, not pain intensity, predicts disability. `leeuw2006` (F §3) audited it: intense pain is itself threatening, disuse is weakly supported, and the causal claims had not been tested by manipulation.

**What changed by the end.** "ACC encodes unpleasantness" became the standard citation, although its authors hedged it. "Affect" meant a rating in humans and avoidance in animals. Fear-avoidance was the clinical default, with causal tests still missing.

### 2.3 Pain's badness and pull on behaviour become explicit problems (2007–2013)

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
  - `tiemann2014` (E1 §5): dopamine depletion raised a single post-task unpleasantness rating (p = .048); intensity did not change significantly.
  - `hayen2017` (E2 §1): an opioid lowered the unpleasantness of *breathlessness*; intensity did not change significantly (one-tailed tests, no interaction test).
  - `claes2015` (F §5): reward changed avoidance choices while ratings did not change.
  - `corder2019` (G1 §3): silencing an amygdala ensemble reduced tending and escape, not reflexes.
  - `talbot2019` (D §4): a systematic review found intensity not selectively modifiable and unpleasantness only tentatively and slightly so, and leans toward pain as unitary.
- **Cingulate and action.** `misra2014`, `budell2015`, `procyk2014`, `tolomeo2016`, `han2017` (I §3–§7).

**What changed by the end.** The philosophical question became one about *valence in general*. Relief-seeking became a named test. Pain as a learning signal got a formal architecture. The main human evidence for separable dimensions got its first systematic, and sceptical, audit.

### 2.5 Revised IASP definition, all-affect valence and graded dissociations (2020–2026)

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

Statuses use the five-point scale defined in [Reading conventions](#reading-conventions) and describe the reviewed corpus. `positions.csv` is the authoritative list of which works hold which position.

### 3.1 How many components does pain have, and can they be moved separately? — **open**

**In plain words.** Are "how strong" and "how bad" two separate parts of pain, or two descriptions of one experience?

**Positions.**
- *Separable and serial.* Intensity causes unpleasantness, which feeds secondary suffering; the ACC tracks unpleasantness (`price2000`, D §2; `rainville1997`, E1 §1).
- *Distinct lateral and medial systems.* `kulkarni2005` (E1 §4) and `zidda2024` (E2 §4) claim a separation. `craig2003` (F §2) assigns sensation to insula and drive to ACC.
- *Manipulation shifts unpleasantness, intensity not significantly.* `tiemann2014` (E1 §5; no neural correlate, no lateral/medial claim). `hayen2017` (E2 §1) shows the same pattern for breathlessness, a non-pain analogue.
- *Relative specialisation or graded difference.*
  - `hofbauer2001` (E1 §2): against a simple dichotomy.
  - `zubieta2001` (E1 §3): regions overlap.
  - `stankewitz2023` (E2 §3): "we can not assume distinct processes".
  - `singh2020` (E2 §2): the streams integrate.
- *Unitary lean.* `talbot2019` (D §4): "pain is a unitary unpleasant and sensory experience".
- *Recast axis.* Pain shares signed valence and unsigned intensity codes with pleasure (`lee2024`, H §1; `leknestracey2008`, D §3).

**Key exchanges, in order.**
1. Rainville 1997 moves unpleasantness.
2. Price 2000 reads the hypnosis asymmetry as seriality.
3. Hofbauer 2001 attempts the mirror image and finds unpleasantness moves with intensity.
4. Kulkarni 2005 criticises hypnosis as a tool and uses attention instead.
5. Talbot 2019 reads the same kind of asymmetry as the sensory rating being non-modifiable, adding bias and demand caveats (D cross-paper note 2). Its review excluded pharmacological and lesion evidence by design (D §4), so its unitary lean does not weigh `tiemann2014`, `hayen2017` or asymbolia.
6. Stankewitz 2023 avoids manipulation altogether and reports a graded difference.

**Evidence each side leans on.** Separation: rating dissociations plus region-specific neural changes (E1 batch note 2), lesion and asymbolia cases (D §2). Unitary lean: the risk of bias across all 12 reviewed studies, small effects (3–4.4 points per 100 for external stimuli), and untrained raters not separating the dimensions (D §4).

**Status now: open.** The same one-directional pattern (unpleasantness moves, intensity does not significantly move) is read as seriality by `price2000` and as near-unitary by `talbot2019`. The 2023–2024 studies describe graded differences. No primary study reviewed in E1–E2 moves intensity while leaving unpleasantness fixed (E2 §5); in Talbot's review only two very-high-bias studies claimed to (D §4). *Corpus limit:* Talbot covered cognitive manipulations only; drug and lesion evidence enters through a few small separate studies.

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

**Status now: open.** The latest exchange (`mb2026` replying to `carruthers2023`) has no counter-reply in the corpus. The imperativists are divided among themselves on whether the command targets the world or the experience (B3 §4). *Corpus limit:* the seed survey favoured imperativism; imperativist authors wrote twice as many reviewed works as evaluativists, and evaluativist replies such as Cutter & Tye 2014, Bain 2014 and Jacobson 2019 are known here only through citations ([§10](#10-known-works-not-held)).

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

**Status now: open.** Four rival accounts persist and `carruthers2023` presses a hedonism charge against the experience-directed one. No side concedes in the corpus. *Corpus limit:* the replies written directly on this question, Cutter & Tye 2014 (for evaluativism) and Jacobson 2019 (against it), are not held.

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

**Evidence each side leans on.** The same handful of case reports from 1928–1988, all cited second-hand. The Berthier 1988 threshold data (3 asymbolics vs 5 controls, untested difference described as "over 25% higher") are treated as normal by the standard reading; Griffith & Kind only flag the gap "for the sake of completeness" (C §2). All three papers agree the "affect without sensation" half (Ploner 1999) is weak (C §4).

**Status now: stalled** (in the sense defined above: no new evidence enters; the debate moves by reinterpretation). The philosophical exchange was active in 2023–2025, but all three papers agree the clinical record is small, old and confounded by aphasia (C §4), and no clinical data newer than Ploner 1999 enter the corpus.

### 3.5 Is felt unpleasantness separable from avoidance and motivation? — **open**

**In plain words.** Is how bad pain feels the same thing as the urge to get away from it? Can you change one without the other?

**Positions.**
- *Escape desire accompanies unpleasantness, with no separate dimension* (`price2000`, D §2). `talbot2019` explicitly equates unpleasantness with "the aspect that makes us want to take protective action" (D §4).
- *Avoidance is the readout of affect.* Animal work infers unpleasantness from avoidance and never measures it independently (`johansen2001`, `johansen2004`, `corder2019`, G1 §5 note 2; `singh2020`, E2 §2).
- *Hard to disentangle.* `leknestracey2008` (D §3). In `cuttertye2011`, represented badness is carried by a state defined by its avoidance role (B1 §2).
- *Behaviour moves while ratings do not* (`claes2015`, F §5; `flury2025`, H §2; `becker2018`, G2 §3).
- *Behaviour, not report, is the ultimate measure* (`seymour2019`; G2 §4).
- *Liking and wanting come apart.* Both philosophical camps accept these dissociations and disagree on what they show (`loopy2019`, B2 §8; `barlassina_reflection`, B3 §3; `carruthers2023`, A §5).
- *Urge to withdraw rated beside action.* In `perini2013` (I §2) urge did not dissociate from intensity; in `perini2020` (I §8) insula–cingulate coupling tracked urge in controls.

**Key exchanges, in order.**
1. Johansen 2001 already allows that unpleasantness and aversion learning may "not [be] separable at the neural level" (G1 §1).
2. Leknes & Tracey 2008 name the problem (D §3).
3. Claes 2015 separates choice from ratings (F §5).
4. Carruthers 2023 and Loopy 2019 read liking/wanting dissociations in opposite theoretical directions (A §5; B2 §8).
5. Lee 2022's pathway manipulation moves reflex *and* avoidance together, unlike 2001–2019 (G1 §5 note 3).
6. Flury 2025 replicates behaviour-without-ratings but declines a differential conclusion (H §2).

**Evidence each side leans on.**
- *Fused.* Correlated ratings and correlated measures. For example, urge and intensity slopes correlate at r = 0.53–0.83 (I §2).
- *Separable.* Choice rose with a reward effect size of η²_G = .557 while ratings did not change (F §5). Rodent manipulations spared a sensory-side measure, though that measure differs by paper: nocifensive formalin behaviour in the Johansen studies, reflex thresholds in Corder (G1 §5; [§1](#1-vocabulary)).

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

### 3.7 Is pain's felt badness the learning signal, and how is learning from pain structured? — **open**

**In plain words.** That painful input teaches animals and people what to avoid is textbook fear conditioning and is not disputed in the corpus. The live questions are narrower: is the *felt badness* of pain itself the teaching signal, and do people learn more from pain that happened or pain they escaped?

**How this debate is framed (recorded rule).** The draft split "whether" (leaning) from "how" (open). Following the professor-pain-modeling feedback, the uncontested claim (nociceptive input supports aversive learning) is treated as background, not as a debate, and the debate is restricted to the contested claims, so it carries a single status.

**Positions.**
- *ACC aversive teaching signal, in the same circuit as unpleasantness* (`johansen2004`; G1 §2).
- *Pain is the reinforcement and control signal.* `seymour2019` makes the identity claim, with control behaviour as the ultimate measure (G2 §4); `wiech2013` frames pain as a motivator (G2 §1).
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

**Status now: open.** No reviewed study tests the identity claims against felt badness: `seymour2019` is a theoretical review, and `johansen2004`'s one-circuit claim links to unpleasantness only through human literature (G1 §2). None of the G2 experiments rated pain during avoidance (G2 §8 note 4). Learning asymmetry conflicts between `jepma2022` and `le2024` (G2 §8 note 2), and whether the signal is value or command is disputed (A §5; B3 §2). *Corpus limit:* the reviewed computational papers were selected for this framing, so their agreement that pain drives learning is uninformative about rival framings.

### 3.8 What drives pain-related avoidance and disability: fear, pain itself, or competing goals? — **leaning**

**In plain words.** Do people with chronic pain avoid activity because they are afraid, because pain itself is threatening, or because avoiding pain crowds out their other goals?

**Positions.**
- *Fear* (`vlaeyen2000`, F §1). `vlaeyen2016` (F §6) keeps the fear → avoidance loop as its core, so it is listed here as well as under goal competition.
- *Intense pain is itself threatening* (`leeuw2006`; F §3).
- *Goal competition* (`crombez2012`, F §4; `claes2015`, F §5; `vlaeyen2016`, F §6; `becker2018`, G2 §3).
- *Homeostatic drive* (`craig2003`; F §2).
- *Learned decision.* `seymour2019` and `wiech2013` (G2 §4, §1); `gandhi2021` finds avoidance vigour falls after failure and helplessness (G2 §5).
- *Active-defence circuit, stated as speculation* (`lee2022`; G1 §4).

**Key exchanges, in order.** Vlaeyen & Linton 2000 → Leeuw 2006 (intensity matters; causality untested) → Crombez 2012 (goals) → Claes 2015 (lab test) → Vlaeyen 2016 (goal-priority fork in the model's diagram). F connections describe this as one research programme with changing diagrams.

**Evidence each side leans on.**
- *Fear.* Task performance tracked fear rather than pain intensity (Crombez et al. 1998, as reported in `vlaeyen2000`, F §1); graded exposure improved accelerometer-measured behaviour where education alone did not, though both lowered self-reported fear (de Jong et al. 2005, as reported in `leeuw2006`, F §3). Evidence is mostly cross-sectional, and the authors warn it "should not be confused with causal effects" (F §1).
- *Pain intensity.* Intense pain "in itself" drives escape and avoidance (`leeuw2006`, F §3, citing Eccleston & Crombez 1999); `crombez2012` says the model "underplayed" intensity (F §4).
- *Goal competition.* A competing reward raised choice of a painful movement while fear stayed unchanged (`claes2015`, F §5); the originators' 2016 diagram adds a goal-priority fork (F §6).
- *Decision and circuits.* Avoidance vigour falls after failure and with helplessness (`gandhi2021`, G2 §5); an ACC→PAG pathway is proposed, speculatively, to contribute (`lee2022`, G1 §4).

**Status now: leaning, toward fear plus goal competition.** The originators' 2016 model keeps the fear loop and adds goal priority as the fork (`crombez2012`, `vlaeyen2016`); it does not move away from fear. Causal tests remain few: `leeuw2006` notes components had not been manipulated, and `claes2015` is one healthy-student experiment with self-selected goal groups. *Corpus limit:* only the originators' programme is reviewed; rival clinical models such as endurance responses (`hasenbring2010`) are named-only.

---

## 4. How the communities relate

Citation links below come only from what the reviews record (`edges.csv`, 182 documented engagements). A missing link means none was recorded among the 65 reviewed papers. It does not mean none exists in the wider literature.

**Dense within, thin between.** Of the 182 recorded engagements, 69 are philosophy citing philosophy and 36 are human neuroscience citing human neuroscience. In the recorded engagements, philosophy is the most self-contained community: its outgoing engagements with other communities are 8 to named-only clinical case reports (Ploner 1999, Berthier 1988), 1 to `craig2003` and 1 to `price2000`, both from `klein2015asym` (C §1). Recording density differs by review tier, which inflates this: reviewed-full entries average 3.2 recorded out-links and short entries 1.8, and 21 of the 23 reviewed philosophy papers are full-tier. **Among the 31 reviewed non-philosophy papers dated after Klein 2007 (the corpus's first philosophy paper), none is recorded citing a corpus philosophy paper.** Earlier non-philosophy papers could not have cited one. The nearest things are indirect:
- Corder 2019 cites Grahek's 2007 philosophy book, which is not in the corpus (G1 §3).
- Wiech & Tracey 2013 call pain "imperative" in passing, with no reference to philosophical imperativism (G2 §1, §8 note 7).
- Perini 2013 describes the action component as "an imperative desire to escape", also without a philosophical citation (I §2).

**Computational modelling and philosophy do not meet.** "No G2 paper engages that literature" (G2 §8 note 7). Going the other way, the philosophy papers argue about learning and decision science through models outside the corpus (Schultz; Juechems & Summerfield; Rangel; B3 §2; A §5). They cite none of `wang2018`, `seymour2019`, `jepma2022` or `le2024`.

**Craig 2003 sits apart from fear-avoidance.** Craig cites none of the fear-avoidance literature, and none of the four fear-avoidance papers that post-date him cites him (F connections). He is picked up instead by `leknestracey2008` (D §3), `seymour2019` (G2 §4) and `klein2015asym` (C §1).

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
3. Engagement is recorded only where a reviewer noted it, and only for works in the manifest. For short-tier entries this is mostly the "responds to / builds on" list, which is why short entries have fewer recorded links.
4. `gordon2023`, `gandhi2021`, `tumulty2009`, `vogt1992`, `bolles1980`, `vase2003`, `vase2005`, `raja2020` and `nickel2017` have no recorded engagement with other manifest works. That is a gap in the corpus, not evidence of isolation.

---

## 5. What the evidence does and does not show

### 5.1 Consistent findings

| Finding | Where it recurs | Qualification |
|---|---|---|
| Manipulations shift unpleasantness more readily than intensity | Hypnotic suggestion (`rainville1997`, E1 §1); dopamine depletion (`tiemann2014`, E1 §5); emotional primes (`zidda2024`, E2 §4); 4 of 5 hypnosis studies (`talbot2019`, D §4). Non-pain analogue, not counted: opioid in breathlessness (`hayen2017`, E2 §1) | Intensity nulls are non-significant, not shown to be equivalent. Talbot rates every included study at high or unclear risk of bias (D §4; E2 §5 note 2) |
| No primary study in E1–E2 moves intensity alone | Intensity suggestions also moved unpleasantness (`hofbauer2001`, E1 §2); `talbot2019` concludes intensity "cannot be selectively modulated" (D §4) | In Talbot's 12 studies, two at very high risk of bias (Dahlgren 1995, Kunz 2012) did claim selective intensity change (D §4) |
| The two ratings are tightly coupled | r = 0.81 (`hofbauer2001`); r = 0.86 across trials (`stankewitz2023`) | Coupling measured in different ways. Non-pain analogue, not counted: r = 0.59 for drug-induced breathlessness changes (`hayen2017`) |
| Rodent manipulations reduce learned or ongoing avoidance while sparing each paper's sensory-side measure | `johansen2001`, `johansen2004` (spared: nocifensive formalin licking, lifting, flinching); `corder2019` (spared: reflex thresholds and withdrawal) (G1 §5 note 3) | Classification clash: the behaviour Johansen reports as spared is the kind Corder counts as affective-motivational and reports as reduced. Not uniform: `lee2022`'s pathway moved reflex and avoidance together |
| Behaviour can change without ratings changing | Reward raised choice of a painful movement (`claes2015`, F §5) and avoidance performance (`flury2025`, H §2) | Cross-phase and probe-trial ratings; mild stimuli; task-compliance confound |
| Midcingulate "pain" responses depend on action | `perini2013`, `perini2020`, exploratory `koppel2022` (I §2, §8, §9) | Correlational fMRI; Koppel's preregistered action tests were null |
| Pain-avoidance choices fit reinforcement-learning models | `wang2018`, `jepma2022`, `le2024` (G2) | Direction of learning asymmetry conflicts |

### 5.2 Findings that rest on weaker ground

- **One-directional, and "unchanged" is not "shown unchanged".** Every human dissociation in E1–E2 moves unpleasantness, never intensity alone (E2 §5 note 2). Every "unchanged" in these studies is a non-significant difference; no reviewed study reports an equivalence test. `tiemann2014`'s intensity null is far better powered (75 single-trial ratings) than its affect effect (one rating).
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
| No rating of desire or urge for relief next to unpleasantness | Not found in these 65 reviewed papers. `perini2013` and `perini2020` rate "urge to move" but not unpleasantness; `han2017`'s "willingness to help" is not an urge to escape. This is a *corpus* gap, not a field gap: placebo and expectation research rated desire for relief beside pain (Vase 2003, named-only; the strand is listed in [§10](#10-known-works-not-held)) |
| Intensity always rated before unpleasantness | `stankewitz2023` and `zidda2024`; order not stated in `hayen2017`. None discusses order effects (E2 §5 note 4) |
| No equivalence tests for intensity nulls | None of the E2 papers reports one (E2 §5 note 2) |
| "ACC" names different subregions | Rostral/perigenual rat ACC vs mouse area 24 (G1 §5 note 5); perigenual ACC vs aMCC vs pMCC across human studies, where "perigenual" is broader than Vogt's pregenual pgACC (E1 batch note 4); the concordance table in I |
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

Statuses describe the reviewed corpus (see the scale in [Reading conventions](#reading-conventions) and `status_scope` in `debates.csv`).

| Debate | Status (2026) | Why, in one line | What the field itself says is open |
|---|---|---|---|
| How many components; can they be moved separately? | open | Same asymmetry read as seriality or near-unitary; recent studies call differences graded | Talbot et al. call for methods that exclude demand effects (D §4); "we can not assume distinct processes" (`stankewitz2023`, E2 §3) |
| Evaluation, command or something else? | open | `mb2026`'s reply to `carruthers2023` unanswered in corpus; imperativists split | Barlassina concedes valence's evolutionary function is unexplained (B3 §3); no metasemantics for evaluative states proposed (`mb2026`, B3 §2) |
| Why take painkillers? | open | Four rival accounts plus a hedonism charge | Martínez calls the spam mechanism "to a large extent an empirical matter" (B2 §1) |
| Is asymbolic pain pain? | stalled | No clinical data newer than 1999 in corpus; dispute moved to taxonomy | Griffith & Kind call for more clinical research (C §2); taxonomy unsettled (C §3) |
| Unpleasantness vs avoidance | open | Behaviour moved without ratings, but never measured on the same trials | Flury et al. note behaviour and self-report often diverge and that the design "did not target generalisation" (H §2) |
| Where pain meets action in cortex | open | Integration and action-dependence readings coexist | Shackman: monitor vs controller unresolved (I §1); Koppel: cingulate not action-selective at whole-brain threshold (I §9) |
| Is felt badness the learning signal? | open | Identity claims untested against felt badness; conflicting asymmetry; value vs command readings (nociceptive input driving learning is uncontested background) | Jepma et al. offer task framing among explanations of their asymmetry (G2 §6); Seymour's Box 1 predictions have mixed or no behavioural support yet (G2 §4) |
| What drives avoidance | leaning, toward fear plus goal competition | Originators' 2016 model keeps the fear loop and adds a goal fork; few causal tests | Leeuw: causality "can only be established when each construct is experimentally manipulated" (F §3) |

---

## 8. Relevance to this project (interpretive)

> **Interpretive, not a finding.** Nothing in the corpus shows that an artificial agent has pain or valence. The agent's internal damage signal is **nociception**. Experiment ideas are out of scope here and belong to **`research-postdoc`** (triage) and **`professor-pain-modeling`** (whether a construct is valid enough to support "pain-like" claims).

The project's agents learn with a nociception signal and show pain-like behaviour, such as what the project labels hypervigilance after injury (a behavioural signature, not the clinical attentional construct). Four points bear on how to describe it.

1. **The field's measurement gap is the project's interpretive risk.** In animals, "unpleasantness" is often avoidance under another name (G1 §5 note 2), and an agent resembles the animal case. Behaviour alone cannot separate a command reading, a value reading, or plain learned avoidance (A §7; A §5). The one affect-specific animal readout, avoidance with a spared reflex or nocifensive measure, has no agent analogue without a reflex arc.
2. **Theories come apart on dissociations:** signal without concern (asymbolia), lowering the signal rather than repairing damage (painkillers), avoidance changing while ratings do not (`claes2015`, `flury2025`), and reflex vs learned avoidance (G1).
3. **Learning asymmetry is contested in humans** (`jepma2022` vs `le2024`), so there is no single human benchmark for learning from damage received vs avoided.
4. **Seymour 2019's claim that behaviour should measure pain** is a position in an open debate, not a settled method.

---

## 9. Data files for diagrams

All in `field_history_data/`, UTF-8 CSV with a header row, using manifest keys throughout. They were generated from one transcription of the reviews and validated against the manifest: all 89 keys present, no extra keys, every debate id, position key and `not_held.csv` citing key cross-checked.

| File | Rows | Contents |
|---|---|---|
| `works.csv` | 89 | Every manifest key: label, plot year, print year, community, era, status, one-line role, debates |
| `eras.csv` | 5 | Era id, label, start and end year, summary |
| `debates.csv` | 8 | Debate id, title, plain question, status, reason, first and latest year of positioned works |
| `positions.csv` | 52 | Positions per debate with keys and one-line summary |
| `edges.csv` | 182 | Documented engagements (builds-on / critiques / replies-to / reinterprets / uses-as-evidence) with review section |
| `dissociation_evidence.csv` | 25 | Empirical reviewed papers measuring two or more outcomes; each outcome coded changed / unchanged / not-measured / correlational |
| `dimension_models.csv` | 23 | How the number and kind of pain components was modelled over time |
| `survey_corrections.csv` | 47 | Survey claim, what the paper shows, verdict |
| `not_held.csv` | 29 | Important works and strands known from the reviews but not in the manifest ([§10](#10-known-works-not-held)) |

**Legend and conventions for the figures.**
- **`positions.csv` is authoritative** for which works belong to which debate; `works.csv` `debates` is derived from it. Works with no position have an empty `debates` cell.
- **`dissociation_evidence.csv` codes.**
  - *changed*: a significant difference was reported for the contrast named in `contrast_of`.
  - *unchanged*: no significant difference was reported. Equivalence was not tested unless the caveat says so (no row says so).
  - *correlational*: an association, not a contrast.
  - *not-measured*: no own-pain measure of that kind. Ratings of *another person's* pain (`budell2015`, `han2017`) are coded not-measured.
  - `contrast_of` names what the coded cells compare: `manipulation`, `stimulus-class` (painful vs non-painful stimuli), `pre-task`, `attention-condition`, or `none-correlational` (added value: every coded cell is a correlation, so there is no contrast). Where cells in one row differ, the caveat says how (`jepma2022`: intensity is a pre-task drug check; `perini2013`: ratings compare stimuli while the neural finding follows the press manipulation).
  - `reflex_or_nocifensive`: the caveat names which kind was measured ([§1](#1-vocabulary)).
  - `n_primary` is the main analysed N as an integer, blank when the sample is not a single number; `n_analysed` keeps the full text.
- **Communities.** `unknown` is its own lane, not missing data.
- **Statuses** in `debates.csv` follow the scale in [Reading conventions](#reading-conventions). `status_direction` is filled only for `leaning`; `status_scope` states the corpus limit.

Notes for the page builder are in [§11](#11-scope-and-provenance).

---

## 10. Known works not held

The reviews cite many works that are not in the manifest. The ones that matter most for the history are listed in `field_history_data/not_held.csv` (29 rows: label, year, community, why relevant, and which reviewed papers cite them), so that their absence is visible rather than silent. None of them carries a claim in this document. Highlights:
- **Evaluativist and critical replies:** Cutter & Tye 2014 (reply to Jacobson on painkillers), Bain 2014 (evaluativist account of asymbolia), Jacobson 2019, Cochrane 2019, Aydede & Fulkerson. Their absence tilts the philosophical record toward imperativism (see Reading conventions).
- **Imperativist and asymbolia sources:** Martínez 2022; Grahek 2007, the source of the standard asymbolia reading; Hardcastle 1997/1999; Klein & Duval 2023.
- **Empirical anchors used second-hand:** Rainville et al. 1999; Price et al. 1985; the rat liking/wanting studies (Berridge & Valenstein 1991; Flynn 1991; Galaverna 1993); Mower 1976; Kragel et al. 2018; Seymour et al. 2004/2005; Roy et al. 2014; Lethem 1983; Crombez 1998; de Jong 2005; Asmundson 2004.
- **Pre-1962 origins:** Sherrington's "imperative protective reflex"; Schilder & Stengel 1928/1931; Beecher 1956/1959.

**Omitted strands** (named by the professor-pain-modeling feedback; the page should name them, not fill them in):
1. **Desire for relief, expectation and placebo** (Price; Vase 2003/2005, named-only; Wager; Atlas; Büchel). This strand *did* rate desire for relief beside pain, so the §5.3 gap on desire ratings is a gap in this corpus, not in the field.
2. **The IASP definition history** (Merskey 1979 to Raja 2020), the source of the pain vs nociception distinction this document relies on.
3. **The chronic-pain affective shift** (Apkarian and Baliki; Hashmi 2013; Borsook's negative hedonic shift), present only through `becker2018` and citations.
4. **Attention and interruption** (Eccleston & Crombez 1999) and **Fields' motivation–decision model** (2006), the psychological and neuroscientific ancestors of the reinforcement-learning strand; both are named-only in the manifest.
5. **Pre-1962 origins**, as above.

---

## 11. Scope and provenance

- **Counts** (from `references_manifest.csv`): 89 references. 46 reviewed in full, 19 reviewed as short summaries, 24 named-only.
- **Part A records.** Part A predates the field-history record block. Its five records (year, community, question, position, engagements) were derived here from its entries and its §6 cross-paper map.
- **Ambiguous years.** In each case below, `works.csv` gives the first public year in `year` and the print year in `year_print`.

  | Key | year | year_print | Why |
  |---|---|---|---|
  | `loopy2019` | 2019 | 2020 | Volume dated 2019, printer's stamp 9/30/20 (B2 §8) |
  | `gandhi2021` | 2022 | 2022 | Manifest key and filename say 2021; the accepted-manuscript cover sheet says 2022 (G2 §5). An earlier online date is possible but not recorded |
  | `barlassina_reflection` | 2020 | (blank) | Year inferred from the text (B3 §3) |
  | `km2018` | 2018 | 2018 | Written c. 2014 (B2 §6) |
  | `mb2026` | 2026 | 2026 | Accepted 2023 (B3 §2) |
  | `carruthers2018`, `bain2019` | 2017 | print year | Online 2017 |
  | `martinez2011`, `bain2013`, `martinez2015` | online a year before print | print year | |
  | `griffithkind2023`, `duvalklein2025`, `flury2025` | online year | volume year the following year | |
  | `leeuw2006` | 2006 | 2007 | |
  | `misra2014`, `procyk2014` | 2014 | 2015, 2016 | |

- **Communities for named-only works** were assigned only where a citing review describes the work's field. Seven are `unknown`: Wall 1979, Bolles & Fanselow 1980, Fields 2006, Auvray 2010, Raja 2020, Vase 2003, Vase 2005. `tolomeo2016`'s record says "neurosurgery-neurology", normalised here to `neurology-neurosurgery`.
- **`craig2003` community: kept as `animal-circuits`.** This is a close call. The plan-reviewer suggested `human-neuroscience`. Part F's own field-history record codes it `animal-circuits`, and Craig states the view "arises directly from functional anatomical findings in cat and monkey" (F §2), with human imaging and lesion findings as support. The page may note in the caption that Craig spans both lanes.
- **Survey verdict recoding.** Verdicts follow the batch reviewers, with three changes. `budell2015` is coded does-not-hold because the survey reverses the paper's conclusion (the reviewer rated it partly). `hayen2017` and `tolomeo2016` are coded misattributed because the finding exists but concerns breathlessness or emotion recognition, not pain.
- **Generator.** `field_history_data/build_field_history_data.py` produces every CSV and validates keys, codes, positions and cell lengths. Edit it and rerun; do not hand-edit the CSVs.
- **Excluded from `dissociation_evidence.csv`.** Reviews and theory (`price2000`, `talbot2019`, `seymour2019` and others). Papers with fewer than two of the listed outcomes: `wang2018` (avoidance only), `shackman2011`, `procyk2014`, `tolomeo2016`, `gordon2023`.
- **Edges exclude** the Tumulty 2009 / Klein 2010 exchange, because both endpoints are named-only.

---

## Feedback from professor-pain-modeling — 2026-09-17

Construct-validity and fairness review before the page is built. Rows of `dissociation_evidence.csv` were spot-checked against Parts E1, E2, F, G1, G2, H and I (species and N match the reviews for all 20 rows checked). Items are location → problem → fix. Full list was returned inline to the session that requested the review; this is the condensed record.

**MUST-FIX**

1. **§3 intro / Reading conventions — status scale undefined.** Only "leaning" is defined; "settled / open / stalled / not yet tested" are not. "Stalled" for §3.4 conflates an active philosophical exchange (2023–2025) with a static clinical record. Fix: define all five (e.g. *stalled* = no new evidence has entered the record; the debate moves only by reinterpretation), then keep §3.4 as "stalled" under that definition.
2. **§1 "Avoidance vs escape vs reflex", §5.1 row 4, `dissociation_evidence.csv` column `reflex_or_nocifensive` (rows `johansen2001`, `johansen2004`).** Formalin lifting/licking/flinching are supraspinally organised nocifensive/recuperative behaviours (Bolles & Fanselow 1980, in the manifest), not reflexes; Corder 2019 classifies attending/licking as *affective-motivational*. So the measure Johansen 2001/2004 report as spared is the measure Corder 2019 reports as reduced. "Sparing reflex-like measures" harmonises a real inconsistency. Fix: split the vocabulary row (reflex = spinal withdrawal, paw flick, von Frey threshold; nocifensive = licking, guarding, lifting); reword §5.1 row 4 to name each paper's own sensory contrast and the classification clash; add the clash to the two CSV `caveats` cells.
3. **`dissociation_evidence.csv` legend (§9) — "unchanged" undefined.** Every "unchanged" is a non-significant difference; no row has an equivalence test. Fix: legend states "unchanged = no significant difference reported; equivalence not tested unless the caveat says so". Add to caveats: `claes2015` (unpleasantness p = .133, no equivalence test), `flury2025` (contingency main effect on unpleasantness p = .027 across both phases), `tiemann2014` (intensity null is far better powered than the affect effect: 75 single-trial ratings + threshold vs one post-task rating), `jepma2022` ("unchanged" = drug effect on pre-task ratings only).
4. **§2.4 bullets `tiemann2014` "raised unpleasantness only" and `hayen2017` "lowered … unpleasantness only".** "Only" turns n.s. into a null. Fix: "raised a single post-task unpleasantness rating (p = .048); intensity did not change significantly" / "lowered unpleasantness; intensity did not change significantly (one-tailed, no interaction test)".
5. **§1 Vocabulary — no entry for nociception.** The page's own rule ("nociception, never pain") rests on the IASP 2020 revised definition's note that pain and nociception are different phenomena (`raja2020`, named-only). Add a row: *Nociception* = the neural encoding of noxious stimuli, not pain; distinct per IASP 2020; the agent's channel is nociception in this sense.
6. **§3.7 "leaning (on whether)".** The "whether" as posed (does pain work as a teaching signal for avoidance) is uncontested textbook fear-conditioning; corpus convergence is uninformative. The contested claims are Seymour's identity/primacy claim (pain *is* the reinforcement signal; control behaviour is the ultimate measure) and Johansen & Fields' claim that the teaching signal and the unpleasantness signal are one ACC circuit. Fix: "uncontested: nociceptive input supports aversive learning / open: whether pain's felt badness *is* that signal, and how learning is structured".
7. **§3.8 "leaning" — direction unstated, fear position not at its strongest, and the "Evidence each side leans on" block is missing (present in §3.1–§3.6).** `vlaeyen2016` is filed under goal competition only, but its diagram keeps fear → avoidance as the core loop and adds goal priority as the fork. Fear-side evidence in F §1/§3 (performance tracked fear not intensity, Crombez 1998; exposure changed accelerometer behaviour where education did not, de Jong 2005) is absent. Fix: add the evidence block; state "leaning toward fear-plus-goal-competition (the originators' 2016 model), not away from fear"; list `vlaeyen2016` under both `ad-fear` and `ad-goals` in `positions.csv`.
8. **§3.4 "read as 25% higher by Griffith & Kind".** "Over 25% higher" is Berthier et al.'s own wording (C §2, p. 564; n = 3 vs 5, no test); Griffith & Kind only flag it. Fix attribution.
9. **Entry point / title "1962–2026".** 1962 is the earliest manifest key, not the field's start; the corpus itself cites Schilder & Stengel 1928 and Sherrington, and Beecher's "reaction component" (1956/1959) is the direct precursor of the affective dimension. Fix: "since the corpus's earliest work (1962)" plus one sentence in §2.1 or §10 naming the pre-1962 origins as outside the corpus.

**SUGGEST**

10. §1 "pACC … perigenual": in Vogt's scheme pACC is *pregenual*; "perigenual" (Kulkarni; Johansen's rat rostral ACC) is broader (subgenual + pregenual). Use pgACC and say so.
11. §1 "Affective-motivational … traced to Melzack & Casey 1968": their own order is "motivational-affective" (D §1); the reversed compound is later usage.
12. §3.5 position "urge to withdraw tracks insula–cingulate coupling (`perini2013`, `perini2020`)": the coupling–urge result is `perini2020` only; in 2013 urge did not dissociate from intensity. `positions.csv` `uva-urge` is already correct.
13. `dissociation_evidence.csv` rows `perini2013`, `han2017`: `intensity`/`desire_or_urge` = "changed" codes the pain-vs-non-pain contrast, not the press/no-press manipulation named in `manipulation_or_design`. Define in the legend that codes refer to the named manipulation, or add a `changed_with` column.
14. `dissociation_evidence.csv` rows `budell2015` (`intensity=correlational`), `han2017` (`intensity=changed`): ratings of an *actor's* pain. Code `not-measured` with caveat "observer rating of another's pain", or rename the column.
15. §3.1 "Key exchanges, in order" runs 1997, 2001, 2000. Also add that Talbot's review excluded pharmacological and lesion evidence by design (D §4), so its unitary lean does not weigh `tiemann2014`, `hayen2017` or asymbolia.
16. `positions.csv` `dim-lateral-medial` includes `tiemann2014`, which found no neural correlate and makes no lateral/medial claim. Rename the position "Selective modulation of one dimension by manipulation or anatomy" or move Tiemann.
17. `dimension_models.csv` `flury2025` label "Tripartite components (tested)" lists two components → "Two of Melzack & Casey's three, as behavioural surrogates". `raja2020` components "sensory;affective" → "sensory;emotional (definition wording)".
18. Entry point "Several studies change avoidance behaviour without changing ratings" → "Two experiments (`claes2015`, `flury2025`)".
19. §2 era labels for e3 and e5 are philosophy-led although five of six communities are not philosophy; the 2020 boundary coincides with the revised IASP definition, which the label could carry. State the weighting or relabel e5.
20. §8: "hypervigilance" is a technical term (attentional prioritisation of pain-related information; Eccleston & Crombez 1999, named-only here). Gloss: "what the project labels hypervigilance — a behavioural signature, not the attentional construct of the clinical literature". Add to point 1 that the corpus's only affect-specific animal readout (spared reflex) has no agent analogue unless a reflex arc exists in the architecture.
21. Omitted strands the page should name in §10 (not add): (a) desire-for-relief / expectation / placebo work (Price; `vase2003`/`vase2005` named-only; Wager, Atlas, Büchel) — it *did* rate desire for relief beside pain, so §5.3 row 2 is a corpus gap, not a field gap; (b) IASP definition history (Merskey 1979 → Raja 2020), the source of the page's vocabulary rule; (c) the chronic-pain affective shift (Apkarian/Baliki, Hashmi 2013; Borsook's negative hedonic shift), present only via `becker2018`; (d) the attention/interruption strand (`eccleston1999`) and Fields' motivation–decision model (`fields2006`), the psychology and neuroscience ancestors of the RL strand, both named-only; (e) pre-1962 origins (item 9).

---

## Revision log — literature-curator — 2026-09-17

Applies the professor-pain-modeling gate (items 1–21, above) and the plan-reviewer gate (verdict "sound with concerns"; all Moderate and Low items). The plan-reviewer spot-checked 27 CSV cells and the professor 20 dissociation rows; neither found transcription drift, so these are wording, scope and coding changes.

**Prose**
- **Title and entry point.**
  - Corpus span is now labelled as the corpus's, not the field's (prof 9).
  - The unpleasantness-vs-intensity bullet is qualified by small, high-bias studies (plan-reviewer, Low).
  - "Several studies" became "Two experiments … though neither rated pain on the avoidance trials" (prof 18 / plan-reviewer 1).
- **Reading conventions.** Added a five-point status scale with definitions (prof 1), a note that statuses describe the reviewed corpus, and a corpus-balance note: 14 imperativist vs 7 evaluativist reviewed works (plan-reviewer 3, 8).
- **§1 Vocabulary.**
  - Added *nociception* (prof 5).
  - Split *reflex* from *nocifensive* and recorded the Johansen/Corder classification clash (prof 2).
  - Changed pACC to pgACC and glossed "perigenual" (prof 10).
  - Recorded Melzack & Casey's own order, "motivational-affective" (prof 11).
- **§2 Eras.**
  - Relabelled e3 and e5 and stated how the labels are weighted (prof 19).
  - Added pre-1962 origins (prof 9).
  - Clarified that Melzack & Wall's command vocabulary implies no lineage (plan-reviewer, Low).
  - Hedged Johansen & Fields 2004 (plan-reviewer, Low).
  - Reworded "only" for Tiemann and Hayen to "did not change significantly" (prof 4).
- **§3 Debates.**
  - §3.1: moved Tiemann/Hayen into a new position, reordered the exchanges, and noted Talbot's exclusion of drug and lesion evidence (prof 15, 16).
  - §3.2 and §3.3: added the not-held evaluativist replies (plan-reviewer 8).
  - §3.4: Berthier threshold attribution corrected; "stalled" tied to its definition (prof 8, 1).
  - §3.5: urge–coupling result attributed to Perini 2020 only; the sensory-side measure named per paper (prof 12, 2).
  - §3.7: reframed as "is felt badness the learning signal", status **open** with the framing rule recorded, plus a corpus-selection caveat (prof 6, plan-reviewer 3).
  - §3.8: added an evidence block; status "leaning, toward fear plus goal competition"; `vlaeyen2016` listed under fear too (prof 7).
- **§4 Communities.**
  - "No engagement" now scoped to the 31 non-philosophy papers dated after Klein 2007 (plan-reviewer 4).
  - "Self-contained" qualified, with recording density by tier (3.2 full vs 1.8 short out-links) (plan-reviewer 5).
  - Craig: "none of the four that post-date him" (plan-reviewer, Low).
- **§5 Evidence ledger.**
  - Breathlessness removed from pain rows 1 and 3 and shown as a non-pain analogue (plan-reviewer 2).
  - Row 4 names each paper's sensory-side measure and the clash (prof 2).
  - "Unchanged ≠ shown unchanged", with the Tiemann power asymmetry (prof 3).
  - The desire-rating gap is a corpus gap, not a field gap (prof 21).
- **§7 Status table.** Updated for §3.7 and §3.8, with a corpus-scope note.
- **§8 Relevance.** Glossed hypervigilance as the project's behavioural label; added the no-reflex-arc point (prof 20).
- **§9 Data files.** Added a legend for the dissociation codes, `contrast_of`, `n_primary`, the unknown-community lane, and the rule that positions are authoritative.
- **§10 Known works not held.** New section, pointing to `not_held.csv`, with the omitted strands paragraph (prof 21, plan-reviewer 8).
- **§11 Scope and provenance.** Renumbered from §10. Added the generator location and the `craig2003` decision.

**Data files** (all regenerated by `field_history_data/build_field_history_data.py`)
- **`works.csv`.** `debates` is now derived from `positions.csv`, so named-only works without a position have an empty cell (plan-reviewer 6). `vase2005` debates are empty. `barlassina_reflection` `year_print` is blank.
- **`positions.csv`.** 52 rows (was 51).
  - New position `dim-affect-selective` holds `tiemann2014` and `hayen2017`.
  - `vlaeyen2016` added to `ad-fear`.
  - `uva-urge`, `ls-teaching` and `ls-rl-control` summaries reworded.
- **`debates.csv`.**
  - New columns `status_direction` and `status_scope`.
  - `learning-signal` retitled and set to `open`.
  - `asymbolia` reason restated in the terms of the stalled definition.
- **`dissociation_evidence.csv`.**
  - New columns `n_primary` (integer or blank) and `contrast_of`.
  - `budell2015` and `han2017` observer ratings recoded to not-measured.
  - Reflex vs nocifensive stated in the caveats for `johansen2001`, `johansen2004`, `corder2019` and `lee2022`.
  - Caveats added for `claes2015`, `flury2025`, `tiemann2014` and `jepma2022`.
- **`dimension_models.csv`.** `flury2025` label and `raja2020` components revised (prof 17).
- **`eras.csv`.** e3 and e5 labels revised.
- **`not_held.csv`.** New, 29 rows.

**Deviations, recorded.**
- **`contrast_of`.** Takes one extra value, `none-correlational`, for rows whose every coded cell is a correlation (`zubieta2001`, `stankewitz2023`, `le2024`, `lee2024`); none of the four requested values describes them honestly. Rows with mixed contrasts (`jepma2022`, `perini2013`) are explained in `caveats` rather than split, so each key stays one row.
- **`han2017`.** The observer's own unpleasantness at viewing is also coded not-measured, consistent with the own-pain meaning of the column.
- **`budell2015`.** Kept although no own-pain outcome remains, flagged in its caveat.
- **`craig2003`.** Community kept as `animal-circuits`, against the plan-reviewer's suggestion; reason in §11.
