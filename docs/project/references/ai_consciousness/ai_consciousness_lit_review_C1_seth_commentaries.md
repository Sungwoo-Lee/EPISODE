# AI consciousness — Part C1: twelve open peer commentaries on Seth (BBS e316–e327)

## What this part covers (plain-language entry point)

In 2025 the neuroscientist Anil Seth published a "target article" in the journal *Behavioral and Brain Sciences* (BBS). He argued that running the right computer program is probably **not** enough to make a machine conscious, and that consciousness may depend on being a **living thing**. This view is called *biological naturalism* (the idea that consciousness is a biological phenomenon, tied to life). BBS then printed short replies from other researchers, called *open peer commentaries*, and a final reply from Seth.

This file reviews the first twelve of those commentaries, in the journal's numbering order (e316 to e327). The writers are philosophers, neuroscientists, computer scientists, AI researchers and one novelist. They split roughly three ways:

- **Supportive or extending.** Block, Cao and colleagues, and Blackburne and colleagues add new reasons why biology might matter.
- **Qualifying.** Allen, Larkum and colleagues, Bayne, Birch and Chiang accept parts of the view but say the argument is not yet decisive. Chiang also argues that "life" could exist inside a computer simulation.
- **Rejecting.** Baltieri and Kanai, Blum and Blum, Bowes, and Chrisley say Seth's tools do not single out biology, or that his conclusion does not follow.

A newcomer can read the "Verdict" line of each entry and then the **Cross-commentary notes** at the end.

---

> **Correction from the coordinator (2026-10-07), applying to every section-number note below.** The
> section list in the shared review brief was incomplete. Seth's version of record also has **§3.9
> (Summary)**, **§4.0 (Towards biological naturalism — the opening of §4)**, **§4.5 (Summary)** and **§5.0
> (Scenarios for real artificial consciousness — the opening of §5)**. A commentator who cites one of these
> is citing a real section of the published article. Any note below that says such a citation is "not in
> the section list", or infers from it alone that the commentator "worked from a different draft", is
> withdrawn. Whether the *content* a commentator attributes to a section matches the published text was
> not checked here; the synthesis should check it against Part B before relying on it.

## Table of Contents

