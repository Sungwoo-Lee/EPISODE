# AI Consciousness — Part A3: Biology and Feeling

**Topic folder:** `docs/project/references/ai_consciousness/`
**Part of:** a multi-file, deliberately neutral review of the field of *consciousness in artificial intelligence*. Each part is written by a different reviewer; a later synthesis page organises the arguments. This part does not take sides.
**This part:** 2 papers, both read in full, reviewed 2026-10-07.
**Reviewer:** literature-reviewer (batch A3)

## What this part covers (plain-language entry point)

**The question.** Does it matter that the only things we know to be conscious are living bodies with brains? Or is the body just a container, so that the right program could be conscious on any hardware?

**The two papers.** Both are written by neuroscientists, and both say that biology contributes something real.

- **Aru, Larkum and Shine (2023)** ask whether today's large language models (LLMs — text-predicting programs such as chatbots) are conscious. They answer: very unlikely. LLMs receive only text, not a living sensory world. They lack the brain circuits that most theories link to consciousness. And consciousness may depend on the many-layered self-maintenance of living things, which software leaves out. The authors still do not say that software can never be conscious.
- **Damasio and Damasio (2022)** do not discuss machines at all. They propose that consciousness starts with *homeostatic feelings* — felt states such as hunger, pain and well-being that report how the body's self-regulation is going. On their account these feelings need a nervous system that is physically intertwined with the body's organs and chemistry.

**Why it matters.** Together the papers show two different ideas of what biology adds: specific brain mechanisms and living organisation (Aru et al.), and a body-and-nervous-system partnership that produces feeling (the Damasios).

---

## Table of Contents

