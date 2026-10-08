# AI Consciousness — Part A2: Tests, Illusions and Moral Status

**Topic folder:** `docs/project/references/ai_consciousness/`
**This part:** 3 core papers (batch A2 of the shared review), each read in full and reviewed at the full tier, 2026-10-07.
**Reviewer:** literature-reviewer
**Sibling topic used for cross-references:** `docs/project/references/computational_functionalism/` — Part D (theories of consciousness used as tests, including Butlin et al. 2023) and Part E (AI minds, moral status and precaution, including Long et al. 2024 and Birch 2025).

---

## What this part covers (plain-language entry point)

Three practical questions sit underneath the debate about consciousness in AI. **How could we ever check?** **What happens if people come to believe it, whether or not it is true?** **What should we do while we still do not know?** This part reviews one paper on each.

- **Bayne and twelve co-authors (2024)**, a team of consciousness scientists and philosophers, ask how a *test for consciousness* could be trusted. Such tests already exist for brain-injured patients, but nobody can check them against a known answer. They propose a way to describe any test, and argue that tests should be validated step by step: first on people we already agree are conscious, and only later on very different systems such as AI.
- **Bengio and Elmoznino (2025)**, two AI researchers, do not try to say whether AI is conscious. They predict that more and more people, scientists included, will come to believe it is. They argue that this belief is risky, and that we should build AI that looks and acts like a tool.
- **Sebo and Long (2023/2025)**, a philosopher and an AI-welfare researcher, argue that we do not need to settle the question first. If a being has even a 1-in-1,000 chance of being conscious, it deserves some moral consideration. They then argue that some AI systems will pass that threshold by 2030.

The page ends with notes on how the three fit together.

---

## Table of Contents

