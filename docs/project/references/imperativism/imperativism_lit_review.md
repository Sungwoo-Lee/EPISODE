# Imperativism about Pain and Valence — Reference Review

**Topic folder:** `docs/project/references/imperativism/`
**Corpus:** 5 papers (philosophy of mind), reviewed one at a time in the order of the debate, 2026-09-16.
**Reviewer:** literature-reviewer

## What this review is about (plain-language entry point)

**The question.** Why does pain *feel bad*, and why does pleasure *feel good*? Philosophers call this good-or-bad quality **valence**. The five papers here are a running debate between two answers.

**Answer 1 — imperativism: feelings are commands.** Colin Klein (2007) proposed that pain does not *describe* your body ("your ankle is damaged"). It *orders* you ("don't put weight on that ankle!"). Barlassina & Hayward (2019) widened this to every pleasant or unpleasant experience, but changed what the order is about. An unpleasant experience orders "**less of me!**" and a pleasant one orders "**more of me!**" — the order is about the experience itself, not about the body or the world.

**Answer 2 — evaluativism: feelings are perceptions of value.** Peter Carruthers (2018) holds that feeling bad is something *seeming bad* to you. The approaching bear looks bad, much as a tomato looks red, without any words or concepts involved.

**What the corpus claims.**
- Barlassina (2020) argues that imperativism wins by Carruthers's own tests. His cases include a desire that feels unpleasant even though its object looks good, a saint whose pride feels bad, and a sadness with no object.
- Carruthers (2023) replies that brain signals for pleasure and pain track how good or bad things are for survival, so they *represent value*. On his reading, nothing in how we learn, choose or pay attention needs commands.