- [What this part covers](#what-this-part-covers-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Aru, Larkum & Shine (2023) — The feasibility of artificial consciousness through the lens of neuroscience [tier: full]](#1-aru-larkum--shine-2023--the-feasibility-of-artificial-consciousness-through-the-lens-of-neuroscience-tier-full)
  - [Phase 1](#phase-1-plain-overview) · [Phase 2](#phase-2-the-argument-step-by-step) · [Published version versus preprint](#published-version-versus-the-preprint-reviewed-in-the-sibling-topic) · [Backbone](#section-by-section-backbone)
- [2. Damasio & Damasio (2022) — Homeostatic feelings and the biology of consciousness [tier: full]](#2-damasio--damasio-2022--homeostatic-feelings-and-the-biology-of-consciousness-tier-full)
  - [Phase 1](#phase-1-plain-overview-1) · [Phase 2](#phase-2-the-argument-step-by-step-1) · [What the paper says a system needs for feeling](#what-the-paper-says-a-system-needs-for-feeling) · [Backbone](#section-by-section-backbone-1)
- [Cross-paper notes](#cross-paper-notes)

---

## Reading conventions

- **Page numbers.** "(p. N)" is the page's position in the PDF file (p. 1 = first page of the file), as the shared brief requires. Both PDFs are published versions, so the printed journal page is also given where useful: for Aru et al., journal page = 1007 + N (PDF p. 1 = p. 1008); for the Damasios, journal page = 2230 + N (PDF p. 1 = p. 2231).
- **Quotes are verbatim**, with three mechanical normalisations, stated here so no one mistakes them for edits: (1) the PDF uses typographic ligatures (the single character "ﬁ"), written here as the two letters "fi"; (2) words broken by a hyphen at a line end are joined ("con-sciousness" → "consciousness"); (3) where the text extractor dropped a space between two words (it did so in a few lines of the Damasio PDF, e.g. "mapof"), the space visible in the rendered page is restored. Single curly quotation marks (‘ ’) are kept as printed. Typos in the source are kept and marked *(sic)*.
- **Reviewer's notes** are clearly labelled. Everything outside them is the authors' claim.
- **Project vocabulary.** This project's own artificial agents receive a damage signal called *nociception*. This document does not call it "pain". When the word "pain" appears below, it is the authors' word for a human or animal feeling.
- **Sibling topic.** `docs/project/references/computational_functionalism/computational_functionalism_lit_review_C_biological_naturalism.md` ("Part C" below) reviews the Aru et al. preprint (its §4) and the wider biological-naturalism debate. This file cross-references it and does not repeat it.

---

## 1. Aru, Larkum & Shine (2023) — The feasibility of artificial consciousness through the lens of neuroscience [tier: full]

**PDF:** `docs/project/references/ai_consciousness/sources/Aru et al. 2023 - The feasibility of artificial consciousness through the lens of neuroscience.pdf` — **published version** (version of record), *Trends in Neurosciences* 46(12): 1008–1017, December 2023, article type "Opinion", DOI 10.1016/j.tins.2023.09.009. 10 PDF pages: text on pp. 1–9, references on pp. 9–10.

### Phase 1: Plain overview

**The question.** Chatbots built on large language models write fluent, thoughtful-sounding text. That makes many people wonder whether they are conscious, or soon will be. Three neuroscientists — Jaan Aru (computer science, Tartu), Matthew Larkum (biology, Berlin) and James Shine (brain and mind, Sydney) — ask what neuroscience says about this. Their abstract states the short answer: "From the perspective of neuroscience, this position is difficult to defend." (p. 1).

**The three arguments.** First, the *umwelt* argument. "Umwelt" (German for "surroundings") is the slice of the world an animal can perceive. An LLM's umwelt is only coded text, which "does not itself make any robust contact with the world as it is" (p. 3). Second, the architecture argument. Most theories of consciousness give a central place to loops between the cortex and the thalamus (a relay hub deep in the brain) and to arousal systems in the brainstem. LLMs have none of these. Third, the biological-organisation argument. Living things maintain themselves at many levels at once, from molecules to organs. Software leaves those levels out, and consciousness may not survive being separated from them.

**The verdict and its limits.** The authors conclude that "LLMs are not conscious and will likely not be conscious soon." (p. 8). But they do not say that only brains can be conscious, and they write that they are "not necessarily subscribing to the claim that consciousness cannot be captured within software at all" (p. 8). Their stated position is that consciousness "might be implementable in principle", but might need far more biological detail than current AI has (p. 6).

**Why it matters.** The paper moves the debate away from "does the chatbot sound conscious?" towards "what does the brain actually do that might matter?" It is also a frequent source of the phrase "skin in the game": a living system has something to lose, and a program that is shut down does not (Box 1, p. 8).

### Phase 2: The argument, step by step

**Narrowing the question.**
- Conversation with an LLM is not a test of consciousness: "Although these conversations are remarkable, they are not formal objective measures of consciousness and constitute only prima facie evidence for conscious agency." (p. 3). ("Prima facie evidence" means evidence at first sight, which can be overturned.)
- The target is *phenomenal* consciousness — what an experience is like from the inside: "we focus mainly on phenomenal consciousness and ask whether machines can experience the world phenomenally." (p. 3). They distinguish *levels* of consciousness (awake, asleep, in a coma; the neurologist's sense) from *contents* (what one is conscious of; the psychologist's sense).
- Why look at brains at all? Because "we can currently be absolutely sure of only a version of consciousness that arises from brains embedded within complex bodies" (p. 2).

**Argument 1 — the umwelt of an LLM (pp. 3–4).**
1. Every animal's umwelt is set by its body. Humans see light of about 380–740 nm and hear 20–20 000 Hz; honeybees see ultraviolet; some snakes sense infrared. Psychologist James Gibson called the action-relevant part of this information *affordances* (what the world offers an animal to do).
2. An LLM receives only "binary-coded patterns" (p. 3). "Text and speech coded into strings of letters are simply no match for the dynamic complexity of the natural world" (p. 3).
3. Comparison with Nagel's bat (the classic example of an alien point of view): "While there is no definite way to quantify this difference, we highlight that the informational input accessible to LLMs is likely to exhibit a more significant disparity." (p. 3).
4. Objection granted: "there is no conceptual barrier stopping the input of future AI systems from being much more enriched" (p. 4).
5. Reply: the umwelt is not set by input alone. In a flotation tank, with almost no sensory input, "consciousness persists" (p. 4). So "having an umwelt presupposes an inherent subjective perspective, that is, an agent to begin with" (p. 4), and affordances depend on the agent's "motivations and goals" (p. 4).
6. Conclusion: "simply adding massive data streams to future AI systems will not, by itself, lead to consciousness." (p. 4).
7. Lesson for consciousness science: "one will have to re-evaluate the necessity of more basic self- and agency-related processes for the emergence of consciousness, as posited by some of the theories of consciousness" (p. 4). The theories cited here [42–46] are Damasio & Damasio 2022 (paper 2 of this file), a second Damasio & Damasio 2022 paper, Damasio 2021, Panksepp 2005 and Solms 2021.

**Argument 2 — the architecture of conscious integration (pp. 4–6).**
1. Many theories hold that consciousness depends on the dense, re-entrant (looping back on itself) *thalamocortical* network: cortical areas, cortex-to-cortex connections, and higher-order thalamic nuclei that project widely to cortex. This network is said to support *conscious integration* — "the fact that consciousness feels unified despite arising from processes happening in different brain areas" (p. 4).
2. Theories differ on how integration happens:
   - *Global neuronal workspace theory* (GNWT): a frontal–parietal "workspace" collects information and broadcasts it to the whole brain; broadcast marks what is conscious.
   - *Binding-by-synchrony*: integration through fast, synchronised oscillations between cortical areas.
   - *Dendritic integration theory* (DIT, the authors' own theory): integration also happens inside single **layer 5 pyramidal neurons** (large excitatory cells in the fifth layer of cortex). These cells have two input zones: the *basal* dendrites carry "externally-grounded information" and the *apical* dendrites carry "internally-generated information" (p. 4). In conscious states the two zones are coupled. Figure 2 adds that the cell fires bursts when both kinds of input coincide, especially with gating input from "higher-order, matrix-type thalamus" (p. 5).
3. Present-day AI has none of this: "there is no equivalent of dual-compartment pyramidal neurons, nor a centralized thalamic architecture, a global workspace, or the many arms of the ascending arousal system." (p. 5).
4. Hedge: "Although we are not arguing that the mammalian brain is the only architecture capable of supporting conscious awareness" (p. 5), the evidence suggests "very specific architectural principles" matter, and current AI is "extremely simple in comparison" (p. 5).
5. What each theory implies for future AI (pp. 5–6):
   - GNWT: global broadcast can be built, so "an artificial system with a computationally equivalent global workspace would include a core ingredient underlying consciousness according to this theory" (p. 5).
   - *Integrated information theory* (IIT; consciousness is a system's integrated cause–effect structure): software on a typical computer cannot be conscious "because modern computers do not have the appropriate architecture to realise the cause-effect power necessary for sufficiently integrating information" (p. 6).
   - The authors' "third possibility": "consciousness might be implementable in principle, but it might require a level of computational specificity that is beyond the present-day (and perhaps future) AI systems." (p. 6).

**Argument 3 — consciousness as a complex biological process (pp. 6–8).**
1. Structure is not enough: "the structure of the thalamocortical system does not change when we are in deep sleep or undergo anesthesia, yet consciousness disappears." (p. 6). Local sensory responses can also persist in deep sleep.
2. DIT's candidate process: many anaesthetics *decouple* the apical and basal zones of layer 5 neurons, while the neurons stay intact and still fire. "This dendritic coupling was demonstrated to be controlled by metabotropic receptors, which are often overlooked in computational models and in artificial neural networks." (p. 6). (*Metabotropic receptors* act through slower chemical cascades inside the cell rather than by opening an ion channel directly.) Higher-order thalamus may control them.
3. Even this may be too coarse. Current concepts may "miss the necessary computational details", and "perhaps we simply do not yet have the right mathematical and experimental tools to understand consciousness." (p. 6). Figure 3 draws this as overlapping ellipses: all possible computations; the "normative" computations we can currently formalise; biological computations; AI computations. Its caption concludes: "there is little a priori reason to assume, we would argue, that the computations of present-day AI systems are related to computations underlying phenomenal consciousness." (p. 7).
4. Living organisms maintain themselves "across several levels of processing" and their existence depends on their actions — "they have ‘skin in the game’" (pp. 6–7). This cross-level organisation "is not captured within present-day computer software", so "as long as AI is based on software, AI might be poorly placed to recapitulate conscious experience and agency." (p. 7).
5. The cellular level too: "A biological neuron is not just an abstract entity that can be fully captured with a few lines of code." (p. 7). The Krebs cycle (the chain of chemical reactions that powers cell respiration) is not "compressible" into software, because it needs real molecules. Disclaimer: "To be clear, our aim is not to suggest that consciousness requires the Krebs cycle" (p. 7); the point is that understanding consciousness may face similar problems: "perhaps it cannot be abstracted away from the underlying machinery" (p. 7).
6. The anti-software claim is disowned once more (p. 8, quoted above), and replaced by a claim about what must be *entertained*: consciousness may be linked to the biological organisation of life, so adequate computational descriptions "may be much more complex than our present-day theories suggest" (p. 8). "It might be impossible to ‘biopsy’ consciousness and remove it from its organizational dwellings." (p. 8). This contradicts "many current theories", which assume consciousness can be captured at an abstract computational level; the authors cite Seth & Bayne 2022 and Butlin et al. 2023 here [47, 88].
7. Conditional conclusion: AI may copy brains at the network level while abstracting away "all the other levels of processing that causally contribute to consciousness", and so "possibly" consciousness itself. Hence "LLMs and future AI systems may be trapped in a compelling simulation of the signatures of consciousness, but without any conscious experience to speak of." (p. 8).

**Box 1 — "skin in the game" and moral worry (p. 8).**
- The opposing view is stated first: some (Metzinger 2021 is cited) argue that if an AI could have negative experiences, it could suffer, so caution is due.
- The authors' claim: "We claim that LLMs do not (and will not) have experiences that can be considered suffering in any sense that should matter to human society." (p. 8).
- The phrase comes from Taleb: those with a personal stake judge better. An LLM can say it does not want to be shut down, but "an LLM does not have ‘skin in the game’, as arguably there is no real consequence to the software when it is actually shut down." (p. 8).
- A living system "has something to lose on several levels": cell, organ, organism (quoting Hans Jonas: "The organism has to keep going, because to be going is its very existence"). "The system has skin in the game across levels of processing, which is arguably prerequisite for caring about agency and consciousness" (p. 8). This sentence cites Man & Damasio 2019 [73] on homeostasis and "feeling machines".
- Last step: "not having the capacity for phenomenal consciousness would preclude suffering and, therefore, personal investment." (p. 8).

**Concluding remarks (pp. 8–9).** The three arguments together make it "extremely unlikely" that current LLMs have phenomenal consciousness. "Rather, they mimic signatures of consciousness that are implicitly embedded within the language that people use to describe the richness of their conscious experience." (p. 9). The paper is "Rather than representing an antithetical account" a source of useful questions: for ethics, "perhaps any worries about potential moral quandaries regarding sentience in LLMs are currently more hypothetical than real" (p. 9); for AI and neuroscience, mutual progress through brain-inspired design.

**Limits the authors state.** They do not claim the mammalian brain is the only possible architecture (p. 5). They do not "necessarily" subscribe to the claim that software cannot be conscious (p. 8). They say current theories and tools may be inadequate (p. 6). Their "Outstanding questions" box (p. 8) lists open problems: whether consciousness can be judged from text alone; how a thalamocortical system or ascending arousal system could be implemented in AI; whether dendrites matter beyond efficiency; whether the organisational complexity of life can be formalised ("New mathematical frameworks are required"); and whether understanding consciousness first requires understanding agency.

> **Reviewer's note.** Part C (§4) noted an ambiguity in Box 1: absence of a stake is used as a reason to deny phenomenal consciousness, while absence of phenomenal consciousness is used to deny suffering. In the published version the added sentence ("skin in the game ... arguably prerequisite for caring about agency and consciousness") makes the stake a stated prerequisite, but the final sentence still runs from no consciousness to no suffering. The text does not say whether these are two independent supports or one circular chain.

> **Reviewer's note.** Argument 1, step 5, rests on one observation (the flotation tank) plus citations. A functionalist could reply that "being an agent with motivations and goals" is itself a functional property that could be built. The paper does not discuss this reply directly; its third argument is the closest it comes.

### Published version versus the preprint reviewed in the sibling topic

Part C §4 reviewed the **author preprint**. This entry reviews the **version of record**. The comparison below is made against the quotations and descriptions in Part C §4, not against a fresh reading of the preprint PDF (the shared brief limits this reviewer to the assigned PDFs). Where Part C quotes a passage and the published text differs, the difference is reported. Where Part C is silent, presence or absence in the preprint is **not** asserted. A later check against the preprint PDF itself is recommended before any of these differences is quoted in the synthesis.

**Format.** The published paper has journal pagination (pp. 1008–1017), a **Highlights** box (p. 1), rendered figures, and an **Outstanding questions** sidebar (p. 8). Part C records "three figures ... present as captions" and Box 1, and does not mention Highlights or Outstanding questions. Page numbers differ throughout: Part C's "PDF p. 1–17" become PDF pp. 1–9 here. Box 1 is placed on p. 8 next to the concluding sections.

**Changes in wording that change the strength of a claim.**

| Topic | Preprint, as quoted in Part C | Published version (this PDF) | Effect |
|---|---|---|---|
| Conversation as evidence | "do not constitute prima facie evidence for conscious agency" (preprint PDF p. 4) | "constitute only prima facie evidence for conscious agency" (p. 3) | **Reversed**: conversation is now weak, defeasible evidence, not no evidence. The published text also adds that LLMs have "demanded a re-evaluation" of inferring consciousness from verbal interaction (p. 3). |
| Bats | "more different from the one presented to humans than ours is from bats" | "While there is no definite way to quantify this difference ... likely to exhibit a more significant disparity" (p. 3) | Softened and hedged. |
| LLM input | "Text and strings of keystrokes on a keyboard" | "Text and speech coded into strings of letters" (p. 3) | Wording broadened to include speech. |
| Flotation tank | "consciousness does not extinguish" | "consciousness persists" (p. 4) | Wording only. |
| More data | "will not lead to consciousness" | "will not, by itself, lead to consciousness" (p. 4) | Softened. |
| Lesson of Argument 1 | "pops out" view must be reconsidered; "Perhaps, to be conscious, the external world must be integrated with the internal needs and processes" (preprint PDF pp. 6–7) | Not found in the published text. Replaced by: re-evaluate "more basic self- and agency-related processes ... as posited by some of the theories of consciousness" (p. 4), citing the Damasios, Panksepp and Solms. | The "internal needs" formulation is gone; the published lesson points to named affect-and-self theories instead. |
| Scope of the architecture claim | "no LLM equivalent"; "we are hesitant to ascribe phenomenal consciousness to present-day LLMs" | "present-day LLMs and other AI systems ... there is no equivalent"; "we are cautious in ascribing phenomenal consciousness to them" (p. 5) | Scope widened from LLMs to AI systems generally. |
| GNWT implication | "ought to be considered conscious by proponents of this theory" | "would include a core ingredient underlying consciousness according to this theory" (p. 5) | Weakened: a core ingredient, not sufficiency. |
| IIT implication | "computer software does not have real cause-effect power" | "modern computers do not have the appropriate architecture to realise the cause-effect power" (p. 6), for "a software-based AI system instantiated on a typical modern computer" | Re-located: the obstacle is now the hardware architecture of typical computers, not software as such. |
| Metabotropic receptors | "not usually modeled in artificial neural networks" | "often overlooked in computational models and in artificial neural networks" (p. 6) | Wording; adds computational models generally. |
| Figure 3 caption | "a priori, there is little reason to think that the computations of present-day AI systems are related to computations underlying consciousness" | "little a priori reason to assume, we would argue, that the computations of present-day AI systems are related to computations underlying phenomenal consciousness" (p. 7) | Marked as the authors' argument; narrowed to *phenomenal* consciousness. Figure labels in the PDF: "All possible computational mechanisms", "Normative", "Biological", "AI systems" (the extractor garbles the "ti" ligature in two labels). |
| Krebs-cycle disclaimer | "perhaps consciousness is similar: it cannot be abstracted away from the underlying machinery" | "understanding consciousness may involve similar challenges in translating from the biological to the artificial realms: perhaps it cannot be abstracted away from the underlying machinery" (p. 7) | Re-framed in terms of *understanding* consciousness. |
| Living-systems hedge | "here we are not arguing that consciousness can only arise in living systems" (preprint PDF p. 12) | **Not found** in the published text (searched the full extraction). | One of the three disclaimers Part C lists is absent. |
| Software hedge | "we are not claiming that consciousness cannot be captured within software at all" | "Importantly, we are not necessarily subscribing to the claim that consciousness cannot be captured within software at all" (p. 8) | Weakened: "not necessarily subscribing" instead of "not claiming". |
| Complexity claim | "any computational description of consciousness will be much more complex" | "computational descriptions that capture the essence of consciousness may be much more complex" (p. 8) | "will" → "may". |
| Status of the assumption | "contradicts most of today's theories" | "contradicts many current theories" and adds that the assumption "might be one that will require updating in light of modern AI systems" (p. 8) | "most" → "many"; a forward-looking sentence added. |
| Abstracted-away conclusion | "Hence, we have abstracted away consciousness itself" | "and, possibly, have therefore abstracted away consciousness itself" (p. 8); adds "If consciousness is indeed related to these other levels ... we might still be far from the possibility of conscious machines" | Softened with "possibly"; conditional sentence added. |
| Final framing | "Rather than representing a deflationary account" | "Rather than representing an antithetical account" (p. 9) | Wording. Published also adds that moral worries about LLM sentience are "currently more hypothetical than real" (p. 9). |
| Box 1 | Included a paragraph on legal penalties: without personal investment, fines and incarceration "would therefore likely destabilize the rule of law" | **Not found** in the published Box 1, which has two paragraphs only (p. 8, checked on the rendered page). | The legal argument is absent. |
| Box 1 wording | "claim in a conversation"; "no real consequence"; "it cannot stop living, as otherwise it will die"; "the cell dies" | "state in a conversation"; "arguably there is no real consequence"; "if it stops living, it will die"; "the cell may die" (p. 8) | Hedged. A sentence is added: skin in the game is "arguably prerequisite for caring about agency and consciousness", citing Man & Damasio 2019. |

**What did not change.** The three arguments and their order; the umwelt examples (380–740 nm, 20–20 000 Hz, bees, snakes); the flotation-tank reply; the DIT account with the anaesthesia decoupling result (Suzuki & Larkum 2020); the mammalian-brain hedge; the third-possibility thesis, word for word ("consciousness might be implementable in principle, but it might require a level of computational specificity that is beyond the present-day (and perhaps future) AI systems", p. 6); the "biopsy" sentence; the headline conclusion "LLMs are not conscious and will likely not be conscious soon" (p. 8); the Jonas quotation.

**Small items.** The abstract's sentence in Part C has a comma ("depends on their actions, and their survival"); the published abstract has none (p. 1). The acknowledgements print "Jakob Howhy" *(sic)* (p. 9); Part C gives "Hohwy". The published reference list includes Butlin et al. 2023 [88], Man & Damasio 2019 [73], Metzinger 2021 [92], and Searle 1992, Penrose 1994 and Gidon et al. 2022 [85–87] as examples of views that software cannot capture consciousness; Part C's "builds on" list does not name these, but this reviewer has not checked whether the preprint cited them.

> **Reviewer's note.** Taken together, the published version is more hedged in its rhetoric (bats, data, GNWT, "possibly", "may") but it has *fewer* explicit disclaimers about biology: the "not only living systems" sentence and the firm "we are not claiming" about software are absent or weakened. Part C's warning that the paper is not a flat denial of machine consciousness still holds for the published text, but citations of the three disclaimers should be checked against the version being cited.

### Section-by-section backbone

1. **Title, abstract and Highlights (p. 1).** LLMs prompt the suggestion of consciousness; three reasons it is "difficult to defend": inputs lack embodied, embedded content; architecture lacks thalamocortical features; evolutionary and developmental trajectories have no parallel in AI. Highlights restate these, add that LLMs and the debate "provide an opportunity to re-examine some core ideas of the science of consciousness" (p. 1).
2. **Large language models and consciousness (pp. 1–2).** The long tradition of asking which animals are conscious; what LLMs are; why their text persuades; the "Turing test" framing and its moral questions; why neuroscientists should respond. Early neural networks imitated cortex, but modern LLMs "do not retain deep homology with the known structure of the brain" (p. 2). **Figure 1** (p. 2): a stack of feed-forward transformer decoder blocks with text in and out, beside a heuristic map of the thalamocortical system with multimodal input and output through brain–body interaction. Preview of the three arguments.
3. **What is consciousness? (pp. 2–3).** Conversation as only prima facie evidence; levels versus contents; phenomenal versus abstract contents; focus on phenomenal consciousness.
4. **The umwelt of an LLM (pp. 3–4).** Human and animal sensory ranges; Gibson's affordances; LLM input as binary-coded text; the bat comparison, hedged; richer inputs granted; the flotation-tank reply; affordances depend on motivations and goals; data alone does not give consciousness; re-evaluate self- and agency-related processes.
5. **The neural architecture supporting conscious integration (pp. 4–6).** Thalamocortical network; conscious integration; GNWT, binding-by-synchrony, DIT. **Figure 2** (p. 5): DIT, with burst firing of thick-tufted layer 5 neurons when basal and apical input coincide under higher-order thalamic gating. AI lacks all named features; the mammalian-brain hedge; what GNWT, IIT and the authors' third possibility imply for AI.
6. **Consciousness as a complex biological process (pp. 6–8).** Sleep and anaesthesia leave structure intact; DIT's decoupling account; metabotropic receptors; current concepts may lack the computational detail; **Figure 3** (p. 7) on the limits of current computational understanding; multi-level self-maintenance and "skin in the game"; software-based AI "poorly placed"; the neuron is not "a few lines of code"; the Krebs-cycle analogy and disclaimer; the weakened software hedge; "biopsy"; the abstracted-away conditional; "compelling simulation of the signatures of consciousness".
7. **Box 1: LLMs and skin in the game: do we have a moral quandary? (p. 8).** The precautionary view; the claim that LLMs will not suffer in a socially relevant sense; Taleb; shutdown; Jonas; nested stakes; skin in the game as prerequisite; no phenomenal consciousness precludes suffering.
8. **Outstanding questions (p. 8).** Five open questions (listed under "Limits the authors state" above).
9. **Concluding remarks (pp. 8–9).** The three arguments restated; "extremely unlikely"; LLMs mimic signatures embedded in human language; moral worries "more hypothetical than real"; optimism about AI–neuroscience collaboration.
10. **Acknowledgements, interests, references (pp. 9–10).** 94 references. No competing interests declared.

**Field record**
- Year · community: 2023 · neuroscience (systems and cellular neuroscience, addressing AI-and-ML)
- Question it asks: Are present-day large language models conscious, or likely to become so soon, judged by what neuroscience knows about consciousness in mammals?
- Position in one line: Very unlikely — LLMs have an impoverished, text-only umwelt, lack the thalamocortical and arousal architecture that theories link to consciousness, and leave out the multi-level self-maintaining organisation of living systems, from which consciousness may not be separable.
- Stance on computational functionalism: restricts — the authors allow that consciousness "might be implementable in principle" but say it may need a computational specificity beyond present (and perhaps future) AI, and they call the abstract-computation assumption one that "might ... require updating".
- Stance on AI consciousness: present-day LLMs "not conscious" and "will likely not be conscious soon"; future AI not ruled out in principle, but possibly "far from" possible if consciousness depends on biological levels of processing.
- What evidence or method it uses: theory review and empirical review (sensory physiology, theories of consciousness, anaesthesia and dendritic physiology), plus conceptual analysis; no new data.
- Debates it takes part in: whether LLM behaviour is evidence of consciousness; which theory of consciousness to apply to AI (GNWT versus IIT versus DIT); embodiment and the umwelt; whether consciousness can be abstracted from biological organisation; AI suffering and moral status.
- Builds on / argues against: builds on von Uexküll, Gibson, Nagel, Larkum's dendritic integration theory (Aru et al. 2020; Suzuki & Larkum 2020), Damasio & Damasio 2022, Man & Damasio 2019, Seth 2021, Thompson, Jonas, Taleb; discusses GNWT (Dehaene, VanRullen & Kanai) and IIT (Tononi, Koch); argues against claims that LLMs are or may soon be conscious (Chalmers 2023 and Agüera y Arcas 2022 are cited in the framing) and against the precautionary view of Metzinger 2021.
- What would show it wrong: not stated as a test. The authors list open questions instead (Outstanding questions, p. 8). Their neurobiological premises are empirical (e.g. that anaesthetics decouple layer 5 dendritic compartments while neurons keep firing).
- Quotes used:
  - "From the perspective of neuroscience, this position is difficult to defend." (p. 1)
  - "The existence of living organisms depends on their actions and their survival is intricately linked to multi-level cellular, inter-cellular, and organismal processes culminating in agency and consciousness." (p. 1)
  - "we can currently be absolutely sure of only a version of consciousness that arises from brains embedded within complex bodies" (p. 2)
  - "do not retain deep homology with the known structure of the brain" (p. 2)
  - "Although these conversations are remarkable, they are not formal objective measures of consciousness and constitute only prima facie evidence for conscious agency." (p. 3)
  - "we focus mainly on phenomenal consciousness and ask whether machines can experience the world phenomenally." (p. 3)
  - "binary-coded patterns" (p. 3)
  - "Text and speech coded into strings of letters are simply no match for the dynamic complexity of the natural world" (p. 3)
  - "does not itself make any robust contact with the world as it is" (p. 3)
  - "While there is no definite way to quantify this difference, we highlight that the informational input accessible to LLMs is likely to exhibit a more significant disparity." (p. 3)
  - "there is no conceptual barrier stopping the input of future AI systems from being much more enriched" (p. 4)
  - "consciousness persists" (p. 4)
  - "having an umwelt presupposes an inherent subjective perspective, that is, an agent to begin with" (p. 4)
  - "motivations and goals" (p. 4)
  - "simply adding massive data streams to future AI systems will not, by itself, lead to consciousness." (p. 4)
  - "one will have to re-evaluate the necessity of more basic self- and agency-related processes for the emergence of consciousness, as posited by some of the theories of consciousness" (p. 4)
  - "the fact that consciousness feels unified despite arising from processes happening in different brain areas" (p. 4)
  - "externally-grounded information" (p. 4)
  - "internally-generated information" (p. 4)
  - "higher-order, matrix-type thalamus" (p. 5)
  - "there is no equivalent of dual-compartment pyramidal neurons, nor a centralized thalamic architecture, a global workspace, or the many arms of the ascending arousal system." (p. 5)
  - "Although we are not arguing that the mammalian brain is the only architecture capable of supporting conscious awareness" (p. 5)
  - "very specific architectural principles" (p. 5)
  - "extremely simple in comparison" (p. 5)
  - "we are cautious in ascribing phenomenal consciousness to them" (p. 5)
  - "an artificial system with a computationally equivalent global workspace would include a core ingredient underlying consciousness according to this theory" (p. 5)
  - "because modern computers do not have the appropriate architecture to realise the cause-effect power necessary for sufficiently integrating information" (p. 6)
  - "consciousness might be implementable in principle, but it might require a level of computational specificity that is beyond the present-day (and perhaps future) AI systems." (p. 6)
  - "the structure of the thalamocortical system does not change when we are in deep sleep or undergo anesthesia, yet consciousness disappears." (p. 6)
  - "This dendritic coupling was demonstrated to be controlled by metabotropic receptors, which are often overlooked in computational models and in artificial neural networks." (p. 6)
  - "miss the necessary computational details" (p. 6)
  - "perhaps we simply do not yet have the right mathematical and experimental tools to understand consciousness." (p. 6)
  - "across several levels of processing" (p. 6)
  - "there is little a priori reason to assume, we would argue, that the computations of present-day AI systems are related to computations underlying phenomenal consciousness." (p. 7)
  - "is not captured within present-day computer software" (p. 7)
  - "as long as AI is based on software, AI might be poorly placed to recapitulate conscious experience and agency." (p. 7)
  - "A biological neuron is not just an abstract entity that can be fully captured with a few lines of code." (p. 7)
  - "To be clear, our aim is not to suggest that consciousness requires the Krebs cycle" (p. 7)
  - "perhaps it cannot be abstracted away from the underlying machinery" (p. 7)
  - "understanding consciousness may involve similar challenges in translating from the biological to the artificial realms" (p. 7)
  - "We claim that LLMs do not (and will not) have experiences that can be considered suffering in any sense that should matter to human society." (p. 8)
  - "an LLM does not have ‘skin in the game’, as arguably there is no real consequence to the software when it is actually shut down." (p. 8)
  - "The organism has to keep going, because to be going is its very existence" (p. 8)
  - "The system has skin in the game across levels of processing, which is arguably prerequisite for caring about agency and consciousness" (p. 8)
  - "not having the capacity for phenomenal consciousness would preclude suffering and, therefore, personal investment." (p. 8)
  - "Importantly, we are not necessarily subscribing to the claim that consciousness cannot be captured within software at all" (p. 8)
  - "may be much more complex than our present-day theories suggest" (p. 8)
  - "It might be impossible to ‘biopsy’ consciousness and remove it from its organizational dwellings." (p. 8)
  - "might be one that will require updating in light of modern AI systems" (p. 8)
  - "all the other levels of processing that causally contribute to consciousness" (p. 8)
  - "LLMs and future AI systems may be trapped in a compelling simulation of the signatures of consciousness, but without any conscious experience to speak of." (p. 8)
  - "LLMs are not conscious and will likely not be conscious soon." (p. 8)
  - "New mathematical frameworks are required" (p. 8)
  - "Rather, they mimic signatures of consciousness that are implicitly embedded within the language that people use to describe the richness of their conscious experience." (p. 9)
  - "perhaps any worries about potential moral quandaries regarding sentience in LLMs are currently more hypothetical than real" (p. 9)

---

## 2. Damasio & Damasio (2022) — Homeostatic feelings and the biology of consciousness [tier: full]

**PDF:** `docs/project/references/ai_consciousness/sources/Damasio and Damasio 2022 - Homeostatic feelings and the biology of consciousness.pdf` — **published version**, *Brain* 145(7): 2231–2235, article type "Essay", DOI 10.1093/brain/awac194; received 9 May 2022, accepted 12 May 2022, advance access 30 May 2022. 5 PDF pages: text on pp. 1–4, references on p. 5.

### Phase 1: Plain overview

**The question.** What is consciousness, and how does a living body produce it? Antonio and Hanna Damasio, neurologists at the University of Southern California, offer what the journal calls "a new theory of consciousness" (standfirst, p. 1). The essay never mentions computers, machines or artificial intelligence. It is in this AI corpus because it states, in short form, a biological account that AI debates often cite — Aru et al. (paper 1) cite it directly.

**The definition.** For the Damasios, consciousness is not attention and not the integration of information. It is *ownership*: the contents of the mind are felt as belonging to one's own body. "Consciousness occurs when mind contents, such as perceptions and thoughts, are ‘spontaneously identified as belonging to a specific organism/owner’." (p. 1).

**The proposal.** What supplies this sense of ownership is a continuous flow of *homeostatic feelings*. *Homeostasis* is the body's work of keeping its internal state (temperature, energy, chemistry) within a range that keeps it alive. Homeostatic feelings are how that work feels: hunger, thirst, pain, malaise, well-being, and a quiet background "feeling of existence". The authors claim that such feelings are conscious by their very nature, and that they "lend" consciousness to everything else we perceive. They also propose how feelings arise: from a two-way, physical interaction between parts of the nervous system that sense the body's interior (*interoception*) and the body's organs and circulating chemicals.

**Why it matters.** The essay ties consciousness to life regulation, to the body as well as the brain, and to a particular kind of neural tissue. It ends with a strong claim: consciousness "cannot be found in inanimate objects, regardless of how complex they may be" (p. 4), and it "does not depend on the nervous system alone" (p. 4).

### Phase 2: The argument, step by step

**Step 0 — diagnosis of the field (p. 1).** Neuroscience has explained memory, emotion, language and attention, but not consciousness. Some conclude it cannot be solved within biology (Chalmers 1995 is cited) or must be solved in physics (Goff 2019). The authors blame unclear definitions: many proposed solutions focus "on mechanisms underlying other complex processes, such as attention and integration of information" (p. 1; Dehaene 2014, Tononi et al. 2016 and Graziano 2021 are cited here). So they start with a definition.

**Step 1 — the definition (p. 1).**
- Consciousness = the spontaneous identification of mental contents as belonging to one's own organism, "located in its body". This applies to rich minds and to minimal minds, as when waking from deep sleep.
- "Consciousness should not be confused with the mere integration of images, or with the scale of that integration, or with the attention accorded to some images in detriment of others." (p. 1).
- In their own summary words: "‘We become conscious when we know, without any question being asked, that the contents of our minds belong to our respective bodies.’" (p. 1).

**Step 2 — sensing is not minding (p. 1).** Bacteria and plants *sense* (detect and respond to conditions), and sensing "hinges on cell membranes". "But sensing does not require the sensing organism to possess a nervous system" (p. 1), and it makes no internal maps: "Sensing dispenses with representations." (p. 1). Consciousness, by contrast, depends on representations — "mapped patterns" or "images" — of the kind that make up minds. Sensing is "a deep biological foundation" for minding and consciousness, but not the same thing.

**Step 3 — two kinds of image (p. 2).** Minds are streams of images built with the help of a nervous system.
- *Exteroceptive* images (from vision, hearing, touch, smell, taste) represent the outside world. They usually dominate.
- *Interoceptive* images represent the body's interior: "a racing heartbeat, the flow of air in the respiratory system, a gut colic". They carry intensity and quality, pleasant or unpleasant — for example "the more or less intense burning pain caused by acid indigestion". These images *are* the feelings produced by life regulation. They are called *homeostatic* feelings, to separate them from *emotional* feelings caused by emotions. Proprioception (sense of body position) is set aside "For the sake of brevity", though it "also contributes to homeostatic feelings" (p. 2).
- Feelings run "continuously in the awake state" and support the continuity of consciousness, "provided they operate above a requisite threshold" (p. 2).

**Step 4 — the core hypothesis (pp. 2–3).**
1. Feelings are conscious by nature: "‘each homeostatic feeling is itself spontaneously and automatically conscious’" (p. 2). When you feel hunger or pain, you are necessarily conscious of it.
2. Feelings carry graded knowledge about how life is going and what the organism needs: "pain signals the possibility of tissue damage while hunger signals the need for additional energy sources" (p. 2); well-being signals no urgent need, so the organism can explore.
3. That is their function: "Had feelings not been spontaneously conscious they would not have been able to assist living creatures with curating the life process." (p. 2).
4. Evolution: "We venture to propose that homeostatic feelings were the inaugural phenomena of consciousness" (p. 2), selected because they gave an advantage. They made life regulation *overt* and deliberate, beyond the *covert* regulation already present in organisms that sense but do not mind. Organisms behave "according to their principal interest: survival" (p. 2).
5. Self-consciousness builds on this platform: current and past experiences connected to one organism and "coherently organized as the mental counterpart of that organism" (p. 3).
6. Feelings do not borrow consciousness; they produce knowledge of the life state, so "homeostatic feelings can actually ‘lend’ consciousness to other processes, namely, exteroceptive sensory images." (p. 3). Visual images become conscious only when feelings identify them as belonging to the body.
7. No further mechanism is needed for large scenes: "There is no need to invoke an additional mechanism to provide consciousness to large arrays of contents." (p. 3).

**Step 5 — how feelings are generated (p. 3, Table 1 on p. 4).** The authors expect the objection that they have only moved the mystery from consciousness to feelings. Their answer is a mechanism:
1. Feelings arise from "a two-way interaction between (i) the nervous system; and (ii) non-neural components of the organism." (p. 3) — "the body’s interior, namely, viscera and circulating chemical molecules" (p. 1).
2. The result is a "hybrid" representation, at once neural and bodily. Interoceptive maps are not like maps of a landscape. The brain receives signals from the gut and can act back on the gut. "In the interoceptive world, object and map create a hybrid—by which we mean that they not only link up with each other but interact, literally commingle." (p. 3). By contrast, "we cannot have the map of a landscape interact with the landscape itself" (p. 3).
3. "We doubt the physiology of consciousness can be properly understood without considering this particular point." (p. 3).
4. The neural hardware is different. "interoceptive axons (i) are not insulated by myelin; (ii) make frequent non-synaptic contacts; and that (iii) interoceptive neurons are not systematically protected by a blood–brain barrier." (p. 3). (*Myelin* is the fatty insulation that speeds nerve signals; *non-synaptic* contacts release chemicals into the surrounding tissue rather than at a single junction; the *blood–brain barrier* normally keeps blood chemicals away from neurons.) So body chemicals reach interoceptive neurons directly.
5. Table 1 (p. 4) contrasts the two systems:

| | Interoception | Exteroception, movement, cognition |
|---|---|---|
| Axon type | Poorly myelinated or unmyelinated (Aδ/C) | Well myelinated (Aα/Aβ) |
| Signal transmission | Both nonsynaptic and synaptic | Predominantly synaptic |
| Time scale | Both slow (s/min/h) and fast | Very fast (μs–ms) |
| Processes supported ("suported" *(sic)*) | Interoception/visceroception, affect (moods, emotions, feelings) | Fine perception, learning, reasoning, calculation, language, movement |
| Blood–brain barrier | Absent or with major gaps | Continuous |
| Main transmitters and neuromodulators | Monoamines (dopamine, noradrenaline, serotonin), acetylcholine, neuropeptides | Glutamate, GABA |

6. Feelings therefore "refer to and identify the living organism in which they inhere" (p. 3): "Feelings continuously bring consciousness to the minds of ‘their’ organisms because they unmistakably connect those minds to the body where feelings ‘happen’." (p. 3).

**Step 6 — evidence from impaired consciousness (p. 4).**
- *Coma.* The critical lesion site is the back of the brainstem, where the nucleus tractus solitarius, the parabrachial nucleus and the periaqueductal grey (spelled "peri-acqueductal" *(sic)*) collect signals from the body's interior. Here the first whole-body integration of feeling-related signals happens. Damage cuts the link between body representations and the exteroceptive contents built in the posterior cortex. Hence "small brainstem lesions can have a devastating effect on consciousness, whereas even extensive lesions of the cerebral cortex may not." (p. 4). Their summary: the cortex creates most image contents; subcortical regions support the feelings that identify those contents as belonging to a body.
- *General anaesthesia.* Anaesthetics act on the basic "sensing and detecting" level — the membrane-based level shared with bacteria — "well below the functional level of minding at which feelings are generated" (p. 4). Sensing is "the foundational level of a functional hierarchical chain" that leads to feeling once a nervous system is present. "General anaesthetics seem to pre-empt the first link in the chain and thus preclude interoception and exteroception simultaneously." (p. 4). "Once feelings are no longer possible consciousness is also suspended." (p. 4). Anaesthetics also halt the movements of plants, which have no feelings — the authors take this as fitting their view that the drugs act on sensing, not on consciousness directly (Baluška et al. 2016 is cited).

**Step 7 — conclusion (p. 4).**
- "consciousness can be found in many complex living organisms though not in all. It cannot be found in inanimate objects, regardless of how complex they may be." (p. 4).
- It is present in organisms that build sensory representations of their own bodies, not in those limited to sensing.
- Nervous systems are needed for mapped images, so "only organisms with nervous systems are likely to be conscious." (p. 4).
- But nervous systems are not "solely responsible": "We believe that consciousness ‘requires a partnership of nervous systems with the bodies they serve’." (p. 4).
- So the failure of neuroscience is not surprising: "there is no reason why neuroscience should have solved it alone, because consciousness does not depend on the nervous system alone." (p. 4).

**Limits the authors state.** The paper is an essay. It says it will "outline" a mechanism (p. 1), "venture to propose" the evolutionary claim (p. 2), and leaves out proprioception "For the sake of brevity" (p. 2). It does not discuss artificial systems. It cites the authors' books (Damasio 2018, 2021) and Carvalho & Damasio 2021 for fuller treatment.

### What the paper says a system needs for feeling

As requested for this project, this section records **only the paper's claims**, as precisely as the text allows. It does not apply them to any artificial system, including this project's agents.

| # | Requirement stated or implied in the text | Where | How firmly stated |
|---|---|---|---|
| 1 | Being a **living organism** that regulates its own life (homeostasis). Feelings are "generated by the ongoing life regulation as it attempts to maintain operations in the homeostatic range" (p. 2). | pp. 1–2, 4 | Stated. The conclusion adds that consciousness "cannot be found in inanimate objects, regardless of how complex they may be" (p. 4). |
| 2 | More than **sensing**. Sensing/detecting and responding (bacteria, plants) is not enough; it has no representations. | p. 1, p. 4 | Stated. |
| 3 | A **nervous system**, because it is required to build "mapped imagetic representations" (p. 4). | p. 4 | Stated as: "only organisms with nervous systems are likely to be conscious" (p. 4). |
| 4 | **Interoceptive representations** — maps of the state of the body's own interior (viscera, heartbeat, breathing, chemistry), with intensity and pleasant/unpleasant quality. | p. 2 | Stated. |
| 5 | A **two-way physical interaction** between those neural elements and the non-neural body ("viscera and circulating chemical molecules"), such that map and object "literally commingle" as a "hybrid". | pp. 1, 3 | Proposed as "a possible mechanism" (p. 3). |
| 6 | A **particular physiology** at the interface: unmyelinated or poorly myelinated axons, non-synaptic as well as synaptic signalling, no or gappy blood–brain barrier, slow as well as fast time scales, monoamine / acetylcholine / neuropeptide signalling (Table 1). | p. 3, p. 4 | Stated as anatomical fact; its role in generating feeling is part of the proposal. |
| 7 | **Partnership with the body**: nervous systems are necessary but not "solely responsible"; consciousness "requires a partnership of nervous systems with the bodies they serve". | p. 4 | Stated. |
| 8 | **Continuity and threshold**: feelings flow continuously "in the awake state" and support consciousness "provided they operate above a requisite threshold". | p. 2 | Stated; the threshold is not specified. |
| 9 | **Brainstem integration** (in humans): first whole-body integration of feeling-related signals in the posterior brainstem (nucleus tractus solitarius, parabrachial nucleus, periaqueductal grey). | p. 4 | Stated as the human anatomical locus, supported by coma lesions. |
| 10 | An intact **sensing level** (cell membranes) as the first link of the chain; anaesthetics remove it. | p. 4 | Stated as probable ("It is probable, nonetheless"). |

Three further claims define the *role* of feeling rather than its requirements, and are recorded here because they are easily mis-paraphrased:
- Feelings are **intrinsically conscious**: "‘each homeostatic feeling is itself spontaneously and automatically conscious’" (p. 2). They are not made conscious by some other process.
- Feelings **report on life regulation and guide it**: pain "signals the possibility of tissue damage" and hunger "the need for additional energy sources" (p. 2). Their value is that they made regulation overt.
- Feelings **confer ownership** on all other contents: exteroceptive images become conscious when feelings identify them as belonging to the body (p. 3).

**What the paper does not say.** It does not discuss whether any non-living or engineered system could meet these requirements. It does not mention prediction, inference, learning or computation. It does not distinguish a damage *signal* from a *feeling* of pain except through the general split between sensing (no representation) and feeling (represented, intrinsically conscious). These gaps are recorded, not filled.

> **Reviewer's note.** The step from "feelings are generated by a hybrid neural–bodily interaction" to "feelings are spontaneously conscious" is where the explanatory work of the essay sits. The authors anticipate the objection that they have merely moved the problem (p. 3) and answer with a mechanism for *generating* feelings. The essay does not separately argue why that mechanism yields something felt rather than something merely represented. A reader may take this as the theory's central posit rather than a derived result.

> **Reviewer's note.** The claim about inanimate objects (p. 4) appears in the conclusion without a separate argument in this essay. It follows from requirements 1, 5 and 7 only if those are read as necessary conditions, which the essay asserts rather than defends against alternatives.

> **Reviewer's note.** The account of anaesthesia (acting at the membrane "sensing" level, below feeling) is stated with one supporting citation (Baluška et al. 2016, on plants). It competes with other accounts of the same evidence — including the cortical, dendritic account in Aru et al. (paper 1). See Cross-paper notes.

### Section-by-section backbone

1. **Standfirst and opening summary (p. 1).** One-line standfirst: interoception and homeostatic feelings are "crucial to understanding how conscious states emerge". Three unheaded paragraphs state the definition (ownership), the evolutionary proposal (feelings as "inaugural phenomena"), and the mechanism (two-way interaction of early interoceptive neural elements with viscera and circulating molecules, producing "hybrid and continuous phenomena").
2. **The problem of consciousness (p. 1).** Neuroscience's success elsewhere and failure here; pessimism that biology can solve it (Chalmers) or appeals to physics (Goff); proposed solutions often target attention or integration instead (Dehaene, Tononi et al., Graziano); hence the need to define consciousness first.
3. **Consciousness (p. 1).** Definition as spontaneous identification of mind contents with their owner organism; applies to large and small minds; not integration, scale or attention.
4. **Sensing and minding (pp. 1–2).** Sensing in bacteria and plants via membranes; no nervous system, no representations; consciousness depends on representations ("mapped patterns", "images"). **Figure 1** (p. 2): photograph by Martin Liebscher of himself playing piano to an audience of himself, captioned "perhaps the ultimate stage of consciousness!". Minds as streams of images; exteroceptive versus interoceptive images; homeostatic versus emotional feelings; proprioception set aside.
5. **How is consciousness made: a new hypothesis (pp. 2–3).** Identification of mind with organism is provided by homeostatic feelings; examples; continuity above threshold; feelings are spontaneously conscious; their information guides regulation; evolutionary selection; overt versus covert regulation; self-consciousness; feelings "lend" consciousness to exteroceptive images; no extra mechanism for large arrays.
6. **How do living organisms generate homeostatic feelings? (pp. 3–4).** The "moving the problem" objection; two-way interaction; hybrid representations; feelings identify their organism; interoception versus exteroception; map and object "commingle"; the landscape contrast; distinctive neural elements (no myelin, non-synaptic contacts, no blood–brain barrier). **Figure 2** (p. 3): artwork by Fatima Mendonça, "interoception as a dialogue of brain and body". **Table 1** (p. 4): interoception versus exteroception, movement and cognition.
7. **Impaired consciousness (p. 4).** Coma from posterior brainstem lesions; brainstem nuclei collecting interior signals; cortex for image contents, subcortex for ownership feelings; small brainstem versus large cortical lesions; anaesthesia at the sensing level; the hierarchical chain; anaesthetics also halt plants.
8. **Conclusion (p. 4).** Many but not all living organisms are conscious; no inanimate objects; nervous systems necessary but not sufficient; partnership of nervous system and body; neuroscience alone could not have solved it.
9. **Author notes, competing interests, references (pp. 4–5).** Affiliations; Antonio Damasio's book *Feeling & Knowing: Making Minds Conscious*; no competing interests; 11 references.

**Field record**
- Year · community: 2022 · neuroscience (clinical neurology and affective neuroscience); addressed to a neurology readership in *Brain*
- Question it asks: What is consciousness, and how does a living organism generate it?
- Position in one line: Consciousness is the felt ownership of mental contents by one's own body, supplied by continuous homeostatic feelings, which are intrinsically conscious and arise from a hybrid, two-way physical interaction between interoceptive nervous tissue and the body's organs and chemistry.
- Stance on computational functionalism: rejects, by implication only — the essay never mentions computation or functionalism, but its stated requirements are a living body, a nervous system, and physical "commingling" of map and body, and it says consciousness cannot be found in inanimate objects "regardless of how complex they may be".
- Stance on AI consciousness: no view stated — the essay does not mention AI, machines or computers. (Its general claim about inanimate objects is not applied to AI by the authors in this text.)
- What evidence or method it uses: theory proposal with empirical review (neuroanatomy and physiology of interoception, coma lesion evidence, anaesthesia) and evolutionary reasoning; essay form, no new data.
- Debates it takes part in: what consciousness is (ownership versus integration versus attention); brainstem versus cortex as the basis of consciousness; the role of the body and interoception; whether feelings are the origin of consciousness; whether consciousness needs a nervous system (against views that attribute it to all life); what anaesthesia shows.
- Builds on / argues against: builds on Damasio 2018 and 2021, Carvalho & Damasio 2021, Parvizi & Damasio 2001 and 2003; argues against the view that the problem cannot be solved in biology (Chalmers 1995) or belongs to physics (Goff 2019), and against identifying consciousness with integration or attention (Dehaene 2014; Tononi et al. 2016; Graziano 2021, as cited); distinguishes its view from attributing consciousness to plants or bacteria (cites Baluška et al. 2016).
- What would show it wrong: not stated. (The essay's empirical claims — e.g. that small posterior brainstem lesions abolish consciousness while extensive cortical lesions may not, and that anaesthetics act at the sensing level — are open to test, but the authors do not frame them as tests.)
- Quotes used:
  - "a new theory of consciousness" (p. 1)
  - "crucial to understanding how conscious states emerge" (p. 1)
  - "Consciousness occurs when mind contents, such as perceptions and thoughts, are ‘spontaneously identified as belonging to a specific organism/owner’." (p. 1)
  - "on mechanisms underlying other complex processes, such as attention and integration of information" (p. 1)
  - "located in its body" (p. 1)
  - "Consciousness should not be confused with the mere integration of images, or with the scale of that integration, or with the attention accorded to some images in detriment of others." (p. 1)
  - "‘We become conscious when we know, without any question being asked, that the contents of our minds belong to our respective bodies.’" (p. 1)
  - "hinges on cell membranes" (p. 1)
  - "But sensing does not require the sensing organism to possess a nervous system" (p. 1)
  - "Sensing dispenses with representations." (p. 1)
  - "a deep biological foundation" (p. 1)
  - "the body’s interior, namely, viscera and circulating chemical molecules" (p. 1)
  - "hybrid and continuous phenomena" (p. 1)
  - "a racing heartbeat, the flow of air in the respiratory system, a gut colic" (p. 2)
  - "the more or less intense burning pain caused by acid indigestion" (p. 2)
  - "For the sake of brevity" (p. 2)
  - "also contributes to homeostatic feelings" (p. 2)
  - "generated by the ongoing life regulation as it attempts to maintain operations in the homeostatic range" (p. 2)
  - "continuously in the awake state" (p. 2)
  - "provided they operate above a requisite threshold" (p. 2)
  - "‘each homeostatic feeling is itself spontaneously and automatically conscious’" (p. 2)
  - "pain signals the possibility of tissue damage while hunger signals the need for additional energy sources" (p. 2)
  - "Had feelings not been spontaneously conscious they would not have been able to assist living creatures with curating the life process." (p. 2)
  - "We venture to propose that homeostatic feelings were the inaugural phenomena of consciousness" (p. 2)
  - "according to their principal interest: survival" (p. 2)
  - "coherently organized as the mental counterpart of that organism" (p. 3)
  - "homeostatic feelings can actually ‘lend’ consciousness to other processes, namely, exteroceptive sensory images." (p. 3)
  - "There is no need to invoke an additional mechanism to provide consciousness to large arrays of contents." (p. 3)
  - "a two-way interaction between (i) the nervous system; and (ii) non-neural components of the organism." (p. 3)
  - "refer to and identify the living organism in which they inhere" (p. 3)
  - "Feelings continuously bring consciousness to the minds of ‘their’ organisms because they unmistakably connect those minds to the body where feelings ‘happen’." (p. 3)
  - "In the interoceptive world, object and map create a hybrid—by which we mean that they not only link up with each other but interact, literally commingle." (p. 3)
  - "we cannot have the map of a landscape interact with the landscape itself" (p. 3) — the extractor drops the space in "map of"; restored from the rendered page
  - "We doubt the physiology of consciousness can be properly understood without considering this particular point." (p. 3)
  - "interoceptive axons (i) are not insulated by myelin; (ii) make frequent non-synaptic contacts; and that (iii) interoceptive neurons are not systematically protected by a blood–brain barrier." (p. 3)
  - "small brainstem lesions can have a devastating effect on consciousness, whereas even extensive lesions of the cerebral cortex may not." (p. 4)
  - "well below the functional level of minding at which feelings are generated" (p. 4)
  - "the foundational level of a functional hierarchical chain" (p. 4)
  - "General anaesthetics seem to pre-empt the first link in the chain and thus preclude interoception and exteroception simultaneously." (p. 4)
  - "Once feelings are no longer possible consciousness is also suspended." (p. 4)
  - "consciousness can be found in many complex living organisms though not in all. It cannot be found in inanimate objects, regardless of how complex they may be." (p. 4)
  - "only organisms with nervous systems are likely to be conscious." (p. 4)
  - "We believe that consciousness ‘requires a partnership of nervous systems with the bodies they serve’." (p. 4)
  - "there is no reason why neuroscience should have solved it alone, because consciousness does not depend on the nervous system alone." (p. 4)

---

## Cross-paper notes

These notes describe how the two papers relate. They do not decide between them.

### 1. A direct citation link

Aru et al. cite the Damasios twice in ways that matter.
- The published version of their first argument ends by pointing to "more basic self- and agency-related processes" posited by some theories (p. 4 of Aru et al.). The first theory cited [42] is **this Damasio & Damasio (2022) essay**, followed by a second Damasio & Damasio 2022 paper, Damasio 2021, Panksepp 2005 and Solms 2021.
- In Box 1, the claim that a living system "has something to lose on several levels", and that skin in the game is "arguably prerequisite for caring about agency and consciousness", cites Man & Damasio 2019 [73] on homeostasis and feeling machines (Aru et al. p. 8). That 2019 paper is not held in this corpus and is not summarised here.

So the two papers are not independent: part of Aru et al.'s biological case rests on the Damasio line of work.

### 2. Where they agree about what biology contributes

- **Data or neurons are not enough on their own.** Aru et al.: "consciousness does not arise merely from data", and richer input "will not, by itself" produce it (p. 4). The Damasios: exteroceptive images become conscious only when homeostatic feelings tie them to a body (p. 3), and consciousness "does not depend on the nervous system alone" (p. 4). Both make the perceiving system's own stake and body part of the story.
- **Life regulation and stakes.** Aru et al.'s organism that "has something to lose on several levels" (p. 8) and the Damasios' organisms acting on "their principal interest: survival" (p. 2) express the same idea: a living system's continued existence depends on what it does.
- **Conversation and behaviour are not the test.** Aru et al. say this explicitly about LLMs. The Damasios make a parallel move in biology: plants and bacteria show complex responsive behaviour, yet on their account they sense without feeling (pp. 1, 4).
- **Brainstem and arousal matter.** Aru et al. list the ascending arousal system among the features AI lacks and cite Parvizi & Damasio 2001 for it (Aru et al. p. 2, ref. 18). The Damasios place the critical coma lesions in the posterior brainstem (p. 4).

### 3. Where they disagree, or weigh things differently

| Point | Aru, Larkum & Shine (2023) | Damasio & Damasio (2022) |
|---|---|---|
| What consciousness is | Mainly *phenomenal* consciousness; "conscious integration" (unity) is a central explanandum (p. 4). | *Ownership* of mental contents by one's body; explicitly *not* "the mere integration of images" (p. 1). |
| Where in the brain | Thalamocortical loops; layer 5 pyramidal neurons and their dendritic coupling; higher-order thalamus; plus arousal systems. | Posterior brainstem interoceptive nuclei; "even extensive lesions of the cerebral cortex may not" abolish consciousness (p. 4). Cortex supplies contents, not consciousness itself. |
| What anaesthesia shows | Anaesthetics functionally decouple the apical and basal zones of cortical layer 5 neurons, via metabotropic receptors (p. 6). | Anaesthetics act at the membrane "sensing and detecting" level, the first link of the chain, which is why they also stop plants (p. 4). |
| What biology contributes | *Specificity and organisation*: computational detail we may not yet understand, and multi-level self-maintenance that software leaves out. Biology as a possible source of necessary *computational* detail ("computational specificity", p. 6). | *A physical partnership*: neural maps that "literally commingle" with the body they map, using unmyelinated, non-synaptic, barrier-free tissue. Biology as a source of a *non-representational physical relation*, not of extra computational detail. |
| Strength of the claim | Hedged: "might", "may", "possibly"; must "at least entertain the possibility" (p. 8); not "necessarily subscribing" to the denial of software consciousness. | Categorical in the conclusion: consciousness "cannot be found in inanimate objects, regardless of how complex they may be" (p. 4). |
| Scope | Present-day LLMs and AI; the paper is about machines. | Living organisms only; the essay never mentions machines. |

> **Reviewer's note.** The anaesthesia row is the sharpest empirical disagreement: the same observation (general anaesthesia removes consciousness) is explained at the cortical-dendritic level by one paper and at the cell-membrane sensing level by the other. Neither paper discusses the other's account. Both could be partly right (anaesthetics have many sites of action), but as written they assign the effect to different levels.

### 4. How both relate to the biological-naturalism debate (Part C of the sibling topic)

Part C defines **biological naturalism** as the view that consciousness depends on properties of living systems that a simulation would not automatically have, and records several distinctions the synthesis can reuse. The two papers here map onto them as follows.

- **Part C's three biological claims (its cross-paper note 4).** Part C separates (a) metabolism / self-maintenance, (b) allostatic regulation / interoception, and (c) specific neural architecture. Aru et al. hold (c) and (a): thalamocortical and dendritic architecture, and multi-level self-maintenance. The Damasios hold (b), but add a physiological specificity of their own — not brain circuit architecture, but the properties of interoceptive tissue (unmyelinated axons, non-synaptic signalling, no blood–brain barrier) and its physical mixing with the body. Their view therefore cuts across Part C's categories (b) and (c), with "architecture" meaning body–nerve interface rather than cortical wiring.
- **Biopsychism versus biological naturalism.** Part C, following Seth, distinguishes the view that *all* living things are conscious (biopsychism) from the view that *only, but not necessarily all*, living things are. The Damasios are explicit that consciousness is found "in many complex living organisms though not in all" (p. 4), and deny it to bacteria and plants. On Part C's definitions they are biological naturalists, not biopsychists. Aru et al. do not take a position on which living things are conscious.
- **Epistemic versus ontological biological naturalism.** Part C records Seth's distinction between "consciousness can only be *understood* in light of life" and "consciousness *depends on* life". The Damasios' wording is ontological: consciousness "does not depend on the nervous system alone" and is absent from inanimate objects (p. 4). Aru et al.'s published wording leans toward the epistemic form at key points: "understanding consciousness may involve similar challenges" (p. 7) and organisational complexity "cannot be ignored to fully understand consciousness" (p. 8).

> **Reviewer's note.** Part C's cross-paper note 1 found that almost every author in the biological batch "restricts" rather than "rejects" computational functionalism, hedging explicitly. The Damasio essay is a partial exception: it does not discuss computation at all, so it neither restricts nor hedges, but its conclusion about inanimate objects is unhedged. If the synthesis files it, it should be marked "rejects, by implication" and the absence of any discussion of machines should be stated.

- **Interoception without prediction.** Part C records that Seth & Tsakiris (2018) and Seth (2025) build their interoceptive account from predictive processing and the free energy principle. The Damasio essay uses no predictive vocabulary (no mention of prediction, inference or models). The two interoceptive camps share a focus on the body's interior but differ on mechanism: prediction and control of bodily states (Seth) versus physical hybridisation of map and body (the Damasios).
- **IIT, updated.** Part C's cross-paper note 5 contrasts Aru et al.'s reading of IIT ("computer software does not have real cause-effect power", preprint) with Seth (2025), on which IIT makes nothing special about life. The published Aru et al. sentence now locates the obstacle in "the appropriate architecture" of "a typical modern computer" (p. 6), which is closer to Seth's reading: on IIT, the hardware, not the fact of being software or the fact of being alive, is what matters.
- **The hedges Part C relies on.** Part C's caution that Aru et al. is "not a flat denial" lists three disclaimers. In the published version one is absent and one is weakened (see the comparison table above). The synthesis should cite the published version's wording.

---

*Not done in this batch:* (1) The preprint PDF in the sibling topic was not opened; the version comparison relies on Part C's quotations of it. (2) Man & Damasio (2019), which both papers' link runs through, is not held and is not summarised. (3) The PDF page images could not be rendered with the Read tool (the poppler page renderer is not installed); text was extracted with PyMuPDF and three pages were rendered to PNG with PyMuPDF to check layout (Aru et al. p. 8; Damasio pp. 1, 2, 4).