- [Reading conventions](#reading-conventions)
- [e316. Allen — Too soon to say what consciousness is](#e316-allen-2026--too-soon-to-say-what-consciousness-is-commentary)
- [e317. Larkum, Aru, Whyte & Shine — Separating the conscious wheat from the unconscious chaff](#e317-larkum-aru-whyte--shine-2026--separating-the-conscious-wheat-from-the-unconscious-chaff-towards-a-biologically-grounded-computationalism-commentary)
- [e318. Baltieri & Kanai — Steam-engine naturalism](#e318-baltieri--kanai-2026--steam-engine-naturalism-commentary)
- [e319. Bayne — Biases and the question of artificial consciousness](#e319-bayne-2026--biases-and-the-question-of-artificial-consciousness-commentary)
- [e320. Birch — Free energy, consciousness, and the inverse dark room problem](#e320-birch-2026--free-energy-consciousness-and-the-inverse-dark-room-problem-commentary)
- [e321. Blackburne, Liardi, Skipper, Mediano & Rosas — Compatibilist emergence](#e321-blackburne-liardi-skipper-mediano--rosas-2026--compatibilist-emergence-for-the-science-of-consciousness-commentary)
- [e322. Block — A speculative argument against consciousness in AI](#e322-block-2026--a-speculative-argument-against-consciousness-in-ai-and-perhaps-some-invertebrates-commentary)
- [e323. Blum & Blum — Seth's case provides a roadmap for a conscious AI](#e323-blum--blum-2026--anil-seths-case-for-biological-naturalism-provides-a-roadmap-for-a-conscious-ai-commentary)
- [e324. Bowes — Birds do it, we do it, even embodied machines could do it](#e324-bowes-2026--birds-do-it-we-do-it-even-embodied-machines-could-do-it-why-consciousness-is-not-intrinsically-biological-commentary)
- [e325. Cao, Gottlieb & Moore — Because consciousness requires having your own good](#e325-cao-gottlieb--moore-2026--why-biological-naturalism-because-consciousness-requires-having-your-own-good-commentary)
- [e326. Chiang — Biological naturalism is compatible with substrate independence](#e326-chiang-2026--biological-naturalism-is-compatible-with-substrate-independence-commentary)
- [e327. Chrisley — Conscious AI does not require computational functionalism](#e327-chrisley-2026--conscious-ai-does-not-require-computational-functionalism-and-consciousness-may-be-non-biological-like-flight-commentary)
- [Cross-commentary notes](#cross-commentary-notes)

---

## Reading conventions

- **Source.** All twelve commentaries are in one PDF: `docs/project/references/ai_consciousness/sources/Seth 2025 - Conscious artificial intelligence and biological naturalism (BBS with commentaries and response).pdf`. This batch read **PDF pages 21–39 only**. Page numbers in quotes, written (p. N), are positions in that PDF file. In this file they also match the printed journal page numbers.
- **How the text was read.** The page-image reader was not available in this environment (the tool reported that `pdftoppm` is not installed). The text was therefore extracted column by column with the `pdfplumber` Python library. The journal breaks words with hyphens at line ends (for example "con-" / "sciousness"). Quotes were chosen to avoid those breaks, so no word in a quote has been re-joined. One character was garbled: the bullet points in Blackburne et al. came out as `(cid:129)`. No quote uses them.
- **Seth's sections.** We do not have the target article in this batch. The section tags (§) follow the version-of-record section list in the shared brief, and are based on what each commentator quotes or names. Where a commentator cites section numbers that do not exist in that list, this is flagged in a Reviewer's note.
- **Key terms used across entries**, each explained once here:
  - *Computational functionalism* — the view that running the right computation is enough (sufficient) for consciousness, whatever the hardware.
  - *Substrate (in)dependence* — whether consciousness depends on the physical material (the "substrate") that does the work, or only on the pattern of activity.
  - *Predictive processing* — the idea that the brain constantly predicts its inputs and corrects its predictions using the errors.
  - *Free energy principle (FEP)* — Karl Friston's mathematical claim that any system that keeps itself in existence behaves as if it minimises a quantity called variational free energy (roughly, long-run surprise).
  - *Active inference* — the FEP applied to action: an agent acts so that its inputs match its predictions.
  - *Autopoiesis* — "self-making": a living system continually rebuilds the parts that make it up.
  - *Allostasis* — regulating the body by anticipating needs, not only by reacting to them.
- **Project vocabulary.** This project's agents receive a damage signal called *nociception*. Where a commentator writes "pain", the quote keeps their word.
- **Sibling reviews.** The Seth *preprint* is reviewed in [[computational_functionalism_lit_review_C_biological_naturalism]] (§5 there), together with the Aru, Larkum & Shine (2023) paper that Larkum et al. build on (§4 there). The Butlin et al. (2023) report that Larkum et al. call "naive computationalism" is reviewed in [[computational_functionalism_lit_review_D_theories_and_tests]].

---

## e316. Allen (2026) — Too soon to say what consciousness is [commentary]

**Manifest key:** `allen2026bbs` · **PDF pages:** 21–22 · **Field:** philosophy (Department of Philosophy, University of California, Santa Barbara)

- **Which of Seth's claims it addresses:** §1 (defining consciousness as feeling, not function); §3.1–§3.2 (the diagnosis that pro-AI arguments assume computational functionalism); §4.1–§4.2 (the link between predictive processing, the free energy principle and life); the claim that computer versions of active inference are only a "crude facsimile" of what brains do.
- **Verdict on Seth's thesis:** qualifies — Allen shares Seth's hunch that biological complexity matters, but says Seth's own route begs the question as much as his opponents do, so no view can yet be ruled out.
- **The argument in plain words:** Seth defines consciousness by what it feels like, not by what it does. Allen replies that feelings also *do* things (for example, they make us avoid harm), so a feelings-only definition is partial at best. Seth answers the obvious objection — that active inference already runs on computers — by saying computer versions are only a rough copy, because in living things inference is tightly coupled to the fight against entropy (physical disorder) down to single cells. Allen asks whether this is a difference in principle or only of degree. He states a dilemma. Exact Bayesian calculation (exact probabilistic reasoning) is intractable, so both brains and computers only approximate it. Either consciousness comes partly from approximating a computable function, or it does not. If it does not, the free energy principle does not explain how feelings arise. If it does, Seth must explain why biological approximators are conscious and computer approximators are not. Without that account, each side begs the question against the other. Allen concludes that the field is pre-paradigmatic (it has no agreed framework yet), so pluralism should be encouraged.
- **What it adds that Seth did not say:** It turns the "begging the question" charge back on Seth. It frames the whole dispute as normal for a science without a consensus theory. And it adds a policy point: no camp should be allowed to "force hegemony" early.
- **Key quotes:**
  - "plays one hunch, but it is too soon to say whether it is the best hunch." (p. 21)
  - "Without such an account, the FEP-bionaturalist equally begs the question against the computational functionalist." (p. 22)
  - "The current pluralism among consciousness researchers is thus to be encouraged." (p. 22)

---

## e317. Larkum, Aru, Whyte & Shine (2026) — Separating the conscious wheat from the unconscious chaff: Towards a biologically grounded computationalism [commentary]

**Manifest key:** `larkum2026bbs` · **PDF pages:** 22–24 · **Field:** neuroscience and computer science (Humboldt University of Berlin biology; University of Tartu computer science; University of Sydney neuroscience)

- **Which of Seth's claims it addresses:** §3.3 (substrate dependence and the brain's limited flexibility); §3.5 (scales); §3.1 and §5 (whether consciousness is computational at all); the life–consciousness link from §4.
- **Verdict on Seth's thesis:** qualifies — the authors agree that consciousness as we know it is biological, but deny that this ends computationalism; they propose a richer "biological computationalism" instead.
- **The argument in plain words:** Every case of consciousness we can confirm is biological. But it does not follow that *every* biological detail is needed. Some parts seem to matter (the brain-stem arousal system, higher-order thalamus, and the large layer-5 pyramidal neurons of the cortex). Others seem not to (cerebellar Purkinje cells, the brain's outer membrane). These may be "spandrels" (by-products that come along for the ride). So science must first separate what is necessary from what merely supports it. The hardest feature to copy may be *scale-free organisation*: brain activity spans many time and space scales without one dominant scale. This blurs the line between hardware and software, because the computation may need several scales at once. The authors distinguish "naive computationalism" (today's known computations would suffice — they cite Butlin et al. 2023 as an example) from "biological computationalism", which builds such multiscale facts into the theory. In principle a machine could implement the latter, but only after much more biological knowledge.
- **What it adds that Seth did not say:** A concrete list of candidate necessary structures (layer-5 pyramidal cells, thalamus, arousal system). The idea that computationalism "comes in degrees". Scale-free dynamics as a specific obstacle to substrate independence. A research programme of multiscale experiments with in silico models (computer simulations) as a bridge. They also note that others argue life itself is computational, so linking consciousness to life does not by itself show consciousness is non-computational.
- **Key quotes:**
  - "but not every biological detail is essential." (p. 22)
  - "scale-free organisation is likely the most difficult to instantiate in a substrate-independent manner." (p. 23)
  - "we would not announce the end of computationalism yet." (p. 23)
- **Reviewer's note:** The commentary rests on the authors' own prior work (Aru, Larkum & Shine 2023; Gidon, Aru & Larkum 2022, 2025). The 2023 paper is reviewed in the sibling Part C (§4). The claim that scale-free dynamics cannot be captured at a substrate-independent level is stated, not argued in detail here.

---

## e318. Baltieri & Kanai (2026) — Steam-engine naturalism [commentary]

**Manifest key:** `baltieri2026bbs` · **PDF pages:** 24–26 · **Field:** AI research and informatics (Araya Inc., Tokyo; Department of Informatics, University of Sussex)

- **Which of Seth's claims it addresses:** §4.1 (predictive processing); §4.2 (free energy principle, autopoiesis, active inference and interoception — the sense of the body from within); §4.3 implicitly (what counts as "biological").
- **Verdict on Seth's thesis:** rejects the argument as built — none of Seth's three tools picks out biological systems, so they cannot support biological naturalism.
- **The argument in plain words:** Predictive processing comes from standard signal processing and estimation theory, such as the Kalman filter (a standard method for tracking a changing quantity from noisy data). So it is not inherently biological. It cannot tell a human brain apart from a steam engine's Watt governor (a spinning device that regulates engine speed) or a simple Braitenberg vehicle (a toy robot with wired sensors). The free energy principle is now claimed to apply to *any* "thing", including particles and artefacts. So if it is true, artefacts satisfy it as much as organisms do. The authors also say the FEP does not actually model autopoiesis, and that it conflates autopoiesis with homeostasis. The control-theory view of active inference restates classic results — the "good regulator" theorem and the "internal model principle" — which apply to any goal-directed system, including integral controllers in engineering. The authors offer three options: (1) keep biological naturalism but build it with different tools; (2) reject it and embrace a "universal" theory of consciousness; (3) aim for "biological universality", with formal criteria for what counts as biological or alive.
- **What it adds that Seth did not say:** Detailed technical lineage: predictive processing as Kalman filtering, active inference as PID / integral control (standard engineering feedback control), FEP critiques (Markov blankets, the boundary concept the FEP uses), and the three-way choice. It also invites a formal definition of "biological" and "alive".
- **Key quotes:**
  - "it appears that not much is inherently biological about it" (p. 24)
  - "it is perhaps even harder to argue that predictive processing can explain the differences between a steam engine" (p. 24)
  - "making the special role supposedly played by active inference for biological systems not clear." (p. 25)

---

## e319. Bayne (2026) — Biases and the question of artificial consciousness [commentary]

**Manifest key:** `bayne2026bbs` · **PDF pages:** 26–27 · **Field:** philosophy and consciousness studies (Monash University; CIFAR Brain, Mind and Consciousness program)

- **Which of Seth's claims it addresses:** §2 (biases — anthropocentrism, anthropomorphism, human exceptionalism); §3.8 (consciousness versus intelligence); Seth's remark that AI might be improved by building in functions associated with consciousness.
- **Verdict on Seth's thesis:** qualifies — Bayne agrees the three biases exist, but argues they can push towards *pessimism* about AI consciousness too, and that "bias" is hard to define without a theory.
- **The argument in plain words:** The main problem is not that we fail to understand AI but that we fail to understand consciousness. Seth names three non-evidential influences. *Anthropocentrism* is seeing the world through human values. *Anthropomorphism* is projecting human traits onto things. *Human exceptionalism* is seeing ourselves as superior. Seth says these make conscious AI look more plausible than it is. Bayne says they can just as easily make it look less plausible: people want to keep their special place in the "consciousness club". On anthropomorphism, he notes that about 18% of Americans in recent surveys ascribe sentience or experience to AI. But he adds that we already use language and command-following to test for consciousness in humans (after brain injury, under sedation). So treating such abilities as relevant is not simply a bias. Finally, since every test of consciousness must start from ourselves, some anthropocentrism is unavoidable. The real question is which similarities to us matter. Better to ask directly what our best models of human consciousness imply.
- **What it adds that Seth did not say:** That each bias runs in both directions. The "consciousness isn't just about feelings" point (higher capacities like insight and creativity also involve consciousness). Survey figures. And the use of Terry Bisson's story "They're made of meat" to show that doubting silicon may be a mirror of aliens doubting meat.
- **Key quotes:**
  - "these phenomena might also bias us towards an overly pessimistic view of the prospects for artificial consciousness." (p. 26)
  - "“AI might take my job,” we tell ourselves, “But at least I’ve got feelings!”" (p. 26)
  - "any response to the challenge of artificial consciousness will involve a kind of anthropocentrism." (p. 27)

---

## e320. Birch (2026) — Free energy, consciousness, and the inverse dark room problem [commentary]

**Manifest key:** `birch2026bbs` · **PDF pages:** 27–28 · **Field:** philosophy and animal sentience research (Jeremy Coller Centre for Animal Sentience, London School of Economics)

- **Which of Seth's claims it addresses:** §4 (named explicitly — the argument from free energy minimisation, and the "pale shadow" claim that an algorithm on a non-living substrate is a weak copy); §4.2; §3.3 (ephaptic coupling — electrical influence between neurons through the surrounding tissue, which Seth mentions briefly).
- **Verdict on Seth's thesis:** qualifies — Birch thinks the FEP foundation is too speculative and that the argument begs the question, but he holds that neither biological naturalism nor computational functionalism should be the default, and that the dispute can be tested.
- **The argument in plain words:** Biological naturalism is a "slippery target": if AI copies one biological property, the naturalist can point to another. Seth's new FEP argument has two problems. First, a computational functionalist will simply deny the "pale shadow" claim, so it begs the question. Second, the FEP is too speculative. The known "dark room problem" asks why organisms do not hide in dark caves, where everything is predictable. Friston's followers reply that starving would make the *inside* of the body unpredictable. Birch adds an "inverse dark room problem": some organisms *do* starve in dark places when it helps their genes. Female octopuses starve while guarding their eggs. What biology optimises, if anything, is inclusive fitness (the spread of one's genes, including through relatives), not free energy. But Birch is optimistic about testing. Some biological hypotheses have already failed, such as a proposed link to quantum tunnelling in neurotransmitter release. The ephaptic-coupling idea predicts fewer signs of consciousness in heavily myelinated animals (whales, elephants), which already looks implausible. If FEP-pursuit and life can come apart, we can compare species. A long pattern of failed biological predictions would favour computational functionalism.
- **What it adds that Seth did not say:** The inverse dark room problem and the inclusive-fitness alternative. A testability analysis: a dependence that runs through computation cannot separate the two views, because report itself is computational. And a concrete comparative test strategy with a stated way of updating.
- **Key quotes:**
  - "Seth’s case for biological naturalism rests on a worryingly speculative foundation: the free energy principle." (p. 27)
  - "organisms sometimes do starve to death in dark caves when it serves their inclusive fitness interests." (p. 27)
  - "Neither deserves to be the default." (p. 28)
- **What would show it wrong (as stated):** Birch's own test runs both ways. Organisms pursuing free energy minimisation could show *more* consciousness markers than those sacrificing homeostasis (body-state stability) for fitness — this would support Seth. A repeated failure of biological predictions would favour computational functionalism (p. 28).

---

## e321. Blackburne, Liardi, Skipper, Mediano & Rosas (2026) — Compatibilist emergence for the science of consciousness [commentary]

**Manifest key:** `blackburne2026bbs` · **PDF pages:** 28–31 · **Field:** consciousness science, experimental psychology and computing (UCL; Imperial College London; University of Sussex; Oxford; PIBBSS, Prague)

- **Which of Seth's claims it addresses:** §3.5 (named explicitly: "Emergence and the separation of scales"); §4.2–§4.3 (autopoiesis and self-maintenance); the software/hardware distinction (§3.1, §3.3).
- **Verdict on Seth's thesis:** extends — the authors find Seth's life–consciousness link compelling, but argue that life matters *because* it produces the right kind of emergence, not in spite of emergence.
- **The argument in plain words:** Consciousness works at a larger scale than its parts, so the role of the substrate depends on how scales interact — that is, on *emergence*. The authors propose "compatibilist emergence". Higher scales can have new dynamical laws of their own, yet still depend on their parts (they *supervene* on them: no change at the top without a change below). So an emergent feature can be substrate-independent in one sense and substrate-dependent in another. They list three measurable kinds of emergence. (1) *Macroscopic sufficiency*: the large scale predicts itself, and micro detail adds nothing. (2) *Macroscopic causal dominance*: the system is best controlled from the large scale. (3) *Mereological constraints*: the whole carries information beyond the sum of its parts. Seth's argument from evolution and autopoiesis may block the first kind in living things. But it does not block the other two, and autopoiesis actually calls for them. Brain evidence suggests that the third kind drops in states of reduced consciousness. In organisms, unlike machines, the parts depend on the whole. Emergence is "necessary but not sufficient" for consciousness. Measures of emergence could flag systems that deserve closer inspection.
- **What it adds that Seth did not say:** A three-part taxonomy of emergence with formal measures (Figure 1, p. 29). The claim that the human brain shows macroscopic sufficiency, but that this may hinder consciousness. The organism-versus-machine contrast (in organisms the parts depend on the whole). And a proposal to use emergence measures as an indicator for artificial systems.
- **Key quotes:**
  - "Could a process that “looks like” life suffice, or does it need to be “life all the way down”?" (p. 29)
  - "it may be because of – rather than in spite of – emergence that the distinction between software and hardware may not be the right way of understanding creatures like us." (p. 30)
  - "Emergence is the medium, not the message" (p. 30)
- **Reviewer's note:** The commentary says Seth "speculates that biological systems, by their very nature, cannot support emergent phenomena" (p. 29). The authors themselves then narrow this: Seth's argument targets only macroscopic sufficiency. Check Seth's §3.5 wording before carrying the broader paraphrase into the synthesis. Seth co-authored several of the emergence papers cited (Barnett & Seth 2023; Rosas et al. 2020, 2024; Seth 2010).

---

## e322. Block (2026) — A speculative argument against consciousness in AI (and perhaps some invertebrates) [commentary]

**Manifest key:** `block2026bbs` · **PDF pages:** 31–32 · **Field:** philosophy (Department of Philosophy, New York University)

- **Which of Seth's claims it addresses:** §3.3 (substrate dependence); §3.4 and §3.6 (dynamical approaches, "mortal" computation, and the "strong" substrate dependence that rests on intrinsic properties of the material).
- **Verdict on Seth's thesis:** supports — Block offers one new, openly speculative line of evidence for substrate dependence, while noting it does not reach Seth's "strong" version.
- **The argument in plain words:** Brain rhythms (oscillating waves of electrical activity) are central to brain function. Connectome data (maps of every connection) show that single synapses in the vertebrate cortex are too weak to make a neuron fire on their own. Firing depends instead on population-wide electrical waves. These are created partly by ion movements in the fluid around neurons and by glial cells (non-neuronal support cells). Evolutionary evidence points the same way. Comb jellies may have evolved neurons separately, and their nervous system is purely electrical. Yet the line that led to complex brains used *electrochemical* signalling (chemical messengers between neurons). This suggests electrochemical processing has a functional advantage. The argument chain: sophisticated cortical processing needs brain rhythms; rhythms need electrochemical processing; speculatively, our consciousness needs it; more speculatively, all consciousness does. A further layer: widespread low-frequency waves depend on myelin and oligodendrocytes (the cells that make myelin), which only vertebrates have. Many invertebrates (but not the octopus) seem weak in such waves. This might exclude consciousness in some invertebrates. Block notes a complication: slow waves are also present in dreamless sleep and anaesthesia.
- **What it adds that Seth did not say:** A specific physical mechanism — field-driven population waves — as a candidate for why substrate matters. Comparative evidence from early animal evolution. And an extension of the question from AI to invertebrates. It also states plainly that this kind of dependence is not the same as Seth's "strong" (intrinsic-property) dependence.
- **Key quotes:**
  - "that leaves open why that is so and does not entail what Seth calls “strong” substrate dependence" (p. 31)
  - "Brain rhythms depend on electrochemical processing." (p. 31)
  - "there is an intriguing but empirically motivated speculation that argues against consciousness in AI" (p. 32)
- **Reviewer's note:** Block labels each step by how speculative it is. The step from "rhythms need electrochemistry *in us*" to "no non-biological AI can have them" is the most speculative one. He does not discuss whether artificial hardware could produce comparable field-driven waves. Compare Birch (e320), who treats myelination as evidence *against* a related substrate hypothesis (ephaptic coupling).

---

## e323. Blum & Blum (2026) — Anil Seth's case for biological naturalism provides a roadmap for a conscious AI [commentary]

**Manifest key:** `blum2026bbs` · **PDF pages:** 32–34 · **Field:** theoretical computer science (Computer Science Department, Carnegie Mellon University)

- **Which of Seth's claims it addresses:** §4 (named explicitly as "section 4.0": predictive processing, free energy principle, "controlled hallucination"); §3.4 (quantum, analogue, neuromorphic and mortal computation; non-computable functions); §3.1 (whether digital computation is "rigid"); §5 (the theories Seth sees as promising for "real artificial consciousness": global workspace theory, attention schema theory, 4E cognition, integrated information theory).
- **Verdict on Seth's thesis:** rejects — the authors argue that every feature Seth names can be built into a formal machine, so his case is in fact a case *for* AI consciousness, which they call "inevitable".
- **The argument in plain words:** The authors build a formal model of consciousness called the **Conscious Turing Machine (CTM)**. It is based on global workspace theory (the idea that consciousness is information broadcast widely across the brain). A "stage" holds one chunk of information at a time. A large "audience" of processors competes to put chunks on the stage. The winning chunk is broadcast to all processors. The processors include sensors, motors and "gauge" processors that act as internal homeostats (such as fuel and temperature gauges). They talk in a self-made multimodal language ("Brainish"). The CTM runs cycles of prediction, feedback and learning that reduce prediction error, which the authors call analogous to predictive processing and the FEP. Its sensors and actuators act as its Markov blanket. By its axioms, a broadcast chunk gives rise to a unified experience. So the authors say that to infer from biology's richness that AI *cannot* have these features is a non-sequitur. On computation, they deny that digital means rigid. They call some of Seth's alternatives "straw men": quantum computers compute exactly the same class of functions as Turing machines, and analogue computing is not more powerful than digital.
- **What it adds that Seth did not say:** A worked formal architecture mapped point-by-point onto Seth's criteria, and claimed to fit several major theories at once. Facts from complexity theory: quantum and Turing machines compute the same functions, and quantum speed-ups probably do not extend to NP-complete problems.
- **Key quotes:**
  - "But to conclude, as he often does, that AI systems could not entertain these very features is a non-sequitur." (p. 33)
  - "the class of quantum and Turing computable functions is identical." (p. 33)
  - "Conscious AI is inevitable." (p. 33)
- **Reviewer's note:** The CTM's experiences are introduced by axiom ("by CTM's Axiom 1, a unitary experience", p. 33). So the commentary shows that Seth's *functional* features can be modelled. It does not address Seth's claim that modelling a feature differs from having it. That is the very point under dispute (§3.7).

---

## e324. Bowes (2026) — Birds do it, we do it, even embodied machines could do it. Why consciousness is not intrinsically biological. [commentary]

**Manifest key:** `bowes2026bbs` · **PDF pages:** 34–35 · **Field:** engineering and informatics / philosophy of cognitive science (School of Engineering and Informatics, University of Sussex)

- **Which of Seth's claims it addresses:** §3.3 ("limited substrate flexibility"); §3.4 ("broader forms of computation"); §3.5 (emergence and levels); §3.6 (consciousness as possibly depending on intrinsic properties); §4.4 (the "real problem"); §3.8 (intelligence and consciousness dissociate).
- **Verdict on Seth's thesis:** rejects biological naturalism — Bowes agrees that plain digital computation may not be enough, but says this supports a broader, embodied computationalism, not biology.
- **The argument in plain words:** Bowes accepts Seth's line that conscious artefacts "may have to be closer to biological systems". But "closer" can be defined functionally. If consciousness evolved, it must *do* something, so it is functional. If it also had non-functional intrinsic properties, philosophical zombies (beings like us without experience) become possible again. The brain does compute, because its states are *about* things (they have intentionality); a falling brick does not. Turing-style functionalism is too coarse, but finer kinds exist, such as "virtual machine functionalism". Computers look "rigid" only because we design them to follow rules over symbols we interpret. Embodied and embedded computation does not separate syntax from meaning (Boden's reply to Searle). So the need to be embodied in the right way favours a broad computationalism. If only biology now has the right properties, knowing *why* should make copies possible. Bowes also says Seth conflates "intrinsic" with "irreducible": explaining something always needs relations. This leaves Seth facing a dilemma.
- **What it adds that Seth did not say:** The distinction between intrinsic and irreducible (emergent but explicable) properties. Virtual machine functionalism as a middle path. The claim that "carbon-based life is one way" is just naturalism, not *biological* naturalism. And the charge that Seth relies on a "Cartesian intuition" in tension with his own "real problem" approach.
- **Key quotes:**
  - "these are functional requirements, not intrinsic properties." (p. 34)
  - "Embodied and embedded forms of computation are not “pale shadows” of life." (p. 34)
  - "If not, we should accept functionalism. If so, then the hard problem “pops up” again." (p. 35)

---

## e325. Cao, Gottlieb & Moore (2026) — Why biological naturalism? Because consciousness requires having your own good [commentary]

**Manifest key:** `cao2026bbs` · **PDF pages:** 35–36 · **Field:** Stanford University (the affiliation names no department; the cited work is philosophy of mind and affective science)

- **Which of Seth's claims it addresses:** §4.1–§4.3 (predictive processing, FEP, active inference, autopoiesis and action); global workspace theory as one of the theories discussed in §5; Seth's phrase "multimodal survival-relevant integration".
- **Verdict on Seth's thesis:** extends — the authors give a specific reason why life may be necessary (living things are "valuing subjects"), while conceding this does not yet rule out conscious AI.
- **The argument in plain words:** If you push a needle into a teddy bear, nothing is bad *for the bear*. It has no good of its own. The same holds for a simulated person who winces, because what a system computes depends on how we interpret it. The authors claim that conscious subjects are always *valuing subjects* — beings for whom things can go well or badly. The FEP, predictive processing and even global workspace theory describe only structure. That structure also fits video compressors and email servers. Living things are valuing subjects for two reasons. Metabolism keeps them alive through homeostatic and allostatic control, and natural selection acts on them. In both cases, whether they persist depends on the optimisation succeeding: "existential optimization", with "skin in the game". Consciousness needs more than this. The optimisation must be *internal* (natural selection is external to the organism), and the evaluations must be *integrated* (for example, weighing a good-smelling oasis against a predator and against your own thirst). In animals, diffuse neuromodulator systems (acetylcholine, dopamine) attach value to perception and make it widely available, much as a global workspace would. This integration may turn out to be substrate-dependent.
- **What it adds that Seth did not say:** An explicit criterion — *valuation* tied to the system's own persistence — that separates living from non-living predictive systems. A modified global workspace theory in which what is broadcast must be evaluatively relevant, not mere information. And the clear concession that an AI is not excluded: if conscious, it must be a valuing subject.
- **Key quotes:**
  - "Living things are special because they are valuing subjects, for whom things can be good or bad." (p. 35)
  - "optimization with skin in the game." (p. 36)
  - "only that an artificial intelligence, if conscious, must also be a valuing subject." (p. 36)

---

## e326. Chiang (2026) — Biological naturalism is compatible with substrate independence [commentary]

**Manifest key:** `chiang2026bbs` · **PDF pages:** 36–37 · **Field:** fiction writing (Ted Chiang, writer, Bellevue, Washington)

- **Which of Seth's claims it addresses:** §3.7 (simulation, implementation and realisation — the "nothing gets wet in a weather forecasting computer" point); §3.3 (substrate dependence); §5 (the "theory-based computational" scenario); §6.1 (the ethics of creating beings that can suffer).
- **Verdict on Seth's thesis:** qualifies — Chiang accepts that only living systems are conscious, but argues that life, and therefore consciousness, could be realised in software on ordinary Turing computation.
- **The argument in plain words:** Seth says a weather simulation makes nothing wet. Chiang replies that this is only because weather models do not model wet objects. A good aerodynamics simulation *does* produce lift on its digital wing. Saying it produces no lift because the computer stays on the desk would be a category error. So we could build digital organisms with virtual bodies in virtual environments. Their internal processes would stop if they failed to find resources. They would meet Seth's criteria — embodiment, embeddedness, active inference, allostasis, metabolism — *inside their own world*. In the limit, an atom-by-atom simulation of an organism would be a genuine implementation "in a realm that is disjoint from our own". Its consciousness would be substrate-dependent (made of carbon atoms) and substrate-independent (simulated) at once. Such a brute-force simulation would mean we understood nothing, though. Real understanding means finding useful abstractions, as the Reynolds number and the Navier–Stokes equations (the core equations of fluid flow) are for flight. If allostasis matters, a simple digital allostatic system should suffice. On ethics, digital life would likely develop as natural life did, from reflexes upwards, so we would have time to avoid catastrophe.
- **What it adds that Seth did not say:** The idea of a "realm-relative" implementation that fits neither side of Seth's taxonomy. The argument from simulation cost and abstraction. And a gradualist ethical forecast: insect-level digital moral status first, mammal-level only much later.
- **Key quotes:**
  - "I think all the relevant criteria for living systems could be satisfied by software running on Turing computation." (p. 37)
  - "this digital simulation could be considered a genuine implementation in a realm that is disjoint from our own." (p. 37)
  - "we would have plenty of time to avoid an ethical catastrophe." (p. 37)
- **Reviewer's note:** The commentary has no reference list. Its title page (abstract) is on p. 36, and its body is on p. 37.

---

## e327. Chrisley (2026) — Conscious AI does not require computational functionalism, and consciousness may be non-biological, like flight [commentary]

**Manifest key:** `chrisley2026bbs` · **PDF pages:** 38–39 (p. 39 holds only the end of the text and the references) · **Field:** cognitive science and consciousness science (Centre for Cognitive Science, Centre for Consciousness Science and Sussex AI, University of Sussex)

- **Which of Seth's claims it addresses:** §3.1 (computational functionalism defined as sufficiency); §3.2 and §3.6 and §5 (the step "if computational functionalism is false, conscious AI is impossible"); §4 (Seth's "beast machine" passage, which Chrisley rewrites about bird flight); §3.4 (what computation is).
- **Verdict on Seth's thesis:** rejects the argument — Chrisley says Seth's master argument has a missing step and his positive thesis is not shown, while allowing that some of Seth's conclusions may turn out true.
- **The argument in plain words:** Seth's case against conscious AI has two steps. Step one: computation is not sufficient for consciousness. Step two: so conscious AI is impossible. Chrisley says step two is asserted five times without argument. An analogy: "McLarenism" says owning a McLaren car is enough to win a Grand Prix. It is false, but a McLaren owner can still win, and the car can still be a key part of the win. Likewise, computation could be necessary for, or a key part of, a conscious AI, even if it is not sufficient. Indeed, a popular approach to AI consciousness adds robotic sensorimotor grounding to computation. This rejects computational functionalism, yet is still the pursuit of conscious AI. On the positive thesis, Chrisley rewrites Seth's own sentences about consciousness as sentences about bird flight. Bird flight is biological and substrate-dependent, but flight in general is not. We achieved artificial flight only when we stopped copying birds too closely. Finally, "computation" should not be defined as what Turing machines do, since we recognise analogue, neuromorphic and quantum computation too.
- **What it adds that Seth did not say:** It separates "computation is sufficient" from "computation is involved" and from "computation is necessary". The flight analogy is aimed directly at Seth's beast-machine wording. And it draws on Brian Cantwell Smith's view that we lack a unifying account of computation.
- **Key quotes:**
  - "if computational functionalism is false, conscious AI is impossible" (p. 38)
  - "Bird flight is a biological phenomenon, but flight in general is not." (p. 38)
  - "we only achieved artificial flight when we stopped trying too closely to emulate biological flight" (p. 38)
- **Reviewer's note:** (1) Chrisley cites Seth's "sect. 3.9" and "sect. 5.0" and a definition on "(p. 1)" (p. 38). Neither §3.9 nor §5.0 is in the version-of-record section list in the shared brief. He may have worked from a different draft. Map these citations to the final text with care. (2) Chrisley calls Seth's negative thesis "that conscious AI is impossible" (p. 38). Other commentators in this batch describe Seth's position as a "preferred view" or "hunch" (Larkum et al., p. 23; Allen, p. 21). Check how strongly Seth's own text puts it before attributing "impossible" to him.

---

## Cross-commentary notes

### 1. Where commentaries agree

- **The FEP / predictive-processing route does not single out life.** Baltieri & Kanai (e318), Birch (e320), Blum & Blum (e323) and Allen (e316) all say this, each in a different way. Baltieri & Kanai: the formalism fits steam-engine governors and any "thing". Birch: biology optimises inclusive fitness, not free energy. Blum & Blum: their machine already does prediction-error minimisation. Allen: computers and brains both only approximate Bayesian inference. Cao et al. (e325) accept the point, then *repair* it: prediction-error minimisation counts only when done by a valuing subject for its own good.
- **"Both sides beg the question."** Allen (e316) and Birch (e320) independently reach this verdict. Both conclude that neither view should be the default. Birch then adds a test strategy, while Allen recommends pluralism.
- **Life matters, but the reason must be stated.** Larkum et al. (e317: which biological details), Blackburne et al. (e321: which kind of emergence), Cao et al. (e325: valuation), and Block (e322: electrochemical brain rhythms) each offer a candidate for *what in life* does the work. Blackburne et al. ask the question in so many words: "life all the way down" or a process that "looks like" life?
- **A broader notion of computation.** Larkum et al. ("biological computationalism"), Bowes (e324: embodied, "virtual machine" functionalism), Chrisley (e327: no unifying theory of computation) and Blum & Blum all deny that "computation" must mean coarse, Turing-style, disembodied symbol processing. They disagree on the result. Larkum et al. think such computation needs far more biology. Bowes and Chrisley think it removes the motive for biological naturalism. Blum & Blum think plain digital computation already suffices.

### 2. Where commentaries clash

- **Block (e322) vs. Birch (e320) on myelin.** Block uses myelin-dependent, low-frequency waves as a possible marker that *favours* vertebrate consciousness. Birch uses myelination's suppression of ephaptic coupling as evidence *against* an ephaptic-coupling theory. Both reach for comparative anatomy. They test different substrate hypotheses, and so draw opposite conclusions about how they bear on substrate claims.
- **Blum & Blum (e323) vs. Cao et al. (e325) on global workspace theory.** Blum & Blum treat a global-workspace machine with homeostatic "gauges" as enough. Cao et al. say a plain global workspace fits email servers. What is broadcast must matter to the system's *own* persistence, which "gauges" in a designed machine may not provide.
- **Chiang (e326) vs. Larkum et al. (e317) on cost and abstraction.** Chiang expects useful abstractions (a "digital allostatic system") to make consciousness cheap to implement once understood. Larkum et al. suspect that scale-free dynamics resist exactly this kind of abstraction.
- **Chiang (e326) vs. Chrisley (e327) on whether life is required.** Both are anti-substrate-dependence. But Chiang *accepts* that consciousness requires life and puts life in software. Chrisley denies that consciousness must be biological at all (the flight analogy).
- **Bayne (e319) vs. Seth's §2.** Bayne is the only commentator in this batch who addresses the bias section. He says the biases run both ways. No other commentary here takes up §2.

### 3. Recurring themes

- **Analogies as arguments.** Weather and lift (Chiang), flight (Chrisley, and Bowes's title), the steam-engine governor (Baltieri & Kanai), the McLaren car (Chrisley), the teddy bear (Cao et al.), "They're made of meat" (Bayne), and the female octopus (Birch). Several are aimed directly at Seth's own analogies, such as his weather simulation and beast machine.
- **Testability.** Birch, Larkum et al. and Blackburne et al. each propose an empirical route: comparative species tests, multiscale experiments with in silico models, and emergence measures as indicators. Allen and Bayne stress that the evidence will always be read through some theory.
- **Ethics** appears only briefly. Chiang predicts a slow, evolution-like path for digital life. Bayne notes the public's willingness to ascribe sentience to AI.
- **Version caveat.** Chrisley's section numbers (§3.9, §5.0) do not match the version-of-record section list. Other commentators may also have worked from a pre-final draft. The batch-D review of Seth's Response should check whether Seth comments on this.
