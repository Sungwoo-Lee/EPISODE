# Imperativism Field History — Batch G2: Pain as a Learning and Decision Signal (2013–2024)

**Topic folder:** `docs/project/references/imperativism/`
**Batch:** G2 of the field-history expansion — 7 papers, reviewed one at a time in the order assigned, 2026-09-17.
**Reviewer:** literature-reviewer
**Companion files:** Part A, the philosophy debate ([[imperativism_lit_review_A_imperative_theories]]); the corpus manifest `references_manifest.csv`.

## What this batch is about (plain-language entry point)

**The question these papers share.** Pain does more than tell you something hurts. It changes what you do next. You pull back, you learn which choices led to the hurt, and next time you avoid them. From about 2013, a group of researchers began describing that role in the language of **reinforcement learning** — the mathematics of learning by trial and error from good and bad outcomes, the same framework used to train game-playing computer programs. This batch covers that turn, from a 2013 review that calls pain a "motivator" to model-based brain-imaging studies of pain avoidance in 2022–2024.

**Why it matters to the history of the field.** Philosophers asked whether the bad feel of pain is a *command* ("stop that!") or a *judgement* ("this is bad"). Part A covers that debate. This batch shows how neuroscience and computational modelling were treating pain over the same years. Pain appears here as a teaching signal, as a controller of behaviour and as a cost weighed against rewards. Seymour (2019) goes furthest: he argues that how people *behave* around pain, not what they *say* about it, should be "the ultimate measure of pain".

**What the batch shows, in brief.**
- The two broad reviews (Wiech & Tracey 2013; Becker et al. 2018) describe the pain–motivation link as two-way. Pain drives learning and avoidance, and goals, fear and reward in turn change how much it hurts.
- Seymour (2019) proposes a layered learning architecture for pain. It runs from reflexes, through learned warning cues and learned avoidance actions, up to deliberate planning. On this view, the ways the brain turns pain up or down are adjustments that make pain a better teaching signal.
- The three computational experiments disagree on one basic point: do people learn more from pain that *happened* or pain that was *avoided*? Jepma et al. (2022) found learning was stronger after received pain. Le et al. (2024), using a different task, found it was stronger after avoided shock. Wang et al. (2018) found that people switch more readily between planning and habit when avoiding pain than when seeking reward. That result depends on a comparison with a reward study run in another lab, and the authors call it provisional.
- **None of the five empirical papers collected pain ratings during the avoidance task itself** (Wiech & Tracey and Becker et al. are reviews). So none of them can separate how bad the pain *felt* from how strongly people *avoided* it.
- **Two survey claims do not match their papers.** The survey reads Seymour's "precision signal" as "precision-weighted", a predictive-coding term the paper never uses. It also says Gandhi et al. found that avoidance has neural correlates "distinct from pain report", but that study never compared avoidance with pain report.

## Table of Contents