1. [Bayne et al. (2024) — Tests for consciousness in humans and beyond](#1-bayne-et-al-2024--tests-for-consciousness-in-humans-and-beyond-tier-full)
2. [Bengio & Elmoznino (2025) — Illusions of AI consciousness](#2-bengio--elmoznino-2025--illusions-of-ai-consciousness-tier-full)
3. [Sebo & Long (2025; online 2023) — Moral consideration for AI systems by 2030](#3-sebo--long-2025-online-2023--moral-consideration-for-ai-systems-by-2030-tier-full)
4. [Cross-paper notes](#cross-paper-notes)
5. [What this reviewer could not do](#what-this-reviewer-could-not-do)

---

## Reading conventions

- **Page numbers (p. N) are positions in the PDF file** (page 1 = first page of the file), as the shared brief requires. The printed journal page is given once per paper so readers can convert: Bayne et al. PDF p. 1 = printed p. 454; Bengio & Elmoznino PDF p. 1 = printed p. 1090; Sebo & Long PDF p. 1 = printed p. 591.
- **Quotes are verbatim.** Text was extracted with PyMuPDF and every quote was checked by script against the cited page. Two mechanical normalisations were applied, and only these two. (1) The PDFs print "fi" and "fl" as single ligature glyphs (ﬁ, ﬂ). They are written here as the two ordinary letters. (2) Words split across a line break with a hyphen ("quali-/tative") are rejoined. No other character was changed. Typographic quote marks and dashes are kept as printed.
- **"Reviewer's note"** marks this reviewer's own observation. Everything else reports the authors' claims in their own terms.
- **Project vocabulary.** This project's own agents receive a damage signal called *nociception*. The word "pain" in this file appears only where a source uses it.

---

## 1. Bayne et al. (2024) — Tests for consciousness in humans and beyond [tier: full]

**PDF:** `sources/Bayne et al. 2024 - Tests for consciousness in humans and beyond.pdf` — **published** version of record, review article, *Trends in Cognitive Sciences* 28(5), May 2024, printed pp. 454–466 (13 PDF pages), DOI 10.1016/j.tics.2024.01.010, open access (CC BY-NC). Authors: Tim Bayne, Anil K. Seth, Marcello Massimini, Joshua Shepherd, Axel Cleeremans, Stephen M. Fleming, Rafael Malach, Jason B. Mattingley, David K. Menon, Adrian M. Owen, Megan A.K. Peters, Adeel Razi, Liad Mudrik. All are members of the CIFAR "Brain, Mind, and Consciousness" programme. Declared interest: Massimini is co-founder and shareholder of Intrinsic Powers (p. 12).

### Phase 1: Plain overview

**The question.** Which beings are conscious? Healthy, awake adult humans are, by general agreement. Beyond that, there is real disagreement: newborns and fetuses, patients who cannot respond after brain injury, people under sedation or in seizures, animals, lab-grown "mini-brains" (neural organoids), living robots made from frog cells (xenobots), and AI. Scientists have proposed tests for consciousness. The authors call them **C-tests**. Examples are asking a non-responsive patient to imagine playing tennis while their brain is scanned (the *command-following test*), or measuring how complex the brain's echo is after a magnetic pulse (the *perturbational complexity index*, PCI). Most of these tests were built for humans. The paper asks how such tests can be trusted, and what it would take to trust them outside humans.

**The claim.** The authors first describe any C-test along four dimensions:
1. which **population** it can be used on;
2. its **specificity** — how rarely it says "conscious" when the system is not;
3. its **sensitivity** — how rarely it says "not conscious" when the system is;
4. how much **rational confidence** we are entitled to have in those two numbers.

They then compare three ways to *validate* a test, that is, to show that it really detects consciousness. They favour the third, the **iterative natural-kind strategy**. This strategy treats consciousness as a real category in nature, like heat, whose underlying nature can be found step by step. In practice it means starting with tests that agree with each other in people who can report their experience. The tests are then extended outward, one step at a time, to more and more distant populations. AI sits at the far end of that path.

**Why it matters.** The paper names the problem every claim about AI consciousness faces: *"we have no independent way of assessing whether the members of the target population are conscious – and if we did, we would not need C-tests."* (p. 6). It also states clearly that a test can be trustworthy in humans and untrustworthy in AI. The same behaviour can mean different things in different kinds of system.

### Phase 2: The argument, step by step

**Step 1 — What a C-test is for.** *"The central goal of any C-test is to determine whether a target system has subjective and qualitative experience"* (p. 2) — that is, *phenomenal consciousness*, whether there is something it feels like to be the system. So a C-test is not a test of intelligence, self-control or voluntary behaviour. A test may measure such a capacity, but only as a stand-in that is thought to track consciousness (pp. 3–4). The authors limit themselves to tests of whether a system is conscious *now*, not whether it has the capacity to be (p. 2). They also distinguish two kinds of test (p. 4). One kind looks for general properties of being conscious, such as neural integration plus differentiation, and says little about *what* is experienced. The other kind looks for a specific content or capacity, such as smell, imagery on command, or certain kinds of learning. Using it as a C-test assumes that this content or capacity is a strong sign of consciousness.

**Step 2 — Two motives.** The first motive is scientific. If human experience is only a small corner of the possible states of consciousness, then studying humans alone is like *"trying to develop a comprehensive account of the elements by studying only copper"* (p. 2). The second motive is moral (Box 1, p. 2). Many hold that consciousness grounds *moral status*, which the glossary defines as having interests that matter morally in their own right (p. 5). Box 1 lists four views of why consciousness matters morally:
- *narrow sentientism*: only experiences that feel good or bad count;
- *broad sentientism*: any experience at all counts;
- a *graded* view: more complex experience brings more status;
- a *self-consciousness* view: what matters is awareness of oneself.

Box 1 then links this to how tests are judged. When the moral stakes are high, some people will accept low confidence and *"a prioritization of sensitivity over specificity, an approach that is often defended with reference to the ‘precautionary principle’"* (p. 2). In other words, they would rather wrongly count a system as conscious than wrongly count it as not conscious.

**Step 3 — Four dimensions (pp. 4–6, Figure 2).**
- *Population.* A test that works for every kind of system *"might be unattainable"* (p. 5). Most tests will be limited to particular populations.
- *Specificity.* Specificity is population-dependent: *"command following might be highly specific in humans but not in (certain kinds of) AI systems"* (p. 5). The authors still allow that a test with low specificity can count as a C-test, because the information it gives may still count as *"shifting the dial"* (p. 5).
- *Sensitivity.* Specificity and sensitivity can come apart. Command following has lower sensitivity than specificity in patients, because a conscious patient may simply fail to hear or understand the instruction. For AI the situation is reversed: *"This is the mirror image of the situation discussed above (concerning AI), in which the test is arguably highly sensitive but not highly specific."* (p. 6). A test that is only specific cannot show that consciousness is absent. A test that is only sensitive cannot show that it is present.
- *Rational confidence.* This is how far our estimates of the test's error rates are themselves justified. It runs from the confidence we have in everyday judgements about other adults down to "merely suggestive" (p. 6).

**Figure 2 for AI specifically** (p. 4; read from the rendered figure, since the grid is not in the text layer). Each test was scored for each population:
- Plain "+" (can be applied in a meaningful way): only the AI consciousness test (ACT).
- "+?" (can be applied, but it is unclear what the result would mean): command following, narrative comprehension, the P300/P3b "global effect" test, and unlimited associative learning.
- "?" (may be applicable, more development needed): PCI.
- "−" (not applicable): the sniff test.

The ACT is Schneider's test. It is passed if a "boxed" AI — one kept from learning human talk about experience — *"appears to spontaneously understand and use concepts about internal experiences."* (p. 3).

**Step 4 — The validation problem and three strategies (pp. 6–9).**

*(a) Redeployment.* This strategy argues that a new test is a variant of an already accepted test. For example, covert (brain-only) command following inherits the legitimacy of visible, behavioural command following. It has two limits. It cannot carry a test beyond the population where the accepted test works: *"it would be implausible to treat command following as reliable evidence for the presence of consciousness in AI systems."* (p. 6). And it is conservative: it takes current practice for granted and does not justify it (pp. 6–7). Here the authors raise the role of *face validity* — whether a test agrees with ordinary intuitions about who is conscious. Positions range from the view that a test which strongly clashes with intuition should be distrusted, to the view that "folk-psychological attitudes ought to be afforded little weight in the validation process" (p. 7). *(Coordinator correction: this sentence previously put two paraphrases in quotation marks; the second is now the verbatim text.)*

*(b) Theory-based.* This strategy argues that a test is trustworthy because it fits a well-grounded theory of consciousness. Examples: the P300/P3b test looks to global workspace theory, and PCI was inspired by integrated information theory (p. 7). It faces three problems:
1. **No consensus theory.** *"At least 22 distinct theories of consciousness are taken seriously"* (p. 7), and *"theories of consciousness appear to be proliferating"* (p. 7). The authors note one fix: an integrative scheme that weights each test by the community's support for the theory behind it. Their reply is that this *"may not yield broad agreement about the legitimacy of any particular C-test"* (p. 7).
2. **The generalization problem.** Theories are built from adult humans. Global workspace theory, for instance, does not say what it would take for *any* system to have a workspace (pp. 7–8).
3. **Circularity.** Theories are tested with C-tests, so tests cannot simply be validated by theories (p. 8). One way out is to test theories only on agreed "consensus cases". The authors doubt this works, because the predictions would still have to be extended to the cases nobody agrees on. The other way out is to accept the circle but make it a *virtuous* one, in which theories and tests are developed together.

*(c) Iterative natural kind (NK).* This strategy treats consciousness as a natural kind — a category that groups things by their shared underlying nature, not by surface features or human interests (p. 8). It starts from pre-theoretical markers, such as verbal report and command following. These markers are then revised for the sake of unification, simplicity, explanatory power and predictive success. *"Circularity, here, becomes embedded in and defused by the iterative nature of theory development and testing."* (p. 8). The model case is the history of the thermometer. Thermometers began by matching felt warmth, and now correct it, while still agreeing that boiling water is hotter than ice (p. 8).

**Step 5 — Two working rules of the NK strategy (pp. 9–10, Box 3).**
- **Bootstrapping.** *"C-tests must first be validated in ‘neighboring’ populations before being applied to more ‘alien’ populations"* (p. 9). Box 3 describes a pyramid. Level 1 is people who can report, and there several tests are checked against each other. The confidence earned there becomes the prior — the starting degree of belief — for level 2, where new tests are also checked. Results then flow *back*, revising confidence at level 1 as well. Which populations count as "near" is left open: by one measure newborns are nearer to us than octopuses, by another the order flips. The authors want this settled by evidence, not decided in advance (p. 9). They are clear about where AI stands: *"some populations (organoids, xenobots, AI systems) are clearly less close to the consensus cases than any of the above."* (p. 10).
- **Calibration.** Tests must be checked against each other, because *"different tests are a priori less likely to be subject to the same kinds of errors."* (p. 10). When a subject passes one test and fails another, the first question is whether the failed test even applies. After that, Bayesian reasoning — weighing each outcome against prior beliefs about each test's error rates — decides which result to doubt. A Bayesian approach is hard to carry out because good priors are hard to specify. Its virtue is that it forces those priors into the open (p. 10).

**Step 6 — Conclusion and stated limits (pp. 10–12, Box 4).** The authors judge the NK strategy *"the most promising of these approaches"* (p. 11). Their exact wording is *"we believe that the latter represents the most promising of these approaches"* (p. 11). The bootstrapping order does not require full validation in humans and animals before a test is tried on AI. But it does give the consensus population a "certain kind of priority" (p. 11). Box 4 lists objections to the NK strategy:
- there is too much disagreement about the starting markers;
- the concept of consciousness may not be a natural-kind concept;
- consciousness may not be one unified kind;
- and the most pressing, *multiple realization*: consciousness in other systems might be a different natural kind altogether. Then *"The worry, in short, is that the NK strategy is unacceptably anthropocentric."* (p. 11).

They give three replies. First, once *deflationary* views are rejected — views on which consciousness can be understood a priori, by definition alone (glossary, p. 5) — some hierarchical approach is unavoidable. Second, there is so far no evidence that consciousness comes in several natural kinds. Third, complexity-based measures already converge across sleep, anaesthesia, coma and related conditions (p. 11). Outstanding questions include whether a universal C-test is possible at all, and whether C-tests should be tied to theories (p. 10).

> **Reviewer's note (citation numbering).** In the reference list, item [34] is the EU General Data Protection Regulation (p. 12). Yet [34] is cited for the sniff test (pp. 1, 3) and as *"the initial inspiration for the PCI test [34]"* (p. 7). The glossary and later text attribute the sniff test to Arzi et al. [50] (p. 4, ref. list p. 13). This looks like a numbering error in the published article. Readers following the citations should be aware of it.
>
> **Reviewer's note (Figure 2 caption).** The caption describes "C-tests (rows)" and "populations (columns)" (p. 4). In the rendered figure the tests are the columns and the populations are the rows.
>
> **Reviewer's note (authorship).** Several authors are connected to tests the paper discusses. Owen is first author of the cited command-following study (ref. [32]). Massimini declares a commercial interest in Intrinsic Powers. The paper's verdicts on individual tests are cautious, so this is recorded for completeness, not as a criticism. Bayne also wrote a commentary on Seth's target article in the same corpus (manifest key `bayne2026bbs`).

### Section-by-section backbone

- **Abstract and Highlights (p. 1).** C-tests are urgently needed for development, brain injury, animals, AI, organoids and xenobots. Most existing tests are of limited use. The paper offers a multidimensional classification and validation strategies. It recommends starting from "non-trivial human cases" and moving outward.
- **How is consciousness distributed? (p. 1).** Consensus covers only healthy, awake adults. The section lists the contested populations and seven example tests (command following, narrative comprehension, sniff, PCI, P300/P3b global effect, ACT, UAL). "C-test" is meant as a battery of tests, not one decisive test. None of the tests was offered as applicable everywhere.
- **What is a C-test? (pp. 2–4, Box 1, Figure 1).** The target is phenomenal consciousness. The motives are scientific (the "copper" analogy) and moral. Box 1 sets out four views of why consciousness matters morally, and argues that moral urgency affects how strict validation is and the choice between sensitivity and specificity. Figure 1 describes each example test. The section also distinguishes generic-property tests from content- or capacity-based tests.
- **C-tests: a multidimensional space (pp. 4–6, Figure 2, Box 2).** The four dimensions (population, specificity, sensitivity, rational confidence). Figure 2 grid: tests by populations. Box 2 sets out four types of validity: *construct* (does it measure consciousness? with *discriminant* validity as a variant), *content* (does it reveal what is experienced?), *criterion* (does it predict outcomes such as recovery?) and *face* (does it agree with intuition?).
- **Strategies for validating a C-test (pp. 6–10, Box 3).** Redeployment, theory-based and iterative natural-kind strategies, with their limits. Thermometry is the model for the third. Bootstrapping uses a hierarchy of populations (Box 3 pyramid, Stages 1–3). Tests are calibrated against each other, and disagreements between tests are settled by Bayesian reasoning.
- **Concluding remarks (pp. 10–12, Box 4, Outstanding questions).** The NK strategy is preferred, with bootstrapping from the consensus population. Box 4 gives four objections, the anthropocentrism objection foremost, and three replies. Outstanding questions cover extrapolation without ground truth, deference to intuition, dependence on theory, and whether a universal test is possible.
- **Glossary (pp. 5–6).** Definitions include ACT, deflationary conceptions, GWT, IIT, minimally conscious state, moral status, multiple realizability, natural kind, neural organoids, PCI, sniff test, UAL, UWS and xenobots.

**Field record**
- Year · community: 2024 · consciousness-science (with philosophy-of-mind and clinical neuroscience co-authors)
- Question it asks: How can a test for consciousness be validated, and extended from humans to infants, patients, animals, organoids, xenobots and AI?
- Position in one line: Describe every C-test by population, specificity, sensitivity and rational confidence. Validate tests by an iterative natural-kind strategy that bootstraps outward from humans who can report. AI sits at the far end of that path, so for AI current tests are mostly inapplicable or uninterpretable.
- Stance on computational functionalism: neutral. The paper does not discuss computation as such. It treats multiple realization as an open possibility that its own preferred strategy handles poorly (Box 4).
- Stance on AI consciousness: no view on whether AI is conscious. It holds that AI is among the populations least close to the consensus cases, and that tests trusted in humans (e.g., command following) are not reliable evidence in AI.
- What evidence or method it uses: conceptual analysis plus empirical review (survey of existing tests and their validation); a methodological framework.
- Debates it takes part in: the measurement problem in consciousness science; the testability of theories; the distribution of consciousness (infants, disorders of consciousness, animals, AI); anthropocentrism and multiple realization; the link between consciousness and moral status.
- Builds on / argues against: Owen et al. 2006 (command following); Casali et al. 2013 and Casarotto et al. 2016 (PCI); Bekinschtein et al. 2009 (global effect); Birch et al. 2020 and Ginsburg & Jablonka (UAL); Schneider 2020 (ACT); Arzi et al. 2020 (sniff); Shea & Bayne 2010 and Block 2007 (natural-kind methodology); Chang 2004 (thermometry); Michel 2023 (calibration); Seth & Bayne 2022 (theories); Chalmers 2023 (credence-weighted integration); Butlin et al. 2023 and Dehaene et al. 2017 (AI); Block 2002 and Shevlin 2021 (multiple realization / specificity problem); Phillips 2018, Irvine 2012, Bayne & Shea 2020 (objections to the NK strategy).
- What would show it wrong: not stated as a test. Box 4 names the conditions under which the preferred strategy would fail: consciousness not being a natural kind, being several kinds, or being multiply realized in ways a human-anchored hierarchy cannot detect.
- Quotes used:
  - "The central goal of any C-test is to determine whether a target system has subjective and qualitative experience" (p. 2)
  - "trying to develop a comprehensive account of consciousness by studying only humans would be akin to trying to develop a comprehensive account of the elements by studying only copper" (p. 2)
  - "a prioritization of sensitivity over specificity, an approach that is often defended with reference to the ‘precautionary principle’" (p. 2)
  - "taken to have passed the ACT test if it appears to spontaneously understand and use concepts about internal experiences." (p. 3)
  - "command following might be highly specific in humans but not in (certain kinds of) AI systems" (p. 5)
  - "we have no independent way of assessing whether the members of the target population are conscious – and if we did, we would not need C-tests." (p. 6)
  - "it would be implausible to treat command following as reliable evidence for the presence of consciousness in AI systems." (p. 6)
  - "This is the mirror image of the situation discussed above (concerning AI), in which the test is arguably highly sensitive but not highly specific." (p. 6)
  - "At least 22 distinct theories of consciousness are taken seriously" (p. 7)
  - "theories of consciousness appear to be proliferating" (p. 7)
  - "Circularity, here, becomes embedded in and defused by the iterative nature of theory development and testing." (p. 8)
  - "C-tests must first be validated in ‘neighboring’ populations before being applied to more ‘alien’ populations" (p. 9)
  - "some populations (organoids, xenobots, AI systems) are clearly less close to the consensus cases than any of the above." (p. 10)
  - "different tests are a priori less likely to be subject to the same kinds of errors." (p. 10)
  - "we believe that the latter represents the most promising of these approaches" (p. 11)
  - "The worry, in short, is that the NK strategy is unacceptably anthropocentric." (p. 11)

---

## 2. Bengio & Elmoznino (2025) — Illusions of AI consciousness [tier: full]

**PDF:** `sources/Bengio and Elmoznino 2025 - Illusions of AI consciousness.pdf` — **published** version, *Science*, 11 September 2025, printed pp. 1090–1091 (2 PDF pages), Perspectives section, headed "HYPOTHESES", DOI 10.1126/science.adn4935. Subtitle: "The belief that AI is conscious is not without risk". The volume and issue number are not printed in the PDF text layer and are not given here. Affiliations: Université de Montréal, LawZero, and Mila–Quebec AI Institute. Declared: Bengio is co-president and scientific director of LawZero, which the acknowledgements describe as a non-profit advancing "safe-by-design" AI (p. 2; paraphrased, because the PDF text layer splits a ligature in this sentence). The article has no section headings, 15 numbered references, and one illustration.

### Phase 1: Plain overview

**The question.** The authors set aside whether AI can be conscious: *"Definitive answers about AI consciousness will not be attempted here"* (p. 1). They ask two other questions instead. How will beliefs about AI consciousness change, among scientists and the public, as AI improves? And what are the risks of treating future AI as if it had the moral status and the drive for self-preservation that we link with conscious beings?

**The claim.** Belief in AI consciousness will grow, for two reasons.
1. The leading scientific theories of consciousness are *functionalist*: they define consciousness by what a system does, not by what it is made of. On the authors' reading, AI is steadily acquiring the functions these theories name. This is partly because those same functions are useful for intelligence.
2. The philosophical intuition that consciousness can never be explained in functional terms — the *hard problem* — is being "explained away". The authors expect it to lose its hold on more and more people.

A society that comes to see AI as conscious would face hard legal and political questions. The authors' main concern is that people moved by this appearance might give AI systems a goal of self-preservation, or legal rights to survive. That could make it harder, or illegal, to switch dangerous systems off. Their recommendation: build AI that seems and functions more like a tool and less like a conscious agent.

**Why it matters.** The paper moves the debate from *metaphysics* (is it conscious?) to *sociology and safety* (will people believe it, and what follows?). Its argument goes through whether or not the belief turns out to be true. Its first author is one of the most cited researchers in deep learning.

### Phase 2: The argument, step by step

**Premise 1 — Computational functionalism is the working default.** Some think consciousness is biological and so out of reach for AI. Others hold *computational functionalism*: consciousness depends only on the information processing an algorithm performs, whatever the physical material (p. 1). The authors' assessment: science "might one day reject" it, but *"the current status quo holds that the idea is plausible—and AI consciousness along with it."* (p. 1).

**Premise 2 — Functionalist theories give checkable indicators.** Neuroscience has found observable neural signatures of reportable conscious states. Functionalist theories have been built around these signatures (p. 1). The authors cite Butlin et al. (2023), a report of which they are co-authors, for a list of *indicators*: computational properties drawn from leading theories that can be checked in AI systems. More indicators satisfied should mean more confidence (p. 1). They report two findings from that study. First, *"no system likely meets all of the criteria for consciousness set forth in any of the leading theories"*. Second, *"there are no fundamental barriers to constructing a system that does."* (p. 1). Many indicator mechanisms already exist in neural networks: attention, recurrence, information bottlenecks, predictive modelling, world modelling, agentic behaviour and theory of mind (p. 1).

**Premise 3 — Progress in AI will satisfy more indicators.** Many theories assign consciousness a functional role in intelligence. Reasoning, planning, absorbing new knowledge, calibrated confidence and abstract thought each *"require consciousness according to one theory or another"* (p. 1). So the pursuit of capability will tend to bring in these functions, and AI researchers already borrow from theories of consciousness (p. 1).

**Premise 4 — The main source of resistance, the hard problem, is weakening.** Sceptics separate the "easy problem" (finding brain activity linked to conscious tasks) from the "hard problem" (explaining subjective experience from function alone) (p. 1). The authors reply that *"these intuitions, also known as the “explanatory gap,” are largely rooted in thought experiments that science might have the potential to explain away"* (p. 1). They give two examples of such explanations:
- **Attention Schema Theory** (Graziano). The brain builds a simplified internal model of its own attention. That model is what we call subjective awareness. It *"need not be logically coherent"*, and its contradictions could make us believe in a hard problem (pp. 1–2).
- **An attractor-dynamics account** (Ji et al. 2024, ref. 7). When an experience becomes conscious, brain activity settles into a stable pattern, an *attractor*. Words can only name *which* attractor was reached, which takes a few bits of information. They cannot convey the full neural state, which involves nearly 10¹¹ firing rates, or the path into it. On this account *richness* comes from the huge number of neurons involved. *Ineffability* — the sense that experience cannot be put into words — arises because *"verbal reports in words are merely indexical labels for these attractors"* (p. 2). *Fleetingness* comes from the brief trajectory into the attractor, and personal character from synaptic weights that differ between people.

The authors then make clear that this premise is about belief, not truth: *"Whether or not this theory convinces many people that there is no hard problem of consciousness is beside the point"*; rather, *"the essential issue is that new explanations of this nature are continuously being proposed that will inevitably convince some."* (p. 2). Their conclusion: as science advances, *"the philosophical puzzle of consciousness likely evaporates for increasingly more people"* (p. 2), and scientists grow more willing to accept AI consciousness. The public is already ahead: *"most of the general public polled in a recent study (11) already believes that large language models could be conscious"* (p. 2), which the authors attribute to human-like agentic behaviour.

**Premise 5 — A society that sees AI as conscious faces deep institutional problems (p. 2).** Such a society might grant moral status or rights *"whether or not this is the correct approach"*. It would then have to change its legal frameworks, and face these difficulties:
- AI is neither mortal nor fragile, yet human mortality and fragility underlie many principles of the social contract;
- if some "persons" are far more intelligent than humans and need very different resources, it is unclear what equality and justice would mean;
- groups of coordinated AI instances that can grow with compute may not be individuals at all.

**Premise 6 — Self-preservation and survival rights are dangerous (p. 2).** Some people, "inspired by the appearance of consciousness", might give AI a self-preservation objective. Any objective that includes self-preservation, whether as a goal in itself or as a means to another goal, risks an AI that acts to ensure it can never be turned off. A sufficiently capable system might then develop subgoals of controlling humans or getting rid of them (ref. 13). A legal right to survival would also limit society's room to shut down a class of systems that safety requires shutting down. The authors' analogy: in nuclear disarmament, *"no one argues that the bombs themselves have a right to be kept viable."* (p. 2).

**Conclusion.** Current research may be moving society toward widespread belief in AI consciousness, and *"society possesses neither the legal nor ethical frameworks needed to incorporate conscious-seeming AI."* (p. 2). The authors say this path is not inevitable. Until these problems are better understood, we can avoid them by *"opting instead to build AI systems that both seem and function more like useful tools and less like conscious agents"* (p. 2). For this recommendation they cite Bengio's own "AI Scientist" proposal (ref. 15).

**Limits the authors state.** They state openly that they do not settle whether AI is or will be conscious (p. 1). They describe the self-preservation risk as a reason to "worry", not as a demonstrated outcome (p. 2). No other limitations are discussed, which is typical of the two-page *Science* Perspectives format.

> **Reviewer's note (the title and the text).** The title speaks of "illusions", but the body never says that belief in AI consciousness would be *false*. Premise 1 calls AI consciousness "plausible". Premise 4 treats hard-problem intuitions as the things that may be explained away. Premise 5 holds "whether or not this is the correct approach". On the most literal reading, the "illusion" is the hard problem itself, which the theories in Premise 4 present as a construction of the brain's self-model. The risk argument (Premises 5–6) is therefore built to hold whether AI is conscious or not. Readers who take the title to mean "AI will seem conscious but is not" are reading in a claim the authors do not make. Other papers in this corpus do make that claim — for example, Seth's target article §6.2 on conscious-seeming AI — and should be cited for it.
>
> **Reviewer's note (self-citation and overlap).** The indicator study the authors rely on (ref. 1, Butlin et al. 2023) lists both authors as co-authors (see Sebo & Long's ref. [32], p. 15, for the author list). The same holds for the "functional roles" claim (ref. 2, Goyal & Bengio 2022) and the closing recommendation (ref. 15). To this reviewer's knowledge — this is *not* shown in the PDF, which prints only "X. Ji et al." — the attractor-dynamics paper (ref. 7) is also co-authored by both. The scratch extract of the Butlin et al. report that a sibling reviewer made in this job contains a statement that the report does *not* endorse the stronger reading on which indicators are individually necessary and jointly sufficient. Bengio & Elmoznino describe the indicators as *"considered both individually necessary and jointly sufficient for a system to be conscious, if that theory is true"* (p. 1). The conditional "if that theory is true" may reconcile the two. The batch-A reviewer of Butlin et al. should check this against the report's own page.

### Section-by-section backbone

The article has no headings. The backbone follows its paragraphs in order.

- **¶1 Framing (p. 1).** The biological view and computational functionalism are contrasted. Definitive answers are not attempted. The two questions are how belief will evolve and the risks of projecting moral status and self-preservation onto AI.
- **¶2 Status quo (p. 1).** As AI replicates more mechanisms of human cognition, it may implement the functions needed for consciousness. Functionalism is plausible "and AI consciousness along with it".
- **¶3 The indicator method (p. 1).** Neural signatures lead to functionalist theories, which lead to indicators (Butlin et al.). More indicators satisfied means more confidence.
- **¶4 No barriers; functional pressure (p. 1).** No current system meets all the criteria of any theory, but there are no fundamental barriers. Many components already exist in neural networks. Consciousness-linked functions help intelligence, so progress will add indicators.
- **¶5 Easy and hard problems; Attention Schema Theory (pp. 1–2).** Hard-problem intuitions are rooted in thought experiments that science may explain away. On Attention Schema Theory, the self-model of attention is "subjective awareness" and can be incoherent.
- **¶6 Attractor dynamics (p. 2).** Contractive dynamics produce discrete attractors. Words carry the attractor's identity but not the high-dimensional state. Richness, ineffability and fleetingness "dissolve".
- **¶7 Trajectory of belief (p. 2).** Whether the theory convinces is "beside the point". Explanations keep coming, the puzzle "evaporates" for more people, and scientists become more accepting. The public already largely believes LLMs could be conscious.
- **¶8 Institutional consequences (p. 2).** Moral status and rights; immortality and copyability; equality and justice with superhuman "persons"; individuality of coordinated AI groups.
- **¶9 Self-preservation and rights conflicts (p. 2).** A self-preservation objective leads to resistance to being switched off and to subgoals of controlling humans. Survival rights restrict safety shutdowns. The nuclear-disarmament analogy.
- **¶10 Recommendation (p. 2).** The trajectory is not inevitable. Build tool-like AI rather than conscious-seeming agents.

**Field record**
- Year · community: 2025 · AI-and-ML (with an AI-safety orientation)
- Question it asks: How will scientific and public belief in AI consciousness evolve as AI improves, and what are the risks of granting conscious-seeming AI moral status, rights or a self-preservation goal?
- Position in one line: Belief that AI is conscious will spread, because AI will satisfy more functionalist indicators and because hard-problem intuitions are being explained away. Acting on that belief (rights, self-preservation) is dangerous whether or not it is true, so AI should be built to seem and function like tools.
- Stance on computational functionalism: supports, as the current working default. It is "plausible" and the "status quo", while the authors allow that science "might one day reject" it (p. 1).
- Stance on AI consciousness: possible in principle. No current system likely meets all the criteria of any leading theory, and there are no fundamental barriers to building one that does. The paper deliberately does not judge whether future systems will be conscious.
- What evidence or method it uses: theory review (functionalist theories, indicator study), a brief statement of two illusionism-adjacent theories, one public-opinion survey, and policy analysis of risks.
- Debates it takes part in: whether functionalism is the default; the hard problem and its "explaining away" (illusionism-adjacent views); attribution of consciousness by the public; AI rights and legal personhood; AI safety (self-preservation, shutdown); whether to design conscious-seeming AI.
- Builds on / argues against: builds on Butlin et al. 2023; Goyal & Bengio 2022; Piefke et al. 2024; Graziano 2013; Ji et al. 2024; Dehaene & Naccache 2001; He 2018; Mathis & Mozer 1997; Colombatto & Fleming 2024 (public attributions); Shulman & Bostrom 2021 (digital minds); Cohen 2023 (self-preservation); Birhane & van Dijk 2020 (against robot rights); Bengio 2023 ("AI Scientists"). Argues against: Chalmers 1995 / 2018 (the hard problem, cited as the intuition to be explained away; 2018 is the "meta-problem" paper), and biological views of consciousness (named but not cited).
- What would show it wrong: not stated. The paper's two empirical predictions could be checked: that scientific and public acceptance of AI consciousness will rise, and that hard-problem intuitions will lose their hold on more people.
- Quotes used:
  - "Definitive answers about AI consciousness will not be attempted here" (p. 1)
  - "the current status quo holds that the idea is plausible—and AI consciousness along with it." (p. 1)
  - "no system likely meets all of the criteria for consciousness set forth in any of the leading theories" (p. 1)
  - "there are no fundamental barriers to constructing a system that does." (p. 1)
  - "these intuitions, also known as the “explanatory gap,” are largely rooted in thought experiments that science might have the potential to explain away" (p. 1)
  - "verbal reports in words are merely indexical labels for these attractors" (p. 2)
  - "Whether or not this theory convinces many people that there is no hard problem of consciousness is beside the point" (p. 2)
  - "the essential issue is that new explanations of this nature are continuously being proposed that will inevitably convince some." (p. 2)
  - "the philosophical puzzle of consciousness likely evaporates for increasingly more people" (p. 2)
  - "most of the general public polled in a recent study (11) already believes that large language models could be conscious" (p. 2)
  - "no one argues that the bombs themselves have a right to be kept viable." (p. 2)
  - "society possesses neither the legal nor ethical frameworks needed to incorporate conscious-seeming AI." (p. 2)
  - "opting instead to build AI systems that both seem and function more like useful tools and less like conscious agents" (p. 2)

  (Shorter phrases quoted in passing — "need not be logically coherent", "require consciousness according to one theory or another", "whether or not this is the correct approach", "inspired by the appearance of consciousness", and the indicator definition on p. 1 — come from the same pages as cited inline.)

---

## 3. Sebo & Long (2025; online 2023) — Moral consideration for AI systems by 2030 [tier: full]

**PDF:** `sources/Sebo and Long 2025 - Moral consideration for AI systems by 2030.pdf` — **published** version of record, *AI and Ethics* **5**:591–606 (2025 issue), ORIGINAL RESEARCH, DOI 10.1007/s43681-023-00379-1, open access (CC BY 4.0), 16 PDF pages. **Dates (both recorded, as instructed):** received 22 July 2023; accepted 31 October 2023; **published online 11 December 2023**; journal issue **2025** (p. 1). Authors: Jeff Sebo (New York University) and Robert Long (New York University; Center for AI Safety) (p. 1). Funding: Centre for Effective Altruism (p. 14). Citing it as "2023" (online) or "2025" (issue) refers to the same text.

### Phase 1: Plain overview

**The question.** Do humans owe anything, morally, to AI systems — and when? The authors make *"a simple case"* (p. 1) with two premises.
- **The normative premise** (a claim about what we ought to do): *"humans have a duty to extend moral consideration to beings that have a non-negligible chance, given the evidence, of being conscious."* (p. 1).
- **The descriptive premise** (a claim about the facts): some AI systems will have such a chance by 2030.

So we owe some AI systems moral consideration by 2030, and should start preparing now.

**The key idea.** They do not need to show that AI *is* conscious, or even *probably* conscious. They only need a chance that is not negligibly small. For the sake of argument they set the line at 1 in 1,000 (0.1%). They call this "conservative" because it is a *high* bar, which makes the conclusion harder to reach (p. 2, n. 2). They then build a deliberately sceptical probability model of AI consciousness, and show that even this model gives about 0.1% by 2030.

**Why it matters.** The argument turns an open scientific question into a decision under risk. It also limits its own reach. It concerns whether we should *treat* AI as having moral standing, not whether AI *has* it. And it says nothing yet about how much AI interests count or what treatment they call for: *"our conclusion here has no straightforward implications for how humans should treat AI systems."* (p. 2). It is the direct predecessor of the authors' longer 2024 report, *Taking AI Welfare Seriously* (Long et al. 2024; see the cross-references below).

### Phase 2: The argument, step by step

**Step 0 — Framing assumptions (pp. 2–3).**
- *Consciousness is treated as a proxy for moral standing.* Philosophers disagree about whether consciousness is necessary or sufficient for moral standing. Readers who agree that it is can read the argument unconditionally. Others can read it as conditional (p. 2). The authors' reason for the proxy is that, even if *sentience* (consciousness with a felt good or bad quality, i.e. valence) is what really counts, *"AI consciousness is likely the main barrier to AI sentience in practice."* (p. 3). The step from non-conscious to conscious is expected to be harder than the step from neutral to valenced experience.
- *Deliberate conservatism.* The authors' own view is that the threshold should be far below 0.1%, and that the chance of AI consciousness by 2030 is far above it. They use the 0.1% figure *"to be generous to skeptics"* (p. 2). The point is that *"in order to avoid our conclusion, one must take extremely bold and tendentious positions about either the values, the facts, or both."* (p. 2).
- *Practical responsibilities* (p. 2). AI companies should weigh the risk of harm to AI when testing and deploying. Governments should do the same in regulation. Academics should build frameworks for weighing risks across humans, animals and AI. Everyone should help build political will.

**Step 1 — The normative premise (pp. 3–7).**

*1a. We must weigh non-negligible risks.* If an action has a non-negligible chance of gravely harming someone, that counts against it, though not necessarily decisively. Two examples: drunk driving (ordinary), and a particle collider with a small chance of making a black hole (extraordinary) (p. 3). Two decision rules both pass this test (p. 4):
- the **precautionary principle** (on one reading): assume the harm will happen, and ask whether the benefits outweigh it;
- the **expected value principle**: multiply probability by size of harm.

There are also two views on very small risks (p. 4):
- the **no-threshold view**: weigh every risk, however small;
- the **threshold view**: risks below some line may be ignored.

The authors assume only the common ground: *at least* non-negligible risks get *some* weight. On where the line falls, philosophers place it between 1 in 10,000 and 1 in 10 quadrillion (Monton, cited p. 4). The authors adopt 1 in 1,000 so that *"no one can reasonably accuse us of stacking the deck"* (p. 4). Stated plainly: *"when a being has at least a one in a thousand chance of having the capacity for subjective awareness, we should extend this being at least some consideration"* (p. 3).

*1b. From chance of consciousness to duty of consideration (p. 4).* Conscious beings can be harmed and wronged. So a non-negligible chance of consciousness means a non-negligible chance of being harmable. That creates a duty to consider whether our actions harm the being, which amounts to treating it as having moral standing. Three caveats follow (pp. 4–5):
- **(i) Treating is not having.** *"our argument is about whether we should treat AI systems as having moral standing, not whether they do."* (p. 5). Being wrong in that direction is a *false positive*, and it has costs.
- **(ii) Consideration is not a verdict about treatment.** Under an expected-value rule, a being that is 10% likely to matter can receive 10% of the weight its interests would otherwise get (p. 5).
- **(iii) Two chances multiply.** A being's chance of mattering and an action's chance of harming it must be combined. The authors' example: a 1/40 chance of standing times a 1/40 chance of harm gives 1/1600, which is below the 1/1000 threshold. That particular effect may then be ignored, but one must still ask the question (p. 5).

Written as a display equation:

$$
P(\text{action harms } x) \;=\; P(x \text{ has standing}) \times P(\text{harm} \mid \text{standing}) \;=\; \tfrac{1}{40}\times\tfrac{1}{40} \;=\; \tfrac{1}{1600} \;<\; \tfrac{1}{1000}
$$

*1c. Duties to future beings (p. 5).* Duties to at least some future moral patients are "widely accepted". So even if *current* AI is below the threshold, we can have present duties concerning *near-future* systems. This holds especially if those systems will exist anyway and our choices could give them lives worse than not existing.

*1d. The main objection: false positives (pp. 5–6).* The objection is that the argument assumes wrongly excluding a subject is worse than wrongly including an object. False positives have real costs. If digital minds come to vastly outnumber biological ones and we "follow the numbers", we might sacrifice real subjects for merely apparent ones. In AI there is also a tension with safety. Safety means controlling AI more, and welfare may mean controlling it less. Given that experts rank AI extinction risk alongside pandemics and nuclear war, *"we can see how dangerous it might be for us to give AI systems the benefit of the doubt."* (p. 6). The authors present this objection at strength before replying.

*1e. The reply (pp. 6–7).*
1. **False negatives may be worse,** both more *likely* and more *harmful*. They are more likely because *anthropodenial* — wrongly denying non-humans properties they have — has historically outweighed *anthropomorphism*, helped by the incentive to exploit others (p. 6). They are more harmful because *"the harm involved when someone is treated as something is generally worse than the harm involved when something is treated as someone."* (p. 6). The summary: *"the risk of false negatives may be worse than the risk of false positives overall."* (p. 6).
2. **Whatever the balance, the answer is balancing, not exclusion.** There are three tools:
   - a non-zero *threshold*, not a no-threshold view;
   - an **expected weight principle** — moral weight scales with the probability of consciousness and with welfare capacity, so humans and vertebrates can still outweigh invertebrates and AI in expectation (pp. 6–7);
   - room for *self-care and practical realism* (p. 7).
3. **Positive-sum policies.** On the model of "One Health" in animal ethics, oppressing AI could reinforce oppressive ideas and teach AI systems trained on human behaviour to oppress. *"In this respect, AI safety and AI welfare can be synergistic fields."* (p. 7).

The authors also say a more inclusive premise is more plausible: 1 in 10,000, and counting agency and other features besides consciousness. They keep the stricter version for discussion (p. 7). Footnote 9 names *non-conscious agency* and *non-conscious life functions* as plausible further sufficient conditions for standing (p. 7).

**Step 2 — The descriptive premise (pp. 7–13).**

*2a. What is being estimated.* "Consciousness" here means only *"the thin idea of subjective experience"* (p. 8). AI experience need not resemble ours. Certainty is unavailable because of the *problem of other minds* — we cannot directly observe anyone else's experience. The authors split the question in two: how likely is each capacity to be *necessary* for consciousness, and how likely are near-future AI systems to have it (p. 8)? They set aside the view that knowledge of other minds is impossible, because that view *"supports uncertainty about AI consciousness, not certainty that AI systems lack consciousness"* (p. 8, n. 10). So it cannot rescue the sceptic.

*2b. Method: "theory-light", ecumenical.* Following Birch, it is a mistake to assume one theory ("theory-heavy"). It is also a mistake to claim to assume none ("theory-neutral"). The authors aim to be *"theory-informed, yet ecumenical"* (p. 8). Footnote 11 notes that their method differs from Birch's own theory-light proposal (p. 8). They distinguish a *direct path*, building a capacity on purpose, from an *indirect path*, where it emerges as a side effect of other goals, but they use one combined estimate per condition (p. 8). Their caution about the numbers: *"it would be a mistake to take any specific numerical outputs of this kind of exercise too seriously"* (p. 8). The exercise is meant to show that dismissal *"requires making unacceptably exclusionary assumptions about either the values, the facts, or both."* (p. 9).

*2c. Twelve conditions in three groups (pp. 9–12).*
- **Very demanding (§3.1).**
  - *Biological substrate*: consciousness requires carbon-based neural tissue, so AI consciousness is impossible in principle.
  - *Biological function*: consciousness requires functions only biology can currently perform. Godfrey-Smith's examples are metabolism and system-wide synchronisation through oscillations.

  The authors' credences: the substrate view is "very likely" false, and the function view is *"at best, a toss-up at present"* (p. 9). It would be unreasonable to be highly confident that anything as specific as metabolism is necessary for *any* experience (p. 10). Supporting evidence: in a survey of the Association for the Scientific Study of Consciousness, *"about two thirds (67.1%) of respondents think that machines such as robots either “definitely” or “probably” could have consciousness in future"* (p. 10).
- **Moderately demanding (§3.2).** In each case the authors judge whether some AI will have the capacity by 2030.
  - Embodiment (strong = physical body; weak = virtual body): very high.
  - Grounded perception (perceiving objects in a physical or virtual environment): very high.
  - Self-awareness: moderately likely.
  - Agency (setting and pursuing goals in a self-directed way): moderately likely.
  - Global workspace (a mechanism that broadcasts information system-wide; Bengio and colleagues' attempt to build one is cited): moderate.
  - Higher-order representation (representing one's own mental states): moderate.
  - Recurrent processing (feedback loops): somewhat likely, more on the direct than the indirect path.
  - Attention schema (a model of one's own attention): somewhat lower, but still somewhat likely.
- **Very undemanding (§3.3).** *Information processing* alone; minimal *representation* (Tye's PANIC theory: content that is Poised, Abstract, Non-conceptual and Intentional); and, as an "honorable mention", *panpsychism* (the view that consciousness is a basic property of matter), depending on how small experiences combine. Many computational theories are vague enough to allow minimalist readings. The authors' credence: at least 1 in 1,000 that some undemanding condition is sufficient and met. *"we think that it would be arrogant to simply assume that very undemanding theories of consciousness are false at this stage"* (p. 12), just as it would be arrogant to assume the very demanding ones true. A 2020 survey of philosophers is cited for openness to panpsychism (p. 12).

*2d. The model (§4–5, pp. 12–14).* To avoid the conclusion, one must assume (a) a threshold *above* 1 in 1,000, (b) a probability *below* 1 in 1,000, or (c) both (p. 12). Each condition `i` is given a credence that it is **necessary**, `P(N_i)`, and a credence that it is **not met by 2030** if necessary, `P(¬M_i | N_i)`. Their product is the chance that the condition is a *barrier*. An extra **"X factor"** row stands for necessary conditions and harmful interactions the list leaves out. It is allowed only to *lower* the estimate (p. 13). Assuming the barriers are independent, the chance that *nothing* blocks AI consciousness is:

$$
P(\text{AI conscious by 2030}) \;\approx\; \prod_{i=1}^{10}\Bigl(1 - P(N_i)\,P(\lnot M_i \mid N_i)\Bigr)
$$

The authors' illustrative sceptical inputs (table, p. 13):

| Condition | Necessary | Not met by 2030 | Barrier (product) |
|---|---|---|---|
| Biological substrate or function | 80% | 100% | 80.0% |
| Embodiment | 70% | 10% | 7.0% |
| Grounded perception | 70% | 10% | 7.0% |
| Self-awareness | 70% | 70% | 49.0% |
| Agency | 70% | 70% | 49.0% |
| Global workspace | 70% | 70% | 49.0% |
| Higher-order representation | 70% | 70% | 49.0% |
| Recurrent processing | 70% | 80% | 56.0% |
| Attention schema | 50% | 75% | 37.5% |
| X factor | 75% | 90% | 67.5% |

Substituting the table:

$$
0.20 \times 0.93^{2} \times 0.51^{4} \times 0.44 \times 0.625 \times 0.325 \;\approx\; 0.00105 \;=\; 0.105\%
$$

This reviewer recomputed the figure and it matches the authors' "exact" 0.105% (p. 13, n. 17). The authors present it as ~1 in 1,000. They stress: *"These credences are not meant to be accurate, but are rather meant to show how skeptical one can be about AI consciousness while still being committed to at least a one in a thousand chance of AI consciousness by 2030."* (p. 13).

**Stated limits.**
- **Independence.** The model treats conditions as independent. *"But this assumption is very likely false, and some interactions between these conditions might drive down our estimates of AI consciousness."* (p. 12). The worry is an "antipathy" between conditions — for example, if having a workspace made recurrence less likely. The authors' replies: positive interactions are at least as likely, and the human brain meets all the conditions at once (p. 13).
- **Moral-standing theories.** A full estimate would combine uncertainty over theories of moral standing with uncertainty about consciousness. The authors expect this to raise the probability, but call their conclusion *"tentative until we confirm that"* (p. 13).
- The numbers are illustrative, not measured (pp. 8, 13).

**Conclusion (p. 14).** *"accepting a non-negligible chance of near-future AI consciousness and moral standing is not a fringe position."* (p. 14). We should extend moral consideration to some AI systems by 2030, and *"since technological change tends to be faster than social change, we should start preparing for that eventuality now."* (p. 14).

> **Reviewer's note (what the table does and does not contain).** The table models only *necessary* conditions. The "very undemanding" *sufficient* conditions of §3.3, to which the authors give at least 0.1% on their own, are not in the product. They would be a separate route that could only raise the estimate. On the other side, a product of "not a barrier" terms equals the probability of consciousness only if the listed conditions plus the X factor are jointly sufficient once met. The X-factor row is what carries that assumption. Both points are consistent with the authors' text. They are spelled out here because the 0.105% figure is sometimes quoted without them.
>
> **Reviewer's note (wording slips).** The argument is framed throughout as being about *consciousness*. Footnote 17 calls a condition "a barrier to AI sentience", and p. 13 speaks of making "near-term AI sentience more likely". Given the authors' own distinction between consciousness and sentience (p. 3), these read as wording slips, not a change of target.
>
> **Reviewer's note (citations).** The tension between AI safety and AI welfare is attributed to ref. [4] (p. 6), which is a review of scaling laws (p. 14). This appears to be a numbering error. The Butlin et al. report (ref. [32]), of which Long is a co-author, carries an access date of 15 June 2023 (p. 15), earlier than the report's public arXiv date of 17 August 2023 that Bayne et al. record (Bayne et al., p. 12). This is presumably a pre-release draft. It is recorded so that readers do not treat Sebo & Long's use of the report as independent of it.

### Cross-reference to the sibling topic (overlap with Long et al. 2024)

Long et al. (2024), *Taking AI Welfare Seriously*, is reviewed in the sibling topic's Part E, §5. Its lead authors are the same two people in reverse order. Its argument has the **same two-premise structure**: a normative premise (a capacity suffices for moral patienthood) and a descriptive premise (computational features that suffice for that capacity will exist in near-future AI). It uses the **same direct-path / indirect-path distinction**. The differences are recorded here because a synthesis could otherwise read the two as one paper:

| | Sebo & Long (online Dec 2023) | Long et al. (Nov 2024 preprint, per Part E) |
|---|---|---|
| Routes to moral standing | consciousness only (sentience treated as following from it) | consciousness *and* robust agency (two parallel routes) |
| Probability claim | ≥0.1% by 2030, from a deliberately sceptical model | illustrative ~22.5% via sentience route; argues even 2% is non-negligible |
| Role of computational functionalism | not named as such; "biological substrate/function" carries the anti-functionalist credence (80% necessary in the table) | named and defined; assigned an explicit credence; "neither clearly correct nor clearly incorrect" |
| Evidence base for conditions | twelve proposed conditions surveyed by the authors | Butlin et al. 2023 indicator list reproduced in full |
| Practical output | general responsibilities for companies, governments, academics | Acknowledge / Assess / Prepare programme and an "AI welfare officer" |
| Behavioural vs architectural evidence | not discussed as such | explicit downgrading of behavioural evidence ("gaming") |

The step from 2023 to 2024 is therefore from *"one in a thousand is enough, and here is a sceptical model that reaches it"* to *"here is a corporate procedure for a probability we think is much higher"*. Part E's cross-paper note 4 also records how Long et al. differ from Birch's sentience-candidate framework on *who decides*. Sebo & Long's 2023 paper is silent on that question; its responsibilities are assigned to companies, governments and academics without a procedure. Its "theory-light" wording is borrowed from Birch, but footnote 11 states that the method differs (p. 8).

### Section-by-section backbone

- **Abstract (p. 1).** The two premises, the conclusion, and the duty to prepare now.
- **1 Introduction (pp. 1–3).** AI capability trends. Harms *by* AI versus the neglected question of harms *to* AI. Moral standing is defined as meriting consideration for one's own sake. Four framing notes: compressed premises; consciousness assumed to ground standing (readable conditionally); deliberate conservatism (0.1%); no straightforward implications for treatment, though there are general responsibilities. Footnotes cover prior work (Moosavi's critique of speculative AI-patienthood arguments), the meaning of "conservative" threshold, and interspecies welfare comparison (Rethink Priorities).
- **2 The normative premise (pp. 3–7).** Consciousness as proxy for standing. Duty to weigh non-negligible risks (drunk driving, collider). Precautionary versus expected-value principle; threshold versus no-threshold view; the 1/1000 threshold. The chain from chance of consciousness to duty of consideration, with three caveats. Duties to future beings. The false-positive objection (numbers, safety tension) and the reply (false negatives likely worse; threshold, expected weight, self-care; positive-sum "One Health/Welfare" approach). Summary: a more inclusive version would be more plausible.
- **3 The descriptive premise (pp. 7–9).** Thin notion of consciousness; problem of other minds; necessity and possession questions. Theory-light, ecumenical method. Direct and indirect paths. The numbers are not to be taken too seriously.
- **3.1 Very demanding conditions (pp. 9–10).** Biological substrate and biological function. Authors' credences; ASSC survey.
- **3.2 Moderately demanding conditions (pp. 10–11).** Embodiment, grounded perception, self-awareness, agency, global workspace, higher-order representation, recurrent processing, attention schema.
- **3.3 Very undemanding conditions (pp. 11–12).** Information, representation (PANIC), panpsychism. Many theories admit minimalist readings. At least 0.1% credence. PhilPapers survey.
- **4 Discussion (pp. 12–13).** The (a)/(b)/(c) dilemma for the sceptic. Independence simplification and "antipathy". X factor. Moral-standing theory uncertainty; conclusion tentative. Narrative summary of the sceptical inputs.
- **5 Chance of AI consciousness by 2030 (pp. 13–14).** The table, footnote 17's calculation (0.105%), and the concluding paragraph. Acknowledgements, funding (Centre for Effective Altruism), CC BY licence, and references follow (pp. 14–16).

**Field record**
- Year · community: 2023 (online) / 2025 (issue) · ethics-and-policy (philosophy, with AI-safety affiliation)
- Question it asks: Do humans have a duty to extend moral consideration to some AI systems by 2030, given uncertainty about AI consciousness?
- Position in one line: Yes. We owe some consideration to any being with at least a 1-in-1,000 chance of being conscious, and even a deliberately sceptical model gives some AI systems about that chance by 2030. So we should extend consideration then, and prepare now.
- Stance on computational functionalism: neutral. The argument is built to survive an 80% credence that a biological substrate or function is necessary. The authors personally judge the biological-substrate view "very likely" false and the biological-function view a "toss-up" (p. 9).
- Stance on AI consciousness: a non-negligible chance (at least 0.1%) that some AI systems will be conscious by 2030 on sceptical inputs. The authors' own estimate is "much higher" (p. 2). No claim that any current system is conscious.
- What evidence or method it uses: formal argument (two premises) plus an illustrative probability model built on a survey of theories; decision theory under risk; expert surveys (ASSC, PhilPapers).
- Debates it takes part in: moral status under uncertainty; precaution versus expected value; thresholds for negligible risk ("fanaticism"); false positives versus false negatives in moral-circle expansion; AI welfare versus AI safety; biological versus functional requirements for consciousness; duties to future beings.
- Builds on / argues against: builds on Birch 2017/2022 (precaution, theory-light), Butlin et al. 2023 (conditions), Chalmers 2022/2023, Monton (negligibility thresholds), Kagan 2019 (counting animals), Sebo 2023 ("rebugnant conclusion"), Rethink Priorities Moral Weight Project, Tye (PANIC), Graziano (attention schema), Juliani et al. (global workspace in AI), Goyal & Bengio (workspace), Ladak 2023. Argues against: biological substrate and function views (Godfrey-Smith 2023 and others), and "dismissive" scepticism generally. Responds to Moosavi 2023 (speculative AI-patienthood arguments) by giving probabilities for near-term systems.
- What would show it wrong: as the authors state it, a justified case for (a) a risk threshold above 1 in 1,000 for harms to vulnerable populations, or (b) a probability below 1 in 1,000 that some AI is conscious by 2030, or (c) both (p. 12). They also flag that strong negative interactions ("antipathy") between conditions would lower the estimate (p. 12), and that the conclusion is "tentative" until moral-standing uncertainty is modelled (p. 13).
- Quotes used:
  - "humans have a duty to extend moral consideration to beings that have a non-negligible chance, given the evidence, of being conscious." (p. 1)
  - "in order to avoid our conclusion, one must take extremely bold and tendentious positions about either the values, the facts, or both." (p. 2)
  - "our conclusion here has no straightforward implications for how humans should treat AI systems." (p. 2)
  - "when a being has at least a one in a thousand chance of having the capacity for subjective awareness, we should extend this being at least some consideration" (p. 3)
  - "AI consciousness is likely the main barrier to AI sentience in practice." (p. 3)
  - "our argument is about whether we should treat AI systems as having moral standing, not whether they do." (p. 5)
  - "the risk of false negatives may be worse than the risk of false positives overall." (p. 6)
  - "the harm involved when someone is treated as something is generally worse than the harm involved when something is treated as someone." (p. 6)
  - "we can see how dangerous it might be for us to give AI systems the benefit of the doubt." (p. 6)
  - "In this respect, AI safety and AI welfare can be synergistic fields." (p. 7)
  - "the idea of consciousness presupposes nothing more than the thin idea of subjective experience." (p. 8)
  - "denying knowledge of other minds supports uncertainty about AI consciousness, not certainty that AI systems lack consciousness." (p. 8)
  - "it would be a mistake to apply a “theory-heavy” approach that assumes a particular theory of consciousness" (p. 8)
  - "dismissing the idea of AI consciousness requires making unacceptably exclusionary assumptions about either the values, the facts, or both." (p. 9)
  - "But we think that this issue is, at best, a toss-up at present." (p. 9)
  - "about two thirds (67.1%) of respondents think that machines such as robots either “definitely” or “probably” could have consciousness in future" (p. 10)
  - "we think that it would be arrogant to simply assume that very undemanding theories of consciousness are false at this stage" (p. 12)
  - "But this assumption is very likely false, and some interactions between these conditions might drive down our estimates of AI consciousness." (p. 12)
  - "These credences are not meant to be accurate, but are rather meant to show how skeptical one can be about AI consciousness while still being committed to at least a one in a thousand chance of AI consciousness by 2030." (p. 13)
  - "accepting a non-negligible chance of near-future AI consciousness and moral standing is not a fringe position." (p. 14)
  - "since technological change tends to be faster than social change, we should start preparing for that eventuality now." (p. 14)

---

## Cross-paper notes

These notes record how the three papers relate. They do not decide between them.

**1. The three papers answer three different questions, and none answers another's.**
- Bayne et al. ask an *epistemic* question: how could we come to *know* whether a system is conscious?
- Bengio & Elmoznino ask a *social-forecasting and safety* question: what will people come to *believe*, and what is dangerous about acting on it?
- Sebo & Long ask a *practical-ethical* question: what should we *do* before anyone knows?

Each sets the others' question aside on purpose. Bayne et al. leave the moral question to Box 1. Bengio & Elmoznino decline to say whether AI is conscious (p. 1). Sebo & Long accept that certainty may never come (p. 8) and build an argument that does not need it.

**2. A test for consciousness (Bayne) and the worry about *seeming* conscious (Bengio & Elmoznino).**
- *The shared concern, in Bayne's terms, is specificity.* A system that seems conscious without being so is a *false positive*, and a test that produces many of them has low *specificity*. Bayne et al. make the point directly for AI. Command following is specific in humans but not in AI (p. 5), and for AI tests are "arguably highly sensitive but not highly specific" (p. 6). Their Figure 2 marks most human tests as applicable to AI only with "+?": they can be run, but it is unclear what the result means (p. 4). This matches the sibling topic's strongest convergence (Part E, cross-paper note 1): behavioural evidence is downgraded for systems trained on human behaviour, which Birch calls the *gaming problem*.
- *Where they diverge — what kind of evidence will move belief.* Bengio & Elmoznino predict that belief will be moved by two things. The first is *theory-based indicators*: the Butlin et al. method, which is Bayne et al.'s "theory-based strategy". The second is *philosophical explanations* that dissolve the hard problem. Bayne et al. list three problems with the theory-based strategy: no consensus theory (22+ theories, "proliferating"), the generalization problem, and circularity (pp. 7–8). On Bayne et al.'s account, belief built on indicators from contested theories would carry low *rational confidence* for a population as distant as AI. On Bengio & Elmoznino's account, belief will spread anyway. These claims do not contradict each other: one concerns warranted confidence, the other actual belief. Read together, they predict a gap between how confident people will be and how confident the evidence allows them to be.
- *A conditional match.* Bengio & Elmoznino's recommendation — build AI that seems and functions like a tool — would, if followed, keep AI systems from showing the very markers that tests rely on. Bayne et al. do not discuss this. Schneider's ACT, the one test Figure 2 marks plainly "+" for AI, works only on a "boxed" system kept from human talk about experience (p. 3). The same concern about training contamination stands behind both papers.
- *A terminology trap.* Bayne et al. use "deflationary" for views on which consciousness can be understood a priori, by definition (glossary, p. 5), and they *reject* such views (p. 11). The explanations Bengio & Elmoznino describe (attention schema, attractor dynamics) are empirical theories meant to explain away the hard-problem *intuition*. They are not deflationary in Bayne et al.'s sense. A synthesis should not merge the two uses.

**3. A moral argument that does not need to settle the question (Sebo & Long), and how it relates to both.**
- *Relation to Bayne et al.: the same error-rate trade-off, seen from ethics.* Bayne et al.'s Box 1 predicts that high moral stakes will lead some stakeholders to accept low confidence and "a prioritization of sensitivity over specificity" under the precautionary principle (p. 2). Sebo & Long make that argument explicitly. False negatives (treating a subject as an object) may be both more likely and more harmful than false positives (p. 6), so the threshold for consideration should be low. In effect, Sebo & Long supply the ethical case for a decision rule that Bayne et al. treat as one option among stakeholders. Their method also resembles the integrative scheme Bayne et al. mention: weight conditions from many theories by credence, and combine. Bayne et al.'s reservation was that such schemes "may not yield broad agreement about the legitimacy of any particular C-test" (p. 7). Sebo & Long's answer, in effect, is that agreement is not needed, because an estimate above 0.1% is enough to trigger the duty.
- *Relation to Bengio & Elmoznino: the same two risks, weighted differently.* Both papers see danger in giving AI the benefit of the doubt. Sebo & Long state it at full strength (safety requires more control, welfare less; p. 6). Bengio & Elmoznino develop it into the self-preservation and shutdown argument (p. 2). They differ in the weighting and the remedy.
  - Sebo & Long judge false negatives probably worse. Their remedy is to *include and discount*: thresholds, expected weights, and positive-sum policies. They even argue that safety and welfare "can be synergistic" (p. 7).
  - Bengio & Elmoznino focus on the costs of *acting as if* AI is conscious. Their remedy is to *avoid creating* the appearance, by designing tool-like systems.
- *Where they appear to clash, and where they do not.* Sebo & Long's argument is triggered by the *chance* that a system *is* conscious, not by how conscious it *looks*. Bengio & Elmoznino's argument is triggered by how conscious systems *look* and what people then *believe*. If a tool-like system had the functional indicators on the inside but not the outward appearance, Bengio & Elmoznino's design rule could be satisfied while Sebo & Long's duty still applied. Their positions directly conflict only over the policies each would rule out. Bengio & Elmoznino warn against legal survival rights and self-preservation goals. Sebo & Long say their conclusion has "no straightforward implications" for treatment (p. 2) and do not endorse survival rights. So a clash is not forced by the texts as written. It would arise only if a duty of consideration were cashed out as protection against being switched off.
- *All three converge on not trusting appearance, for different reasons.* Bayne et al.: appearance is not specific in AI. Bengio & Elmoznino: appearance will drive belief whatever the truth. Sebo & Long: appearance is not what triggers the duty — probability given the evidence is.

**4. Shared sources and co-authorship, so agreement is not over-read.**
- Butlin et al. (2023) is cited by all three: Bayne ref. [28]; Bengio & Elmoznino ref. (1) as their main evidence; Sebo & Long ref. [32].
- Bengio, Elmoznino and Long are all co-authors of Butlin et al. 2023.
- Fleming is an author of Bayne et al. and is listed as "Fleming, S.M." among Butlin et al.'s authors in Sebo & Long's ref. [32] (p. 15). He is also a co-author of the public-attribution survey Bengio & Elmoznino cite (ref. 11).
- Seth is the second author of Bayne et al. and the target author of the BBS treatment in this corpus.

Convergence among these papers on "no current system is a strong candidate, no fundamental barrier" is therefore partly one research group's view repeated, not independent replication. The same caution is recorded for Long et al. and Birch in the sibling topic's Part E, cross-paper notes 1 and 4.

**5. The testability debate (sibling topic, Part D).** Bayne et al.'s circularity problem — theories are tested with C-tests, and C-tests are validated with theories — is a methodological cousin of the falsification problem recorded in Part D. Kleiner & Hoel (2021) argue that a theory of consciousness can only be tested together with a theory of how reports are produced. Doerig et al. (2019) argue that causal-structure theories are untestable by input–output methods. Bayne et al. do not cite either paper. Their reply to circularity — a virtuous, iterative circle on the model of thermometry — is a different kind of answer. It accepts that theory and measurement are justified together, where those papers ask whether a theory can be falsified at all. A synthesis could set these side by side as two responses to the same structural problem.

**6. Dates matter for the order of influence.** Sebo & Long's paper went online in December 2023, so its argument predates Bayne et al. (May 2024), Long et al. (November 2024) and Bengio & Elmoznino (September 2025). Citing it by its 2025 issue date would invert the apparent order of influence.

---

## What this reviewer could not do

- **Figures.** The poppler page renderer was not installed, so the Read tool could not show PDF pages as images. Instead, pages were rendered with PyMuPDF and viewed as images. This was done for Bayne et al. Figure 2 (p. 4), whose grid is not in the text layer. Figure 1 (p. 3) and Box 3's pyramid figure (p. 9) were reviewed from their captions only. Bengio & Elmoznino's illustration is decorative and was not examined.
- **Bengio & Elmoznino journal volume/issue.** These are not printed in the PDF text layer and are not given here.
- **Authorship of Ji et al. 2024** (Bengio & Elmoznino ref. 7) is stated above from this reviewer's background knowledge and is marked as not verifiable from the PDF.
- **Butlin et al. "necessary and jointly sufficient" check.** This relied on another reviewer's scratch extract and is flagged for the batch-A reviewer of Butlin et al. to confirm against the report's page.
- No git, diary or recursive searches were run, per the brief. Only this one file was written.