The debate is not settled within this corpus. [§6](#6-cross-paper-map-of-the-debate) sets out who answers whom. [§7](#7-relevance-to-this-project-interpretive) gives a cautious, interpretive note on what each view would ask of an artificial agent's damage (nociception) signal.

## Table of Contents

- [What this review is about (plain-language entry point)](#what-this-review-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Klein (2007) — An Imperative Theory of Pain](#1-klein-2007--an-imperative-theory-of-pain)
  - [Phase 1](#phase-1-foundational-overview) · [Phase 2](#phase-2-graduate-level-deep-dive) · [Argument reconstruction](#argument-reconstruction) · [Backbone](#appendix-section-by-section-backbone)
- [2. Carruthers (2018) — Valence and Value](#2-carruthers-2018--valence-and-value)
  - [Phase 1](#phase-1-foundational-overview-1) · [Phase 2](#phase-2-graduate-level-deep-dive-1) · [Argument reconstruction](#argument-reconstruction-1) · [Backbone](#appendix-section-by-section-backbone-1)
- [3. Barlassina & Hayward (2019) — More of Me! Less of Me! Reflexive Imperativism about Affective Phenomenal Character](#3-barlassina--hayward-2019--more-of-me-less-of-me-reflexive-imperativism-about-affective-phenomenal-character)
  - [Phase 1](#phase-1-foundational-overview-2) · [Phase 2](#phase-2-graduate-level-deep-dive-2) · [Argument reconstruction](#argument-reconstruction-2) · [Backbone](#appendix-section-by-section-backbone-2)
- [4. Barlassina (2020) — Beyond Good and Bad: Reflexive Imperativism, not Evaluativism, Explains Valence](#4-barlassina-2020--beyond-good-and-bad-reflexive-imperativism-not-evaluativism-explains-valence)
  - [Phase 1](#phase-1-foundational-overview-3) · [Phase 2](#phase-2-graduate-level-deep-dive-3) · [Argument reconstruction](#argument-reconstruction-3) · [Backbone](#appendix-section-by-section-backbone-3)
- [5. Carruthers (2023) — On Valence: Imperative or Representation of Value?](#5-carruthers-2023--on-valence-imperative-or-representation-of-value)
  - [Phase 1](#phase-1-foundational-overview-4) · [Phase 2](#phase-2-graduate-level-deep-dive-4) · [Argument reconstruction](#argument-reconstruction-4) · [Backbone](#appendix-section-by-section-backbone-4)
- [6. Cross-Paper Map of the Debate](#6-cross-paper-map-of-the-debate)
- [7. Relevance to This Project (interpretive)](#7-relevance-to-this-project-interpretive)
- [Not in this corpus](#not-in-this-corpus)

(Sub-entry anchors follow GitHub's duplicate-heading numbering: `-1`, `-2`, … in paper order.)

---

## Reading conventions

- **Page citations** differ by paper, because the PDFs differ:
  - *Klein 2007* (author copy, unnumbered) and *Carruthers 2023* (author copy with "000" placeholders): cited as **"ms. p. N"**, where N is the page of the PDF manuscript in `sources/`. These page numbers do **not** match the published journal pages.
  - *Barlassina & Hayward 2019*: filed as an author copy, but the PDF is the typeset Advance Access version with journal pagination printed. Cited by journal page (pp. 1013–1044).
  - *Carruthers 2018* and *Barlassina 2020*: published versions, cited by journal page.
- **No invented mathematics.** These are philosophy papers with no equations. The "rigor" part of each Phase 2 is an **argument reconstruction**: numbered premises, the *content schema* each theory gives an experience, the counterexamples, and which premise each counterexample attacks. Display blocks are used only where a schema is clearer than prose. The one formula-like learning update in §5 is explicitly marked as the reviewer's rendering of prose.
- **Vocabulary.**
  - *Valence*: the pleasant/unpleasant dimension of an experience.
  - *Affective phenomenal character*: Barlassina & Hayward's term for the same thing.
  - *Content*: what a mental state is about or says. *Indicative* content describes ("the ankle is damaged"); *imperative* content commands ("don't put weight on the ankle!").
  - *First-order*: about the non-mental world or body. *Higher-order*: about a different mental state. *Reflexive / same-order*: about the very state that has the content.
  - *Evaluativism*: valence = a non-conceptual representation of good/bad (value).
  - *Hedonic account* (Carruthers's other foil): valence = an intrinsic good/bad feel of the experience.
- **Project vocabulary.** For the project's agents the internal damage signal is **nociception**; "pain" refers only to the human/animal phenomenon these papers discuss.

---

## 1. Klein (2007) — An Imperative Theory of Pain

**Citation:** Colin Klein, "An Imperative Theory of Pain," *The Journal of Philosophy* 104(10): 517–532, 2007.
**PDF:** `docs/project/references/imperativism/sources/Klein 2007 - An imperative theory of pain (author copy).pdf` — author copy (24 manuscript pages, unnumbered; published version is 16 pages). Page citations below are manuscript pages.

### Phase 1: Foundational Overview

#### Introduction

Philosophers who think that *what an experience feels like* is fully fixed by *what the experience is about* ("intentionalists") have trouble with pain. Seeing red plausibly just is being presented with a red surface. But what is pain about? The natural answer — "tissue damage" — seems to leave out the thing that matters most about pain: it *pushes* you. A paper cut reports something trivial yet grabs you urgently; and some patients on morphine say the pain is still there but they no longer care. Klein's proposal is that pain *is* about something, but the "aboutness" is of a different grammatical kind. Pain does not **describe** ("your ankle is damaged"); it **commands** ("don't put weight on that ankle!"). This is the founding statement of **imperativism** about pain.

#### Key Findings

1. **Pains are negative imperatives.** Hunger says "eat!", an itch says "scratch here!". Pain rarely demands a specific positive action, so Klein proposes that its content is a *prohibition*: stop using this body part in this way. A burn forbids contact with the burned area; a sprain forbids moving the joint; the burn of exertion forbids continued use of the tired muscle.
2. **Pain is tied to action, not just to body location.** The telling phrase is "it hurts **when I** do A", not "my B hurts".
3. **Pain is not a report of tissue damage** (the "myth of tissue damage"). Pain often occurs without damage (hand near a flame, exertion, long after an injury heals), is a poor guide to its cause (most low-back pain has no identifiable origin), and a merely *informative* pain signal would be biologically worse than a command, because information invites flexible, context-dependent responses where only one response is appropriate.
4. **Morphine pain does not refute the view.** Morphine and lobotomy remove the *secondary* emotional reaction (worry, fear) and the patient's general drive to do anything. A prohibition has nothing to prohibit if you are not trying to act — "like a stop sign in a ghost town" (ms. p. 20). When lobotomised patients *do* act, they still avoid walking on a broken ankle, as the theory predicts.

#### Initial Takeaway

Pain's "hurtfulness" is not an extra ingredient added on top of a damage report; it *is* the content — a bodily command against certain actions. This preserves the idea that experience is fully explained by content while explaining why pain motivates so directly. The theory is about pain only (not pleasure or emotions); extending it to all pleasant and unpleasant experience is the job of the later papers in this corpus.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Dialectical setting.** Klein targets two positions: (i) *representationalist* intentionalism about pain (Tye 1995, Byrne 2001), on which a pain represents a bodily disturbance at a location, and (ii) *dual-aspect* theories (Melzack & Wall; Hardcastle 1997), on which pain = a sensory-discriminative component + a separable motivational-affective component (perhaps an irreducible quale). Klein keeps intentionalism but rejects the assumption that all sensory content is *declarative*. Sentences come in declarative, interrogative, imperative moods; sensations may too.

**Imperatives vs. desires.** Both have world-to-mind direction of fit, but an imperative is satisfied only by **the addressee's action**, not merely by the world coming to be a certain way (a command to a student to write a paper is not satisfied by a paper with her name on it appearing; ms. pp. 3–4). This matters: pain's content is about *what the subject does with their body*, which is why a proscription can be satisfied by inaction.

**Content schema.** For a pain `p` located in body part `B`, Klein assigns a proscriptive content over action types involving `B`:

$$
\mathrm{Content}(p) \;=\; \text{!}\,\neg\big[\,\text{use } B \text{ in manner } M\,\big]
$$

where the leading "!" marks imperative mood and `M` is fixed by how and where the pain is felt (weight-bearing for a broken ankle; contact for a burn; movement along a degree of freedom for a sprain). Klein stresses that the content is **not** a list of forbidden actions (standing, kickball, hopscotch…) but a general prohibition from which those follow (ms. p. 8). Withdrawal reflexes are a **limit case**: a very strong prohibition on "any action that would keep your hand in contact with the stove (including the trivial action of keeping it exactly where it is)" (ms. p. 8) — withdrawal is demanded only indirectly.

**Intensity.** Pain intensity is the *strength* of the imperative. Imperatives enter action planning and can be overridden (carrying a hot casserole to the table), and their strength rises while the prohibited action continues and falls as one backs off (ms. p. 9). Analgesia = weakening the imperative; complete analgesia = removing it.

**Strong intentionalism.** "There is no difference in the phenomenology of a pain experience without some difference in the intentional content" (ms. p. 10): phenomenal character supervenes on (imperative) content.

#### Argument Reconstruction

**Argument A — Pain is imperative (from the family of imperative sensations).**

- A1. Itch, hunger and thirst have imperative content (Hall): they carry little information about their cause, are poorly localised, are not assessable as veridical, and are individuated by the action they demand.
- A2. Pains share these marks: poorly localised, attention-grabbing, uninformative about cause (argued in §3).
- A3. Pains differ only in not demanding a single *positive* action type.
- A4. A negative imperative (a proscription) is individuated by what it forbids, not by a positive action.
- **C.** Pains have negative imperative content.

**Argument B — Against the "myth of tissue damage" (§3).** The opponent's argument: (M1) pain's biological purpose is to inform about damage; (M2) so pain's content must be informative. Klein denies (M1) and argues against the conclusion directly:

- B1. *Causal heterogeneity*: pain arises before damage (near a flame), after healing (chronic post-injury pain), and in exertion that is not even counterfactually linked to damage; these are adaptive, not pathological (congenital insensitivity to pain kills through joint degeneration and over-exertion, not acute trauma).
- B2. *Unreliability*: pain is a poor guide to its cause (only ~10% of low-back pain cases have an assignable origin; abdominal pain poorly localised; serious injuries can be painless for a time — Beecher).
- B3. *Functional argument*: an informative content produces **contingency of response** — the right response to a perceived property depends on context (the right response to seeing blue varies). For pain, "other things being equal", there is only one appropriate response: stop acting in the injurious way. Hence "an informative content to pain would be positively maladaptive" (ms. p. 15); an organism that has not eaten "needs to be driven to eat and drink" rather than informed (ms. p. 16).
- **C.** Pain's content is not a report of tissue damage. Learning *that* one is damaged from a pain is like a soldier learning that war has begun from his marching orders: the order's content is exhausted by the command (ms. pp. 10–11).

**Argument C — Morphine pain (§4).**

- Objection: (O1) morphine patients report pain but no motivation; (O2) so motivation is dissociable from pain; (O3) so motivation is not constitutive of pain — contradicting imperativism.
- Reply: distinguish **primary affect** (immediate unpleasantness = the imperative itself) from **secondary affect** (fear, anxiety, second-order reactions to pain). Then:
  - R1. Morphine/lobotomy removes secondary affect and produces general apathy and immobility.
  - R2. A *positive* motivational theory would predict that residual pain still prompts action; morphine refutes that.
  - R3. A *negative* imperative only forbids; with no intended action there is nothing for it to forbid, so its presence is behaviourally silent ("stop sign in a ghost town", ms. p. 20).
  - R4. Prediction: if such patients act, pain still restricts action. Confirmed by Melzack & Wall's lobotomy reports — patients "still withdraw from pinprick, avoid walking on broken ankles" (ms. p. 21).
  - Hence (O2) is false for primary affect; the reply targets (O2).

**Side note on Gracely et al. (1979).** Klein dismisses fentanyl tooth-pulp evidence for "unpleasantness without sensory pain" as ambiguous — shocked tooth pulp may simply be unpleasant *simpliciter* (ms. p. 18, fn. 19).

#### Open problems Klein flags (§5)

Headache, menstrual cramps and deep visceral pain have no clear proscribed action ("degenerate cases" at worst); qualitative differences (stabbing vs. burning) might track proscribed action types rather than injury types; emotional pain; and the pain–attention relationship (hypnotic analgesia). The Barlassina & Hayward and Carruthers papers later use exactly such "no-action" cases and the scope question (pain only vs. all affect) against body-directed imperativism.

#### Critical assessment (reviewer)

- The theory is about **pain only**; it says nothing about pleasure, emotions or moods. It also does not by itself explain why the imperative is *felt as bad* rather than merely obeyed — the gap later pressed by evaluativists (Bain 2013, not in this corpus) and addressed by Barlassina & Hayward's reflexive variant.
- The content is **world/body-directed** (about bodily action), so Klein-style imperativism shares with representationalism the problem of pains whose "object" is unclear (visceral pain, headache).
- The lobotomy evidence is secondary (Melzack & Wall's summary), not a controlled test.

### Appendix: Section-by-Section Backbone

**§1 Introduction (ms. pp. 1–3).** Intentionalism = phenomenal character exhausted by intentional content; restricted intentionalism exempts bodily sensations, pains most of all. Representational theories struggle because pain's motivating feel seems unrelated to its (sometimes trivial) content, and morphine cases push many toward dual-aspect theories or primitive pain qualia. The assumption at fault is that sensory content must be declarative. Thesis: pains are exhausted by their content, but it is imperative — "Pains thus command rather than describe" (ms. p. 3).

**§2.1 Imperative sensations (ms. pp. 3–5).** Imperatives don't represent the world; they have desire-like direction of fit but are satisfied only by the addressee's action. Hall: itch = "Scratch here!", hunger = "Eat something!". Such sensations carry little information about cause, localise poorly, are not veridical/non-veridical, and are unified by the action demanded (scratching with nails, tree bark, or a ruler all satisfy the itch).

**§2.2 Pains as negative imperatives (ms. pp. 5–10).** Obstacle: most pains demand no positive action (withdrawal is spinal reflex). Solution: "The content of any pain is a negative imperative" (ms. p. 6). Examples: broken ankle, burn, sprain, incipient damage, exertion. Withdrawal is a limit case. Pains attach to the *use* of body parts ("It hurts when I A"). Pains show up against ongoing planned action and can be overridden; intensity tracks the imperative's strength. Strong intentionalism: the difference between being in pain and not is "just the presence or absence of an imperative" (ms. p. 9).

**§3 Objection 1: Tissue damage (ms. pp. 10–16).** Names "the myth of tissue damage". Marching-orders analogy. Three arguments: non-damage causes; unreliability as information; biological function (contingency of response would be maladaptive). Footnotes cite premotor and anterior cingulate involvement in pain as evidence of a pain–action-planning link (ms. pp. 14–15, fn. 15).

**§4 Objection 2: Morphine pain (ms. pp. 16–22).** Motivational theories face morphine pain. Don't over-read patient phrasing ("It hurts but I no longer care" is more common than "pain that doesn't hurt"). Primary vs. secondary affect. Morphine removes secondary affect and drive to act; the negative imperative persists without anything to forbid. Prediction confirmed in lobotomised patients' behaviour. Masochism aside: the masochist seeks to be *hurt*, so pain is not simply inverted in valence (fn. 21).

**§5 Remaining problems (ms. pp. 22–24).** Headache/cramps/visceral pain; qualitative variety of pains; emotional pain; attention. Closing thesis: rival accounts err by treating the body as "just another object out in the world that we need to be kept informed about"; "Pain is there to stop us" (ms. p. 24).

---

## 2. Carruthers (2018) — Valence and Value

**Citation:** Peter Carruthers, "Valence and Value," *Philosophy and Phenomenological Research* 97(3): 658–680, 2018 (online 2017). doi:10.1111/phpr.12395.
**PDF:** `docs/project/references/imperativism/sources/Carruthers 2018 - Valence and value.pdf` — published version; page citations below are the printed journal pages (journal page = PDF page + 657).

> **Scope note.** This paper does **not** discuss imperativism or Klein. Its foil is the *hedonic* (intrinsic-quale) account of valence. It enters the imperativism debate because Barlassina & Hayward (2019) and Barlassina (2020) take Carruthers's "evaluativism" as the main rival and use his own criteria against him.

### Phase 1: Foundational Overview

#### Introduction

Pains, pleasures, fear, grief, boredom, sexual pleasure and depressed moods look like very different things, but they all share one feature: they feel *good* or *bad*. Psychologists call this dimension **valence**. Carruthers's first claim is empirical: valence seems to be **one and the same kind of thing** across all these states (the same brain network, the same drugs blunt both physical pain and social pain and pleasure, the same placebo effects), and it acts as the brain's **common currency** for comparing options that otherwise have nothing in common. His second claim is philosophical: the best theory of what valence *is* says that valence is a **non-verbal, perception-like representation of value** — when you fear a bear, the bear *looks bad* to you, in roughly the way a tomato looks red, without you needing the concept "bad". This position is later labelled **evaluativism**.

#### Key Findings

1. **Valence is a unitary natural kind and plausibly underlies all decided-upon action.** Goals and intentions can run without current affect, but they were formed by affect-laden imagination of options; beliefs about what is good motivate only by changing affect (patients with orbitofrontal damage judge well but choose badly).
2. **Two general theories of valence are available.** (a) *Representational* (Carruthers): valence represents the object of the experience as good/bad. (b) *Hedonic*: valence is an intrinsic good/bad feel of the experience itself, which the agent is motivated to get more or less of.
3. **Arguments for the representational view:**
   - *Phenomenology*: in fear, anger and desire, attention is on the world (the bear, the insult, the cake), and it is those that seem bad or good.
   - *Animals*: the hedonic view requires creatures to be aware of their own experiences as such, yet animals and infants feel pain and plan by valence.
   - *Self-sacrifice*: people die for a cause or donate a kidney for a loved one; a hedonist must treat these as mistaken predictions about future feelings.
   - *Evolutionary mismatch*: the brain appraises the *world* on the input side; it would be odd for the output to value only *feelings* — "evolution couldn't care less about how one feels" (p. 670).
   - *Unconscious valence*: cognitive science posits unconscious valence; an intrinsic *feel* cannot be unconscious, but a representation can.
4. **Pain on this view** = a sensory representation of a bodily property (location, intensity, stabbing quality) *plus* negative valence representing **that sensation** as bad ("Make that go away!", said of the gouty toe, p. 665).

#### Initial Takeaway

For Carruthers, feeling bad is *seeing something as bad*. This keeps affect pointed at the world, makes valence a single comparable "value signal" that drives choice, and fits a view of consciousness on which experience is a kind of representation. The paper also shows how evaluativism handles hard cases (moods, pain) — the handling that imperativists will later dispute.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**The unity premise (§1).** Evidence offered: a shared valuation network (basal ganglia, anterior insula, anterior cingulate, orbitofrontal and ventromedial prefrontal cortex); valence from many attributes can be "summed and subtracted" into an overall response and compared across incommensurable options (p. 659); acetaminophen blunts social pain *and* pleasure; placebo/nocebo effects apply to both pain and pleasure; moderate pain that is less than expected can be felt as pleasant (Leknes et al. 2013). Methodological upshot: an account of the hurtfulness of pain must generalise to fear and grief, which rules out, e.g., Cutter & Tye's analysis of hurtfulness as represented *harmfulness* (sadness is not a representation of harm) (p. 660). A footnote adds that valence is also a **teaching signal** for evaluative learning — better-than-expected pleasantness raises stored value (p. 659, fn. 2).

**The motivational premise (§1).** The necessity is *psychological*, not conceptual (p. 660, fn. 4). Habits and emotion-specific action tendencies are excluded (fn. 3; "wanting" is reinterpreted as primitively caused approach, "liking" as pleasure at the thought of acting). Intentions are affect-independent once formed but *distally* dependent on valence. Evaluative beliefs acquire motivational force only through affect: via social admiration, via predictive-coding placebo effects ("expecting something to be good can lead one to experience it as more valuable", p. 662), and via choice-induced preference change.

**The content schema (§2).** The valence component of any affective experience is "a fine-grained, nonconceptual, representation of the goodness or badness of the object of that experience" (p. 663). Writing `O` for the object of experience `E` (a bear, a cake, a represented bodily sensation) and `v` for a signed magnitude on a single continuum:

$$
\mathrm{Content}_{\mathrm{val}}(E) \;=\; \big\langle\, O \text{ is (nonconceptually) good/bad to degree } v \,\big\rangle, \qquad v \in \mathbb{R}
$$

Properties: (i) **indicative** mood (it can be correct or incorrect); (ii) **amodal** (not tied to a sense modality); (iii) **nonconceptual** — analogous to approximate-numerosity representations that discriminate 30 from 40 dots but not 30 from 35, without the concept THIRTY (p. 663); (iv) **intrinsically motivating** — positive valence motivates obtaining `O`, negative valence motivates avoiding or getting rid of `O` (p. 664); (v) by default causes the belief that `O` is good/bad, as seeing red causes believing red (p. 664); (vi) fine-grained, so it can ground comparative judgements ("better than") in prospection.

**Pain.** Pain experience = sensation (nonconceptual representation of a bodily property; Carruthers leaves open whether this is a secondary quality or Tye's physical disturbance, p. 663, fn. 6) + negative valence whose object is **the sensation**. Crucially, "it is one's sensations that are evaluated as good or bad, not (in the first instance) one's experience of those sensations" (p. 665). Morphine and anterior cingulotomy remove the valence and leave the sensation.

**The rival hedonic account.** Valence = intrinsic, non-representational, non-relational quality of the experience, felt as good/bad and motivating one to prolong or remove the experience; in prospection the present feeling is treated as a signal of future feelings (p. 664). This is "meta-experiential": what is bad is one's *experience* of pain.

#### Argument Reconstruction

**Argument 1 — Phenomenology (§2).**
- P1. In fear, anger and desire, attention is outward; what seems bad or good is the bear, the insult, the cake or the act of eating it.
- P2. An adequate theory should fit this phenomenology.
- P3. The representational account assigns valence exactly these worldly objects; the hedonic account makes the bear bad only derivatively (believed to cause bad qualia).
- C. The representational account fits the phenomenology better.
- *Hard cases.* (a) Moods: depression makes the world seem "flat, colorless, and empty of meaning" (p. 665), so whatever is attended to is represented as bad; or, for non-worldly depression, the bodily state (lassitude, slumped posture) is represented as bad. (b) Pain and orgasm: the object is the bodily sensation. (c) The hedonist's challenge "is it the cake or your experience of the cake that is good?" is answered by separating the *existence condition* of valence (it exists only within an ongoing experience) from its *object* (the cake) (p. 666).

**Argument 2 — Meta-representational demand (§2).**
- P1. On the hedonic account, to be motivated to remove a bad quale one must be aware of it *as an experience* (represent one's own experience).
- P2. Many animals and infants feel pain/fear and engage in valence-based prospective planning (rooks, crows, apes).
- P3. It is implausible that all such creatures are meta-aware of their experiences.
- C. The hedonic account over-intellectualises; the representational account (valence about body or world) does not.

**Argument 3 — Hedonism and self-sacrifice (§3).**
- P1. If valence is a hedonic quale and all decision-making is affect-based, motivational hedonism follows: one chooses so as to obtain good and avoid bad experiences (the Gilbert & Wilson "prefeel" model, quoted p. 667).
- P2. People rationally sacrifice their lives for a cause and take on costs for loved ones.
- P3. Hedonist replies fail: (a) an unconscious belief, immune to top-down correction, that one will feel good after the revolution — ad hoc and inconsistent with how penetrable affect is to top-down influence; (b) anticipated guilt if one does not sacrifice — depends on a false belief, given how resilient people are to loss, and misdescribes the agent ("it isn't about me at all", p. 668).
- P4. Hedonism therefore reclassifies many ordinary sacrifices as prospective reasoning errors; the representational account does not: "It is because one values the loved one that one makes the sacrifice" (p. 668).
- C. The representational account handles such cases better.

**Argument 4 — Input/output mismatch (§3).**
- Distinction: **input content** = the appraisals that cause affect (processed subcortically against standing values; values are stored as *dispositions* of appraisal mechanisms, p. 668, fn. 9). **Output content** = the object, usually the current object of attention, to which the resulting valence is attached and which guides planning. They normally overlap but can diverge — hence **affective priming**: masked happy faces raise how much people drink and pay for a beverage (Winkielman et al.); a disgusting environment makes moral violations seem worse (Schnall et al.); hard-to-process images seem less attractive (p. 669).
- P1. Input content is world-directed.
- P2. On the hedonic view, output content (what the agent values in choosing) is self-directed feelings.
- P3. Evolution selects for survival and reproduction, not feelings, so a world-in/feelings-out architecture that needs extra beliefs linking feelings to world is puzzling (p. 670).
- P4. The reply that information alone would not motivate fails: something must wire hedonic feelings to decision-making, and it is no harder to wire value-representations the same way.
- C. The representational account (world-in, world-out) is evolutionarily more plausible.
- *Error theory*: hedonism seems attractive because redirecting attention to oneself turns world-directed valence into self-directed valence; some people with a habitual self-focus may really be hedonists (pp. 670–671).

**Argument 5 — Consciousness (§4).**
- Criterion: phenomenally conscious states are those that generate hard-problem thought experiments (zombies, Mary), which arguably means access-conscious states with nonconceptual content.
- Valence passes the test: a zombie who groans but is not *hurt*; a Mary-style neuroscientist with congenital pain asymbolia who, once cured, learns "So this is what the hurtfulness of pain is like!" (p. 672). (fn. 13: strictly, the asymbolic could be told pain hurts "like the hurtfulness of grief", given that valence is unified.)
- P1. Both accounts can say valence is phenomenally conscious.
- P2. The hedonic account entails valence is *always* phenomenally conscious (unless unconscious qualia make sense).
- P3. Cognitive science treats valence as often unconscious (relevance detection, guiding attention).
- C. Prefer the representational account.

**The naturalisation problem and correctness conditions (§4).** Aydede's challenge: what *natural property* does negative valence represent? Cutter & Tye's answer "harmfulness" fails because (i) representing harm is not intrinsically motivating and (ii) moods occur without any harm. Externalist tracking theories look poor for valence (no natural property is tracked as good/bad across all affect); a teleological version ("valence represents adaptive / maladaptive, relative to the ancestral environment") is possible; Carruthers prefers functional/inferential-role or non-reductive content (pp. 674–675). Tentative correctness condition:

$$
\text{valence of degree } v \text{ directed at } o \text{ is correct} \iff \text{nothing other than } o \text{ contributed to } v \quad \text{(p. 675)}
$$

On this condition, affective priming = misrepresentation.

**Summary (the six conclusions, p. 675–676).** (1) fits world-directed phenomenology; (2) no meta-representation needed; (3) handles sacrifice and explains away hedonism's appeal; (4) avoids evolutionary mismatch; (5) permits unconscious valence; (6) no general barrier to a representational account of valence content, and it coheres with representational theories of consciousness.

#### Critical assessment (reviewer)

- The main dialectical weakness later exploited by imperativists is Carruthers's handling of **pain and moods**: for pain he *moves the object inward* (the sensation is represented as bad), which concedes that some valence is not world-directed, and his "Make that go away!" gloss (p. 665) is itself phrased as an imperative.
- The correctness condition is admitted to be a sketch; the evaluativist owes an account of what "good" means that does not collapse into "what my reward system responds to".
- The paper's positive case is almost entirely *against hedonism*; imperativism, which is also a representational (content-based) view but not an *evaluative* one, is not considered — the gap Barlassina & Hayward exploit.

### Appendix: Section-by-Section Backbone

**Abstract (p. 658).** Valence is a central component of all affective states; enough is known to treat it as a unitary natural-psychological kind that motivates intentional action. Two sufficiently general accounts: nonconceptual representation of value vs. intrinsic qualitative property; both hold valence to be directly motivating. The representational account is more plausible.

**§1 Affect, Valence, and Motivation (pp. 658–662).** Affective states share valence and arousal. Individuation debates (core affect; appraisal; action tendencies) are set aside. Unity evidence: shared network, common currency, shared pharmacology and placebo effects, relief-pleasure. The unity constraint rules out pain-specific accounts (harmfulness). Valence is intrinsically motivating and underlies prospection; exceptions (habit, emotional action tendencies) noted. Intentions/goals depend distally on valence; evaluative beliefs motivate only via affect (vmPFC patients; flattened affect), through social routes, placebo-like expectation effects and choice-induced preference change. Two working assumptions: valence is a natural kind; valence is directly motivating.

**§2 The Nature of Valence: Two Views (pp. 662–666).** Pain = sensory + valuational component (morphine, cingulotomy). Representational account defined; analogy to nonconceptual numerosity; valence amodal yet phenomenally present; intrinsically motivating; seeming-good causes believing-good by default; nonconceptual status explains phenomenal consciousness and grounds comparative judgement. Hedonic account defined (intrinsic value qualia; chocolate-cake prospection). Phenomenology argument (bear, insult, cake, fame). Moods (world seems flat; bodily lassitude). Pain and orgasm: the sensation is evaluated, "Make that go away!" (p. 665). Hedonic account is meta-experiential and over-intellectualises animals/infants. Cake-vs-experience reply.

**§3 Valence and Hedonism (pp. 666–671).** Prospection is world-focused on the representational account; hedonic account + affect-based choice → motivational hedonism (Gilbert & Wilson). Counterexamples: revolutionary self-sacrifice; two hedonist replies rejected; kidney/second mortgage. Input vs. output content; affective priming evidence; priming as a by-product of valence's summative function; mood as representation of momentum (fn. 11). Evolutionary mismatch argument; rejection of the "information isn't motivating" reply. Error theory of hedonism via self-directed attention; individual differences in attending to feelings.

**§4 Valence and Consciousness (pp. 671–675).** Valence is access-conscious; is it phenomenally conscious? Hard-problem criterion; nonconceptual access-conscious content. Zombie and asymbolic-Mary cases. Both accounts permit phenomenal valence; only the hedonic account makes it always conscious, contrary to cognitive science. Hedonic valence would threaten representationalism about consciousness; Aydede & Fulkerson and Kind reverse the argument. What natural property does valence represent? Cutter & Tye (harmfulness) rejected. Tracking theories vs. teleology vs. functional-role/non-reductive content. Correctness-condition sketch.

**§5 Conclusion (pp. 675–676).** Six numbered advantages; call for philosophers to attend to valence as the foundation of decision making.

---

## 3. Barlassina & Hayward (2019) — More of Me! Less of Me! Reflexive Imperativism about Affective Phenomenal Character

**Citation:** Luca Barlassina and Max Khan Hayward, "More of me! Less of me!: Reflexive Imperativism about Affective Phenomenal Character," *Mind* 128(512): 1013–1044, 2019. doi:10.1093/mind/fzz035.
**PDF:** `docs/project/references/imperativism/sources/Barlassina and Hayward 2019 - More of me Less of me - Reflexive imperativism about affective phenomenal character (author copy).pdf` — filed as an author copy, but the PDF is the typeset Advance Access version and carries the journal pagination; page citations below are journal pages (journal page = PDF page + 1012).

> **Scope note.** The targets are *not* Klein 2007 directly. "First-order imperativism" is Manolo Martínez's view (2011, 2015a, 2015b); "higher-order imperativism" is Klein's later book (*What the Body Commands*, 2015). Klein 2007 appears only as the origin of imperative treatments of pain (p. 1020). Evaluativism (Bain 2013; Carruthers 2018; Cutter & Tye 2011; Tye 2005) is named as a rival (p. 1014) and receives a short but important critique in §4.3.

### Phase 1: Foundational Overview

#### Introduction

Klein's original theory said pain commands you to do something *to your body* ("don't put weight on the ankle"). But what makes pain, misery, orgasm or joy feel *bad* or *good* — what philosophers call **affective phenomenal character**? Barlassina and Hayward agree that the answer lies in commands rather than descriptions, but they argue the command has been aimed at the wrong target. An unpleasant experience does not command you to fix the world or your body; it commands you to **get less of that very experience**. A pleasant experience commands **more of itself**. Their slogan: experiences feel pleasant or unpleasant "in virtue of commanding us *Get more of me! Get less of me!*" (p. 1014). This is **reflexive imperativism**.

#### Key Findings

1. **What a theory must explain.** Three questions: (Q1) what makes an experience feel pleasant/unpleasant at all; (Q2) what makes it positive rather than negative; (Q3) why that feeling motivates **all by itself** (without any further desire) and **reflexively** — why pain makes you want to be rid of *the pain*, not just of its cause.
2. **Commands about the world fail (Martínez's first-order imperativism).**
   - Itches and hunger issue world-directed commands ("scratch!", "eat!") yet can feel neutral.
   - Misery feels awful but commands nothing about the world; depression is a *loss* of world-directed urges.
   - Nothing principled decides whether "eat!" is an approach command or an avoidance command, so polarity is arbitrary.
   - A command to fix a tooth cavity does not explain why you take a painkiller.
   The same problems, they argue, hit **evaluativism** (the view that pain represents body damage as bad), because it is also directed at the world.
3. **A second, separate commanding state also fails (Klein 2015's higher-order imperativism).**
   - If the *commanding* state is the one that feels bad, it tells you to get rid of the (neutral) sensation rather than the bad feeling.
   - If instead the *targeted* sensation is the one that feels bad, cases break it: smokers can have an urge for more of a sensation that is not pleasant, and brain-lesion patients report unpleasantness with no sensation to target (Ploner et al. 1999).
4. **The fix: one experience that commands about itself.** An unpleasant pain is a single compound state = a bodily description (e.g. "burning disturbance in your right hand") + a self-directed command "Less of this experience!". This explains the cases: pain asymbolia (the description without the command) and Ploner's patient (the command without the description).
5. **Why would evolution build this?** Reflexive commands are a **reward/punishment system for learning**. A complex creature with a hurt ankle is not told what to do; it is told "less of this!", and it tries gaits, sleeping positions and ice until the command is satisfied.

#### Initial Takeaway

Unpleasantness is an experience's built-in order to make itself stop; pleasantness is an order to keep itself going. The theory makes every kind of affect alike in *how* it feels good or bad (the same command), while letting affects differ in *what else* they contain (sensations, thoughts, moods). It also gives a learning-based story of why suffering exists — a story that is directly interesting for agents that learn by reward and punishment.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**The explanandum and constraints (§2).** Affective phenomenal character (APC) is intentionalistically explained: phenomenal character depends on intentional content, so naturalising content naturalises phenomenology (pp. 1015–1016). APC has **intrinsic motivational force** — "Once you have told us that your experience feels bad, you have fully explained why you are motivated to get rid of it" (p. 1016) — understood dispositionally and *pro tanto* (a marathon runner can override it; fn. 4). What is distinctive is **reflexivity**: hunger is intrinsically motivating without always feeling bad, but APC motivates for or against *the very state that has it* (p. 1017). Pain asymbolia (pain reported as not unpleasant) is set aside as non-affective (fn. 3, p. 1015).

**Two kinds of content (§3.1, p. 1018).**

| | Indicative content (Indicators) | Imperative content (Commands) |
|---|---|---|
| Function | carry information that *p* | direct the addressee to φ |
| Evaluation | truth conditions | satisfaction conditions (satisfied iff addressee φs) |
| Correct uptake | forming a belief | forming a motivation |

Visual phenomenal character is motivationally inert and fits indicative content; APC is motivating and fits imperative content, whose correct uptake *is* a motivation (p. 1020). The Fregean alternative (one content, different forces) is set aside (fn. 5).

**Content schemas of the three imperativisms.** Let `E` be an experience, `S` a sensory state, and "!" the imperative mood.

First-order (Martínez) — George's hand in scalding water (p. 1021):

$$
E = \underbrace{\langle \text{there is a burning disturbance in your right hand} \rangle}_{\text{Indicator: sensory character}} \;+\; \underbrace{!\langle \text{see to it that the disturbance does not exist} \rangle}_{\text{Command: affective character}}
$$

Higher-order (Klein 2015), two numerically distinct states:

$$
\text{(HO1)}\;\; U \text{ feels bad},\; \mathrm{Content}(U) = !\langle \text{less of } S \rangle,\; S \neq U \qquad
\text{(HO2)}\;\; E \text{ feels bad iff targeted by } H \neq E,\; \mathrm{Content}(H) = !\langle \text{less of } E \rangle
$$

Reflexive (Barlassina & Hayward), one compound state (pp. 1032–1033):

$$
U = F \wedge K^{-}, \qquad \mathrm{Content}(K^{-}) = !\langle \text{less of the experience of which } K^{-} \text{ is a constitutive part} \rangle = !\langle \text{less of } U \rangle
$$

$$
P = F' \wedge K^{+}, \qquad \mathrm{Content}(K^{+}) = !\langle \text{more of } P \rangle
$$

where `F` is a first-order Indicator (possibly itself a first-order Command, fn. 11). Formal definition: "An experience E of a subject S has affective phenomenal character in virtue of being (at least partly) constituted by a Command K with reflexive imperative content" (p. 1032). If the experience has no constituent other than `K`, the command is about `K` alone.

**Same-order vs. higher-order (fn. 12).** One might call the view "reflexive higher-order imperativism"; the substantive point is one state targeting itself (Kriegel's same-order model) vs. two states, and this "apparently small distinction makes a huge explanatory difference" (p. 1033).

#### Argument Reconstruction

**Argument 1 — Against first-order imperativism (§4.2).** Target thesis FO: `E` has APC in virtue of first-order (world-directed) imperative content; negative APC = aversive first-order content, positive = appetitive.

| Counterexample | What it shows | Premise attacked |
|---|---|---|
| Mild itches and hunger: first-order commands ("Scratch!", "Eat!") that feel neither good nor bad (pp. 1021–1022) | first-order imperative content is **not sufficient** for APC | FO (sufficiency direction) |
| Alice's misery: she lies in bed all day; felt bad, no world-directed motivation (p. 1022). Martínez-style reply "Don't do anything!" rejected: depression is a global *loss* of world-directed urges, not a negative urge | first-order imperative content is **not necessary** for APC | FO (necessity direction) |
| Agonising hunger has appetitive content "Eat something!" but is unpleasant; redescribing as "Stop having an empty stomach!" shows the appetitive/aversive distinction is arbitrary, while (un)pleasantness is not (p. 1023) | FO has no principled answer to Q2 | polarity mapping |
| Toothache content "See to it that the cavity does not exist!" motivates dental care, not taking painkillers or distraction (pp. 1023–1024). Martínez (2015b) calls residual pain "spam", predicting painkiller-seeking only after one realises nothing else can be done; the authors report the opposite order (often we fix the body *to avoid the pain*) | FO cannot explain **reflexive, intrinsic** motivation (Q3) | FO's account of motivation |

**Diagnostic step (§4.3, p. 1025) — extension to evaluativism.** First-order *evaluative* content ("this bodily damage is bad for Joe") inherits the same defects: (i) if it motivates at all, it motivates care of the body, not getting rid of the experience; (ii) misery has no obvious first-order object to be represented as bad. Conclusion: "the problem with the contents chosen by Martínez is not that they are imperative. It is that they are first-order." The authors note evaluativists have replied (Bain 2013, 2019; Cutter & Tye 2014) and defer rebuttal (fn. 8).

**Argument 2 — Against higher-order imperativism (§5).**
- *HO1* (the Command itself feels bad). Advantages: mild itches lack the higher-order command; misery = neutral state + "Less of S!". Fatal problem: "Less of S!" motivates you to get rid of `S`, which is by hypothesis not unpleasant — "clearly absurd" (p. 1028). Attacks HO1's answer to Q3 (object of motivation misidentified).
- *HO2* (the targeted state feels bad). Gets the object of motivation right, but:
  - *Smoker case* (5.3.1): the urge "More of S!" (for the sensation of smoke at the back of the throat) co-occurs with `S`, yet `S` is neutral or unpleasant (p. 1029). HO2's sufficiency claim fails. Parallel to the desire theory of pleasure (Heathwood 2007): a celibate ascetic intrinsically desires that unbidden sexual arousal end, yet the arousal is pleasant (pp. 1029–1030).
  - *Pure affect* (5.3.2): depression's "black feeling"; Ploner et al. (1999) — a patient with a postcentral (somatosensory cortex) lesion reported a "clearly unpleasant" stimulus he wanted to avoid, while denying every sensory descriptor (pp. 1030–1031). No lower-order state exists for H to target; positing an unconscious somatosensory state is ad hoc and contradicted by the lesion. HO2's structural requirement (a distinct target) fails.
  - *Q3 again* (§7.1, pp. 1036–1037): in HO2 motivation is not *intrinsic* to the affective experience; it comes from a separate, affectless Command.

**Argument 3 — For reflexive imperativism (§6.2), an inference to the best explanation.**
- R1. *Taxonomy*: first-order Commands without `K` (mild hunger) are non-affective; any experience type can become affective by incorporating `K` (p. 1034).
- R2. *Double dissociation*: pain asymbolia = `F` without `K⁻`; Ploner's patient = `K⁻` without `F` ("Get less of me!" and nothing else); pure-affect depression likewise (p. 1034).
- R3. *Unity and diversity of pleasure*: all pleasant experiences share a `K⁺` (same order-type, different token referents — like "I am French" said by Margot and by Charlotte, fn. 13); they differ in their other constituents (pp. 1034–1035). fn. 14 argues APC is phenomenally **homogeneous**: common neural correlates; decisions require a common currency; when describing different pleasures we cite only non-affective differences (p. 1035).
- R4. *Intrinsic + reflexive motivation*: the content is imperative (intrinsic force) and about the experience it belongs to (reflexive) (p. 1035).
- C. Reflexive imperativism solves every problem that sank FO, HO1 and HO2.

**Argument 4 — Metaphysics of the compound (§7.1).** Objection: what is the difference between one conjunctive state and two co-occurring states? Answer at the syntactic level: believing *that the sun is shining and the sky is blue* = one token #SUN-SHINE & SKY-BLUE#, vs. two tokens; unpleasant pain = #F & K⁻# (p. 1037). Mixed indicative–imperative conjunction is defended by (a) explanatory payoff, (b) functional role — the Indicator part is consumed by belief, the Command part by motivation, which is why unpleasant pain yields both a belief that something is wrong in the body *and* a motive to end the experience, (c) precedent: Millikan's pushmi-pullyu representations, emotion models combining appraisals and action tendencies (Seth & Friston 2016), Martínez's own compounds (p. 1038).

**Argument 5 — Naturalisation and function (§7.2).** A "how-possibly" teleosemantics, explicitly not a commitment:

$$
K \text{ has imperative content } C \iff K \text{ has the biological function of making it the case that } C \quad \text{(p. 1039)}
$$

$$
K^{-} \text{ has content } !\langle\text{less of the experience of which } K^{-} \text{ is part}\rangle \iff K^{-} \text{ has the function of producing less of that experience}
$$

*Evolutionary story (pp. 1039–1041).* Simple creatures get by on fixed, specific responses. Complex creatures have many goals, many means, and bodies liable to a nearly endless variety of damage, so responses cannot be pre-programmed; they must **learn**, often by trial and error. APC "works as a system of reward and punishment" (p. 1040). The injured creature CC: uses its leg normally → unpleasant → "Less of this experience!" → changes gait, sleeping position, applies ice; when injured similarly later it re-enacts the strategy. Courtship success → "More of me!" → re-enact.

*Objection (p. 1041).* If the function of the ankle pain's unpleasantness is to stop weight-bearing, teleosemantics gives it first-order content "Don't put weight on your ankle!" (i.e., Klein 2007). *Reply*: there is no single world-directed behaviour APC has the function to produce, even for one ankle injury; a first-order content would be "a very, very long disjunction". APC "tells you *More/Less of this experience!* and leaves to you the task of figuring out which behaviour, if any, can satisfy this request" — cavity repair (world-directed) or a painkiller (mind-directed) (pp. 1041–1042). "It is a very self-centred character indeed" (p. 1042).

*Infants (fn. 16, p. 1040).* Worry: reflexive content is too sophisticated for infants. Reply: infants show mindreading at 6–8 months, which requires richer metarepresentation than reflexive commands.

#### Critical assessment (reviewer)

- **Relation to Klein 2007.** The ankle objection in §7.2 is essentially Klein's 2007 content. The authors' reply turns Klein's own functional argument around: Klein argued a *command* beats *information* because only one response is appropriate; Barlassina & Hayward argue that for complex learners *many* responses are appropriate, so the command must leave the choice of means open by targeting the experience.
- **Pressure points later exploited by Carruthers (2023).** (i) The evidential weight placed on reports of pure affect (Ploner) and on the smoker/ascetic intuitions; (ii) the claim that APC is phenomenally homogeneous; (iii) the risk that a self-directed command makes all motivation ultimately about one's own experiences — a form of **motivational hedonism**, which Carruthers 2018 attacked (self-sacrifice, input/output mismatch); (iv) the requirement of self-reference, which Carruthers 2018 used against the hedonic account (meta-representation in animals).
- The critique of evaluativism in §4.3 targets *Bain/Cutter & Tye*-style evaluativism about **body damage**. Carruthers's evaluativism says that in pain it is the *sensation* that is represented as bad, which already partly addresses the "why take painkillers?" objection; this is taken up in Barlassina 2020 and Carruthers 2023.

### Appendix: Section-by-Section Backbone

**Abstract and §1 Introduction (pp. 1013–1015).** Imperativism is on the right track but developed wrongly; first-order (Martínez) and higher-order (Klein 2015) versions fail; reflexive imperativism: P pleasant in virtue of a Command "More of P!", U unpleasant in virtue of "Less of U!". The in-virtue-of relation spans supervenience to identity (fn. 1). Fine-grained differences between "More of me!", "Get more of me!" are ignored (fn. 2). Rivals: evaluativism, psycho-functionalism, desire theory. Argument limited to "best form of imperativism", though the authors think it is the best theory overall.

**§2 The explanandum (pp. 1015–1017).** Experiences and phenomenal character; affective experiences (pain, orgasm, intense itch, emotions, moods). Q1, Q2. Intentionalism as a route to naturalising phenomenal character. APC explains motivation; intrinsic motivational force (dispositional, pro tanto). Reflexive motivational force distinguishes APC from hunger/desire. Q3.

**§3 Imperativism (pp. 1017–1020).** §3.1: indicative vs. imperative content (function, satisfaction/truth, uptake). Mental Indicators and Commands (Shea 2013). §3.2: first-order vs. higher-order indicative contents in perception; imperativism denies that indicative content suffices for all phenomenal character. History: Hall 2008 (itches), Klein 2007 (pain), Martínez 2011 (pain affect), Martínez 2015a and Klein 2015 (all affect).

**§4 First-order imperativism (pp. 1020–1025).** §4.1: definition; George (7) + (8); elegant but false. §4.2.1: first-order content without APC (itch, hunger). §4.2.2: APC without first-order content (misery); "Don't do anything!" reply rejected. §4.2.3: positive/negative arbitrary (agonising hunger). §4.2.4: no reflexive/intrinsic force (toothache; Martínez's "spam" quote; the predicted order of painkiller-seeking is wrong). §4.3: the fault is first-order-ness, which also sinks first-order evaluativism; imperativists should go mind-directed — Klein 2015 went higher-order.

**§5 Higher-order imperativism (pp. 1025–1031).** Definition of higher-order imperative content; Klein 2015 quote ("second-order imperative directed towards a first-order sensation"). §5.1 HO1; George as two experiences; gustatory pleasure. §5.2 advantages (taxonomy, misery) and the absurdity of commanding away the neutral state. §5.3 HO2; Louise's finger. §5.3.1 smoker's urge; desire theory and celibate ascetic; Heathwood's idiosyncratic intrinsicality (fn. 10). §5.3.2 pure affect: depression and Ploner et al. 1999; unconscious-sensation reply rejected. §5.4 moral: mind-directed imperatives are right, higher-order ones wrong.

**§6 Reflexive imperativism (pp. 1031–1035).** §6.1: reflexive/same-order states; definition of reflexive Command; theory statement; (22)/(23); George's U = F + K⁻; pleasant neck sensation. fn. 12 on same-order vs. higher-order. §6.2: taxonomy; asymbolia and Ploner as double dissociation; pure-affect depression; commonality and heterogeneity of pleasures (fn. 13 indexical analogy; fn. 14 homogeneity of APC); intrinsic and reflexive motivational force.

**§7 But how? And why? (pp. 1036–1042).** §7.1 "Get it together!": conjunction vs. co-occurrence; why HO1 is not reflexive and HO2 not intrinsic; syntactic account #F & K⁻#; mixed indicative–imperative representations defended (functional consumers, pushmi-pullyu, emotion science). §7.2 "Reflexive imperative content naturalised": toy teleosemantics; evolutionary function of APC as reward/punishment enabling learning in complex creatures; CC's ankle and courtship; Bentham's "two sovereign masters"; infants (fn. 16); the first-order-function objection and the "long disjunction" reply; "a very self-centred character indeed".

---

## 4. Barlassina (2020) — Beyond Good and Bad: Reflexive Imperativism, not Evaluativism, Explains Valence

**Citation:** Luca Barlassina, "Beyond good and bad: Reflexive imperativism, not evaluativism, explains valence," *Thought: A Journal of Philosophy* 9(4): 274–284, 2020. doi:10.1002/tht3.471.
**PDF:** `docs/project/references/imperativism/sources/Barlassina 2020 - Beyond good and bad - Reflexive imperativism not evaluativism explains valence.pdf` — published version; page citations are journal pages (journal page = PDF page + 273).

> **Role in this corpus.** This is the anchor paper: a short, head-to-head comparison of Carruthers's (2018) evaluativism and Barlassina & Hayward's (2019) reflexive imperativism, judged by the two tests Carruthers himself set — does the theory explain **what valence feels like**, and does it explain valence's role in **deciding by imagining the options**?

### Phase 1: Foundational Overview

#### Introduction

Both sides agree on a lot: valence (pleasantness/unpleasantness) is one kind of thing across pains, pleasures, emotions and desires, and it is the brain's common currency for comparing options. They disagree about what valence *is*. For Carruthers, feeling bad is **something in the world seeming bad** (the bear seems bad). For Barlassina, feeling bad is **an experience urging you to have less of that kind of experience** ("Get less of me!"). Barlassina argues that, measured by Carruthers's own yardsticks, the imperativist account wins.

#### Key Findings

1. **Four stories in which "feeling bad" and "the world seeming bad" come apart** (pp. 277–279):
   - *The cake*: Olivia, hungry and without her wallet, desires a cake that looks delicious. The cake seems *good*, yet her desire feels *unpleasant* and she wants to be rid of it.
   - *The general and the saint*: both are proud of saving a village; their pride presents their deeds as *good*. The general's pride feels pleasant; the saint's feels unpleasant, because she believes she should stay humble.
   - *The dentist*: heavily anaesthetised, Barlassina sees his wrecked mouth in the mirror. It *looks bad*, but the experience feels neither pleasant nor unpleasant.
   - *Bonjour tristesse*: Jean-Paul wakes up miserable. Nothing in particular seems bad, yet the misery is unpleasant and he wants it gone.
   Evaluativism can patch each case only separately; reflexive imperativism handles all four the same way.
2. **Deciding by imagination is about imagined experiences, not imagined objects.** When choosing pizza or pasta, people imagine *tasting* pizza, not just pizza. Three kinds of evidence are cited: forecasting uses the brain's default network, which also supports memory and imagination of experiences; the valuation region (ventromedial prefrontal cortex) is engaged in first-person thinking; and current hunger biases choices about food for later ("projection bias"), as expected if imagining re-uses the real experience system.
3. **Carruthers's two objections are turned around.**
   - *Self-sacrifice*: people who die for a group typically experience "identity fusion" with that group, so they can imagine *themselves* going on to enjoy the outcome after their bodily death.
   - *Evolution*: evolution builds on what already exists, and human future-thinking already works by simulating experiences. An experience-directed decision system fits that existing format.
4. **Two worries are answered.**
   - Why do you drink when an unpleasant thirst says "less of me"? Because drinking satisfies both the desire's own command ("drink!") and the reflexive command.
   - Why order pizza rather than keep imagining tasting it? Because only ordering answers the question actually being decided, "what shall I order?" — "Imagining tasting pizza is not on the menu" (p. 283).

#### Initial Takeaway

What makes an experience feel good or bad is not *what it shows the world to be like* but *what it urges you to do about the experience itself*. The cases are compact and memorable, and they make the debate testable in part: the theories disagree about which kind of imagination drives choice and about whether valence can come apart from evaluation.

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Shared ground (§2, p. 275).** Barlassina accepts Carruthers's three reasons for treating valence as a natural kind: (i) a common valuation network (anterior insula, striatum, dorsomedial and ventromedial prefrontal cortex), engaged both when having and when imagining (dis)pleasure; (ii) shared interventions (acetaminophen blunts physical and emotional pain, and pleasure); (iii) the common-currency role in choosing between incommensurable options (film vs. restaurant).

**The two content schemas as stated here (§3, p. 276).**

Evaluativism — first-order, evaluative, nonconceptual:

$$
E \text{ is (un)pleasant} \iff E \text{ represents its worldly object } O \text{ as good (bad)}
$$

Reflexive imperativism — same-order, imperative, experience-directed:

$$
E \text{ is (un)pleasant} \iff E \text{ has the content } !\langle \text{get more (less) of the type of experience of which I am a token} \rangle
$$

**A refinement relative to 2019.** "Here 'me' picks out the type of experience, rather than the token experience" (p. 276). In 2019 the command's referent was the experience of which the command is a constituent (a token; see 2019 fn. 13). Making the referent a *type* is what allows "more of me!" to be satisfied by future experiences of the same type, which the decision-making argument (§5) and the pizza reply (§6.2) require. Reflexive content is **same-order** (Kriegel): about a mental state, but about *itself* rather than a distinct state (fn. 1).

**Divergent phenomenological predictions (§4.1, p. 277).** Evaluativism predicts valence phenomenology is *evaluative and world-directed* (the genitals' condition appears good in orgasm; the bear appears bad). Reflexive imperativism predicts it is *conative and experience-directed*: unpleasantness is felt as "an inclination to get less/more of that very state". Since evaluativism **identifies** felt (un)pleasantness with worldly objects' seeming bad/good, any case where these dissociate is a counterexample.

#### Argument Reconstruction

Let EV be evaluativism's biconditional, split into:
- **EV-suff**: if `E` represents `O` as bad (good), `E` is unpleasant (pleasant).
- **EV-nec**: if `E` is unpleasant (pleasant), `E` represents some worldly `O` as bad (good).
- **EV-uni**: a single, uniform first-order content explains valence across all affect (the unification virtue Carruthers claims).

**The four cases and what each attacks (§4.2).**

| Case | Structure | Premise attacked | Evaluativist repair considered | Why the repair fails | Reflexive-imperativist account |
|---|---|---|---|---|---|
| **The cake** (p. 277–278) | desire represents the cake as good; desire feels unpleasant | EV-suff (with a good-based theory of desire, Oddie 2005, all desires would feel pleasant) | unfulfilled desires represent *not having the cake* as bad | then all unfulfilled desires would feel unpleasant; counterexample: the guitarist driving to her concert, whose unfulfilled desire to play feels extremely pleasant (p. 278) | desire's first-order content is irrelevant to valence; Olivia's desire says "Get less of me!", the guitarist's "Get more of me!" — which also explains the felt inclination to be rid of / prolong the desire |
| **General Bouba and Saint Kiki** (pp. 277–279) | both prides represent self and deeds as good; only Kiki's is unpleasant | EV-suff | (a) valence is sometimes higher-order; (b) Kiki's shame represents her pride as bad | (a) makes evaluativism patchy (attacks EV-uni); (b) even granted, her pride still represents her deeds as good, so evaluativism predicts **ambivalence** (pleasure + displeasure), "But she is not feeling any pleasure at all" (p. 278) | Kiki's pride = evaluative content "I and my deeds are good" + reflexive "Get less of me!" |
| **The dentist** (p. 278–279) | anaesthetised; visual experience itself nonconceptually represents mouth as bad; valence-neutral | EV-suff (evaluative content without valence) | none offered | — | drugs prevent the visual experience from acquiring reflexive imperative content, so no inclination for or against it |
| **Bonjour tristesse** (pp. 278–279) | objectless misery; nothing appears bad | EV-nec | Carruthers 2018: depression represents the world or the body as bad | granted for some moods (Kind 2014), but not this one — there is no worldly object | pure reflexive content: "Get less of me!" alone = pure misery ("Get more of me!" alone = "pure elation"); misery felt as a "free-floating" inclination to get rid of itself (p. 279) |

Meta-claim: even if each case can be handled, only piecemeal changes will do it, so evaluativism trades **explanatory unification** for adequacy, whereas reflexive imperativism gives one principled treatment (p. 277).

**Argument on decision-making architecture (§5).**

Shared three-step architecture (p. 279): (1) imagine each option; (2) affective forecasting — each imagining elicits (un)pleasantness; (3) compare and select the most pleasant.

| | Reflexive imperativism | Evaluativism (Carruthers) |
|---|---|---|
| What is imagined | the **experiential** outcome (imagining *tasting* pizza) | the **worldly** outcome (imagining *pizza*) |
| What feels (un)pleasant | the simulated experience | — (valence represents the pizza as good) |
| What is compared | strength of the simulated experiences' imperative contents | expected values of worldly outcomes |
| Fit with psychology | received view of affective forecasting (Gilbert & Wilson 2007; Miloyan & Suddendorf 2015) | requires revising the received view |

Evidence that forecasting takes **experiential imaginings** as input (§5.2, p. 280):
- E1. Affective forecasting engages the default network, which supports experiential projection (episodic memory, perspective-taking, experiential imagination).
- E2. Ventromedial prefrontal cortex, the main value-comparison region, is recruited in first-person thinking and hypothesised to process experiential imaginings.
- E3. Experiential imagination is cognitive **re-use**: to simulate fear one runs the fear system off-line. Prediction: the current state of the re-used system biases forecasts. Confirmed as **projection bias** (Loewenstein et al. 2000): current hunger changes choices about food to be eaten later.

**Rebuttals of Carruthers's two arguments for world-directed choice (§5.3).**
- *Self-sacrifice.* Carruthers (2018, p. 667): the martyr imagines the post-revolution world as better than continued life without it; an experience-directed account seems unable to explain this, since one cannot imagine enjoying a world after one's death. Reply: if one identifies with one's group rather than one's body, one *can* imagine experiencing the outcome. Prediction: extreme self-sacrifice should be preceded by **identity fusion**; reported as confirmed across fundamentalists, insurgents and tribal warriors (Whitehouse 2018; Swann et al. 2012) — "the survival of the group constitutes a form of immortality" (Whitehouse, quoted p. 281). The argument is claimed to become evidence *for* reflexive imperativism.
- *Evolution.* Carruthers (2018, p. 670): "Evolution couldn't care less about how one feels"; expected pleasantness is an imperfect proxy for fitness. Reply: evolution is a **tinkerer** constrained by existing structures; human future-thinking is already episodic (simulating future experiences; Boyer 2008; Schacter et al. 2017), so an experience-directed decision architecture "had the right representational format to interface with experiential future thinking" (p. 281). Note the form of the reply: it concedes the fitness-proxy point and explains selection by historical constraint rather than optimality.

**Replies to objections (§6).**
- *Unpleasant desires (§6.1, p. 282).* Problem: an unpleasant desire for water commands "Get less of me!"; why does the decision-making system (DMS) choose to drink rather than suppress the desire? Reply: the desire also carries first-order content ("Drink water!"); the DMS maximises satisfaction of all incoming requests; drinking satisfies both. *Exclusion worry*: then valence is motivationally idle. Reply: valence adds force — a neutral thirst loses to the wish to keep watching an enjoyable film, an unpleasant thirst is more likely to win.
- *Simulated experiences (§6.2, pp. 282–283).* Problem: imagining tasting pizza is pleasant, so commands "Get more of [simulated gustatory experience]!", which predicts continuing to imagine rather than ordering. Reply: because simulation re-uses the genuine system, the DMS treats genuine and simulated experiences as the same *type*; both ordering and continued imagining satisfy the command, but only ordering solves the decision problem that prompted the imagining ("What food shall I order?").

#### Critical assessment (reviewer)

- **Evidential status of the cases.** The four cases are intuitions about imagined scenarios (plus one first-person anecdote). The dentist case leans on the claim that the *visual experience itself* nonconceptually represents the mouth as bad; an evaluativist can deny this and say only a judgement is involved — which is essentially Carruthers's 2023 line: the dentist case involves conceptual recognition of damage, not valence (see [§5](#5-carruthers-2023--on-valence-imperative-or-representation-of-value)).
- **Shift to experience-directed choice.** The architectural argument commits reflexive imperativism to something close to the "prefeel" model Carruthers (2018) called motivational hedonism. Barlassina accepts the received view in affective-forecasting psychology rather than denying the hedonist resemblance; the self-sacrifice reply shows the cost (it needs identity fusion to handle altruistic sacrifice).
- **Type vs. token.** The move to type-reference is necessary for the decision-making story but makes the content less obviously "reflexive" in the 2019 sense; it is now a command about a kind of experience that the present token instantiates.
- **Exclusion reply.** The reply shows valence *adds* motivational force but does not show it is *necessary*; neutral desires motivate too, which is compatible with evaluativism's view that valence is one input to a common currency.

### Appendix: Section-by-Section Backbone

**Abstract and §1 Introduction (pp. 274–275).** Both theories treat valence as a natural kind; evaluativism: (un)pleasant in virtue of representing the worldly object as good/bad; reflexive imperativism: in virtue of commanding more/less of itself. Thesis: reflexive imperativism is superior by Carruthers's standards (phenomenology; imagination-based decision-making). Epigraph from Nietzsche: "One loves ultimately one's desires, not the thing desired." The narrower debate on pain's unpleasantness (Bain 2013; Jacobson 2019; Martínez 2011) may be too narrow.

**§2 A kind of (un)pleasantness (p. 275).** Varieties of affect; Carruthers's three reasons for a natural kind (network, interventions, common currency). Barlassina and Hayward accept the claim; the disagreement is about explanation.

**§3 A tale of two theories (p. 276).** Both intentionalist. §3.1 Evaluativism: toothache as sensory content + evaluative content; applied across all affect (bear, team victory, itch); first-order, evaluative, nonconceptual. §3.2 Reflexive imperativism: "Get more/less of me!", "me" = type; warmth-in-neck example; reflexive content is same-order, experience-directed. Theories should be compared on phenomenology and imagination-based decision-making.

**§4 The phenomenology of valence (pp. 277–279).** §4.1: divergent predictions (evaluative/world-directed vs. conative/experience-directed); four dissociation cases force piecemeal repairs. §4.2: The cake; General Bouba and Saint Kiki; The dentist; Bonjour tristesse — each analysed as above.

**§5 Imagination-based decision-making (pp. 279–281).** §5.1: shared three-step architecture; experience-directed (RI) vs. world-directed (EV) versions. §5.2: three lines of evidence for experiential imagination (default network; vmPFC; cognitive re-use and projection bias). §5.3: self-sacrifice via identity fusion; evolution as tinkerer and episodic future thinking.

**§6 Better be good (pp. 281–283).** Being better than evaluativism is not being correct; fuller treatment deferred to Barlassina & Hayward (2020, "Loopy regulations"). §6.1: unpleasant desires; request-satisfaction maximisation; exclusion problem and the movie example. §6.2: simulated vs. genuine experience as one type for the DMS; "Imagining tasting pizza is not on the menu."

---

## 5. Carruthers (2023) — On Valence: Imperative or Representation of Value?

**Citation:** Peter Carruthers, "On Valence: Imperative or Representation of Value?," *The British Journal for the Philosophy of Science* 74(3): 533–553, 2023 (electronically published 26 July 2023). doi:10.1086/714985.
**PDF:** `docs/project/references/imperativism/sources/Carruthers 2023 - On valence - Imperative or representation of value (author copy).pdf` — author copy with placeholder page numbers ("000"); page citations below are manuscript pages ("ms. p. N"), which do not match the published pages 533–553.

> **Citation-key warning.** Carruthers cites two Barlassina & Hayward papers: **[2019a] = "Loopy Regulations: The Motivational Profile of Affective Phenomenology"** (*Philosophical Topics* 47: 233–261), which is **not in this corpus**, and [2019b] = the *Mind* paper reviewed above. Several objections Carruthers answers — the pure-mood objection as he states it, the trainee-doctor/expert injury case, the liking-vs-wanting dissociation argument, and the appeal to affective-forecasting language — are attributed to "Loopy Regulations". This review reports how Carruthers represents them but cannot check them against their source.

### Phase 1: Foundational Overview

#### Introduction

Five years after "Valence and Value", Carruthers replies to the imperativists. His question is which theory gives the best interpretation of **the science of affect**: are the brain's pleasantness/unpleasantness signals *commands* ("more of this!", "less of this!") or *measurements of value* (how good or bad something is for the organism in evolutionary terms)? He argues for the second. His main strategy is to go on the offensive with neuroscience and theories of mental representation, then to rebut the imperativists' counterexamples one by one. Compared with 2018, the content of valence is now stated as **adaptive value**: valence represents how beneficial or harmful something is for survival and reproduction, or what has been learned to predict such benefit or harm.

#### Key Findings

1. **Valence must at least *represent* value.**
   - Affect is triggered by appraisals that track things that were good or bad for survival and reproduction ("primary" rewards and punishers such as food when hungry, tissue damage, nausea) or that have been learned to predict them (after food poisoning, chicken becomes disgusting).
   - So valence signals reliably carry information about value, and they do their job *because* they carry it.
   - On standard scientific theories of mental content, that makes valence a representation of value. Imperativists can at most add a command on top, and they have not shown the command is needed.
2. **The science does not need imperatives, and sometimes contradicts them.**
   - *Learning*: prediction-error learning can be described entirely as updating stored values.
   - *Decision-making*: neuroeconomic models integrate value, probability and effort.
   - *Brain location*: commands should live in motor-planning areas, but valence signals are found in value areas (striatum, amygdala, insula, orbitofrontal cortex), separate from motivation and action networks.
   - *Attention*: people stare at a gruesome accident even though it is horrible; "less of this experience!" predicts they would look away.
3. **The counterexamples are answered by multiple appraisals.**
   - *Depression*: the world seems flat, and "the fact that nothing seems good seems bad".
   - *The saint*: she appraises her own pride as a betrayal.
   - *Unpleasant desires*: the desired thing seems good, but the prospect of not getting it seems bad.
   - *The dentist*: seeing damage is a conceptual recognition, not negative valence.
   - *The brain-lesion patient* (Ploner et al. 1999): he still felt something bad "somewhere between fingertip and shoulder", so the case is not pure objectless valence.
4. **Stakes.** If valence underlies all decisions, then an imperativism aimed at experiences implies **motivational hedonism** — every choice would be made in order to get certain experiences for oneself.

#### Initial Takeaway

For Carruthers, pleasure and pain are the brain's gauges of how good or bad things are for the organism, and those gauges feed learning, choice and attention. Commands to have more or less of an experience, he argues, add nothing that the science needs and make at least two false predictions (where valence is computed in the brain, and whether we look at horrible sights).

### Phase 2: Graduate-Level Deep Dive

#### Technical Analysis

**Refined evaluativist content (§1, §3).** Valence is a pair of **analogue-magnitude** representations. Positive and negative valence are processed by largely distinct networks, so valence is better described as a common *scale* than a single signed currency (ms. p. 1, citing Rolls). Content:

$$
V^{+}(o) \;=\; \langle\, o \text{ has adaptive value of magnitude } m \,\rangle, \qquad V^{-}(o) \;=\; \langle\, o \text{ has adaptive disvalue of magnitude } m \,\rangle
$$

where `o` is the appraised item or event (in the world or body), and "adaptive value" covers both primary reinforcers (value fixed by natural selection) and secondary reinforcers (value acquired by learning) (ms. pp. 8–9). Valence does not represent goodness "as such": it is prior to the concepts GOOD/BAD, like approximate-numerosity impressions (ms. p. 14, fn. 10). Contrast Carruthers 2018, where the content was "goodness/badness" with correctness conditions left open; here the teleosemantic/informational commitment is explicit.

**Imperativist content as Carruthers states it (§1, §3).** "Graded-strength imperatives with the content, 'more of this!' and 'less of this!'" (ms. p. 2); the reflexive version refers to the whole experience of which the valence is a part. For pain, Martínez's non-reflexive version (target = sensory component) and the reflexive version "pretty nearly coincide" (ms. p. 2). A *world-directed* imperativism (Martínez 2011 on fear: "less of [the approaching bear]!") "would pick on the wrong component of affect to identify with valence", because world-directed urges are separate from valence (ms. p. 3).

**The affective-science background (§2).** Affective states form a homeostatic property cluster (Boyd) with four features:
1. **Appraisal** of value — world-focused (fear), body-involving (hunger), almost wholly bodily (pain), or generalised (moods as appraisals of environmental opportunity; Eldar et al. 2016). Appraisals need not be judgement-like or conscious.
2. **Arousal**.
3. **Automatic motor plans** (fear face, fleeing or freezing, approach/avoid reaction-time effects; pain activates nursing and protecting the painful part). Crucially, these are produced "independently of the valence component": valence and action tendencies share a *common cause* (the appraisal), and neither runs via the other (ms. p. 4, citing LeDoux). Valence later interacts with them (feedback builds habits; suppressing urges is effortful and negatively valenced; fn. 4).
4. **Valence**, with three roles: (i) decision-making by prospection (also in birds); (ii) evaluative learning via prediction errors (Schultz et al. 1997), possible without consciousness; (iii) biasing perception and competing for attention in the salience system, which implies valence need not be conscious (ms. pp. 5–6). Valence is modulated top-down (placebo/nocebo; parachute belief turns terror into exhilaration; ms. p. 6).

On this picture experience-directed imperativism "treats valence as a wholly unspecific generalization of the automatic action-initiation tendencies" (ms. p. 5).

#### Argument Reconstruction

**Argument 1 — Direct vs. indirect motivation is a wash (§3, ms. pp. 6–7).** Imperativism's advertised advantage: valence is an urge toward unspecified action, a "high-level motor instruction", hence *directly* motivating. On evaluativism motivation is indirect: via decision → intention, and via attention strengthening appraisal-caused action tendencies (Cochrane 2019). But both sides agree that where decisions are made, valence acts through decision-making; whether decision-making is competition among value indicators or among imperatives gives "not … a strong advantage either way" (ms. p. 7).

**Argument 2 — The meta-representation worry, raised and softened (§3, ms. p. 7).**
- P1. Reflexive imperatives refer to an experience, so valence is meta-mental (Barlassina & Hayward's "same-order" label hides this).
- P2. Valence exists in almost all creatures capable of evaluative learning, including snails; meta-representation outside humans is disputed.
- Tentative C. Imperativism takes on a controversial commitment.
- Carruthers's own mitigation: the reference is via a **pure indexical**, needing no theory of mind or mental-state concepts; non-conceptual metacognition may be widespread (Shea 2014 on error signals). So this "perhaps does not present any deep difficulty" (ms. p. 7). (Note the reversal: in 2018 an analogous meta-awareness requirement was used as a strike against the *hedonic* account.)

**Argument 3 — The pushmi-pullyu argument: valence represents adaptive value (§3, ms. pp. 8–9).** This is the paper's central positive argument.
- P1. Affective states are caused by appraisals that are sensitive to primary reinforcers/punishers (adaptive value fixed by selection: eating when hungry, drinking when thirsty, orgasm, social admiration; tissue damage *or risk of tissue damage*, nausea, physical danger, social disrespect) and secondary ones (learned predictors; the Garcia effect — after vomiting from chicken salad, chicken evokes disgust for weeks) (ms. p. 8).
- P2. Hence positive (negative) valence reliably indicates an overall balance of valuable over disvaluable (disvaluable over valuable) properties in the appraised item (ms. p. 9).
- P3. Valence's roles are adaptive *because of* this information: choosing the most positively valenced option is adaptive because valence tracks adaptive value; prediction-error learning is adaptive because errors update indications of value; valenced items attract attention because of their relevance.
- P4. On informational/teleosemantic theories of content — Shea (2018): content is the information whose carrying explains the stabilisation of the signal's roles; Rupert (2018): the information that explains the signal's computational role — a signal satisfying P2–P3 represents what it carries information about.
- P5. Downstream consumers treat valence as a representation of value: it gives rise to judgements of good and bad ("Oh, this is bad!", ms. p. 9).
- C1. Valence represents adaptive value or disvalue.
- C2. Imperativists must at least accept that valence is a **pushmi-pullyu** representation (Millikan 1995: indicative and imperative at once), and the burden is on them to show the imperative part is needed — "Otherwise evaluativism gets to win by default" (ms. p. 9).

**Argument 4 — Imperatives are explanatorily idle in the science (§4, ms. pp. 10–11).**
- *Evaluative learning.* Imperativists can re-describe learning: stored expectations of imperative urgency are updated when "more of me!" is stronger or weaker than expected. This is consistent but unnecessary; "the entire story of affective learning can be told in terms of value" (ms. p. 10). Schematically, the standard story is a value update driven by a valence prediction error:

  $$
  \delta \;=\; v_{\text{experienced}} - v_{\text{expected}}, \qquad V_{\text{stored}}(\text{event type}) \leftarrow V_{\text{stored}}(\text{event type}) + \alpha\,\delta
  $$

  (the equation is the reviewer's schematic rendering of the prose description on ms. p. 10 — Carruthers gives no formula; the step size α is not in the text).
- *Decision-making.* Neuroeconomic models integrate outcome value, likelihood and energetic cost of acting; valence appears twice (outcome value; negative valence of expected effort). They are formulated in terms of value, so "some form of evaluativism is implicit in the science" (ms. p. 11).
- *Affective forecasting language.* Psychologists' talk of anticipated experiences (Gilbert & Wilson) "does no serious work in their theories"; it may be "a hedonist gloss". Whether forecasting errors are errors of predicted value or of predicted imperative strength has no bearing on the findings (ms. p. 11). (This is Carruthers's reply to the experiential-imagination premise; see also Argument 7.)

**Argument 5 — False localisation prediction (§4, ms. pp. 11–12).**
- P1. If valence were an imperative ("do something to get more/less of me!"), or an active goal to sustain or eliminate an experience, it should be realised in abstract premotor cortex or in dorsolateral prefrontal goal-maintenance networks.
- P2. Valence is instead realised in ventral striatum–orbitofrontal networks (positive) and amygdala–anterior insula–orbitofrontal networks (negative); orbitofrontal cortex codes outcome values; ventromedial/medial prefrontal cortex integrates expected value; anterior cingulate–dorsolateral prefrontal interaction resolves competition into decisions.
- P3. So valence and motivation are realised "in very different non-overlapping networks" (ms. p. 12).
- C. Imperativism's localisation prediction is false, unless neuroscientists have misidentified orbitofrontal cortex as a value area when it is really a high-level motor area, a revision no philosophical argument should force (ms. p. 12).

**Argument 6 — The attention asymmetry (§4, ms. p. 13).**
- Positive case (handled): mind-wandering while proof-reading — the word "island" unconsciously cues Caribbean memories, whose positive valence captures attention. The imperativist reading works: "more of me!" is satisfied by attending.
- Negative case (not handled): "I couldn't help looking, it was so horrible". Imperativism: the experience of seeing the accident scene commands "less of me!", so one should look away or never notice. People are instead drawn to look. Evaluativism: adaptively bad things are highly relevant, so they attract attention (Cochrane 2019).
- Target premise: that negative valence *is* an experience-directed avoidance command operating in the salience system.

**Summary of §4 (ms. p. 13).** Imperativism is (i) unnecessary, (ii) wrong about localisation, (iii) wrong about negative valence and attention. Evaluativism fits "synergistically": the same adaptive values appraised on the input side are represented by valence on the output side (echoing the 2018 input/output argument, now with adaptive value as the content).

**Argument 7 — Replies to the counterexamples (§5).** Preliminary: introspection has little discriminating power. Both theories predict that we judge worldly contents good/bad and are motivated to pursue/reject them (ms. p. 14). The general diagnosis: imperativists underestimate how **multiple appraisals and re-appraisals**, including appraisals of higher-order contents and appraisals that follow the shifting focus of attention, combine in one affective state.

| Imperativist case (source) | Carruthers's reply (2023) | Premise of the objection targeted |
|---|---|---|
| **Pure moods / depression** (attributed to B&H 2019a; corresponds to Barlassina 2020's *Bonjour tristesse* and B&H 2019's "black feeling") | Moods lack an identifiable *cause*, not an object: the depressed look at a blue sky, azaleas or favourite music and think "Meh!". Absence of positive affect is not negative affect, but appraisal can take higher-order contents: "the fact that nothing seems good seems bad"; attention to one's listless body makes it seem bad; cheerfulness is the mirror image. Challenge: produce a case that cannot be handled this way (ms. pp. 14–15) | that the mood has *no* object available for evaluation |
| **Ploner et al.'s patient** (B&H 2019b) | fn. 11: B&H's quotation omits that the patient described a "clearly unpleasant" feeling "emerging from an ill-localized and extended area 'somewhere between fingertip and shoulder'". So a vaguely specified body region was felt as the site of something bad — not objectless valence (Cochrane 2019 makes a similar point) (ms. p. 15) | that the case is *pure* valence with no represented object |
| **The general and the saint** (Barlassina 2020) | Both appraise their deeds as worthy and the applause as admiration, so both have positive non-conceptual valence directed at themselves. The saint, aware of feeling pride, additionally appraises that as a betrayal of her values and undergoes a *large-magnitude* negative valence directed at herself (ms. p. 15) | that evaluativism cannot explain the saint's unpleasantness. **Not addressed:** Barlassina's rejoinder that this predicts ambivalence while the saint feels "no pleasure at all"; the reply implicitly relies on magnitude dominance |
| **Unpleasant and pleasant desires** (Barlassina 2020, the cake / the guitarist) | All felt desires represent their objects as non-conceptually good, but the *desire* need not feel good: awareness that the object will not be obtained (or conflicts with a stronger want) is appraised as frustration → negative valence directed at the *situation*; expectation of satisfaction → positive valence (ms. p. 16) | that one uniform desire-content must fix the valence of the desire |
| **Trainee doctor vs. expert viewing an injury** (attributed to B&H 2019a) | Both visually represent the injury as *conceptually* bad; only the novice appraises it as disgusting (non-conceptual badness); the expert is habituated (ms. p. 16) | conflation of conceptual with non-conceptual evaluative content |
| **The dentist** (Barlassina 2020) | Seeing that the teeth are misaligned is a conceptual recognition of damage, or a non-conceptual representation of something that *implies* damage; "No evaluativist would identify such contents with negative valence" (ms. p. 16) | that the anaesthetised visual experience has the evaluative content evaluativism equates with valence |
| **Experiential imagination in prospection** (Barlassina 2020 §5) | Everyone agrees prospection uses sensory imagery in sensory brain regions; what is appraised is the *represented content* of the images, not the images as experiences — and imperativists should say the same, since in real fear the appraisal responds to the bear even if its output were "less of me!" (ms. p. 16) | the inference from "prospection is experiential" to "valence is experience-directed" |
| **Liking/wanting dissociations** (attributed to B&H 2019a; Berridge & Kringelbach) | These dissociations are the main evidence for the distinction between direct, valence-free, appraisal-caused motivation and indirect, valence-based motivation — agreed science, fully consistent with evaluativism (ms. p. 17) | that dissociation of pleasure from world-directed motivation favours experience-directed valence |

**Not answered in the 2023 paper** (verified by text search of the extract): Barlassina 2020's identity-fusion reply to the self-sacrifice argument, the evolution-as-tinkerer reply, the projection-bias evidence, the unpleasant-desire exclusion problem (§6.1), and the "not on the menu" reply (§6.2). The guitarist is answered only implicitly through the desire reply.

**Conclusion (§6, ms. p. 17).** Imperativism is unnecessary, since valence already represents adaptive value, and faces "severe difficulties" with established neuroscience; evaluativism is consistent with the science and faces no difficulties "that cannot readily be overcome".

#### Critical assessment (reviewer)

- **Where the burden shifts.** Argument 3 is the strongest move: if informational/teleosemantic content is accepted, *any* reliable value-tracking signal represents value, so imperativists must argue for an *additional* imperative content. Note, however, that Barlassina & Hayward (2019, §7.2) also used teleosemantics, assigning content by *function* (the function of producing less of the experience). The disagreement is thus partly about which effect explains stabilisation: *information about value* (Carruthers) vs. *regulating one's own experience* (Barlassina & Hayward). Neither paper settles this empirically.
- **Localisation argument.** The argument assumes imperative content must be realised where motor plans or goals are maintained. An imperativist can reply that content is fixed by functional role, not anatomical neighbourhood. The inference from "not in premotor cortex" to "not imperative" is therefore contestable, though the dissociation of valence from action tendencies (common-cause structure) is a substantive empirical point.
- **Attention argument.** The gruesome-accident case targets the *reflexive* formulation specifically. Imperativists might reply that looking is driven by separate appraisal-caused orienting urges (which Carruthers himself says are distinct from valence), so the case may not discriminate — a symmetry Carruthers does not discuss.
- **Unaddressed replies.** The identity-fusion and tinkerer replies from Barlassina 2020, and the exclusion problem, remain open in this corpus.
- **Reading of Klein 2015.** Carruthers says Klein (2015) gives an imperative theory of the *sensory* component of pain and "is explicit that he lacks a theory of the badness, or painfulness, of pain" (ms. p. 2, fn. 2). Barlassina & Hayward (2019) instead read Klein 2015 as a higher-order imperativism *about unpleasantness* and quote him to that effect (p. 1026). These readings conflict; Klein 2015 is not in this corpus, so the conflict cannot be settled here.

### Appendix: Section-by-Section Backbone

**Abstract and §1 The Two Theories (ms. pp. 1–3).** Affect spans bodily pains and pleasures, emotions, felt desires and moods; valence is the common currency (better: common scale) of non-discursive decision making in humans and animals. Evaluativism (Carruthers 2018; Cochrane 2019): analogue-magnitude representations of value. Imperativism (B&H 2019a, 2019b): graded imperatives "more/less of this!". The pain debate as background; Martínez and reflexive imperativism nearly coincide on pain (fn. 2 on Klein 2015 and other views). World-directed imperativism rejected: action urges are distinct from valence. High stakes: experience-directed imperativism + valence-based decision-making = motivational hedonism. Naturalist methodology.

**§2 The Science of Affect (ms. pp. 3–6).** Homeostatic property cluster. Appraisal (world, body, generalised); arousal; automatic motor plans independent of valence (common cause); valence's three roles (prospective decision-making, evaluative learning via prediction error, salience/attention; valence can be unconscious); top-down modulation of valence (placebo, wine, parachute).

**§3 Imperativism: An Initial Look (ms. pp. 6–10).** Reflexive imperativism as the target. Direct vs. indirect motivation — no strong advantage. Meta-representational commitment (snails) — softened by pure indexical reference and non-conceptual metacognition. Imperativism must be expanded to a pushmi-pullyu view: appraisals track primary and secondary reinforcers/punishers (Garcia effect), valence carries information about adaptive value, and teleosemantic/informational theories (Shea 2018; Rupert 2018) then assign it value content; consumers form value judgements. Burden on imperativists; they have argued only negatively.

**§4 Imperativism and the Science of Valence (ms. pp. 10–14).** Evaluative learning (imperativist retelling possible but unnecessary). Neuroeconomic decision models are value-based; affective-forecasting language is a hedonist gloss. Localisation: valence networks (striatum/amygdala/insula/orbitofrontal) vs. motor and goal networks. Salience: mind-wandering handled; gruesome accident not handled. Summary: three difficulties; evaluativism's synergistic fit. fn. 9: urges exist but are distinct from valence.

**§5 Replies to Objections (ms. pp. 14–17).** Introspection non-discriminating (fn. 10 numerosity analogy). Pure moods (higher-order appraisal; listless body). Ploner case misquoted (fn. 11). General and saint. Pleasant/unpleasant desires. Trainee doctor vs. expert. Dentist. Experiential imagination in prospection. Liking/wanting dissociations.

**§6 Conclusion (ms. p. 17).** Imperativism unnecessary and in conflict with neuroscience; evaluativism consistent with it.

---

## 6. Cross-Paper Map of the Debate

**Who is answering whom.** The exchange is not a clean five-step chain:

- **Klein 2007** founds imperativism about *pain*, with commands aimed at bodily action. Its foils are representationalism about pain and dual-aspect theories.
- **Carruthers 2018** does not mention imperativism. It argues for evaluativism against the *hedonic* (intrinsic-feel) account.
- **Barlassina & Hayward 2019** attack Martínez's first-order imperativism and Klein's *2015* higher-order imperativism, not Klein 2007 directly. They give first-order evaluativism one paragraph (§4.3). Their §7.2 does answer a Klein-2007-style objection: that ankle pain's function is "don't put weight on it".
- **Barlassina 2020** is the first paper to take on Carruthers 2018 directly.
- **Carruthers 2023** replies to Barlassina 2020, to the *Mind* paper, and to a Barlassina & Hayward paper not in this corpus ("Loopy Regulations", 2019).

Columns group each side's papers. "—" means the paper does not address the question.

| Question | Klein 2007 (body-directed imperativism) | Carruthers 2018 / 2023 (evaluativism) | Barlassina & Hayward 2019 / Barlassina 2020 (reflexive imperativism) |
|---|---|---|---|
| **What is valence / unpleasantness?** | Pain's felt character is exhausted by a *negative imperative* against certain uses of the body; intensity is the imperative's strength ([§1](#1-klein-2007--an-imperative-theory-of-pain)). Primary affect is the imperative; secondary affect (fear, worry) is an evoked reaction | 2018: a fine-grained non-conceptual representation of the goodness/badness of the object of experience. 2023: an analogue-magnitude representation of **adaptive** value/disvalue; positive and negative on partly separate scales ([§2](#2-carruthers-2018--valence-and-value), [§5](#5-carruthers-2023--on-valence-imperative-or-representation-of-value)) | An experience is (un)pleasant in virtue of a constituent Command "More/Less of me!". 2019: the referent is the experience itself (token); 2020: the experience **type** ([§3](#3-barlassina--hayward-2019--more-of-me-less-of-me-reflexive-imperativism-about-affective-phenomenal-character), [§4](#4-barlassina-2020--beyond-good-and-bad-reflexive-imperativism-not-evaluativism-explains-valence)) |
| **Grammatical mood of the content** | imperative | indicative (evaluative), non-conceptual | imperative (compound with an indicative sensory part: `U = F ∧ K⁻`) |
| **World/body-directed or experience-directed?** | directed at the subject's *bodily actions* ("It hurts when I A") | world/body-directed; for pain and orgasm the object is the represented *bodily sensation* (2018, p. 665) | experience-directed ("same-order"); world-directed contents may co-occur but do not fix valence |
| **Scope** | pain only (itch, hunger, thirst as related imperative sensations; emotional pain left open) | all affect: pains, pleasures, emotions, desires, moods | all affect |
| **How valence motivates** | directly: a proscription constrains action planning; it can be overridden (hot casserole) | 2018: intrinsically motivating (pursue what seems good). 2023: motivation largely *indirect*, via decision → intention and via attention; action urges are caused by appraisal separately from valence | intrinsically and *reflexively*: it motivates for or against the very experience, leaving the means open (painkiller, dentist, change of gait) |
| **Role in imagination-based / prospective decisions** | — | the imagined *worldly* outcome is represented as good/bad; valence is the common currency/scale; neuroeconomic value models; forecasting talk of "experiences" is a hedonist gloss (2023) | the imagined *experience* (tasting pizza) carries "More of me!"; supported by default-network use, ventromedial prefrontal involvement, and projection bias (2020 §5) |
| **Role in learning** | — | 2018 fn.: teaching signal; 2023: prediction-error update of stored values, fully describable without imperatives | 2019 §7.2: the *evolutionary function* of affect is a reward/punishment system for trial-and-error learning in complex creatures |
| **Motivational hedonism?** | — | 2018: hedonism is refuted by self-sacrifice and by the input/output mismatch. 2023: experience-directed imperativism *entails* motivational hedonism | 2019: "a very self-centred character indeed". 2020: accepts experience-directed choice; handles self-sacrifice via identity fusion with the group |
| **Pain asymbolia / "pain that doesn't hurt"** | not discussed by name; warns against over-reading "pain that does not hurt" reports | 2018: valence removed, sensation kept (morphine, cingulotomy); asymbolic "Mary" thought experiment shows valence is phenomenally conscious | 2019: asymbolia = sensory Indicator `F` without `K⁻` (half of a double dissociation); asymbolic pain is not an affective experience (fn. 3) |
| **Morphine / lobotomy / analgesia** | morphine pain still carries the full imperative but, with no intended action, it has nothing to forbid ("stop sign in a ghost town"); lobotomised patients still avoid loading broken ankles | 2018: morphine and cingulotomy remove the valence component. 2023: *the dentist* is conceptual recognition of damage, not valence | 2020 *The dentist*: anaesthesia blocks the reflexive Command, so seeing a damaged mouth is valence-neutral |
| **Unpleasant (and pleasant) desires** | — | 2023: desires represent their objects as good; the *situation* (the object will not be obtained) is appraised as bad (frustration) | 2020 *The cake* vs. the guitarist: valence is independent of the desire's first-order content. §6.1: drinking satisfies both "Drink!" and "Less of me!"; valence adds motivational force |
| **Objectless moods / pure affect** | — | 2018: the world seems flat, or the listless body is represented as bad. 2023: higher-order appraisal — "the fact that nothing seems good seems bad"; the Ploner patient still felt something bad in a vague body region | 2019: misery sinks first-order views; Ploner's patient = `K⁻` alone. 2020 *Bonjour tristesse*: pure "Get less of me!" = pure misery |
| **Valence dissociated from evaluation** | — | 2023: the saint's pride is appraised as betrayal (a second, larger negative appraisal); trainee doctor vs. expert conflates conceptual and non-conceptual badness | 2020 *General Bouba and Saint Kiki*: same evaluation, opposite valence; evaluativism predicts ambivalence she does not feel |
| **Main neural / scientific evidence** | premotor and anterior cingulate activation by pain; congenital insensitivity to pain | 2018: shared valuation network, placebo, affective priming. 2023: valence in striatum/amygdala/insula/orbitofrontal value networks, separate from motor and goal networks; gruesome-accident attention | 2019: Ploner et al. 1999 lesion case; hedonic homogeneity. 2020: default network, ventromedial prefrontal cortex, projection bias, identity fusion |
| **Evolutionary rationale** | information invites context-dependent responses; a command is better when one response (stop) is right | 2018: "evolution couldn't care less about how one feels" — world-in/world-out architecture. 2023: valence tracks adaptive value (teleosemantics) | 2019: complex creatures cannot be pre-programmed, so affect guides learning. 2020: evolution is a tinkerer building on episodic (experience-simulating) future thought |
| **Meta-representation demand** | none (content about bodily action) | 2018: used *against* the hedonic account (animals, infants). 2023: raised against reflexive imperativism, then softened (pure indexical; non-conceptual metacognition) | 2019 fn. 16: infants' mindreading shows reflexive content is not too demanding |

**Direct reply ledger (Barlassina 2020 → Carruthers 2023).**

| Barlassina 2020 argument | Answered in Carruthers 2023? | How |
|---|---|---|
| *The cake* (unpleasant desire) + guitarist | Yes (ms. p. 16) | frustration appraisal directed at the situation; expected satisfaction appraised as good |
| *General Bouba and Saint Kiki* | Yes (ms. p. 15) | second, large-magnitude negative appraisal of one's own pride; the ambivalence rejoinder is not addressed |
| *The dentist* | Yes (ms. p. 16) | seeing damage = conceptual recognition, or non-conceptual representation of something that *implies* damage; not valence |
| *Bonjour tristesse* (objectless misery) | Indirectly (ms. pp. 14–15), under "pure mood states" attributed to B&H 2019a; Jean-Paul is not named | depression is world-focused ("Meh!") plus a higher-order appraisal that nothing seems good; challenge to produce an unaccommodated case |
| Experiential imagination as input to forecasting (§5.1–5.2) | Yes (ms. pp. 11, 16) | imagery's *contents* are appraised, not the experiences; experiential talk in forecasting research is a hedonist gloss |
| Projection bias as evidence of re-use | No | — |
| Self-sacrifice via identity fusion (§5.3) | No | — (2023 instead re-asserts that experience-directed imperativism entails motivational hedonism) |
| Evolution as tinkerer (§5.3) | No | — (2023 replaces the "couldn't care less" argument with the teleosemantic argument) |
| Unpleasant desires and exclusion (§6.1); "not on the menu" (§6.2) | No | — |

**Strongest objection each side faces (reviewer's judgement, grounded in the corpus).**
- *Against Klein-style body-directed imperativism*: it cannot handle affect without a proscribable action (headache and visceral pain, which Klein flags himself; objectless misery), and it gives no principled account of positive/negative polarity outside pain (B&H 2019 §4.2).
- *Against reflexive imperativism*: Carruthers 2023's burden-shifting argument. Valence reliably carries information about adaptive value, so on standard theories of content it *represents* value, and nothing in learning, choice or neuroscience needs a further imperative. Add the attention asymmetry (we stare at horrible scenes) and the charge that the view entails motivational hedonism.
- *Against evaluativism*: dissociations between valence and evaluation — the saint whose pride evaluates her deeds as good but feels only bad; objectless misery — which evaluativism handles only with extra, case-by-case higher-order appraisals, sacrificing the unification it claims (Barlassina 2020 §4). Also the unanswered question of why people take painkillers rather than only tending the damage (B&H 2019 §4.2.4, §4.3).

---

## 7. Relevance to This Project (interpretive)

> **Status: interpretive, not a finding.** The papers are about what makes *conscious experiences* feel good or bad. Nothing here shows that an artificial agent has valence. For the agent, the internal damage signal is called **nociception**; "pain" is the thing the project is trying to explain and is never used for the agent's signal. Concrete experiment ideas are not proposed here. They should go to **`research-postdoc`** (triage) and **`professor-pain-modeling`** (whether the constructs are valid enough to support "pain-like" claims), with `professor-rl` for the reinforcement-learning mapping.

This project trains reinforcement-learning agents in a grid world with an internal damage (nociception) signal, and studies behaviour that looks pain-like, such as hypervigilance after injury. Each theory in the corpus implies a different answer to the question *what would the agent's signal have to do to count as valence?* Read functionally:

- **Klein 2007 (body-directed imperativism).** Valence-like nociception would be a signal whose job is to **forbid particular uses of the body**.
  - Its strength grows while the forbidden action continues and fades as the agent backs off.
  - It is tied to *actions* ("it hurts when I move this way") more than to a location or damage level.
  - It can outlast the damage: Klein cites pain that persists after healing and is linked to the risk of re-injury.
  - An agent with no current plan would show no behavioural sign of it ("stop sign in a ghost town").
  - What it takes: a clear link from the signal to action-specific restriction. A number merely standing for how much damage there is would not be enough.
- **Reflexive imperativism (Barlassina & Hayward).** It would be a signal whose job is to **reduce itself** — "less of this state!" — while leaving *how* to the learner.
  - The authors' own evolutionary story (2019 §7.2) is trial-and-error learning under reward and punishment, which is why the view is easy to map onto RL. The nearest analogue is a cost the agent learns to minimise that is defined on its *own internal signal*, not on the external damage.
  - A signature would be that, when the signal can be lowered without repairing the damage (an analogue of the painkiller), the agent is still pulled toward doing so.
  - A caution: in an engineered agent, the "function" that teleosemantics appeals to is whatever the designer chose to reward. So a self-reducing signal may meet the letter of the theory without showing anything about valence.
- **Evaluativism (Carruthers).** It would be a **learned, graded estimate of how good or bad the current or imagined state of the world or body is**, in the sense of survival-relevant value.
  - Its roles: feeding choice (compared on a common scale), driving prediction-error learning of stored values, and grabbing attention — including attention *toward* bad things.
  - The obvious RL analogue is a value estimate, such as a learned critic, over body and world states, where states that predict damage acquire negative value by learning ("secondary punishers"). Hypervigilance after injury would then be a learned re-valuation of those states.
  - Carruthers 2023 also separates valence from direct, appraisal-caused action tendencies, which would correspond to hard-wired or reflex action biases.

The corpus also warns against a shortcut. Carruthers 2023 argues that the same learning and decision machinery can be *described* either as updating values or as updating commands (ms. p. 10). A standard actor-critic agent does not by itself favour one theory. The theories only come apart on the dissociations the papers argue over:

- signal without valence (asymbolia-like);
- valence without an object (objectless misery);
- lowering the signal instead of the damage (painkillers);
- whether strongly negative states attract or repel attention.

Whether any of these can be operationalised in this project, and what such a result would or would not license about "pain-like" states, is a construct-validity question for `professor-pain-modeling` and a triage question for `research-postdoc`. It is not settled here.

---

## Not in this corpus

Relevant but **not reviewed** (not read by this reviewer; do not cite this document for their content):

- **Bain, D. (2013). "What makes pains unpleasant?"** *Philosophical Studies* 166: 69–89. An evaluativist critique of imperativism about pain, arguing that imperatives cannot supply pain's reason-giving force. The PDF could not be retrieved because the site served a bot check.
- **Martínez, M. & Klein, C. (2016). "Pain signals are predominantly imperative."** *Biology & Philosophy*.
- Also cited within the corpus but not reviewed: Klein (2015) *What the Body Commands* (MIT Press), whose reading is disputed between B&H 2019 and Carruthers 2023; Barlassina & Hayward (2019) "Loopy Regulations" (*Philosophical Topics* 47), the source of several objections Carruthers 2023 answers; Martínez (2011, 2015a, 2015b); Bain (2019) "Why take painkillers?" (*Noûs*); Cochrane (2019); Cutter & Tye (2011, 2014).
