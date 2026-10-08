# AI consciousness — Part A1: Indicator properties (Butlin et al. 2023; Butlin et al. 2025)

## What this part covers (plain-language entry point)

This part reviews two papers by the same large team of philosophers, neuroscientists and AI researchers. Both ask one practical question: **how could we tell whether an AI system is conscious** — that is, whether it has experiences, so that there is "something it is like" to be it?

Their answer is a checklist. Scientists who study consciousness in humans have several competing theories. Each theory says that some kind of information processing in the brain is what makes an experience conscious. The authors turn these theories into a list of properties ("indicators") that an engineer can look for inside an AI system — for example, "the system has a shared workspace whose contents are sent to all its parts". The more of these properties a system has, the more seriously we should take the idea that it is conscious.

The 2023 report (88 pages) builds the list of 14 indicators, checks several real AI systems against it, and concludes that **no current system is a strong candidate, but nothing obvious stops engineers from building one that meets the indicators**. The 2025 journal article (14 pages) keeps the same list but turns it into a general method, with probability-based rules for using it. It drops the verdicts on named systems and is more open about doubts over its key assumption: that running the right computation is enough for consciousness.

## Table of Contents

- [Reading conventions](#reading-conventions)
- [1. Butlin, Long et al. (2023) — Consciousness in Artificial Intelligence: Insights from the Science of Consciousness](#1-butlin-long-et-al-2023--consciousness-in-artificial-intelligence-insights-from-the-science-of-consciousness-tier-full)
- [2. Butlin, Long, Bayne et al. (2025) — Identifying indicators of consciousness in AI systems](#2-butlin-long-bayne-et-al-2025--identifying-indicators-of-consciousness-in-ai-systems-tier-full)
- [Cross-paper notes](#cross-paper-notes)

## Reading conventions

- **Page numbers** are positions in the PDF file (page 1 = first page of the file). For the 2023 report, the printed page numbers happen to equal the PDF positions (the printed "4" is on PDF page 4), so the page numbers used in the sibling review agree with the ones here.
- **Text extraction.** Both PDFs were read through their text layer (the page-image renderer was not available on this machine). The 2025 article's text layer uses the single-glyph ligature "ﬁ" (and occasionally "ﬂ"); in the quotes below these are written as the two ordinary letters "fi" / "fl". Words broken across a line with a hyphen in the PDF (e.g. "nec-essary") are written whole. The 2025 text layer also inserts stray spaces inside some words (e.g. "suf ﬁcient", "app ly", "a ssess"); these spaces are removed in the quotes. Footnote markers are left out. No other characters were changed. Where a passage was garbled in extraction, it was not quoted.
- **Key terms used throughout.**
  - *Phenomenal consciousness* — having experiences at all; there is "something it is like" to be the system.
  - *Computational functionalism* — the view that running the right kind of computation (the right algorithm, on the right internal representations) is both necessary and sufficient for consciousness, whatever the system is made of.
  - *Indicator property* — a feature one can look for in an AI system that should make us more (or less) confident that the system is conscious.
  - *Credence* — a degree of belief, expressed as a probability between 0 and 1.
- **Sibling review.** The 2023 report is also reviewed in full in the sibling topic, [[computational_functionalism_lit_review_D_theories_and_tests]] (Part D, §6, at `docs/project/references/computational_functionalism/computational_functionalism_lit_review_D_theories_and_tests.md`). That review focuses on how the report defines and uses computational functionalism. This entry focuses on what the report says about **AI consciousness** and does not repeat the sibling's detail.
- **Reviewer's notes** are marked as such and are never the authors' claims.

---

## 1. Butlin, Long et al. (2023) — Consciousness in Artificial Intelligence: Insights from the Science of Consciousness [tier: full]

**PDF:** `sources/Butlin et al. 2023 - Consciousness in artificial intelligence - Insights from the science of consciousness.pdf` — report (preprint), arXiv:2308.08708v3 [cs.AI], dated 22 August 2023, 88 pages, 19 authors; Patrick Butlin and Robert Long are joint first authors.

**What was re-read and what was taken from the sibling review.** For this entry I re-read **34 PDF pages** directly: pp. 1–18 (abstract with its amended last sentence, author list, funding and conflicts statement, executive summary with the indicator table, contents, introduction, terminology, the three working assumptions, and the theory-heavy method); pp. 45–47 (§2.5, the indicator list with its table of entailments, and the opening of §3 with its three "lessons"); and pp. 58–70 (§3.2 case studies of existing AI systems, §4 implications, risks and recommendations, and Box 4 of open questions). I did **not** re-read pp. 19–44 (the individual theories: recurrent processing, global workspace, higher-order, attention schema, predictive processing, midbrain, unlimited associative learning, agency and embodiment, time), pp. 48–57 (§3.1, how each indicator could be built), or the glossary and references (pp. 71–88). For those parts, the summaries below rely on the sibling review (Part D §6) and say so.

### Phase 1: Plain overview

**The question.** Could current or near-future AI systems be conscious? The authors say the question is pressing for two reasons. AI researchers are deliberately copying brain functions linked to consciousness to make AI more capable. And chatbots that talk like humans will lead many people to believe they are conscious, whether or not they are (p. 4, p. 9).

**The answer, as a method.** Instead of asking the AI system whether it is conscious, or watching its behaviour, look inside it. Take the leading scientific theories of consciousness — each says some kind of brain processing marks the difference between conscious and unconscious experience in humans. Restate each theory's key requirement in computational terms. This gives 14 "indicator properties". Then check whether real AI systems have them (pp. 4–5). The authors do not back any one theory. Their claim is only comparative: a system with more indicators is a better candidate for consciousness (p. 5, p. 45).

**The result.** Some indicators are easy to find in today's AI — for example, recurrence (the same processing step is applied again and again, as in a recurrent neural network) (p. 6). But no existing system they examined comes close to having the full set. Large language models do poorly on the "global workspace" indicators; the Perceiver architecture does better but lacks "global broadcast"; among three embodied agents, DeepMind's Adaptive Agent (AdA) comes closest to the embodiment indicator (pp. 59–63). The headline: "Our analysis suggests that no current AI systems are conscious, but also suggests that there are no obvious technical barriers to building AI systems which satisfy these indicators." (p. 1). A footnote records that an earlier version said there were "no obvious barriers to building conscious AI systems"; the authors changed it because "satisfying the indicators would not mean that such an AI system would definitely be conscious" (p. 1).

**Why it matters.** This report set the agenda for a "look inside the system, using theories" approach to AI consciousness. It also made the cost of its key assumption visible: everything depends on computational functionalism being true. If consciousness instead needs something only living organisms have, the indicators tell us little about AI (p. 14).

### Phase 2: The argument, step by step

**Premise 1 — Computational functionalism, as a working hypothesis.** "Implementing computations of a certain kind is necessary and sufficient for consciousness, so it is possible in principle for non-organic artificial systems to be conscious." (p. 11). The authors adopt this "primarily for pragmatic reasons" (p. 14): most leading theories can be read computationally, so the assumption lets them carry theories from human brains to AI. They name what is lost if it is false: "It could be, for instance, that some non-computational feature of living organisms is necessary for consciousness (Searle 1980, Seth 2021), in which case consciousness would be impossible in non-organic artificial systems." (p. 14). They do not all agree on how likely it is: "Although we have different levels of confidence in computational functionalism, we agree that it is plausible." (p. 14). Their version is a careful one: what matters is the algorithm and the format of the internal representations, not the input–output behaviour alone, and not every material can implement the relevant computations (p. 13). (The sibling review, Part D §6.1–2.1, sets out these qualifications in detail.)

**Premise 2 — Scientific theories carry real evidence.** Neuroscience has identified functions associated with consciousness by "contrastive analysis" — comparing brain activity when a person reports seeing a stimulus with activity when they do not (p. 15). The authors list the method's known problems: reports may need more processing than experience itself, and experience may be richer than what can be reported ("overflow"). They mention partial remedies: "no-report" experiments, in which consciousness is inferred from other measures already calibrated against reports, and confidence ratings (p. 15). They also separate scientific theories (which brain processes go with consciousness) from metaphysical theories (how consciousness relates to the physical world at all), and say the science has work to do whether one is a materialist, a property dualist, a panpsychist or an illusionist (pp. 14, 16–17).

**Premise 3 — A "theory-heavy" method, not behavioural tests.** Confidence that a system is conscious should depend on "(a) the similarity of its computational processes to those posited by a given scientific theory of consciousness, (b) our confidence in this theory, (c) and our confidence in computational functionalism" (p. 17). Behavioural tests are rejected for now because AI systems can be trained to imitate humans: "this method is unreliable because AI systems can be trained to mimic human behaviours while working in very different ways." (p. 4). Schneider's Artificial Consciousness Test, which looks for a natural grasp of consciousness-related ideas in conversation, would need to keep human writing about consciousness out of training data. The authors doubt that this can be done in a way that still lets the system take the test (p. 18).

They state the strongest objection to their own method, from Birch: evidence from humans does not tell us how far a theory's conditions can be relaxed and still be enough for consciousness (p. 17). Their reply is comparative. Even so, "those using more similar processes are correspondingly better candidates for consciousness" (p. 18). They also explain why they treat AI differently from animals. For animals, evolutionary relatedness and behaviour are already some evidence. For AI, there is no shared ancestry to rely on, so "a theory-heavy approach is necessary for AI" (p. 12, p. 18).

**Move 1 — Which theories, and which are left out.** The survey covers recurrent processing theory, global workspace theory, computational higher-order theories, attention schema theory and predictive processing, plus agency and embodiment (p. 5). Integrated information theory (IIT) is excluded: "We do not consider integrated information theory, because it is not compatible with computational functionalism." (p. 5). IIT says consciousness depends on the physical cause–effect structure of a system, not on the algorithm it runs, so on IIT ordinary digital computers are unlikely to be conscious whatever program they run (sibling review, Part D §6, 2.3, quoting report p. 33).

**Move 2 — The 14 indicators** (p. 5, Table 1; restated with entailments on p. 46, Table 2). In plain words:

| Code | Indicator (authors' wording, p. 5) | What it means in plain words |
|---|---|---|
| RPT-1 | Input modules using algorithmic recurrence | Perception applies the same processing step repeatedly, rather than in a single forward pass |
| RPT-2 | Input modules generating organised, integrated perceptual representations | Perception builds a structured scene (objects, figure and ground), not a set of separate features |
| GWT-1 | Multiple specialised systems capable of operating in parallel (modules) | Many specialist parts work at the same time |
| GWT-2 | Limited capacity workspace, entailing a bottleneck in information flow and a selective attention mechanism | A small shared "workspace"; attention chooses what enters it |
| GWT-3 | Global broadcast: availability of information in the workspace to all modules | What is in the workspace is sent to every specialist |
| GWT-4 | State-dependent attention, giving rise to the capacity to use the workspace to query modules in succession to perform complex tasks | What enters the workspace depends on the current state, so the system can work through multi-step tasks |
| HOT-1 | Generative, top-down or noisy perception modules | Perception can produce representations from the inside (as in imagery), so some of them are unreliable |
| HOT-2 | Metacognitive monitoring distinguishing reliable perceptual representations from noise | A second-level monitor judges which perceptions reflect the world |
| HOT-3 | Agency guided by a general belief-formation and action selection system, and a strong disposition to update beliefs in accordance with the outputs of metacognitive monitoring | A general belief-and-action system that trusts what the monitor marks as real |
| HOT-4 | Sparse and smooth coding generating a "quality space" | Experiences are coded so that similar qualities sit close together (as colours do) |
| AST-1 | A predictive model representing and enabling control over the current state of attention | The system keeps a simplified model of its own attention and uses it to control attention |
| PP-1 | Input modules using predictive coding | Perception works by predicting inputs and passing on prediction errors |
| AE-1 | Agency: Learning from feedback and selecting outputs so as to pursue goals, especially where this involves flexible responsiveness to competing goals | The system learns from feedback how to reach goals, and balances goals that compete |
| AE-2 | Embodiment: Modeling output-input contingencies, including some systematic effects, and using this model in perception or control | The system models how its own actions change what it senses, and uses that model |

The theories make strong claims — for example, global workspace theory says GWT-1 to GWT-4 are necessary and together sufficient (p. 46). The report deliberately claims less: "Systems that have more of these features are better candidates for consciousness." (p. 45). The authors add that some indicators may be needed but add little on their own, "perhaps including RPT-1, GWT-1 and HOT-1" (p. 45). Table 2 records the dependencies between indicators: GWT-3 and GWT-4 entail RPT-1; PP-1 entails RPT-1 and HOT-1; the first clause of HOT-3 entails AE-1; and systems meeting AE-2 are likely, but not certain, to meet AE-1 (p. 46).

**Move 3 — Three lessons from applying the list** (p. 47). (i) Deciding whether a system has an indicator needs interpretation, because the theories themselves are not precise. Making the indicators more precise would go beyond the evidence. (ii) Architecture, training and behaviour are not always enough to decide. For example, an agent trained with reinforcement learning (RL — learning from rewards and penalties) to control a virtual body may or may not have learned a model of how its actions change its inputs. Only interpretability methods (tools that examine what a network's internal layers represent) can settle this. (iii) "If it is possible at all to build conscious AI systems without radically new hardware, it may well be possible now." (p. 47).

**Move 4 — Case studies of existing systems** (pp. 58–63).
- *Transformer-based large language models* (GPT-3, GPT-4, LaMDA). One can argue that the "residual stream" — the running internal signal that every layer reads from and adds to — is a workspace, with the attention heads as modules. The authors reject the argument. The residual stream is no narrower than the input, so it is not clearly a bottleneck. More basically, "Transformers are not recurrent": no module both writes to the workspace and receives from it (p. 59). Verdict: "There is only a relatively weak case that Transformer-based large language models possess any of the GWT-derived indicator properties." (p. 59).
- *Perceiver / Perceiver IO.* Arguably GWT-1, GWT-2 and the first part of GWT-4. But the system must be reset for each new task, and "the clearest missing element of the global workspace in the Perceiver is the lack of global broadcast" (p. 60).
- *PaLM-E* (a language model connected to a robot through a separately trained control policy). Both parts are trained to imitate humans, not to learn from success or failure. So the system "arguably imitates planning and using visuomotor control to execute plans, as opposed to actually doing these things" (p. 61). It is not trained end-to-end, so it has never been exposed to the effects of its own outputs. That makes the embodiment indicator hard to meet (p. 62).
- *A "virtual rodent"* trained end-to-end by RL to control a simulated rat body with 38 degrees of freedom. "It is trained by RL, which is sufficient for agency." (p. 62). But its tasks may have been solvable with a fixed set of stereotyped movements, so it may never have needed a self-model (p. 63).
- *AdA*, DeepMind's Adaptive Agent, trained by RL and meta-learning across many tasks, with an objective to predict from interleaved past inputs and outputs. "AdA may, therefore, be the most likely of the three systems we have considered to be embodied by our standards" (p. 63).
- Overall: "This work does not suggest that any existing AI system is a strong candidate for consciousness." (p. 6).

**Move 5 — Implications and recommendations** (pp. 64–70).
- *Two kinds of error.* Under-attribution — failing to recognise consciousness that is there — risks large-scale harm. The authors compare it to farmed animals and note that developers have economic reasons to play down welfare concerns (p. 64). They separate being conscious from being able to suffer: "being conscious is not the same as being capable of conscious suffering." (p. 64). Over-attribution is also a risk, and already happening: "There is also a significant chance that we could over-attribute consciousness to AI systems—indeed, this already seems to be happening" (p. 65). The costs named are: wasted resources; discrediting better-supported claims; conflict with safe AI development; and harm to human relationships, including manipulation (pp. 65–66).
- *Capabilities.* Animal minds evolved under limits on data, energy and ancestry that AI design does not face, "So we may well find ways to build high-performing AI systems which are not conscious." (p. 67). But some researchers (Bengio's global-workspace work, LeCun's "configurator") are building consciousness-linked features to gain capability, so this route is likely to be taken (p. 67). Being conscious need not mean having human-like motives or emotions (p. 67). Arguments that AI is an existential risk do not assume consciousness (p. 68).
- *Recommendations, kept narrow.* Support consciousness science and its application to AI; use the theory-heavy method both before systems are built and after (with mechanistic interpretability); extend theories to animals; develop computational theories of valence (experiences that feel good or bad); keep working on behavioural tests, which need not be "theory-neutral" (pp. 68–70). The report lists, but does not assess, others' policy proposals — Bryson (avoid conscious AI), Metzinger (a moratorium), Graziano (build it), Schwitzgebel and Garza (build a system only if confident either way) (p. 68). The executive summary also calls for "urgent consideration of the moral and social risks of building conscious AI systems, a topic which we do not address in this report" (p. 6).
- *Open questions (Box 4).* Among them: whether consciousness is possible on conventional hardware, including the biological-naturalist point that living cells maintain themselves (citing Seth 2021 and Aru et al. 2023); how to count AI systems that can be copied and run in many places at once; and the ethics of the research itself — it "runs the risk of building (or enabling others to build) a conscious AI system, which should not be done lightly." (p. 70).

**Limits the authors state.** The rubric is "provisional" (p. 4). It depends on computational functionalism and on theories built mostly from data on healthy adult humans (pp. 14, 16). Interpretations of theories range from restrictive to liberal, and moderate readings are attractive, "but it is not clear that these have empirical support over the alternatives" (p. 17). A formal scoring procedure would be questionable "at present" (pp. 69–70). They do not study valence (p. 65).

> **Reviewer's note.** The method's output is a count of indicators, but the report does not give weights to indicators or theories. It says that some combinations are more compelling and that some indicators add little on their own (p. 45). How to turn the indicators into a single credence is left to the reader. The 2025 article (entry 2) partly addresses this with an explicitly Bayesian framing.

### Section-by-section backbone

(Sections marked † were not re-read for this entry; their summaries come from the sibling review, Part D §6.)

- **Abstract and footnote (p. 1).** Assess AI in light of neuroscientific theories; derive indicators; apply them. No current system is conscious, and there are no obvious *technical* barriers to building systems that meet the indicators. The footnote explains the amended wording.
- **Authors, details, funding (pp. 2–3).** 19 authors in philosophy, neuroscience, psychology and machine learning. Nick Bostrom proposed the project. Workshops were funded by Effective Ventures and the EA Long-Term Future Fund. "The authors have no conflicts of interest to report." (p. 3). Tim Bayne and David Chalmers are thanked for taking part in workshops or discussions.
- **Executive summary (pp. 4–6).** Three contributions (the question can be studied scientifically; a rubric; initial evidence). Three tenets (computational functionalism; scientific theories; theory-heavy method). Full indicator table. Case studies previewed. If computational functionalism is true, conscious AI "could realistically be built in the near term" (p. 6).
- **§1 Introduction (p. 9).** Expert opinion diverges, but progress is possible because some theories have empirical support and fit many metaphysical views. Conscious AI could be built "within the next few decades" (p. 9).
- **§1.1 Terminology (pp. 9–11).** "Conscious" means phenomenally conscious, explained with examples (seeing, hearing, pains and itches, imagery, emotions) and non-examples (hormone regulation, stored memories, masked stimuli). Different from access consciousness. "Sentient" avoided because a system could have only neutral experiences.
- **§1.2 Methods and assumptions (pp. 11–13).** The three assumptions. Box 1: consciousness may be indeterminate, come in degrees, vary along several dimensions, or have separable elements. Reason in credences.
- **§1.2.1 Computational functionalism (pp. 13–14).** Definition; multiple realisability; not every substrate works; same input–output function does not imply the same consciousness; representational format may matter; Marr's algorithmic level. Adopted pragmatically; what follows if it is false; the gradual-neuron-replacement argument (Chalmers) in a footnote.
- **§1.2.2 Scientific theories (pp. 14–17).** Scientific vs metaphysical theories; contrastive analysis; problems with reports; no-report paradigms and confidence ratings; subjects who cannot report. Box 2 on four metaphysical positions.
- **§1.2.3 Theory-heavy approach (pp. 17–18).** Three-factor credence rule; Birch's theory-light objection and the comparative reply; why AI differs from animals; behavioural tests can be gamed.
- **§2.1–2.4 The theories (pp. 19–44)†.** Recurrent processing (RPT-1, RPT-2); global workspace (GWT-1–4); higher-order theories, with perceptual reality monitoring as the computational version (HOT-1–4); IIT excluded with a note on "weak IIT"; attention schema (AST-1); predictive processing as a framework (PP-1); midbrain theory and unlimited associative learning as support for agency and embodiment; agency and embodiment (AE-1, AE-2); time and recurrence as a second route to RPT-1.
- **§2.5 Indicators (pp. 45–46).** The list as a rubric; the explicitly weaker claim; Table 2 of entailments.
- **§3 opening (p. 47).** Three lessons: interpretation is needed; interpretability tools may be needed; if conscious AI is possible on current hardware, it may be possible now.
- **§3.1 Implementing indicators (pp. 48–57)†.** How each indicator could be built with standard machine-learning methods. Existing systems built to implement global workspace theory and attention schema theory.
- **§3.2 Case studies (pp. 58–63).** Transformers and Perceiver against GWT; PaLM-E, the virtual rodent and AdA against AE-1/AE-2.
- **§4.1 Attribution (pp. 64–66).** Risks of under- and over-attribution; the difference between consciousness and the capacity to suffer.
- **§4.2 Consciousness and capabilities (pp. 66–68).** Evolutionary limits vs AI design space; capability-driven research on consciousness-linked features; no implication of human-like motives; existential-risk arguments do not need consciousness.
- **§4.3 Recommendations and Box 4 (pp. 68–70).** Narrow recommendations; others' policy proposals listed without assessment; open questions.

**Field record**
- Year · community: 2023 · consciousness-science and AI-and-ML (interdisciplinary report, with philosophy-of-mind and ethics-and-policy contributions)
- Question it asks: Are current or near-term AI systems conscious, and can theories from consciousness science be used to assess them?
- Position in one line: If computational functionalism holds, 14 computational indicators taken from leading theories give a rubric for AI consciousness; no current system is a strong candidate, but no obvious technical barrier blocks systems that meet the indicators.
- Stance on computational functionalism: supports, as a working hypothesis — adopted for pragmatic reasons, judged "plausible" by all authors at differing confidence, with the cost of its being false stated.
- Stance on AI consciousness: possible in principle (given the hypothesis); not present in current systems examined; could realistically be built in the near term.
- What evidence or method it uses: theory review plus applied assessment of named AI architectures (conceptual analysis of their design).
- Debates it takes part in: theory-heavy vs theory-light vs behavioural tests; whether LLMs are conscious; under- vs over-attribution; whether consciousness tracks capability; IIT vs functionalist theories.
- Builds on / argues against: builds on Lamme (recurrent processing), Baars and Dehaene (global workspace), Lau and Brown et al. (higher-order / perceptual reality monitoring), Graziano (attention schema), Seth and Hohwy, Clark (predictive processing), Merker, Ginsburg and Jablonka; responds to Birch 2022b (theory-light) and Schneider 2019 (behavioural test); sets aside Tononi & Koch 2015 (IIT) and Searle 1980 / Seth 2021 (biological views).
- What would show it wrong: the authors state that if computational functionalism is false, the indicators need not track consciousness in AI (p. 14); they also expect the list to change as the science progresses (p. 4).
- Quotes used:
  - "Our analysis suggests that no current AI systems are conscious, but also suggests that there are no obvious technical barriers to building AI systems which satisfy these indicators." (p. 1)
  - "satisfying the indicators would not mean that such an AI system would definitely be conscious" (p. 1)
  - "The authors have no conflicts of interest to report." (p. 3)
  - "this method is unreliable because AI systems can be trained to mimic human behaviours while working in very different ways." (p. 4)
  - "We do not consider integrated information theory, because it is not compatible with computational functionalism." (p. 5)
  - "This work does not suggest that any existing AI system is a strong candidate for consciousness." (p. 6)
  - "urgent consideration of the moral and social risks of building conscious AI systems, a topic which we do not address in this report" (p. 6)
  - "Implementing computations of a certain kind is necessary and sufficient for consciousness, so it is possible in principle for non-organic artificial systems to be conscious." (p. 11)
  - "a theory-heavy approach is necessary for AI" (p. 12)
  - "It could be, for instance, that some non-computational feature of living organisms is necessary for consciousness (Searle 1980, Seth 2021), in which case consciousness would be impossible in non-organic artificial systems." (p. 14)
  - "Although we have different levels of confidence in computational functionalism, we agree that it is plausible." (p. 14) — the PDF has a footnote marker "4" after "plausible."
  - "(a) the similarity of its computational processes to those posited by a given scientific theory of consciousness, (b) our confidence in this theory, (c) and our confidence in computational functionalism" (p. 17)
  - "those using more similar processes are correspondingly better candidates for consciousness" (p. 18)
  - "Systems that have more of these features are better candidates for consciousness." (p. 45)
  - "perhaps including RPT-1, GWT-1 and HOT-1" (p. 45)
  - "If it is possible at all to build conscious AI systems without radically new hardware, it may well be possible now." (p. 47)
  - "Transformers are not recurrent" (p. 59)
  - "There is only a relatively weak case that Transformer-based large language models possess any of the GWT-derived indicator properties." (p. 59)
  - "the clearest missing element of the global workspace in the Perceiver is the lack of global broadcast" (p. 60)
  - "arguably imitates planning and using visuomotor control to execute plans, as opposed to actually doing these things" (p. 61)
  - "It is trained by RL, which is sufficient for agency." (p. 62)
  - "AdA may, therefore, be the most likely of the three systems we have considered to be embodied by our standards" (p. 63)
  - "being conscious is not the same as being capable of conscious suffering." (p. 64)
  - "There is also a significant chance that we could over-attribute consciousness to AI systems—indeed, this already seems to be happening" (p. 65)
  - "So we may well find ways to build high-performing AI systems which are not conscious." (p. 67)
  - "runs the risk of building (or enabling others to build) a conscious AI system, which should not be done lightly." (p. 70)

---

## 2. Butlin, Long, Bayne et al. (2025) — Identifying indicators of consciousness in AI systems [tier: full]

**PDF:** `sources/Butlin et al. 2025 - Identifying indicators of consciousness in AI systems.pdf` — published, open access (CC BY-NC-ND), *Trends in Cognitive Sciences*, Opinion article, doi:10.1016/j.tics.2025.10.011, 14 pages (pp. 1–11 text, pp. 12–14 acknowledgements, declaration of interests and 115 references). The file is an online article-in-press version: its footer reads "Month 2025, Vol. xx, No. xx" and its header "TICS 2797", so volume and page numbers were not yet assigned. 20 authors; Patrick Butlin is corresponding author. All 14 pages were read.

### Phase 1: Plain overview

**The question.** The 2025 article asks a narrower question than the 2023 report. It does not ask whether today's AI is conscious, or whether AI consciousness is possible at all. It asks: *how should we assess AI systems for consciousness?* "In this article we focus on how to assess AI systems for consciousness, rather than on whether AI consciousness is possible at all." (p. 2).

**Why now.** AI capabilities are growing fast. Researchers are building systems that copy computational features linked to human consciousness. A study found that most participants were willing to give ChatGPT some chance of being conscious, and frequent users more so. AI companions are spreading (p. 1). The authors expect "considerable public disagreement" and say we need "a principled basis" for either dismissing concern or acting on it — for example, by regulating AI (p. 1).

**The answer.** The "theory-derived indicator method": take theories of consciousness that are credible and that state conditions an AI system could actually meet; turn their central claims into indicators; look for those indicators in particular systems; and treat each finding as evidence that raises or lowers one's credence (p. 2, p. 4). The 2023 list of 14 indicators is reprinted as an example ("Potential indicators", Table 1, p. 6). The new material is about *how* to build and use such lists: four guidelines for deriving indicators (pp. 6–9), two difficulties in finding indicators in real systems (pp. 9–10), and a Bayesian account of what an indicator tells us (pp. 10–11).

**Why it matters.** It turns the 2023 report into a general, reusable method. The method is open to other theories, including ones not yet developed. It is more open about doubts over computational functionalism: "While many of us are agnostic about computational functionalism, we agree that it provides a useful focus for assessments." (p. 4). It also warns that indicators can be "gamed" — built into a system to make it seem conscious, without making it conscious (Box 3, p. 5).

### Phase 2: The argument, step by step

**Step 1 — The problem: risk on both sides.** If we miss consciousness where it exists, "we risk causing avoidable harms to those systems, which may exist in large numbers"; if we attribute it wrongly, "we may waste resources or risk lives trying to promote their welfare" (p. 1). Tests for consciousness are hard to validate, and AI is a particularly hard case (p. 2, citing Bayne et al. 2024).

**Step 2 — What counts as a usable theory.** Two criteria (pp. 2–3). First, a theory must deserve enough credence to be worth following through. Second, it should imply "clear and testable conditions that AI systems might meet" (p. 3). A theory that requires a cortex fails the second criterion, because no AI system can meet it. Computational functionalist theories pass the second criterion if their conditions are clear. At present this includes recurrent processing theory, global workspace theory, higher-order theories and attention schema theory (p. 3). These are four theories, not the 2023 five. Predictive processing now enters as a "background condition" (Step 4).

**Step 3 — Where computational functionalism now sits (Box 2, pp. 3–4).** "As we interpret them, the theories we rely on to derive indicators for consciousness share a commitment to computational functionalism." (p. 3). One version of the method adopts computational functionalism as a working assumption, "However, many theorists favor alternative views" (p. 3). Two alternatives are described in their own terms:
- *Biological substrate views* — being made of living cells (or similar) is necessary, either because biology allows "fine-grained, non-computational patterns of functional organization" or through "some more direct connection with consciousness" (p. 3). The papers cited for this view include Damasio and Damasio 2022, Aru et al. 2023 and Seth 2025 (refs 1–3), all in this topic's corpus.
- *IIT* — what matters is whether a system's physical parts form a unified causal whole under the theory's mathematical definition, not which algorithm they run (p. 3).
The relation to IIT has changed from 2023. IIT is no longer excluded as incompatible. Instead: "AI systems using non-conventional hardware might meet the conditions of integrated information theory (IIT)" (p. 3). The method focuses on computational functionalist readings because this "makes this method tractable and relevant to current and near-future systems" (p. 4). Biological views fail the second criterion, but "these views should still be considered in overall assessments of the likelihood of consciousness in AI." (p. 4).

**Step 4 — Narrow vs broad theories, and indicators rather than conditions** (p. 4). A *narrow* formulation says what separates conscious from unconscious states in humans. A *broad* one says what is necessary or sufficient in any system. Under a broad theory, if condition C is sufficient, any AI system that meets C is conscious (given the theory). Under a narrow theory, other background conditions may also be needed. Still, "we can reasonably increase our credence that the system is conscious if we have non-zero credence that the relevant background conditions are met" (p. 4). Because no theory dominates, the method draws on several. Their conditions "will not collectively provide a set of necessary and sufficient conditions", so they are used as indicators (p. 4). The authors say indicators have been used before for animals and infants, but "our approach is distinctive in deriving indicators from multiple theories" (p. 4). Indicators come from two places: the theories' own accounts, and *background conditions* that the wider literature suggests may be needed but are not sufficient — for example representation, predictive processing, agency and embodiment (pp. 4–5).

**Step 5 — Look inside, not at behaviour** (p. 5). "We assume that whether a system is conscious depends on features of its internal processes." (p. 5). Behavioural tests face two problems. AI may reach human-like behaviour by routes that do not involve consciousness, because "biological constraints do not apply". And developers have incentives to make systems imitate humans (p. 5). Large language models show that "inferences from behavior to features of internal processes are often unreliable" (p. 5). Unlike in 2023, carefully designed behavioural tests are now given a supporting role: they "could provide some evidence for the presence of our indicators" (p. 5).

**Step 6 — The gaming problem (Box 3, p. 5).** "An indicator is gamed if its presence is better explained by the fact that it makes a system seem to possess a property of interest than by the fact that the system actually possesses the property." (p. 5). The authors extend this beyond behaviour to their own computational indicators: "the problem can also arise for computational markers" (p. 5). If feature N is not sufficient for consciousness, one can build a non-conscious system with N. This happens even without any intent to deceive, whenever users value systems that seem to have indicators. Two remedies: (i) prefer indicators that are sufficient for consciousness, or that cannot easily be built without also creating consciousness; (ii) when an indicator can be gamed, check for supporting features. From the computational-functionalist point of view, high computational similarity to known conscious biological systems makes these conditions more likely to hold (p. 5).

**Step 7 — Four guidelines for deriving indicators** (pp. 6–9).
1. *Focus on each theory's central explanatory claims.* Drop details specific to humans. Example: the current version of global workspace theory says the workspace corresponds to *attended* items in working memory. This detail "does not appear to be central to the account and therefore is not included in the indicators" (pp. 7–8). Short lists also avoid redundancy.
2. *Stay open to unusual forms of consciousness, but avoid the "minimal implementation problem".* Liberal readings of a theory can be met by trivially simple systems that are not plausibly conscious. Such systems then count against the theory rather than for consciousness (p. 8). So some indicators must be demanding — "arguably" GWT-4 ("complex tasks") and HOT-3 ("general belief-formation and action selection system") (p. 8). Simple, common indicators such as RPT-1 are still useful, because their *absence* may be strong evidence against consciousness. Indicators should leave out features, such as particular senses, that are unlikely to be necessary. But RPT-2's demand for perceptual representations stays, even though it may be "chauvinistic" (unfairly biased towards systems like us) for beings with very different perception or none (p. 8).
3. *Include background-condition indicators.* Theories built on human contrasts may miss features humans almost always have. PP-1 is justified this way (p. 8). Agency is justified because several theories link it to consciousness — midbrain theory, neurorepresentationalism and arguably global workspace theory (p. 9). Accounts of agency vary widely (biological autonomy, AI goal-directedness, belief–desire–intention). AE-1 tries to capture what animals and AI agents share: learning to reach goals more effectively through interaction with an environment. "This is a relatively novel proposal compared to other indicators, but such a proposal is needed to begin to synthesize disparate ideas about agency" (p. 9).
4. *Avoid ambiguous terms, but do not fix precise specifications too early.* "Recurrence" is defined at the algorithmic level to avoid confusion with feedback wiring in the brain (RPT-1). AE-2 defines embodiment so that controlling an avatar in a virtual world can count, "motivated partly by the aim of finding a definition that is consistent with computational functionalism" (p. 9). Theories are underspecified, and the indicators should honestly reflect that; they will be updated as research moves on (p. 9).

**Step 8 — Finding indicators in real systems** (pp. 9–10). Two difficulties. First, we cannot easily see the representations and algorithms inside trained networks. Mechanistic interpretability helps but has "significant limitations at present" (pp. 9–10). Example: RPT-2 is best checked by looking inside the network, but a behavioural probe — susceptibility to the Kanizsa illusion, in which people see a triangle that is not drawn — could also help (p. 10). Second, whether a system has an indicator can be a matter of interpretation. A Transformer is a feedforward network. But when it generates text one token at a time, each new token is fed back through the context window, which looks like a loop. So "whether LLMs are recurrent depends on where we draw the boundaries of the system" (p. 10). "Various arguments could be made on this issue, but the point is that whether systems possess indicators can be debatable even if we understand their operation in detail and can turn on philosophical questions such as how to delineate the system in question." (p. 10).

**Step 9 — What an indicator tells us: a Bayesian account** (pp. 10–11). "We propose a broadly Bayesian attitude to indicators." (p. 10). Let H be "the system is conscious" and E the presence of an indicator. For a positive indicator,

$$
p(H \mid E_p) > p(H),
$$

and for a negative indicator,

$$
p(H \mid E_n) < p(H)
$$

(p. 10). Indicators differ in *specificity* — systems that have the indicator tend to be conscious — and *sensitivity* — conscious systems tend to have the indicator. "The absence of a sensitive indicator tells us that a system is unlikely to be conscious; this is why indicators like RPT-1, algorithmic recurrence, may be useful." (p. 10). Indicators are positive *relative to a theory* T:

$$
p(H \mid E \wedge T) > p(H \mid T)
$$

(p. 10). How far one should update depends on one's prior, on one's credence in T, on whether the indicator is really present, and on the dependencies between indicators (p. 10). Final credences should also reflect rival theories and "unknown unknowns". "Sets of theory-derived indicators might leave out some necessary condition for consciousness – either a further computational condition or a requirement for a non-computational feature" (p. 11). The method is worth using only if it shifts credences enough to matter. That requires enough confidence in the source theories, and attention to whether supporters of rival theories treat some indicators as evidence *against* consciousness (p. 11).

> **Reviewer's note (derivation, not in the paper).** The paper's conditional statement can be connected to an overall credence by the law of total probability over theories. With theories T₁, …, Tₖ plus a remainder T₀ ("none of these is right", which covers the biological and IIT alternatives and the unknown unknowns), write
>
> $$
> p(H \mid E) \;=\; \sum_{i=0}^{k} p(H \mid E, T_i)\, p(T_i \mid E).
> $$
>
> The indicator raises the term for each theory Tᵢ from which it was derived. But if T₀ carries much weight and p(H | E, T₀) ≈ p(H | T₀) (for example, ≈ 0 on a strict biological view), the overall shift in credence is small. This is the formal form of the authors' own point that the method has "substantial practical significance" only with "sufficient confidence in theories from which indicators can be derived" (p. 11). It is also the formal counterpart of the 2023 three-factor rule (p. 17 of the 2023 report).

**Step 10 — Looking ahead** (pp. 11–12). AI may help consciousness science. Applying a theory to AI can expose hidden ambiguities. Advocates of global workspace theory "might explain whether they think that the system built to implement all four GWT indicators [5], which we mentioned above, is conscious" (p. 11; ref. 5 is Dossa et al. 2024). AI systems have been used to test predictions of attention schema theory and global workspace theory (p. 11). The method could help validate other tests, but validating the method itself in AI is hard because of the gaming problem (p. 11). "Given that it may already be possible to build AI systems that possess many of the indicators, in looking ahead we should also contemplate the possibility that some near-future AI systems will be plausible candidates for consciousness." (p. 11). Future work: new arguments for or against computational functionalism; a fuller survey of existing systems — "a project that has been begun [11] but is far from being completed" (p. 12); interpretability-based tests; behavioural tests; research on valenced experience (p. 12).

**Outstanding questions box (p. 11).** How to improve the list (new theories, more operational wording, defences against small-network counterexamples and gaming). Which indicators existing systems have — "frontier generative language or multimodal models, language agents, and deep reinforcement learning agents". Quantitative or behavioural tests for "black-box" systems. The implications of "narrow biological views and IIT". Whether implementing these features helps capability, reliability or safety. How careful researchers should be to avoid building systems that may be conscious.

**Limits the authors state.** The indicators are "potential" and revisable. Theories are underspecified. Interpretability is limited. The method may leave out necessary conditions, including non-computational ones. Validation is difficult. Indicators can be gamed. The article gives no verdict on any current system.

### Section-by-section backbone

- **Abstract and Highlights (p. 1).** Urgent need for rigorous methods; derive indicators from theories to inform credences. Progress is possible because some theories, "notably including computational functionalist theories", have implications that can be checked empirically (p. 1).
- **The problem of AI consciousness (pp. 1–2).** Deep uncertainty, with some researchers holding that only living organisms can be conscious. Engineers are deliberately reproducing consciousness-linked features. Public attribution to ChatGPT and AI companions. Risks of under- and over-attribution. Tests are hard to validate. The article is about *how to assess*, not *whether possible*.
- **Box 1, Defining "consciousness" (p. 2).** Phenomenal consciousness; examples; the open question of conscious "pure thought" with no sensory side, relevant to LLMs; consciousness does not require high intelligence or human-like concerns; indeterminacy and degrees; theories of access may still inform phenomenal consciousness; under illusionism, the question becomes what gives entities the *significance* usually linked to consciousness.
- **The theory-derived indicator method; criteria for suitable theories (pp. 2–4).** Sceptics' obstacles; the two criteria; four theories that currently qualify; non-functionalist theories could in principle qualify (IIT on unconventional hardware).
- **Box 2, Computational functionalism and alternative views (p. 3).** The shared commitment; working-assumption version of the method; biological substrate views; IIT.
- **Glossary (pp. 3–4).** Defines algorithmic recurrence, computational functionalism, functionalism, indicators ("We do not claim that the indicators are individually necessary for consciousness or that any combination is sufficient."), interpretability methods, the minimal implementation problem, negative and positive indicators, sparse and smooth coding, specificity and sensitivity, valenced experience.
- **Deriving and interpreting indicators (pp. 4–5).** Narrow vs broad formulations; using several theories; indicators as credence-shifters; theory-attributable indicators and background conditions.
- **Internal and behavioral evidence (p. 5).** Internal processes decide consciousness; why behaviour misleads in AI; a supporting role for behavioural tests.
- **Box 3, The gaming problem (p. 5).** Definition; applies to behavioural and computational markers; two remedies.
- **Identifying indicator properties (pp. 5–9).** Table 1 (the 2023 list, slightly updated); Figure 1 (sketches of the six families of indicators); the four guidelines.
- **Finding indicator properties in AI systems (pp. 9–10).** Interpretability limits; RPT-2 and the Kanizsa illusion; the LLM-recurrence boundary question.
- **What does it tell us if a system possesses indicator properties? (pp. 10–11).** Bayesian framing; positive and negative indicators; specificity and sensitivity; credence relative to theories; dependencies; rival theories and unknown unknowns; conditions for practical significance.
- **Looking ahead (p. 11).** Two-way exchange with neuroscience; validation; near-future plausible candidates.
- **Concluding remarks and Outstanding questions (pp. 11–12).** Method summary; research agenda.
- **Acknowledgments, Declaration of interests, References (pp. 12–14).** Funding from Effective Ventures, the EA Long-Term Future Fund, Open Philanthropy, Templeton World Charity Foundation, ERC, UKRI, ARC and CIFAR. Declared interests: "P.B. has consulted for Anthropic and Conscium, R.L. has consulted for Anthropic, and J.B. has received research funding from Google." (p. 12). Also declared: D.C.'s paid talks to technology companies, A.C.'s consulting for Verses AI, and R.K.'s role as founder and president of Araya, Inc.

> **Reviewer's note (possible citation-numbering slip in this version).** In the running text (p. 3), the theories are cited as recurrent processing [24–26], global workspace [22,23,27,28], higher-order [29–31] and attention schema [32,33]. In Table 1 (p. 6), the same theories are cited as [24–26], [27–30], [31–33] and [34,35]. In the reference list, refs 29–30 are higher-order papers, 32–33 are attention schema papers, and 34–35 are Crick & Koch and Francken et al. The table caption also cites "[12]" (Seth & Bayne 2022) where "[11]" (the 2023 report) would be expected. From the global workspace row onward, the table's numbers appear shifted. This is a reading of the in-press file only; the final typeset version may differ.

**Field record**
- Year · community: 2025 · consciousness-science (with philosophy-of-mind and AI-and-ML authors; published in a cognitive-science journal)
- Question it asks: How should AI systems be assessed for consciousness, given deep disagreement in consciousness science?
- Position in one line: Derive indicators from credible theories that state conditions AI could meet, look for them inside systems, and update credences in a Bayesian way, while guarding against gaming, minimal implementations and missing conditions.
- Stance on computational functionalism: neutral to supportive as a working focus — "many of us are agnostic" (p. 4), but it is the focus that makes the method tractable; biological and IIT views are to be weighed in overall assessments.
- Stance on AI consciousness: no verdict on current systems; possible in principle if computational functionalism (or a suitable alternative) is true; some near-future systems may be "plausible candidates".
- What evidence or method it uses: conceptual analysis and methodology (with a formal probabilistic framing); no new assessment of systems.
- Debates it takes part in: theory-derived vs behavioural tests; gaming of indicators; the minimal implementation (small-network) problem; whether LLMs are recurrent; computational functionalism vs biological substrate views vs IIT; validating tests for consciousness.
- Builds on / argues against: builds on Butlin et al. 2023 and Bayne et al. 2024 (tests for consciousness); Birch 2022 and 2024 (theory-light approach; gaming); Pennartz et al. 2019 (indicators); Herzog et al. 2007 and Doerig et al. 2021 (small-network / minimal implementation objections); Michel & Lau 2021; Shanahan 2024; Chalmers 2024 (pure thought). Engages, without rejecting, Damasio & Damasio 2022, Aru et al. 2023, Seth 2025, and Tononi & Koch 2015 / Albantakis et al. 2023 as alternatives.
- What would show it wrong: as the authors state it — the method lacks practical significance if confidence in the source theories is too low, or if rival theories treat the indicators as evidence against consciousness (p. 11); indicators may leave out a necessary computational or non-computational condition (p. 11).
- Quotes used:
  - "In this article we focus on how to assess AI systems for consciousness, rather than on whether AI consciousness is possible at all." (p. 2)
  - "we risk causing avoidable harms to those systems, which may exist in large numbers" (p. 1)
  - "we may waste resources or risk lives trying to promote their welfare" (p. 1)
  - "clear and testable conditions that AI systems might meet" (p. 3)
  - "As we interpret them, the theories we rely on to derive indicators for consciousness share a commitment to computational functionalism." (p. 3)
  - "AI systems using non-conventional hardware might meet the conditions of integrated information theory (IIT)" (p. 3)
  - "While many of us are agnostic about computational functionalism, we agree that it provides a useful focus for assessments." (p. 4)
  - "But these views should still be considered in overall assessments of the likelihood of consciousness in AI." (p. 4)
  - "our approach is distinctive in deriving indicators from multiple theories" (p. 4)
  - "we stress that indicators are merely intended to be credence-shifting; we do not need to be certain that a theory is correct for it to provide useful indicators." (p. 4)
  - "We assume that whether a system is conscious depends on features of its internal processes." (p. 5)
  - "inferences from behavior to features of internal processes are often unreliable" (p. 5)
  - "An indicator is gamed if its presence is better explained by the fact that it makes a system seem to possess a property of interest than by the fact that the system actually possesses the property." (p. 5)
  - "the problem can also arise for computational markers" (p. 5)
  - "This is a relatively novel proposal compared to other indicators, but such a proposal is needed to begin to synthesize disparate ideas about agency" (p. 9)
  - "whether systems possess indicators can be debatable even if we understand their operation in detail and can turn on philosophical questions such as how to delineate the system in question." (p. 10)
  - "We propose a broadly Bayesian attitude to indicators." (p. 10)
  - "The absence of a sensitive indicator tells us that a system is unlikely to be conscious; this is why indicators like RPT-1, algorithmic recurrence, may be useful." (p. 10)
  - "Sets of theory-derived indicators might leave out some necessary condition for consciousness – either a further computational condition or a requirement for a non-computational feature" (p. 11)
  - "Given that it may already be possible to build AI systems that possess many of the indicators, in looking ahead we should also contemplate the possibility that some near-future AI systems will be plausible candidates for consciousness." (p. 11)
  - "P.B. has consulted for Anthropic and Conscium, R.L. has consulted for Anthropic, and J.B. has received research funding from Google." (p. 12)

---

## Cross-paper notes

### What changed from 2023 to 2025

| Aspect | 2023 report | 2025 article |
|---|---|---|
| **Format and venue** | 88-page arXiv report, not peer reviewed | 14-page peer-reviewed Opinion in *Trends in Cognitive Sciences* |
| **Authors** | 19 authors | 20 authors: the same team minus Chris Frith, plus Tim Bayne and David Chalmers (both were thanked in the 2023 acknowledgements, p. 3). Butlin and Long are now at the Global Priorities Institute (Oxford) and Eleos AI Research |
| **Main question** | Are current or near-term AI systems conscious? | How should we assess AI systems for consciousness? (explicitly *not* whether it is possible, p. 2) |
| **Method name** | "Theory-heavy approach" | "Theory-derived indicator method" — open to any theory, "including theories yet to be developed" (p. 2) |
| **Computational functionalism** | Working hypothesis; all authors find it "plausible" (p. 14) | The source theories "share a commitment" to it (p. 3), but "many of us are agnostic" (p. 4); it is a "useful focus", and one version of the method adopts it as a working assumption (p. 3) |
| **IIT** | Excluded as "not compatible with computational functionalism" (p. 5) | Could in principle meet the second criterion on unconventional hardware (p. 3); its implications are an outstanding question (p. 11) |
| **Biological views** | Named as the cost of the hypothesis being false (p. 14); listed among open questions (p. 70) | Described in their own terms in Box 2; "should still be considered in overall assessments" (p. 4) |
| **Theories that qualify** | Five theories plus agency and embodiment | Four theories (RPT, GWT, HOT, AST); predictive processing and agency/embodiment reclassified as *background conditions* |
| **Indicators** | 14 (Table 1, p. 5) | The same 14, called "Potential indicators" (Table 1, p. 6), now an *example* of the method. Wording is identical apart from American spelling ("organized", "specialized") and AE-1 relabelled "Minimal agency". Notes added (e.g. "HOT-3 is connected to PP"; PP-compatible versions of GWT and HOT). The 2023 note that both AE indicators are "also supported by midbrain and UAL theories" is no longer in the table note; midbrain theory now appears in the agency discussion (p. 9) |
| **How indicators combine** | Informal count: more is better; some combinations more compelling (p. 45) | Explicitly Bayesian: positive/negative indicators, specificity/sensitivity, credence relative to each theory, dependencies, unknown unknowns (pp. 10–11) |
| **New concepts** | — | Narrow vs broad theory formulations; four derivation guidelines; the minimal implementation problem; gaming of *computational* indicators (Box 3); illusionist reframing (Box 1) |
| **Behavioural tests** | Rejected for now as gameable; worth further research (pp. 18, 69) | Still distrusted, but given a supporting role as evidence for indicators (e.g. the Kanizsa illusion, p. 10) |
| **Large language models** | "Transformers are not recurrent" (p. 59); weak case for GWT indicators | Whether LLMs are recurrent "depends on where we draw the boundaries of the system" — the context-window feedback loop (p. 10). No verdict |
| **Verdict on existing systems** | No current system is a strong candidate; case studies of six kinds of systems | No verdicts; a survey of existing systems is "begun [11] but is far from being completed" (p. 12) |
| **Outlook** | Conscious AI "could realistically be built in the near term" if computational functionalism is true (p. 6) | "some near-future AI systems will be plausible candidates for consciousness" should be contemplated (p. 11) |
| **Ethics** | Risks of under- and over-attribution set out at length; others' policy proposals listed, not assessed (pp. 64–68) | Both risks stated briefly; need for "a principled basis" for regulation (p. 1); research ethics as an outstanding question |
| **Declared interests** | "no conflicts of interest to report" (p. 3) | Consulting for Anthropic (P.B., R.L.), Conscium (P.B.) and Verses AI (A.C.); Google research funding (J.B.); and others (p. 12) |
| **Tone** | Report with conclusions about named systems | More cautious, method-only, with more stress on uncertainty and revisability |

### What the 2025 paper keeps, drops and adds — in short

- **Keeps:** the core idea (theory-derived indicators, more is better); the exact 14 indicators; the preference for internal evidence over behaviour; the two-sided risk framing; valence as a research priority; the interpretive and interpretability difficulties (2023's first two "lessons", p. 47, become 2025's two challenges, pp. 9–10).
- **Drops:** the case-study verdicts on Transformers, Perceiver, PaLM-E, the virtual rodent and AdA; the long discussion of capabilities and existential risk; the recommendations section; the exclusion of IIT; the shared statement that computational functionalism is "plausible".
- **Adds:** a probabilistic model of what indicators mean; guidelines for deriving indicators; the minimal implementation problem; gaming of computational indicators; an explicit place for biological substrate views and IIT in the final credence; an acknowledgement that LLM recurrence is debatable; a research link back to neuroscience (AI as a test bed for theories).

### How both papers relate to the computational-functionalism assumption

Both papers make the assumption explicit and say what depends on it. Neither argues for it at length. The 2023 report gives one supporting argument in a footnote, the gradual replacement of neurons by functionally equivalent prostheses (p. 14, n. 4). The 2025 article leaves the question to "new arguments for or against computational functionalism" (p. 12).

What changes is how the assumption is used. In 2023 it is a gate: theories that deny it (IIT) are left out, and the conclusions are stated conditionally ("if computational functionalism is true", p. 6). In 2025 it is one weight in a mixture. The indicators are evidence *relative to* the computational-functionalist theories, and the final credence must also include biological and IIT views and unknown unknowns (pp. 4, 10–11). The 2025 framing therefore lets a reader who rejects computational functionalism still use the method: such a reader gives the indicators little weight in the final credence, rather than rejecting the method outright. This places the 2025 article closer to the critics in this corpus (Aru et al. 2023; Seth 2025; Damasio & Damasio 2022 — all cited by it as refs 1–3) without accepting their conclusions.

> **Reviewer's note — links to the rest of this topic.** The 2025 article cites five other papers in this topic's corpus: Damasio & Damasio 2022, Bayne et al. 2024 (tests for consciousness — the validation problem the 2025 article relies on), Sebo & Long (moral consideration by 2030 — the under-attribution risk), and Aru et al. 2023 and Seth 2025 (biological views). The synthesis page may want to treat the move from 2023 to 2025 as a response to these critics. The 2025 text itself does not say this, so it should be presented as an interpretation.

> **Reviewer's note — relevance to this project (labelled interpretation, not the authors' claim).** This project trains reinforcement-learning agents with recurrent policies in a grid world, and the agents receive a damage signal (nociception). On the 2023 report's own terms, two indicators are relevant to such agents: RPT-1 (algorithmic recurrence, which the report says existing systems "clearly" meet, p. 6) and AE-1 (agency — "It is trained by RL, which is sufficient for agency", p. 62). AE-2 (embodiment) would be the open question. As the report says of the virtual rodent, it depends on whether the agent has learned a model of how its actions change its inputs, and that needs interpretability tools to settle (p. 47). Both papers stress three points that matter for any "pain-like" claim this project makes. The indicators concern *consciousness in general*, not valence. Theories of valenced experience are "less mature" (2023, p. 65). And the 2023 report says that some common indicators may be necessary while adding little on their own (p. 45); RPT-1 is one of the examples it names. No claim about this project's agents should be read off these papers without that caveat.