- [What this batch is about (plain-language entry point)](#what-this-batch-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Wiech & Tracey (2013) — Pain, decisions, and actions: a motivational perspective [tier: short]](#1-wiech--tracey-2013--pain-decisions-and-actions-a-motivational-perspective-tier-short)
- [2. Wang et al. (2018) — Model-based and model-free pain avoidance learning [tier: short]](#2-wang-et-al-2018--model-based-and-model-free-pain-avoidance-learning-tier-short)
- [3. Becker et al. (2018) — Emotional and motivational pain processing [tier: short]](#3-becker-et-al-2018--emotional-and-motivational-pain-processing-tier-short)
- [4. Seymour (2019) — Pain: a precision signal for reinforcement learning and control [tier: full]](#4-seymour-2019--pain-a-precision-signal-for-reinforcement-learning-and-control-tier-full)
  - [Phase 1](#phase-1-foundational-overview) · [Phase 2](#phase-2-graduate-level-deep-dive) · [Backbone](#appendix-section-by-section-backbone)
- [5. Gandhi et al. (2022; filed as 2021) — Neural and behavioral correlates of human pain avoidance in participants with and without episodic migraine [tier: full]](#5-gandhi-et-al-2022-filed-as-2021--neural-and-behavioral-correlates-of-human-pain-avoidance-in-participants-with-and-without-episodic-migraine-tier-full)
  - [Phase 1](#phase-1-foundational-overview-1) · [Phase 2](#phase-2-graduate-level-deep-dive-1) · [Backbone](#appendix-section-by-section-backbone-1)
- [6. Jepma et al. (2022) — Different brain systems support learning from received and avoided pain during human pain-avoidance learning [tier: full]](#6-jepma-et-al-2022--different-brain-systems-support-learning-from-received-and-avoided-pain-during-human-pain-avoidance-learning-tier-full)
  - [Phase 1](#phase-1-foundational-overview-2) · [Phase 2](#phase-2-graduate-level-deep-dive-2) · [Backbone](#appendix-section-by-section-backbone-2)
- [7. Le et al. (2024) — The neural correlates of individual differences in reinforcement learning during pain avoidance and reward seeking [tier: short]](#7-le-et-al-2024--the-neural-correlates-of-individual-differences-in-reinforcement-learning-during-pain-avoidance-and-reward-seeking-tier-short)
- [8. Notes for the cross-paper synthesis](#8-notes-for-the-cross-paper-synthesis)
- [Not reviewed (no PDF)](#not-reviewed-no-pdf)

## Reading conventions

- **Page citations follow each PDF.**
  - *Wiech & Tracey 2013* (Frontiers, pp. 1–10), *Wang et al. 2018* (Brain and Neuroscience Advances, pp. 1–8), *Becker et al. 2018* (Pain Research and Management, pp. 1–12): published versions, cited by the page number printed on the article.
  - *Seymour 2019*: published Neuron review, cited by journal page (pp. 1029–1041).
  - *Jepma et al. 2022*: published eLife article, cited as "p. N of 31".
  - *Gandhi et al.* and *Le et al. 2024*: **accepted manuscripts**, cited as **"ms. p. N"** using the page number printed on the manuscript. These do not match the published journal pages.
- **No invented mathematics.** Equations appear only where the paper prints them (Jepma et al.; Le et al.; Wang et al.). Seymour (2019) has no equations. His learning rule is described in words, and the review keeps it that way.
- **Vocabulary.**
  - *Reinforcement learning (RL)*: learning the value of states or actions from outcomes, by trial and error.
  - *Prediction error*: the difference between the outcome you got and the one you expected. It drives learning.
  - *Learning rate*: how far one prediction error moves the expectation.
  - *Model-free / model-based*: learning cached action values (habit-like) versus using an internal map of how the world works to plan.
  - *Pavlovian*: learned responses to cues that predict an outcome, independent of any action. *Instrumental*: learned actions that change the outcome.
  - *Escape*: ending a pain that is under way. *Avoidance*: preventing a pain before it happens.
- **Project vocabulary.** "Pain" is correct for the human and animal work reviewed here. In this project's artificial agents the internal damage signal is **nociception**. This batch makes no claims about those agents.

---

## 1. Wiech & Tracey (2013) — Pain, decisions, and actions: a motivational perspective [tier: short]

**Citation:** Katja Wiech & Irene Tracey, "Pain, decisions, and actions: a motivational perspective," *Frontiers in Neuroscience* 7: 46, 2013. DOI 10.3389/fnins.2013.00046.
**PDF:** `docs/project/references/imperativism/sources/Wiech and Tracey 2013 - Pain decisions and actions - A motivational perspective.pdf` — published version (typeset Frontiers article, 12 PDF pages).

**Claim.** The relationship between pain and motivation is "clearly bidirectional" (p. 1). Pain motivates decisions and actions, and motivational states (fear, goals, reward expectation, social context) in turn shape how pain is perceived. The review argues for "a functional perspective on pain that sees pain not only as a somatosensory experience" (p. 9).

**Method/type.** Narrative review of behavioural and neuroimaging studies, organised in two halves.
- *How pain influences decisions and actions:* pain as a primary reinforcer in conditioning, avoidance learning, goal conflict, and pain's interruption of attention.
- *How motivational states influence pain:* fear and anxiety, stress-induced analgesia, placebo analgesia and dopamine, social influences.

**Key result or argument.**
- **Pain as a teaching signal.** The review summarises early prediction-error work with painful stimuli (Ploghaus et al. 2000; Seymour et al. 2004, 2005, 2012). It notes that learning about *relief* from pain follows "reward-like learning signals", while worsening pain follows "aversion-like signals" (p. 2).
- **Avoidance.** It presents Mowrer's two-factor theory, in which avoidance is maintained by fear reduction, and the hypothesis that successful avoidance "might be rewarding" (p. 3). It flags a limit: in avoidance studies, "aversive outcome has so far commonly been operationalized as loss of monetary reward or absence of gains" (p. 3), so whether the findings transfer to pain is untested.
- **Goals versus habits.** It suggests avoidance may be goal-directed ("model-based") or habitual, which would call for different clinical interventions (p. 3).
- **Other threads.** Costs such as pain are integrated into value signals in orbitofrontal and prefrontal cortex (Talmi 2009; Park 2011) (p. 4). The salience network gives pain priority access to attention (pp. 4–5).
- **Asymbolia and imperatives.** Pain asymbolia is cited as showing "the biological significance of this motivational component" (p. 2). The article also calls pain "imperative" in passing: "Its imperative character has made pain a popular tool in studies investigating different aspects of learning" (p. 1).

**Place in the field's history.** A pre-computational synthesis from a leading human pain-imaging group (Oxford FMRIB). It gathers the separate literatures on conditioning, decision-making, attention and modulation under one motivational framing. It predates Seymour's (2019) RL architecture, but already names temporal-difference learning, the goal-directed/habitual split and cost–benefit integration as the tools for the next step. It calls for "computational models that inform brain imaging analysis" (p. 4). The review's editor was Ben Seymour (p. 1).

**Relevance.** It records the state of the field in 2013. Pain's motivational role was accepted, but most avoidance-learning evidence still used money rather than pain. Studies correlated brain regions with processes, and the review explicitly calls this "rather descriptive" (p. 1). The word "imperative" is used informally, with no link to the philosophical theory in Part A.

**Field-history record**
- Year · community: 2013 · human-neuroscience
- Question it asked: How do pain and motivational states influence each other, in both directions, at the behavioural and neural levels?
- Position / finding in one line: Pain both motivates decisions and actions (learning, avoidance, goal conflict, attentional interruption) and is itself modulated by motivations (fear, reward expectation, social context), so it should be studied functionally rather than as a pure somatosensory experience.
- Responds to / builds on: Mowrer & Lamoreaux 1946 (two-factor theory); Vlaeyen & Linton 2000 (fear-avoidance); Ploghaus et al. 2000; Seymour et al. 2004, 2005, 2012; Kim et al. 2006; Schlund et al. 2010, 2011; Talmi et al. 2009; Park et al. 2011; Rangel & Hare 2010; Daw & Shohamy 2008; Eccleston & Crombez 1999; Scott et al. 2007
- Measures (empirical only): n.a. (review)
- Dissociation reported (empirical only): n.a. (review)
- Survey claim check: yes — cited as "Wiech & Tracey's motivational perspective" review → it is that review. The subtitle is "a motivational perspective", and it frames the pain–motivation relation as "clearly bidirectional" (p. 1).
- PDF version: published

---

## 2. Wang et al. (2018) — Model-based and model-free pain avoidance learning [tier: short]

**Citation:** Oliver Wang, Sang Wan Lee, John O'Doherty, Ben Seymour & Wako Yoshida, "Model-based and model-free pain avoidance learning," *Brain and Neuroscience Advances* 2: 1–8, 2018. DOI 10.1177/2398212818772964.
**PDF:** `docs/project/references/imperativism/sources/Wang et al. 2018 - Model-based and model-free pain avoidance learning.pdf` — published version (SAGE typeset, CC BY).

**Claim.** Pain avoidance, like reward learning, draws on two control systems: a planning ("model-based") system and a habit-like ("model-free") system. Control switches between them according to how reliable each one currently is. This switching is "possibly more dynamically flexible" for pain avoidance than for reward (abstract, p. 1).

**Method/type.** Behavioural and computational experiment, with no brain imaging.
- **Participants and stimuli.** N = 15 healthy adults (2 female). Painful electric shocks to the hand, calibrated to a rating of 5 ("moderate pain") on a 0–10 scale; mean current 32.07 mA (p. 3).
- **Task.** A two-step choice task, adapted from a reward task by Lee et al. (2014). Two sequential left/right choices lead to coloured "coins" worth 0, 1, 2 or 4 shocks.
- **Conditions (2 × 2).**
  - *Specific goal* (favours planning): only the coin matching a trial-by-trial colour rule keeps its value; any other coin gives 4 shocks.
  - *Flexible goal* (favours habit): every coin keeps its face value.
  - *Low vs. high transition uncertainty*: 0.9/0.1 vs. 0.5/0.5 state-transition probabilities.
- **Model and fitting.** The Lee et al. (2014) arbitration model: a model-free learner (SARSA) updated by outcome prediction errors; a model-based learner updated by state prediction errors, with backward planning when the goal changes; reliability estimates for each; a two-state transition process that weights them; a softmax choice rule. Six free parameters were fitted by maximum likelihood (pp. 3–4). Parameters were then compared with Lee et al.'s reward data.

**Key result or argument.**
- **Both systems show up.** Choices were better explained by the model-free learner in the flexible-goal condition (likelihood-ratio test, p < 10⁻³) and by the model-based learner in the specific-goal condition (p < 10⁻⁸) (p. 5).
- **Pain versus reward, behaviour.** In the flexible-goal, high-uncertainty condition, participants avoiding pain made fewer optimal choices than participants seeking reward in Lee et al.'s task (t = 5.335, p = 6.16 × 10⁻⁶). At the second step they fell below chance (t = 12.427) (pp. 4–5).
- **Pain versus reward, parameters.** Of six parameters, only the learning rate of the estimator that tracks model-free reliability differed: it was higher for pain (p = 0.009). The ordinary value learning rate did not differ (p. 5). The authors read this as more rapid switching between controllers under pain, which is sometimes suboptimal.
- **Authors' caveat.** The reward data come from a scanner-based task run in another lab, so "the result should be cautiously interpreted and considered provisional in the absence of a within-experiment/subject contrast" (p. 7).
- **Discussion.** The near-identical parameters "would seem to better support the existence of a common control architecture" for reward and avoidance. Differences may lie in how the outcome is represented (relief/safety vs. reward) rather than in the controller (pp. 6–7). Implications for obsessive-compulsive disorder, understood as over-habitual avoidance, are discussed (p. 7).

**Place in the field's history.** One of the first explicit transfers of the model-based/model-free arbitration framework from reward to *pain* avoidance. It supplies the empirical citation for Seymour's (2019) claim that the brain hands control between cognitive and habitual pain controllers (Seymour 2019, p. 1033 cites Wang et al. 2018). It extends two-factor and cognitive theories of avoidance (Mowrer 1947; Seligman & Johnston 1973) into formal RL terms.

**Relevance.** Pain here is purely an outcome to be minimised (a count of shocks). No trial-by-trial pain or unpleasantness ratings were collected, so the study says nothing about how the feel of pain relates to avoidance. Its evidence is behavioural and model-based, with a small sample and a between-study comparison.

**Field-history record**
- Year · community: 2018 · computational
- Question it asked: Is pain-avoidance learning controlled by separable model-based and model-free systems under a reliability-based arbitrator, as has been proposed for reward learning?
- Position / finding in one line: Choices under pain were fitted by model-free learning when outcomes did not depend on a rule and by model-based learning when they did. Arbitration looked more volatile for pain than for reward, but that comparison is cross-study and provisional.
- Responds to / builds on: Lee, Shimojo & O'Doherty 2014; Daw, Niv & Dayan 2005; Gläscher et al. 2010; Dayan & Balleine 2002; Dickinson 1985; Mowrer 1947; Dinsmoor 2001; Mineka 1979; Seligman & Johnston 1973; Gillan et al. 2014, 2016; Bolles 1970; Robbins et al. 2012
- Measures (empirical only): intensity rating [yes — calibration only] · unpleasantness rating [no] · avoidance/escape behaviour [yes — choices to avoid shocks] · desire/urge rating [no] · neural [no]
- Dissociation reported (empirical only): none between affective and behavioural measures (only one behavioural measure). Parameter-level difference: model-free reliability learning rate higher for pain than for reward (cross-study), with other parameters unchanged.
- Survey claim check: yes — "model-based and model-free routes" of pain-avoidance learning → the paper reports evidence that "avoidance learning can be under the control of two different systems – a cognitive 'model-based' system and a 'model-free' habit system" (p. 5). The survey claim omits that the pain-vs-reward difference is called "provisional" (p. 7) and that there are no neural data.
- PDF version: published

---

## 3. Becker et al. (2018) — Emotional and motivational pain processing [tier: short]

**Citation:** Susanne Becker, Edita Navratilova, Frauke Nees & Stefaan Van Damme, "Emotional and Motivational Pain Processing: Current State of Knowledge and Perspectives in Translational Research," *Pain Research and Management* 2018: 5457870, 2018. DOI 10.1155/2018/5457870.
**PDF:** `docs/project/references/imperativism/sources/Becker et al. 2018 - Emotional and motivational pain processing.pdf` — published version (Hindawi typeset, CC BY; Wiley Online Library download stamp).

**Claim.** Chronic pain involves a "shift to negative emotional-motivational processing" (p. 1). Changes in reward processing, learning, goal regulation and avoidance may drive the transition from acute to chronic pain. Human and animal research need each other to test this. "Unrelenting pain loses its alerting and motivational utility and becomes a constant burden that disrupts goal-directed behavior" (p. 7).

**Method/type.** Narrative translational review in three parts.
- Human studies in healthy volunteers and chronic pain patients, organised by reward processing, learning, and goal regulation/approach/avoidance.
- Preclinical animal studies of pain-motivated behaviour and corticolimbic circuits.
- A section on translating between them.

**Key result or argument.**
- **Goal regulation.** Self-regulation theory: in persistent pain, repeated failure to pursue valued goals can shift priority to a dominant "pain control" goal, with narrowed attention and avoidance (p. 2).
- **Reward.** Pain relief is itself rewarding and engages endogenous pain inhibition (Becker et al. 2015) (p. 3). The review cites a wanting/liking dissociation (Berridge): "Pain has been reported to increase wanting while leaving liking unaltered" (p. 2, citing Gandhi et al. 2013).
- **Learning.** A caveat on operant studies that reward pain *reports*: "it is conceivable that in those studies, only participants' rating behavior was changed ... but not necessarily the perception of pain" (p. 3).
- **Competing goals.** A competing money goal reduces avoidance of a pain-associated movement. In Claes et al., the rewarded pain movement was performed more often "although pain-related fear remained unaltered" (p. 4).
- **Animal work on dopamine and relief.**
  - Midbrain dopamine neurons respond in mixed ways to noxious events: most are inhibited, some are excited, some rebound at pain offset.
  - Fast-scan voltammetry shows a tail pinch raises dopamine in the dorsal striatum and nucleus-accumbens core, suppresses it in the shell, and raises it again at offset (p. 5).
  - Pain relief produces conditioned place preference "only in injured but not sham-operated animals" (p. 5). This preference depends on dopamine in the nucleus accumbens and on opioids in the anterior cingulate cortex (pp. 5–6).
- **Translation.** Operant assays (conditioned place preference/avoidance, the place escape/avoidance paradigm) are presented as the available animal readouts of "affective-motivational aspects" of pain (p. 6).

**Place in the field's history.** A 2018 bridge between the clinical-psychology tradition (fear-avoidance, goal/self-regulation models: Van Damme, Crombez, Vlaeyen) and animal circuit work on relief reward (the Porreca/Navratilova line). It treats emotional and motivational processing as one construct ("emotional-motivational"). It is not an RL paper; it contains no formal models.

**Relevance.** It collects, second-hand, several reported dissociations useful to a field history: wanting vs. liking under pain; avoidance behaviour changing while fear stays constant; relief acting as a reward only in animals that are in pain. It also records the methodological worry that reinforcing ratings may change reports rather than experience.

**Field-history record**
- Year · community: 2018 · clinical-psychology
- Question it asked: What human and animal evidence explains the shift toward negative emotional-motivational processing in chronic pain, and how can translational research connect the two?
- Position / finding in one line: Chronic pain is associated with altered reward, learning, goal regulation and avoidance, supported by corticolimbic dopamine/opioid circuits in animals, and these emotional-motivational changes (not only nociception) plausibly contribute to chronification.
- Responds to / builds on: IASP definition (Loeser & Treede 2008); Van Damme et al. 2008, 2010; Crombez et al. 2012; Leeuw et al. 2007; Berridge et al. 2009 (liking/wanting); Gandhi et al. 2013; Leknes & Tracey 2008; Cabanac 1979; Baliki et al. 2010; Brandtstädter & Rothermund 2002; Taylor et al. 2016
- Measures (empirical only): n.a. (review)
- Dissociation reported (empirical only): n.a. (review; it cites wanting-vs-liking and avoidance-vs-fear dissociations from other studies, p. 2 and p. 4)
- Survey claim check: yes — cited as a review on "emotional-motivational processing" → it is that review, titled "Emotional and Motivational Pain Processing", organised around "a shift to negative emotional-motivational processing in chronic pain" (p. 1).
- PDF version: published

---

## 4. Seymour (2019) — Pain: a precision signal for reinforcement learning and control [tier: full]

**Citation:** Ben Seymour, "Pain: A Precision Signal for Reinforcement Learning and Control," *Neuron* 101(6): 1029–1041, 2019. DOI 10.1016/j.neuron.2019.01.055.
**PDF:** `docs/project/references/imperativism/sources/Seymour 2019 - Pain - A precision signal for reinforcement learning and control.pdf` — published version (Neuron Review, typeset, 13 PDF pages; PDF p. 1 = journal p. 1029).

### Phase 1: Foundational Overview

**Introduction.** Pain research has had three puzzles. (1) Pain activates many brain regions, none unique to pain. (2) People's pain reports vary from moment to moment. (3) Pain is turned up and down by emotion, expectation, attention and context ("endogenous modulation"). Seymour argues that all three make sense once pain is seen as a **learning and control signal**, not a readout of tissue damage. The paper's abstract states the core claim: "the core function of pain is motivational—to direct both short- and long-term behavior away from harm" (p. 1029).

**Key findings (argument).**
- **Learning is central.** A child who touches a hot stove benefits mainly because the pain teaches them not to touch stoves again. When a harmful outcome comes at the end of a long chain of actions, finding which action was to blame is the *credit assignment problem*. RL solves it by passing predictions back in time (p. 1030).
- **Four layers of control.** The pain system is organised as a hierarchy: (1) innate reflexes and defensive responses; (2) Pavlovian learning, where cues come to predict pain; (3) instrumental, habit-like ("model-free") learning of escape and avoidance actions; (4) cognitive, planning ("model-based") learning. The layers interact, with faster, cruder systems setting the starting point for slower, cleverer ones (pp. 1031–1033).
- **Pain is separate from the sensing of damage.** In this architecture "'pain' is the internal reinforcement signal used for learning and is distinct from the nociceptive sensing process" (p. 1031).
- **Modulation has a purpose.** Pain *should* be modulated if it is to work as a good control signal. Seymour gives four reasons: better sensory estimates, the value of pain as a predictor of other events, conflict with more important goals, and the information value of learning (pp. 1033–1035).
- **Self-report loses its privileged place.** Because pain is about control, "control behavior should serve as the ultimate measure of pain" (p. 1037).

**Initial takeaway.** This is the most explicit statement in the corpus that pain *is* a reinforcement-learning signal. On this view, pain's tuning by context is part of its job, not noise. The title's word "precision" means *precise and objectively definable* ("recasting pain as a precise and objectifiable control signal", p. 1029). It is not the "precision-weighting" of predictive-coding models.

### Phase 2: Graduate-Level Deep Dive

**Technical analysis — the historical argument (pp. 1029–1030).** Seymour positions RL as the next step in a lineage of theories:

| Theory | What it added (per Seymour) | What it left open |
|---|---|---|
| Melzack & Casey 1968, tripartite model | sensory-discriminative, affective-motivational and cognitive-evaluative components; protective behaviour intrinsic to pain; the "man-in-the-brain" problem | how behaviour is controlled |
| Melzack & Wall 1965, gate control | descending modulation of dorsal-horn transmission | — |
| Craig 2002, 2003, homeostatic model | pain as an interoceptive feeling with intrinsic motivational value; posterior-to-anterior insula hierarchy | "how homeostatic behaviors were actually implemented, and why pain was modulated by so many factors" |
| Fields 2006, 2018, motivation-decision model | pain inhibited when more important goals dominate (via the brainstem descending route from periaqueductal grey to rostral ventromedial medulla, PAG–RVM); role of learning, escape and avoidance; pain as predictive | — |
| Bayesian inference / predictive coding (Büchel et al. 2014), free energy / active inference (Friston 2010; Tabor & Burr 2019) | pain as inference combining prior expectations and nociceptive input; explains expectancy, placebo and nocebo | "inferential theories of pain processing leave open an account of how the motivational function of pain is directed" |

The paper's pivotal question is whether conscious pain reflects "an optimal inference of a real or presumed nociceptive stimulus, or an optimal control signal to minimize current and future nociceptive stimuli?" (p. 1030). The paper answers: control signal.

**Technical analysis — the architecture (pp. 1030–1033, Figures 1–2).**

1. *Credit assignment.* The Rescorla–Wagner rule updates predictions from a prediction error at the outcome, which fails when outcomes are far in the future. RL "simply use[s] the next available prediction (formalized as the value) as a proxy for the outcome". It computes differences between successive value predictions plus any outcome received, which "passes the prediction back to the earliest reliable predictor" (pp. 1030–1031). The paper gives this rule in words only (Figure 1B caption); it prints no equation.
2. *Agent–environment interface* (Figure 1C). Sensing produces an internal representation of state and of salient outcomes. The agent learns state and action values, computes prediction errors and selects actions. Pain is the internal reinforcement signal, distinct from nociceptive sensing, "in the same way that reward is distinct from the sensory properties of a reinforcer" (p. 1031).
3. *Innate responses.* Motor, autonomic and behavioural defences, "stimulus specific, situation specific, and species specific", fast and strong enough to override ongoing behaviour. They run through spinal, brainstem and hypothalamic–PAG circuits (p. 1031).
4. *Pavlovian learning.*
   - Higher-order pain prediction errors transfer predictions back to the earliest cue (Seymour et al. 2004).
   - Two kinds of response: pain-specific (well-timed motor responses, possibly cerebellar) and non-specific (withdrawal, arousal; amygdala, ventral putamen, ventral PAG, VTA, dorsal raphe).
   - Uncertainty raises learning rates. Values generalise to similar cues (pp. 1031–1032).
5. *Instrumental learning.*
   - Escape (from ongoing pain) and avoidance (of upcoming pain). Separate action values for relief and for pain are learned in parallel and combined ("multi-attribute RL").
   - "Relief values can approximate the best-case scenario of future actions ('what to do'), and pain values can approximate the worst-case scenarios ('what not to do')". Keeping them separate "conserves information and allows for safer behavior" (Elfwing & Seymour 2017) (p. 1032).
   - Neural substrates: posterior putamen and amygdala, with ventromedial prefrontal action values. Pain-predictive action values generalise via insula and relief-predictive ones via ventromedial prefrontal cortex (Norbury et al. 2018) (p. 1033).
6. *Cognitive (model-based) learning.* Internal models support planning, explicit evaluation ("the ability to report a pain prediction or intensity judgment"), instructed and observational learning, and inference of hidden states. Substrates are prefrontal, anterior cingulate and hippocampal (p. 1033).
7. *Conscious pain and interacting controllers.* Controllers need not share one reinforcement signal. Innate defences are tied to early nociceptive input, while the cognitive controller uses slower, conscious processing. Even if conscious pain were an epiphenomenon, "its perception would still lead to avoidance of this state in the future, given the choice. For this reason, at the very least conscious pain must act as a control signal related to cognitive learning systems" (p. 1033). Innate and Pavlovian systems set "action priors". The model-free system takes over when avoidance becomes reliable (citing Wang et al. 2018). The cost is susceptibility to impulsivity and compulsivity (p. 1033).

**Technical analysis — endogenous control as optimisation (pp. 1033–1036).** Four sources of modulation, each derived from the needs of an RL controller:

| Modulation | Rationale in the RL model | Examples cited |
|---|---|---|
| Sensory inference | Nociceptive input is noisy; approximately Bayesian estimation improves the intensity estimate. It may be weighted by asymmetric error costs, since under-estimating pain can cost more than over-estimating. | expectancy biases scaling with prior certainty (Brown et al. 2008; Yoshida et al. 2013); disconfirming evidence under-weighted (Jepma et al. 2018) |
| Predictive value | Pain is both an outcome and a cue, so its aversiveness combines its value as an outcome with its value as a predictor. | Pavlovian counter-conditioning, where pain predicting food loses its aversive response (Erofeeva 1921); dread plus temporal discounting giving an "n"-shaped function (Story et al. 2013); peak-end effect |
| Decision conflict | Innate responses are wired early in the pathway, so the only way to suppress them when a competing action matters more is to suppress ascending nociceptive signals, which produces analgesia. This extends to cognitive conflict. | Fields 2006, 2018; Dum & Herz 1984; Eccleston & Crombez 1999 |
| Informational value | The benefit of learning depends on uncertainty, opportunity and controllability. Phasic pain should be *enhanced* when these are high; tonic pain should be *reduced* when learning about relief is valuable. | Zhang et al. 2018a, 2018b; attention and controllability effects (Salomons et al. 2007, 2015); offset hypoalgesia / onset hyperalgesia |

The paper identifies the effector as PAG–RVM–dorsal horn descending control. Pregenual anterior cingulate cortex is "the most consistently implicated cortical region" across placebo, uncertainty, controllability, habituation and stress-induced analgesia (p. 1035). It also names a paradox: modulation risks degrading pain's information. The proposed resolution is that discriminative information is preserved while affective components are suppressed. Evidence cited: opioid and cingulotomy observations (Melzack & Casey 1968); medial vs. lateral pain systems; preferential descending control of C-fibres over A-delta fibres (p. 1036).

**Box 1 predictions (p. 1035).**
1. Controllability and uncertainty have opposite effects on phasic and tonic pain. The paper describes existing support as "mixed".
2. Endogenous control should drive exploratory choice.
3. Fine pain discrimination should be preserved during endogenous analgesia. The paper notes there is "yet no behavioral evidence" for this.

**Chronic pain (pp. 1036–1037).** Tonic pain has adaptive functions: it promotes rest, makes relief a goal, and sensitises the injured area. Chronic pain is proposed to arise from interacting individual RL parameters, a "computome" of risk factors (Figure 3). Examples: excessive aversive valuation, asymmetric aversive learning rates, over-generalisation, loss of endogenous control, excessive dread, and an "irrefutable belief" biasing inference.

**Argument reconstruction (the rigour of this conceptual paper).**
- P1. The primary function of the pain system is to minimise current and future harm (p. 1030).
- P2. Most harm reduction comes from learning to predict and avoid harm, which requires solving the credit assignment problem (p. 1030).
- P3. RL solves credit assignment, and there is evidence that the brain uses RL-like prediction errors for pain (Seymour et al. 2004 onward) (pp. 1030–1031).
- P4. Speed, sophistication and safety trade off; a nested hierarchy of controllers (innate → Pavlovian → model-free → model-based) balances them (pp. 1031–1033).
- P5. For such a controller to work well, the reinforcement signal must be adjusted by sensory inference, predictive value, decision conflict and informational value (pp. 1033–1035).
- C1. The many known modulations of pain are therefore expected features of an optimal control signal, not noise (pp. 1033–1036).
- C2. Pain is "a precision signal", tuned precisely to its function. As a prospective control signal it "behaves in precisely the way it needs, and hence should not be considered to be modulated at all" (p. 1037).
- C3. Because pain is fundamentally about control, "the RL model challenges the primacy of self-report" and "control behavior should serve as the ultimate measure of pain" (p. 1037).

**Where the argument is exposed (reviewer's notes, not the paper's).**
- C2 is partly definitional. Once any modulation can be recast as optimisation, the model's testable content lies in Box 1's specific predictions, which the paper concedes are not yet demonstrated.
- C3 sets behaviour above report. The paper does not specify how the four modulations should show up differently in behaviour and in report. That is exactly the valence-vs-avoidance question the wider corpus is concerned with.
- The architecture is a review-level synthesis, with no simulation reported in this paper. It points to Elfwing & Seymour (2017) for simulation evidence that multi-attribute learning is safer.

### Appendix: Section-by-Section Backbone

**Introduction (p. 1029).** Three problems: no pain-specific region, variable self-report, endogenous modulation. Proposal: pain as a learning and control signal; the review's plan.

**Background (pp. 1029–1030).** The lineage: tripartite model and man-in-the-brain problem; gate control; homeostatic/interoceptive model; motivation-decision model; Bayesian and predictive-coding models; free energy and active inference. None fully captures how pain balances stimulus identification, information seeking, harm minimisation and speed. Pivotal question: optimal inference or optimal control signal (p. 1030).

**The RL Model — The Credit Assignment Problem (pp. 1030–1031).** Hot-stove example. Five-action sequence example. Rescorla–Wagner vs. temporal-difference RL. Figure 1: credit assignment, prediction-error rule (in words), agent–environment interface. Pain as the internal reinforcement signal distinct from nociceptive sensing.

**Innate Responses (p. 1031).** Specific, rapid, strong defensive responses; spinal/brainstem/hypothalamic–PAG circuits.

**Pavlovian Learning (pp. 1031–1032).** Higher-order prediction errors; specific vs. non-specific responses; uncertainty raises learning rate; generalisation; negative interaction with reward circuits.

**Instrumental Learning (pp. 1032–1033).** Escape and avoidance; parallel relief and pain action values; multi-attribute RL; Pavlovian–instrumental interactions (two-factor theory, conditioned suppression, Pavlovian-instrumental transfer); posterior putamen/amygdala; generalisation via insula vs. ventromedial prefrontal cortex. Figure 2: the RL model of pain.

**Cognitive Learning (p. 1033).** Model-based learning, hidden states, rules; subsumes Pavlovian and instrumental; Bayesian accounts of conditioning; intermediate strategies (Momennejad et al. 2017); prefrontal, anterior cingulate and hippocampal substrates.

**Conscious Pain Perception and Interactions between Controllers (p. 1033).** Controllers may use different signals; conscious pain must at least control cognitive learning; action priors; hand-off to model-free control (Wang et al. 2018); susceptibility to impulsivity and compulsivity.

**Endogenous Control (pp. 1033–1036).** Sensory inference; predictive value (counter-conditioning, dread, peak-end); decision conflict; informational value (uncertainty, opportunity, controllability; phasic vs. tonic); neural implementation (PAG–RVM, pregenual anterior cingulate); preservation of discriminative information. Box 1: three predictions.

**Translation to Chronic Pain (pp. 1036–1037).** Functions of tonic pain; perceptual and motivational routes to chronicity; fear-avoidance model; the "computome" (Figure 3); a call for simulation.

**Conclusions (pp. 1036–1037).** Four evolutionary problems and their solutions: credit assignment via RL; speed–accuracy via hierarchy; information sampling via endogenous tuning; suppression without information loss via dissociable discriminative and affective components. Implications for the "pain matrix", for self-report, and for the concept of modulation. Open question: "where is the 'cognitive map' of pain?"

**Field-history record**
- Year · community: 2019 · computational
- Question it asked: Is conscious pain best understood as an optimal inference about a nociceptive stimulus or as an optimal control signal for minimising current and future harm, and what architecture would implement the latter?
- Position / finding in one line: Pain is a reinforcement signal within a hierarchy of innate, Pavlovian, model-free and model-based controllers, and its endogenous modulations are optimal tunings of that signal. This challenges the primacy of self-report in favour of control behaviour.
- Responds to / builds on: Melzack & Casey 1968; Melzack & Wall 1965; Craig 2002, 2003; Fields 2006, 2018; Büchel et al. 2014; Friston 2010; Tabor & Burr 2019; Rescorla & Wagner 1972; Sutton & Barto 1998; Seymour et al. 2004, 2005, 2012; Elfwing & Seymour 2017; Wang et al. 2018; Zhang et al. 2018a, 2018b; Vlaeyen & Linton 2000; Eccleston & Crombez 1999
- Measures (empirical only): n.a. (review / theory)
- Dissociation reported (empirical only): n.a. (review / theory; it discusses the preserved-discrimination-under-analgesia dissociation, p. 1036)
- Survey claim check: partly — "the core function of pain is motivational, and it is best understood as a precision-weighted RL control signal" → the first half is verbatim: "the core function of pain is motivational—to direct both short- and long-term behavior away from harm" (p. 1029). The second half misreads "precision". The paper recasts pain "as a precise and objectifiable control signal" (p. 1029) and says pain "behaves in precisely the way it needs" (p. 1037). The phrase "precision-weighted" never appears, and the paper does not adopt the predictive-coding sense of precision weighting. Uncertainty-based modulation is framed as the informational value of learning (p. 1035).
- PDF version: published

---

## 5. Gandhi et al. (2022; filed as 2021) — Neural and behavioral correlates of human pain avoidance in participants with and without episodic migraine [tier: full]

**Citation:** Wiebke Gandhi, Cecile C. de Vos, Susanne Becker, Richard D. Hoge, Marie-Eve Hoeppli & Petra Schweinhardt, "Neural and behavioral correlates of human pain avoidance in participants with and without episodic migraine," *Pain* 163(6): 1023–1034, 2022. DOI 10.1097/j.pain.0000000000002472.
**PDF:** `docs/project/references/imperativism/sources/Gandhi et al. 2021 - Neural and behavioral correlates of human pain avoidance.pdf` — **accepted manuscript**, from the University of Reading repository (CentAUR, "Accepted Version"; 44 PDF pages, of which 2 are repository cover pages). The cover sheet gives the year as 2022 and prints the volume as "136 (6)", which appears to be a typo for 163. The corpus filename and title are shortened: the full title ends "in participants with and without episodic migraine". Page citations are manuscript pages.

### Phase 1: Foundational Overview

**Introduction.** People normally try hard to avoid pain. But repeated pain that *cannot* be escaped can wear this drive down, leading to passivity and helplessness, a phenomenon known since "learned helplessness" experiments in animals. Rodent studies point to the periaqueductal grey (PAG), a midbrain defence hub, as the driver of pain avoidance. This study asked whether the same holds in humans, and whether people who live with frequent unavoidable pain (episodic migraine) respond differently after failing to avoid pain.

**Key findings.**
- In a reaction-time game, a fast button press avoids a painful shock. People responded faster as avoidance got harder. After a failed attempt they were slower on the next difficult trial (ms. pp. 19–20).
- People with migraine slowed more after failure than people without migraine. Within the migraine group, those who felt more helpless about their migraines slowed the most (ms. pp. 20–21).
- Getting ready to avoid pain engaged a wide brain network, including the PAG. But the PAG did *not* change after failure and was *not* related to helplessness. Activity in the **posterior parietal cortex** (an attention area) did both. In people with migraine, a bigger drop in parietal activity after failure went with a bigger behavioural slowdown (ms. pp. 22–24).
- The authors conclude, "in disagreement with the original hypothesis – that PPC rather than PAG plays a key role in human pain avoidance" (ms. p. 25).

**Initial takeaway.** Human pain-avoidance *vigour* (how fast people act to avoid pain) falls after failure, especially in people with a history of unavoidable pain who feel helpless. The neural correlate was an attention and preparation area, not the midbrain defence hub. The study did not collect pain ratings during the task, so it does not compare avoidance with how the pain felt.

### Phase 2: Graduate-Level Deep Dive

**Hypotheses (ms. p. 4).**
- H1: greater avoidance behaviour after successful than unsuccessful avoidance.
- H2: readiness to avoid pain is driven by the PAG.
- H3: in migraine, the reduction in behaviour and neural activation after failure grows with self-reported helplessness.

**Design and sample (ms. pp. 5–6).**
- An a-priori power analysis for a medium interaction effect (f = 0.25) required 28 participants; 34 were recruited (+20%).
- Two were excluded for not following instructions, leaving **N = 32**: 6 male, 26 female, age 27 ± 5; 15 with episodic migraine (ICHD-II criteria, 1–15 attacks/month, pain-free at testing), 17 without.
- Humans, single session, 3 T fMRI.

**Stimuli and calibration (ms. p. 8).**
- Painful stimulus: transcutaneous electrical stimulation over the sural nerve.
- Non-painful stimulus: stimulation over the tibialis anterior.
- Intensities were set by staircase on a **single 0–100 scale anchored "no sensation" to "extremely painful/unpleasant"**, with 10 = "just painful/unpleasant". The painful target was ~75, the non-painful ~5. Intensity and unpleasantness were therefore **not rated separately**, and ratings were used only for calibration.
- Delivered intensities did not differ by group: 6.5 ± 2.8 mA without migraine vs. 7.3 ± 3.5 mA with migraine, p = 0.46 (ms. p. 19).

**Manipulation — the pain avoidance task (ms. pp. 9–10).**
- An adapted Incentive Delay Task (Knutson et al. 2000). A cue word ("safe", "easy", "difficult") is shown for 2–12 s: the *preparatory phase*, analysed in fMRI.
- A target then appears. Pressing within 310 ms (easy) or 230 ms (difficult) delivers the non-painful stimulus; slower responses deliver the painful one. On "safe" trials any response avoids pain.
- Target success rates were 100/67/33%. 36 trials (12 per level), about 11 min.
- A separate motor-visual control task (checkerboard + button press) was used to check that the haemodynamic response did not differ between groups.

**Measures.**
- *Behaviour:* response speed = 1/RT, the index of avoidance vigour. Trials with RT < 150 ms or > 1000 ms were excluded (10 of 1152).
- *Questionnaires:* Beck Depression Inventory-II; the hope/helplessness subscale (HHS) of the Avoidance-Endurance Questionnaire. Participants with migraine answered about their migraine, controls about everyday pains.
- *fMRI:* multiband EPI, TR = 854 ms, 2 mm isotropic; FSL; ICA-AROMA denoising.
  - Preparatory-phase GLMs: a "basic GLM" with 6 conditions (difficulty × previous outcome) and a "linear GLM" weighting difficulty 1/2/3.
  - Group level: FLAME, voxel z > 2.3, cluster-corrected p < 0.05; log HHS as a second-level regressor.

**Key statistics as reported.**

*Behaviour (ms. pp. 19–21).*

| Effect | Statistic |
|---|---|
| Difficulty (faster with harder trials) | F(2,78) = 43.61, p < 0.001 |
| Outcome on preceding trial | F(1,614) = 6.79, p = 0.009 |
| Difficulty × preceding outcome | F(2,692) = 3.48, p = 0.031 |
| Difficult trials, after failure vs. success | −35.86 ms, p < 0.001, d = 0.49 |
| Preceding outcome × group | F(1,614) = 4.43, p = 0.036 |
| Group, after failure | F(1,88) = 9.45, p = 0.003; difficult trials 32.65 ms slower in migraine, p = 0.007, d = 0.59 |
| Group × difficulty (after failure) | F(2,132) = 1.33, p = 0.269 (n.s.) |
| Helplessness vs. slowdown after failure, migraine | r = 0.67, p = 0.007 |
| Same, controls | r = −0.47, p = 0.057 (driven by many HHS = 0) |

The authors note "large overlaps" between groups in individual data (ms. p. 20). Within migraine, HHS ranged 0–48 (mean 21, SD 13) and correlated with attack length (r = 0.59, p = 0.021) (ms. p. 18). Success rates were 68.25% (easy) and 32.25% (difficult), with no group difference (ms. p. 19).

*Neural (ms. pp. 21–24).*
- **"Preparatory matrix."** Activation increasing with difficulty: bilateral dlPFC, anterior insula, PPC, ACC, premotor cortex, SMA, left M1, basal ganglia, cerebellum, **PAG** and superior colliculus.
- **After failure vs. success.** Reduced activation in bilateral PPC, SMA, ACC, premotor cortex, S2 and insula.
- **After failure, by group.** Controls showed a greater difficulty-related increase in right parietal cortex than migraine participants.
- **Helplessness (migraine, difficult trials after failure).** Negative correlation with bilateral M1, left PPC, bilateral S2 and left hippocampus/parahippocampus. The association was stronger in migraine than in controls for right PPC/PCC, bilateral M1, bilateral S2 and right posterior insula.
- **Linking brain to behaviour (migraine).** Activation change (success − failure) in the helplessness-related network correlated with response-speed change, r = 0.53, p = 0.042. This was driven by left PPC (r = 0.668, p = 0.007); the other clusters had p > 0.49.

**Inferential step from result to claim.**
1. PAG/superior colliculus appears in the preparatory matrix but shows no previous-outcome effect and no helplessness association. The authors infer "PAG/SC might be unaffected by immediate performance feedback as well as by long-term experiences with unavoidable pain" (ms. p. 26). They explain the difference from rodent work by design: rodent studies mostly measured defence *execution* or responses to noxious input, not preparation to avoid an imminent pain (ms. p. 26).
2. PPC is reduced after failure, is less recruited in migraine, scales with helplessness, and its change correlates with behavioural change. Hence "PPC rather than PAG plays a key role in human pain avoidance" (ms. p. 25), interpreted as reduced *alertness* after perceived poor performance (ms. p. 27).
3. Helplessness is interpreted as a misappraisal of the benefit/cost ratio, an underestimate of one's own ability to avoid pain (ms. pp. 28–29). This is offered as a way to reconcile the reduced avoidance vigour with the *increased* avoidance usually reported in chronic pain.

**Reviewer's notes on the inference (not the paper's).**
- The abstract says PPC activation "predicted individual's pain avoidance behavior on the next trial" (ms. p. 2). The reported test is an across-participant correlation of difference scores within the 15 migraine participants (ms. pp. 23–24), not a trial-level prediction.
- The PPC region was selected for its correlation with helplessness, and helplessness itself correlates with the behavioural slowdown. The brain–behaviour correlation is therefore not independent of the selection step.
- The PAG conclusion rests on non-significant effects at whole-brain threshold. The authors acknowledge the small sample (ms. p. 29).
- The single painful/unpleasant rating anchor means this study cannot speak to intensity vs. unpleasantness.

**Limitations stated by the authors (ms. p. 29).** Sample sized for the behavioural effect, so relatively small for imaging. Helplessness findings rest on the migraine subsample (n = 15) and "are to be interpreted with caution".

### Appendix: Section-by-Section Backbone

**Abstract (ms. p. 2).** Uncontrollable stress disrupts pain avoidance. PAG role unknown in humans. N = 32 with/without episodic migraine; Incentive Delay Task adaptation; reduced avoidance after failure, especially when difficult; helplessness associations in migraine; PPC predicts behaviour.

**1. Introduction (ms. pp. 3–4).** Avoidance is crucial and adjusts to recent experience; inescapable pain disrupts it (Maier & Seligman 1976; Seligman & Maier 1967). Rodent PAG in risk assessment and defence. Migraine as a model of repeated unavoidable pain with variable helplessness. Hypotheses H1–H3.

**2.1–2.2 Sample size and participants (ms. pp. 5–6).** Power calculation; exclusion criteria; final N = 32; medication; migraine with/without aura.

**2.3 Experimental procedure (ms. p. 7).** Calibration in scanner, practice, pain avoidance task, second task (not reported), structural scan, control task, questionnaires (BDI-II, AEQ-HHS).

**2.4 Electrical stimulation (ms. p. 8).** Sural nerve pain; tibialis non-pain; staircase to ~75 and ~5 on a combined painful/unpleasant 0–100 scale.

**2.5 Behavioral tasks (ms. pp. 9–10).** Pain avoidance task timings and RT windows; motor-visual control task rationale (migraine may alter neurovascular coupling).

**2.6 MRI acquisition (ms. p. 11).** 3 T Siemens Trio, multiband EPI TR 854 ms, MP-RAGE.

**2.7 Statistical analysis (ms. pp. 11–17).** Group as between factor; response speed = 1/RT; mixed rmANOVA; Pearson correlations with log HHS; Bonferroni. fMRI: preprocessing, basic and linear GLMs, FLAME, HHS regressor, FEATquery extraction; finite-impulse-response haemodynamic estimation in V1, M1 and putamen for the control task.

**3.1 Participant characteristics (ms. p. 18).** HHS spread; HHS ~ attack duration; groups matched on age, sex and depression; no haemodynamic response differences.

**3.2 Stimulation and success rates (ms. p. 19).** No group differences in intensities or success rates.

**3.3 Behaviour (ms. pp. 19–21).** Difficulty and previous-outcome effects; group × previous outcome; helplessness correlation in migraine only.

**3.4 Neural (ms. pp. 21–24).** Preparatory matrix; reductions after failure; group difference in right parietal cortex; helplessness-related networks; left PPC brain–behaviour correlation.

**4. Discussion (ms. pp. 25–29).** PPC rather than PAG. PAG/SC and cerebellum consistently engaged but unaffected by outcome or clinical pain; design differences from rodent work. Right insula as a task-performance evaluator feeding PPC attention; reduced alertness. Helplessness and neurobiological individual differences. Benefit/cost misappraisal.

**Limitations and Conclusion (ms. pp. 29–30).** Small sample; migraine subsample. Avoidance adjusts promptly to success; migraine plus helplessness amplifies disruption via reduced PPC.

**Field-history record**
- Year · community: 2022 · human-neuroscience
- Question it asked: How does failing versus succeeding to avoid pain change subsequent avoidance behaviour and preparatory brain activity in humans, is the PAG involved as in rodents, and does helplessness in people with episodic migraine amplify the effect?
- Position / finding in one line: Avoidance vigour dropped after failed avoidance, more so in migraine and with greater helplessness. The accompanying change was reduced posterior parietal (not PAG) activation, which the authors read as reduced alertness.
- Responds to / builds on: rodent PAG defence studies (Bandler & Carrive 1988; Deng et al. 2016); Seligman & Maier 1967; Maier & Seligman 1976; Knutson et al. 2000 (Incentive Delay Task); Gandhi et al. 2013, 2017; Roy et al. 2014; Lynn et al. 2016; Hasenbring et al. 2009 (AEQ)
- Measures (empirical only): intensity rating [yes — calibration only, on a single scale anchored "extremely painful/unpleasant"] · unpleasantness rating [no — not separated from intensity] · avoidance/escape behaviour [yes — response speed to avoid shock] · desire/urge rating [no] · neural [fMRI (BOLD), preparatory phase]
- Dissociation reported (empirical only): Previous avoidance failure lowered response speed and PPC/SMA/ACC/insula preparatory activation, while PAG/superior colliculus and cerebellum activation stayed unaffected by previous outcome and by helplessness. Physical stimulus intensities did not differ between groups. No pain-report measure was taken during the task, so there is no report-vs-avoidance dissociation.
- Survey claim check: no — "Human pain-avoidance behavior has neural correlates distinct from pain report" → the study never compares avoidance with pain report; pain ratings served only to calibrate stimuli before the task (ms. p. 8). Its actual claim is that "PPC rather than PAG plays a key role in human pain avoidance, with diminished PPC activation during pain threats underpinning behavioral disruptions, especially in migraine patients with elevated helplessness levels" (ms. p. 25). The survey also drops the migraine/helplessness focus from the title.
- PDF version: accepted manuscript

---

## 6. Jepma et al. (2022) — Different brain systems support learning from received and avoided pain during human pain-avoidance learning [tier: full]

**Citation:** Marieke Jepma, Mathieu Roy, Kiran Ramlakhan, Monique van Velzen & Albert Dahan, "Different brain systems support learning from received and avoided pain during human pain-avoidance learning," *eLife* 11: e74149, 2022. DOI 10.7554/eLife.74149.
**PDF:** `docs/project/references/imperativism/sources/Jepma et al. 2022 - Different brain systems support learning from received and avoided pain.pdf` — published version of record (eLife typeset, 31 pages including appendices; received 23 Sep 2021, preprinted 18 Oct 2021, accepted 7 Jun 2022, published 22 Jun 2022).

### Phase 1: Foundational Overview

**Introduction.** Two kinds of surprise can teach you what to avoid. One is getting hurt when you did not expect it (a *threat* lesson). The other is *not* getting hurt when you expected to be (a *safety* lesson). A patient recovering from knee surgery needs both: to learn which movements hurt, and later to learn that they no longer do. Does the brain learn both lessons with one system, or with two? And do the brain chemicals dopamine and endogenous opioids play a part?

**Key findings.**
- **Design.** 83 healthy volunteers chose repeatedly between two symbols. Each symbol carried a slowly changing chance of a painful heat stimulus to the leg. Before the task, each person took a pill: levodopa (boosts dopamine), naltrexone (blocks opioid receptors) or placebo.
- **Behaviour on placebo.** A learning model showed that people updated their expectations much more after getting hurt than after escaping pain. Learning rate was 0.72 for received pain vs. 0.32 for avoided pain (p. 5 of 31). A reanalysis of an earlier dataset showed the same direction (p. 7 of 31).
- **Drugs.** Both levodopa and naltrexone raised learning from *avoided* pain to the level of learning from received pain. They did not change learning from received pain (p. 5 of 31).
- **Brain.** Surprise at *received* pain was tracked mostly in deep and limbic regions (brainstem, insula–amygdala, rostral cingulate, cerebellum). Surprise at *avoided* pain was tracked in frontal and parietal cortex (p. 10 of 31).
- **No drug effect on brain signals.** Neither drug changed any of these brain signals (p. 10 of 31).

**Initial takeaway.** The authors conclude that "human pain-avoidance learning is supported by separate threat- and safety-learning systems, and that dopamine and endogenous opioids specifically regulate learning from successfully avoided pain" (p. 1 of 31). Avoided pain did not produce a striatal "reward-like" signal. On the authors' reading, learning from avoided pain is in this respect "not comparable to learning from rewards" (p. 12 of 31).

### Phase 2: Graduate-Level Deep Dive

**Design and sample (pp. 3, 15 of 31).**
- Randomised, double-blind, between-subject pharmacological fMRI study.
- 91 healthy students recruited (18–26 years, 71% female, right-handed). Excluded: 6 for thermode failure, 2 for poor or irrelevant task strategies.
- **Behavioural N = 83**: placebo 28, levodopa 26, naltrexone 29.
- **fMRI N = 74**: 24/24/26, after 9 excluded for head movement > 3 mm.
- Group size was chosen to match earlier between-subject levodopa/opioid studies (13–30 per group).

**Manipulations.**
- *Pharmacological:* a single oral dose of 100 mg levodopa (+25 mg carbidopa), 50 mg naltrexone, or placebo. The task started 60 min after dosing, around peak plasma concentration (p. 15 of 31).
- *Predictions (p. 3 of 31):*
  - If dopamine bursts support learning from avoided pain, levodopa should raise the no-pain learning rate.
  - If dopamine dips support learning from received pain, levodopa, by raising tonic dopamine, might lower the pain learning rate.
  - If μ-opioid activity supports either kind of learning, naltrexone should lower the corresponding rate.
- *Task (pp. 15–16 of 31):*
  - 144 trials in 4 runs. Choice between a diamond and a circle within 1.8 s, then an anticipation period (3/5/7 s), then the outcome: painful contact heat at 49 or 50 °C for 1.9 s on the inner left lower leg, or no stimulus.
  - A red or green plus sign marked pain or no pain for the first 200 ms. Inter-trial interval 6/8/10 s.
  - Pain probabilities for the two options followed independent random walks, so prediction errors persisted throughout. 16% of participants received 49 °C because they could not tolerate repeated 50 °C.

**Measures.**
- Choices and RTs.
- A separate 5-min **pain-rating task before the learning task**, with unavoidable heat at varying temperatures (Figure 1—figure supplement 2).
- Visual analogue scales of alertness, calmness and contentment, taken before and 2 h after dosing.
- 3 T fMRI, TR 2.2 s.
- **No pain ratings were collected during the learning task** (p. 13 of 31).

**Computational model (pp. 16–17 of 31).** Two Q-learning (Rescorla–Wagner) models update the expected pain value `Q_s` of the chosen option. The paper's update rule is

$$
Q_{s,t+1} = Q_{s,t} + \alpha \left( O_t - Q_{s,t} \right)
$$

with outcome `O_t` = −1 for pain and 0 for no pain, initial Q = −0.5, and the unchosen option not updated. The term in parentheses is the prediction error. Choice follows a softmax:

$$
P_{s,t} = \frac{e^{Q_{s,t}\,\beta}}{\sum_{s'=1}^{2} e^{Q_{s',t}\,\beta}}
$$

**Derivation of what the models distinguish.**
- Model 1 has a single `α`. Model 2 uses `α_pain` when `O_t = −1` and `α_no-pain` when `O_t = 0`.
- *After received pain.* With `Q ∈ [−1, 0]`, the prediction error `−1 − Q` is ≤ 0, so Q moves toward −1 (more expected pain) by a fraction `α_pain` of the gap.
- *After avoided pain.* The prediction error `0 − Q` is ≥ 0, so Q moves toward 0 (more expected safety) by a fraction `α_no-pain` of the gap.
- *What asymmetry means.* When `α_pain > α_no-pain`, one painful outcome shifts the expectation further than one pain-free outcome of equal surprise.
- *How β enters.* Higher `β` makes choice more deterministic toward the option with the higher Q, i.e. the lower expected pain.
- Model 1 has two free parameters (`α`, `β`); Model 2 has three.

**Estimation (p. 17 of 31).**
- Hierarchical Bayesian fitting with hBayesDM (Stan, Hamiltonian Monte Carlo), with separate group-level hyperparameters per treatment group.
- Weakly informative priors: normal(0, 1) on means, half-Cauchy(0, 5) on SDs. Probit transform to [0, 1]; `β` scaled to [0, 20].
- 4 chains × 5000 samples, 1000 burn-in, thinning 5 → 3200 samples; R-hat < 1.1.
- Model comparison by the Watanabe–Akaike information criterion (WAIC).
- For fMRI, trial-wise expected pain probability came from the winning model run with mean learning rates (pp. 17–18 of 31).

**Key statistics as reported.**

*Model-independent behaviour (p. 4 of 31).*
- Pain received on 57.1 of 144 trials (SD 8.6).
- Switching after pain 46.6% vs. after no pain 5.4%: t(82) = 18.6, p < 0.001, d = 2.0. The effect decayed over 1–6 trials back.
- No group differences: received pain F(2,80) = 0.56, p = 0.57; switch after pain F(2,80) = 0.03; switch after no pain F(2,80) = 1.18. No drug effects on RTs.
- No drug effects on subjective state or on pre-task pain ratings (p. 4 of 31).

*Model comparison (WAIC, lower is better; p. 5 of 31).*

| Group | Model 1 (single α) | Model 2 (α_pain, α_no-pain) |
|---|---|---|
| Placebo | 3109 | 2959 |
| Levodopa | 2958 | 2941 |
| Naltrexone | 3164 | 3106 |

*Group-level posterior medians (p. 5 of 31).*

| Group | α_pain | α_no-pain | P(α_pain > α_no-pain) | β |
|---|---|---|---|---|
| Placebo | 0.72 | 0.32 | 99.6% of MCMC samples | 8.8 |
| Levodopa | 0.66 | 0.66 | 50% | 5.3 |
| Naltrexone | 0.72 | 0.76 | 38% | 5.7 |

Drug vs. placebo difference distributions:
- `α_no-pain` was higher in both drug groups: 99.7% of the difference distribution above 0 for levodopa, 99.9% for naltrexone.
- `α_pain` did not differ: 34% and 49% above 0.
- `β` was lower in both drug groups: 98.8% and 98.1% below 0.
- At the individual level, `α_pain > α_no-pain` in 50% of levodopa and 41% of naltrexone participants.

*Replication and recovery (p. 7 of 31).*
- 23 untreated participants from Roy et al. (2014): `α_pain` 0.62 vs. `α_no-pain` 0.44 (90% of samples), `β` 7.1.
- Parameter recovery (Appendix 1) recovered the simulated values. Simulated placebo and drug datasets produced similar model-free performance, consistent with the learning-rate and stochasticity changes cancelling out.

*fMRI (pp. 8–10 of 31; FDR q < 0.05, whole brain).*
- **Contrast A** (surprise more for received than avoided pain). Regions: ventromedial prefrontal cortex, rostral ACC, posterior cingulate, insula→parahippocampal, cerebellum, brainstem including part of PAG. Opposite direction: sensorimotor, parietal and occipital cortex, frontal poles. The authors note that this contrast also captures activity tracking expected safety regardless of outcome.
- **Contrast B** (absolute prediction error, surprise for both outcomes). Regions: dorsal ACC→SMA, insula, sensorimotor cortex, thalamus, brainstem, cerebellum.
- **Conjunction, pain-specific prediction errors.** Brainstem (not covering PAG), bilateral insula extending into amygdala, rostral ACC, posterior cingulate, bilateral supramarginal gyrus, cerebellum.
- **Conjunction, no-pain-specific prediction errors.** SMA, left supramarginal/parietal, bilateral postcentral (somatosensory), left dlPFC.
- **Drug effects on any contrast.** None, even at uncorrected thresholds (p. 10 of 31).
- **Appendix 2, "axiomatic" general aversive prediction error** (activity satisfying all three conditions for encoding an aversive prediction error). A midbrain region including part of PAG (16 voxels) and rostral ACC (24 voxels) satisfied all three, replicating Roy et al. 2014. Activity with the opposite, appetitive-like sign appeared in bilateral somatosensory cortex, left frontopolar cortex, right dlPFC and right lateral occipital cortex (p. 31 of 31).

**Inferential step from result to claim.**
1. *Two systems, behavioural level.* Separate learning rates fit better than a single rate in every group. The authors call this "initial support for the idea that learning from received and avoided pain is subserved by different learning systems" (p. 4 of 31). Placebo participants learned more from received pain, replicated in an independent dataset.
2. *Two systems, neural level.* Largely non-overlapping regions encode outcome-specific prediction errors once expected-probability confounds are removed by conjunction (p. 10 of 31).
3. *Neurochemistry.* Both drugs selectively raised `α_no-pain`. The authors infer "a causal role of the dopamine and endogenous opioid systems in learning from avoided, but not received, pain" (p. 14 of 31). For levodopa: "phasic dopamine activity may signal the degree to which outcomes are 'better than expected' across both reward and punishment domains" (p. 11 of 31). The naltrexone result was opposite to prediction, and its mechanism is described as "remain[ing] to be elucidated" (p. 11 of 31).
4. *Relation to reward.* No ventral-striatal prediction error for avoided pain, so learning from avoided pain "is not comparable to learning from rewards" in neural terms (p. 12 of 31). The authors add a design caveat: pain outcomes involved a sensory change and no-pain outcomes did not. The frontoparietal response may reflect attention to checking whether pain really was avoided (p. 12 of 31).
5. *Interpretation of the asymmetry.* It is the reverse of the optimism bias seen with monetary outcomes. The authors offer three explanations: the intrinsic aversiveness and salience of pain; a Pavlovian tendency to change course after pain; or task framing (p. 10–11 of 31). A more complex task (Eldar et al. 2016) found no asymmetry.

**Limitations stated by the authors (pp. 13–14 of 31).**
- Power (between-subject, 24–26 per fMRI group).
- No pharmacological manipulation check.
- "We did not acquire pain ratings during the pain-avoidance learning task", so drug effects on pain sensitivity during the task cannot be excluded; pre-task ratings showed none.
- Orbitofrontal signal dropout.
- No physiological noise correction.
- Serotonin not examined.

**Reviewer's notes (not the paper's).**
- The behavioural two-systems inference rests on a model with two learning rates fitting better. That shows asymmetric updating. On its own it does not show two separate systems, which the authors signal with "initial support".
- The drug effects appear in model parameters but not in model-free behaviour or in fMRI. The causal claim therefore rests on the modelling layer, supported by parameter recovery.

### Appendix: Section-by-Section Backbone

**Abstract and editor's evaluation (p. 1 of 31).** Shared vs. separate systems for learning from unexpected pain and unexpected pain absence; N = 83; levodopa and naltrexone; results and conclusion.

**Introduction (pp. 1–3 of 31).** Threat vs. safety learning (knee-surgery example). Prior RL-fMRI work on cue–pain and avoidance/relief learning. One-system vs. two-system hypotheses (two-factor theory). Dopamine: bursts as safety-learning signal (Mowrer 1956; Dinsmoor 2001; Moutoussis et al. 2008) vs. dips for punishment (Frank 2005). μ-opioids in PAG for fear conditioning and extinction (McNally and colleagues); opioid-mediated relief pleasure (Sirucek et al. 2021). Aims and drug predictions.

**Results — task and behaviour (pp. 3–4 of 31).** Figure 1 task and switching curves; no treatment effects on state, pre-task pain ratings, basic performance or RTs.

**Results — computational modelling (pp. 4–7 of 31).** Model 1 vs. Model 2; hierarchical Bayesian estimation; WAIC; learning-rate asymmetry in placebo; drugs selectively raise `α_no-pain` and lower `β`; replication in Roy et al. 2014 data; parameter recovery.

**Results — fMRI (pp. 8–10 of 31).** Contrasts A and B; conjunction for pain-specific and no-pain-specific prediction errors (Figure 3); no drug effects.

**Discussion (pp. 10–14 of 31).** Learning-rate asymmetry vs. the optimism bias with money; Pavlovian and framing accounts; Eldar et al. 2016. Levodopa → dopamine as a "better than expected" signal across domains. Naltrexone's counterintuitive effect. Choice stochasticity. Separate brain circuits; no striatal reward-like prediction error; sensory-change caveat; speculation that limbic responses to pain prediction errors favour rest. No drug effects on fMRI: power, baseline-dependent (inverted-U) effects, BOLD insensitivity. Limitations. Serotonin.

**Conclusion (p. 14 of 31).** Two learning systems (learning rates and neural encoding); causal role of dopamine and opioids in learning from avoided pain.

**Materials and methods (pp. 15–19 of 31).** Participants; procedure and timing; task; thermal stimulation; behavioural analyses; models, priors, MCMC, WAIC; fMRI acquisition, preprocessing, first- and second-level models, conjunction.

**Appendix 1 (pp. 26–28 of 31).** Simulation and parameter recovery; model-free measures in simulated data.

**Appendix 2 (pp. 29–31 of 31).** Axiomatic tests for general aversive and appetitive prediction errors; PAG and rostral ACC satisfy all aversive axioms; appetitive-like signals in somatosensory, frontopolar, dlPFC and lateral occipital cortex.

**Field-history record**
- Year · community: 2022 · computational
- Question it asked: Do unexpectedly received and unexpectedly avoided pain drive human pain-avoidance learning through shared or separate behavioural, neural and neurochemical (dopamine, opioid) systems?
- Position / finding in one line: Placebo participants learned faster from received than avoided pain. Levodopa and naltrexone selectively raised learning from avoided pain. Prediction errors for received pain were encoded in subcortical/limbic regions and for avoided pain in frontoparietal cortex, supporting separate threat- and safety-learning systems.
- Responds to / builds on: Roy et al. 2014; Seymour et al. 2004, 2005; Ploghaus et al. 2000; Eldar et al. 2016; Zhang et al. 2018; Mowrer 1951, 1956; Dinsmoor 2001; Moutoussis et al. 2008; Frank 2005; Maia & Frank 2011; Schultz et al. 1997; McNally & Westbrook 2003; McNally et al. 2011; Rescorla & Wagner 1972; Sutton & Barto 1998; Wise et al. 2019; Sirucek et al. 2021
- Measures (empirical only): intensity rating [yes — separate pre-task pain-rating task only] · unpleasantness rating [no] · avoidance/escape behaviour [yes — instrumental choices and switching] · desire/urge rating [no] · neural [fMRI (BOLD) with model-based parametric modulators; pharmacological manipulation (levodopa, naltrexone)]
- Dissociation reported (empirical only): Levodopa and naltrexone raised the learning rate for avoided pain and lowered choice determinism, but left unchanged the learning rate for received pain, model-free performance, pre-task pain ratings, subjective state and fMRI prediction-error signals. Neural prediction errors for received vs. avoided pain localised to largely distinct regions.
- Survey claim check: yes — "Pain-avoidance learning has its own neural systems for received vs. avoided pain" → the paper reports "prediction errors evoked by pain and no-pain outcomes are encoded in largely distinct brain regions" (p. 10 of 31) and concludes that received and avoided pain "drive human pain-avoidance learning via two different learning systems" (p. 14 of 31). The paper's own wording is "suggest", and the drug effects appear only at the model-parameter level.
- PDF version: published

---

## 7. Le et al. (2024) — The neural correlates of individual differences in reinforcement learning during pain avoidance and reward seeking [tier: short]

**Citation:** Thang M. Le, Takeyuki Oba, Luke Couch, Lauren McInerney & Chiang-Shan R. Li, "The neural correlates of individual differences in reinforcement learning during pain avoidance and reward seeking," *eNeuro*, 2024. DOI 10.1523/ENEURO.0437-23.2024.
**PDF:** `docs/project/references/imperativism/sources/Le et al. 2024 - Neural correlates of individual differences in reinforcement learning during pain avoidance.pdf` — **accepted manuscript** (eNeuro Early Release: "has not been through the composition and copyediting processes"; received 23 Oct 2023, accepted 5 Feb 2024). **Title note:** the corpus filename drops "and reward seeking". The study is about both. Page citations are the manuscript's printed page numbers.

**Claim.** Individual differences in RL parameters have distinct neural correlates, mostly in cingulate and motor-planning regions. Several of those correlates were found for *pain avoidance* but not for *reward seeking*. The parameters are learning rate, the "subjective impact" of outcomes, a "Pavlovian factor" (how much the value of a cue, independent of learning, pushes toward acting) and action bias (a general tendency to press) (ms. p. 5).

**Method/type.** fMRI plus computational modelling of individual differences.
- **Participants.** N = 82 healthy adults (34 women, 35.9 ± 11.2 years) after 5 motion exclusions.
- **Task.** Probabilistic learning go/no-go task (after Guitart-Masip et al. 2012) crossing action (go / no-go) with goal (win $1 / avoid a painful electric shock). 80/20 contingencies; ~50 trials per cue across 4 runs. Shocks were calibrated as "painful but tolerable".
- **Unusual feature: half of the shocks were omitted.** "Despite the feedback display of the shock image, shocks were randomly delivered only half of the times to minimize head movements" (ms. pp. 12–13). On average participants had 14 real and 14 omitted shocks.
- **Model.** Q-learning with outcome `r` = +1 (gain), −1 (shock), 0 (null), scaled by subjective impact `ρ`; action bias `b` and Pavlovian term `πV` added to the "go" weight; softmax (Eqs. 1–6, ms. pp. 13–14). 14 models were compared stepwise by integrated BIC; parameters estimated by hierarchical type-II maximum likelihood (ms. pp. 14–15, 22).
  - The winning model has four learning rates (win/avoid × positive/negative prediction error), two subjective impacts (win, avoid), `b` and `π` (ms. p. 22).
- **Imaging analysis.** Whole-brain regressions of cue-period activation on each participant's parameters, controlling for sex, age and total shocks (voxel p < 0.001, cluster FWE p < 0.05). Mediation analyses linked activation, parameters and accuracy (ms. pp. 17–20).

**Key result or argument.**
- **Behaviour.** Accuracy was highest for go-to-win (81.1%) and lowest for no-go-to-win (65.1%) (ms. p. 28). Participants switched responses more after unfavourable feedback in avoid than in win trials: F(1,81) = 105.69 (ms. p. 21).
- **Learning rates.**
  - Higher in avoid than win trials: F(1,81) = 146.0.
  - Higher after favourable than unfavourable outcomes: F(1,81) = 45.02; interaction F(1,80) = 11.45 (ms. p. 22).
  - In avoid trials this means **learning was greater after successfully avoiding a shock than after receiving one** (ms. p. 28).
- **Subjective impact.** Greater for money than for shock avoidance (`ρW > ρA`) (ms. p. 22).
- **Neural correlates of individual differences.**
  - Avoidance learning rate correlated positively with cue activation in dorsal ACC, mid-cingulate, left postcentral gyrus and left superior temporal sulcus. Brain–accuracy link r = 0.36, fully mediated by learning rate. The reward learning rate had no significant correlate (ms. pp. 23–24).
  - `ρA` correlated with posterior cingulate and left superior parietal activation (accuracy r = 0.59). `ρW` had no significant correlate (ms. pp. 25–26).
  - Pavlovian factor correlated negatively with left precentral gyrus (avoid) and right superior frontal gyrus/posterior cingulate (win) (ms. pp. 24–25).
  - Action bias correlated positively with SMA/pre-SMA/dACC and dlPFC, and negatively with anterior insula, striatum and right superior frontal gyrus (ms. pp. 26–27).
- **Internal inconsistency.** The abstract says the Pavlovian factor was "represented in" precentral and superior frontal gyri. The results report *negative* correlations, and the discussion says "Higher Pavlovian factor predicted SFG activation" (ms. p. 31), contradicting the results (ms. p. 25).
- **Limitations stated by the authors (ms. pp. 36–37).** Shocks vs. money may differ in salience; skin conductance did not differ, but the data are not shown. The omitted shocks may have weakened learning; feedback without a real shock activated pain-responsive regions similarly, again data not shown.

**Place in the field's history.** A 2020s individual-differences, computational-psychiatry use of pain as a primary reinforcer set against money in one task. It continues the go/no-go "Pavlovian bias" line (Guitart-Masip et al. 2012, 2014) and cites Jepma et al. (2022) only for mid-cingulate involvement (ms. p. 30).

**Relevance.**
- **Its learning-rate asymmetry runs opposite to Jepma et al. (2022).** Jepma et al. found faster learning after received pain; Le et al. found faster learning after avoided shock. The tasks differ in many ways: go/no-go with money mixed in, half of shock feedback without shock, different estimation methods. The paper does not discuss the contrast.
- Pain enters only as a calibrated shock outcome. No pain or unpleasantness ratings are reported beyond calibration.

**Field-history record**
- Year · community: 2024 · computational
- Question it asked: Which brain regions track individual differences in RL parameters (learning rate, subjective impact of outcomes, Pavlovian factor, action bias) when people learn to avoid painful shocks and to seek monetary reward?
- Position / finding in one line: Across 82 adults, individual avoidance learning rate and subjective impact of shock avoidance were tracked by cingulate (dACC/MCC, PCC) and parietal/somatosensory activity. Reward-seeking parameters showed no comparable correlates, and learning was greater after favourable outcomes, including avoided shocks.
- Responds to / builds on: Guitart-Masip et al. 2012, 2014; Oba et al. 2019; Huys et al. 2011; Sutton & Barto 1998; Cazé & van der Meer 2013; Frank et al. 2004; Le et al. 2019; Roy et al. 2011; Jepma et al. 2022; Schlund et al. 2010
- Measures (empirical only): intensity rating [yes — calibration only, "painful but tolerable"] · unpleasantness rating [no] · avoidance/escape behaviour [yes — go/no-go choices to avoid shock] · desire/urge rating [no] · neural [fMRI (BOLD), cue-period activation regressed on individual model parameters; skin conductance mentioned, data not shown]
- Dissociation reported (empirical only): Individual avoidance learning rate and avoidance subjective impact had neural correlates, while the corresponding reward parameters did not. Subjective impact was greater for reward than for shock avoidance, while learning rate was greater for avoidance. No affect-vs-behaviour dissociation was tested.
- Survey claim check: partly — "individual differences in avoidance vs reward learning" → the study models individual differences in both pain avoidance and reward seeking in one task. Most reported neural correlates are for avoidance parameters, and "the multiple regression applied to the learning rate of reward seeking ... did not yield any significant results" (ms. p. 24). It does not treat "avoidance vs. reward" as a single individual-difference dimension. The survey's shortened title also omits "and reward seeking".
- PDF version: accepted manuscript

---

## 8. Notes for the cross-paper synthesis

These notes flag relations among the seven entries for the later synthesis. They take no side in any debate.

1. **Chronology of the framing.**
   - 2013: Wiech & Tracey describe pain as a motivator, with RL tools named as future directions.
   - 2018: Wang et al. apply planning-vs-habit arbitration to pain. Becker et al. treat emotion and motivation jointly, without formal models.
   - 2019: Seymour's RL architecture, in which pain *is* the reinforcement signal and self-report loses primacy.
   - 2022–2024: model-based imaging studies decompose avoidance learning into parameters (Jepma et al.; Le et al.) or tie avoidance vigour to helplessness (Gandhi et al.).
   - Seymour (2019) is the review that connects the earlier literature to the later experiments. It cites Wang et al. (2018) directly, and Wiech & Tracey (2013) was edited by Seymour.
2. **Direct empirical disagreement on learning asymmetry.** Jepma et al. (2022), with a replication in Roy et al. (2014) data, found faster learning from received pain. Le et al. (2024) found faster learning from avoided shock. Wang et al. (2018) did not split learning rates by outcome. Jepma et al. themselves note that Eldar et al. (2016) found no asymmetry. Task structure is a plausible moderator, but no paper in this batch tests that.
3. **Where the survey's claims go wrong.**
   - *Seymour 2019.* "Precision signal" means precise and objectifiable, not predictive-coding precision weighting.
   - *Gandhi et al.* The study does not compare neural correlates of avoidance with pain report.
   - *Le et al., Gandhi et al.* Their titles are truncated in the filenames and survey. Le et al. also covers reward seeking; Gandhi et al. is about participants with and without episodic migraine. The Gandhi file is dated 2021, but the manuscript's cover sheet gives publication in 2022.
4. **Measurement gap relevant to valence-vs-avoidance questions.** None of the five empirical papers collected trial-by-trial pain intensity or unpleasantness ratings during the avoidance task.
   - Wang et al. and Le et al.: calibration only.
   - Gandhi et al.: calibration only, on a single scale anchored "painful/unpleasant" that merges intensity and unpleasantness.
   - Jepma et al.: a separate pre-task rating session only.
   Consequently no paper in G2 reports a dissociation between how pain felt and how it was avoided. The dissociations they do report are between learning parameters, between brain regions, or between drug effects on parameters vs. brain signals. The only affect-vs-behaviour dissociations in the batch are second-hand, in the Becker et al. review: wanting vs. liking, and avoidance changing while fear does not.
5. **The PAG across papers.**
   - Gandhi et al.: PAG engaged in preparing to avoid, but not modulated by failure or helplessness.
   - Jepma et al.: PAG satisfies all three axioms of a general aversive prediction error (replicating Roy et al. 2014), but is excluded from the pain-specific conjunction.
   - Seymour: PAG–RVM as the effector of endogenous control.
   These are different roles (preparation, learning signal, descending modulation), measured with different methods.
6. **Evidence strength.** Wang et al. (N = 15, between-study reward comparison, authors say "provisional") and Gandhi et al. (N = 32, helplessness effects in n = 15) are small. Jepma et al. (N = 83/74) and Le et al. (N = 82) are larger. Jepma et al.'s drug effects appear only in model parameters.
7. **"Imperative" vocabulary.** Only Wiech & Tracey (2013) uses the word, in passing ("imperative character", p. 1), with no reference to the philosophical imperativism in Part A. No G2 paper engages that literature.

## Not reviewed (no PDF)

None — all seven assigned PDFs were present in `sources/` and reviewed.
