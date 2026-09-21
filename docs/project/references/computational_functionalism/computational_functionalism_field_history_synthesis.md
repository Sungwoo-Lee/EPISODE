# Could the Right Computation Be a Mind? — A Field-History Synthesis (corpus span 1967–2026)

**Topic folder:** `docs/project/references/computational_functionalism/`
**Built from:** the per-paper reviews in Parts A1, A2, B, C, D, E, F and G (36 works reviewed from PDF, 6 more known only by name), 2026-09-21.
**Curator:** literature-curator
**Data for diagrams:** `field_history_data/` (8 CSV files; see [§9](#9-data-files-for-diagrams))
**Neutrality:** this document reports positions and states each at its strongest. It adjudicates nothing.

---

## What this document is about (plain-language entry point)

**The idea.** Since the 1960s a family of views has held that what makes something a mind is not what it is made of but what it *does* — specifically, the computation it carries out. If that is right, the same mind could run on neurons, on silicon, on water pipes, or on a billion people passing radio messages. Philosophers call this **computational functionalism**, and its best-known consequence is that a machine running the right program would have a mind, and might feel things.

**Why this history exists.** The idea has never been proved or refuted, and for fifty years it was argued about with imaginary machines. Then systems arrived that people talk to as though they were minds, and the argument acquired a bill: whether to assess machines for consciousness, whether to build them, what is owed to them. This document puts six communities on one timeline, names the debates that cut across them, and records what their arguments can and cannot show.

**Where things stand in 2026.**
- **Nothing is settled.** Of the nine debates traced here, none is closed.
- **The loudest disagreement may not be the load-bearing one.** Almost nobody in this corpus says machines could never have minds. John Searle, the most-engaged opponent *in this corpus*, writes that "only a machine could think" and that whether a silicon system could is "an empirical question". On the reading taken here, the live question is narrower: is organisation *by itself* enough? Readers who weight integrated information theory's rejection more heavily will draw the line differently.
- **A fourth position is easy to miss.** Alongside "the duplicate feels something", "it doesn't" and "we can't tell", one work argues the question has **no determinate answer**, because the felt quality it asks about is not a well-defined thing (Dennett, 1988). That strand has no successor here.
- **The unresolved axis is a dial, and nine works say the dial is the wrong picture.** Those who do set it disagree — the computations a system performs, single neurons, individual synapses, sub-neuronal receptors, or no bottom at all. It has its own data file.
- **The field is almost entirely argument, not data.** One reviewed work turns on measurements, and it answers a different question (what kind of computation the brain performs: neither digital nor analog).

For this project's artificial agents, the internal damage signal is called **nociception**, never pain, and nothing in this corpus is a finding about them ([§8](#8-relevance-to-this-project-interpretive)).

---

## Table of Contents

- [What this document is about (plain-language entry point)](#what-this-document-is-about-plain-language-entry-point)
- [Reading conventions](#reading-conventions)
- [1. Vocabulary](#1-vocabulary)
- [2. Eras](#2-eras)
- [3. Debates](#3-debates)
- [4. How the communities relate](#4-how-the-communities-relate)
- [5. What the arguments and evidence do and do not show](#5-what-the-arguments-and-evidence-do-and-do-not-show)
- [6. Corrections and mis-statements](#6-corrections-and-mis-statements)
- [7. Current status in one page](#7-current-status-in-one-page)
- [8. Relevance to this project (interpretive)](#8-relevance-to-this-project-interpretive)
- [9. Data files for diagrams](#9-data-files-for-diagrams)
- [10. Known works not held](#10-known-works-not-held)
- [11. Scope and provenance](#11-scope-and-provenance)

---

## Reading conventions

- **Citations.** Each claim carries the work's manifest key and the review it comes from, written as (`key`; Part §n). Example: (`searle1980`; B §1) means the Searle 1980 entry, entry 1 of Part B. Cross-paper sections are cited by name, e.g. "A2 cross-paper note 1". Part files:

  | Part | File | Theme |
  |---|---|---|
  | A1 | [[computational_functionalism_lit_review_A1_functionalism_origins]] | Classical functionalism and multiple realizability (3 papers) |
  | A2 | [[computational_functionalism_lit_review_A2_computation_and_implementation]] | Computation and implementation (7 papers) |
  | B | [[computational_functionalism_lit_review_B_substrate_independence]] | Substrate independence and its thought experiments (4 papers) |
  | C | [[computational_functionalism_lit_review_C_biological_naturalism]] | The biological challenge (5 papers) |
  | D | [[computational_functionalism_lit_review_D_theories_and_tests]] | Theories of consciousness as machine tests (7 papers) |
  | E | [[computational_functionalism_lit_review_E_ai_minds_and_ethics]] | AI minds, moral status and precaution (7 papers) |
  | F | [[computational_functionalism_lit_review_F_olympia_and_replies]] | Maudlin's Olympia argument and the field's replies (2 papers) |
  | G | [[computational_functionalism_lit_review_G_deflationary_strand]] | The deflationary strand: Dennett's "Quining Qualia" (1 paper) |

- **Years.** A work is placed on the timeline by its first public year where the reviews record that it differs from the print year; the label keeps the familiar citation year. The four cases are in [§11](#11-scope-and-provenance).
- **Named-only works** (6 keys, no PDF) are mentioned only as "cited by X" and never carry a claim of their own.
- **"Not found"** means not found in the 36 reviewed works. It is never a claim about the wider literature.
- **Neutrality.** Positions are stated at their strongest as the reviews record them. Statuses describe the *reviewed corpus*, not the field; each debate carries a one-line corpus-limit note (`status_scope` in `debates.csv`).
- **Corpus balance.** The corpus was assembled to trace one thesis, so works that address it are over-represented and works in these fields that never mention it are absent by construction. **Corpus-wide**, among 36 reviewed works, 14 support the thesis, 13 restrict it, 5 reject it and 4 decline to take a side. **This tally is used nowhere else in this document.** A work can hold a corpus-wide stance and take no position in a given debate, so per-debate figures are computed separately from `positions.csv` and are always smaller — see [§3.1](#31-is-running-the-right-computation-sufficient-for-a-mind--open). A figure drawn from `positions.csv` must not be captioned with this number.
- **Status scale** (used in §3, §7 and `debates.csv`):

  | Status | Meaning here |
  |---|---|
  | settled | Reviewed works on all sides accept the claim; no live dispute is recorded. **No debate in this corpus is settled.** |
  | leaning | Reviewed works converge in a direction that is always named, but dissent or a missing test remains. |
  | open | Substantive positions remain in dispute, and new argument or evidence is still entering the record. |
  | stalled | No new argument or evidence has entered the record for a long period; the debate moves only by reinterpreting what is already there. |
  | not yet tested (`untested`) | The question is posed, but no reviewed work offers anything that would decide it. |

---

## 1. Vocabulary

One line each, in the reviews' own words where possible.

| Term | Meaning as used in the reviews |
|---|---|
| **Functionalism** | A mental state is defined by the role it plays — what causes it, what it causes, how it relates to other mental states — not by what it is made of (A1 entry point). |
| **Computational functionalism** | Functionalism plus the claim that the relevant roles are *computational*, so that running the right computation in any material would suffice for having the mental states (A1 §1; `butlin2023`, D §6: "it is sufficient for a state to be conscious that it plays a role of the right kind in the implementation of the right kind of algorithm"). |
| **Computational sufficiency** | "There is a class of automata such that any implementation of an automaton in that class will possess a mind" (`chalmers1996rock`, A2 §1, p. 309). Contrast *computational explanation*: computation as the framework for explaining cognition and behaviour (`chalmers1994cfc`, A2 §5). |
| **Machine functionalism** | The version that identifies each mental state with a state in a Turing machine's table of instructions — the specific target of Block & Fodor 1972 and of Block 1978's first half (A1 §1, §3). |
| **Computationalism** | The scientific claim that the brain's functional organisation is *computational* — logically independent of functionalism once function is explained mechanistically (`piccinini2010`, A2 §3, p. 301). |
| **Computational theory of mind / of cognition** | The programme of explaining cognition computationally. Piccinini's point is that this is a third thing again: functionalism is metaphysics, computationalism is science, and the slogan "the mind is the software of the brain" runs all three together (A2 §3). |
| **Three claims, in increasing strength** | The corpus's own ladder, which should not be collapsed. **Multiple realizability**: the same psychological state type can be realised by many different physical state types (A1 reading conventions) — satisfied even in an all-carbon world, since two brains differ. **Substrate independence**: "mental states can supervene on any of a *broad class* of physical substrates" (`bostrom2003`, B §4, p. 244) — adds the class. **Organizational invariance**: the property is preserved under every change preserving *causal topology* (`chalmers1994cfc`, A2 §5) — names what the class has in common. `bostrom2003` is the corpus's clearest case of assuming the middle rung without argument. |
| **Substrate flexibility** | Seth's weaker replacement: mental states "are not tied to carbon-based biological substrates — that they might be realisable in some other, but not necessarily all, types of material" (`seth2025`, C §5, PDF p. 7). |
| **Implementation** | The relation connecting abstract computation to physical system. On Chalmers's account, "a physical system implements a given computation when the causal structure of the physical system mirrors the formal structure of the computation" (`chalmers1994cfc`, A2 §5, PDF p. 2). |
| **Individuation** | Which computation a system is running, as opposed to whether it is running one at all (A2 cross-paper note 1). |
| **Triviality / universal realization** | The claim that every ordinary open physical system realizes every finite automaton, which would make computational functionalism empty (`chalmers1996rock`, A2 §1, reporting Putnam 1988). |
| **Pancomputationalism** | "Everything is a Probabilistic Automaton … under some Description" — which, Piccinini argues, makes the weak reading of the doctrine uninformative (`piccinini2010`, A2 §3, p. 274). |
| **Causal topology** | "The pattern of interaction among parts of the system, abstracted away from the make-up of individual parts and from the way the causal connections are implemented" (`chalmers1994cfc`, A2 §5, PDF p. 7). |
| **Organizational invariant** | A property preserved under every change that preserves causal topology. Chalmers's central claim is that mental properties, including experience, are organizational invariants (A2 §5). |
| **Combinatorial state automaton (CSA)** | An automaton whose internal state is a *vector* of independently varying components occupying distinct physical regions; introduced because arbitrary objects "have no hope of passing" its implementation conditions (`chalmers1996rock`, A2 §1, pp. 325–26). |
| **Grain of functional equivalence** | How finely a system must be copied before the copy counts as functionally equivalent. Left open by every reviewed work, at settings ranging from information-processing computations to sub-neuronal receptors — and denied by nine of them to be a scale at all ([§3.4](#34-how-fine-must-functional-equivalence-be--open); `grain.csv`). |
| **Liberalism / chauvinism** | "Theories are chauvinist insofar as they falsely **deny** that systems have mental properties and liberal insofar as they falsely **attribute** mental properties" (`block1978`, A1 §3, p. 292). |
| **Consciousness / phenomenal consciousness / sentience** | Not interchangeable, and the corpus does not treat them so. *Consciousness* in Nagel's sense: there is something it is like to be the system. *Phenomenal consciousness* is that sense specifically, as against access (`butlin2023`, D §6). **Sentience** is used by Birch in a *narrower* sense — "the capacity to have valenced experiences — experiences that feel bad or feel good to the subject" (`birch2024`, E §6, p. 2) — so a system could be phenomenally conscious without being sentient in his sense. Chalmers treats the two as roughly equivalent and prefers "consciousness"; Long et al. do the opposite (E cross-paper note 7). |
| **Qualia** | The felt, experiential character of a state (A1 reading conventions) — and, in this corpus, a contested rather than a shared starting point: `dennett1988` argues the pre-theoretical notion pulls apart under pressure and answers to no well-defined property (G §1). |
| **To quine** | Dennett's coinage, from a joke dictionary: "to deny resolutely the existence or importance of something real or significant" (`dennett1988`, G §1). His own label for the position is *eliminative materialism*, with eliminative-versus-reductive called "a tactical issue" (endnote 2). |
| **Intuition pump** | A short imagined case designed to make one assumption visible and then unattractive, used "in place of formal argument" because "rigorous arguments only work on well-defined materials" (`dennett1988`, G §1). Fifteen of them carry that paper. |
| **Absent / inverted qualia** | Functionally identical systems, one of which feels nothing at all, or feels something systematically different (A1 reading conventions; `chalmers1995qualia`, B §3). |
| **Fading qualia** | A subject halfway through neuron-by-neuron replacement whose experience has dimmed to a whisper while he sincerely reports vivid colour and cannot notice anything wrong (`chalmers1995qualia`, B §3). |
| **Dancing qualia** | A silicon backup circuit with a switch: flipping it changes the subject's experience while leaving functional organisation and behaviour untouched, so the change is unnoticeable in principle (`chalmers1995qualia`, B §3). |
| **Nonreductive functionalism** | Chalmers's own label: "conscious experience is determined by functional organization without necessarily being reducible to functional organization", compatible with property dualism (B §3, §5). |
| **Minimal computationalism** | The position defended in `chalmers1994cfc`: computational sufficiency plus computational explanation, committed to neither symbols, rules, von Neumann architecture, nor the brain being a computer (A2 §5). |
| **Intrinsic vs observer-relative intentionality** | Actual mental states versus "ways that people have of speaking about entities … lacking intrinsic intentionality"; Searle adds, "Functionalism … is an entire system erected on the failure to see this distinction" (`searle1980`, B §1, Author's Response pp. 451–52). |
| **Syntax vs semantics** | Formal symbol shape versus meaning: "they have only a syntax but no semantics" (`searle1980`, B §1, p. 422). |
| **Biological naturalism** | Searle's label for the view that consciousness is a biological phenomenon caused by and realised in living systems; redefined by Seth as "the claim that consciousness is a property of only (but not necessarily all) living systems" (`seth2025`, C §5, PDF p. 17). |
| **Biopsychism** | The stronger view that "all and only systems that are alive, in the metabolic sense, have subjective experience" (`godfreysmith2016`, C §1, PDF p. 13). Godfrey-Smith states it without endorsing it; Seth explicitly disavows it. |
| **Autopoietic vs allopoietic** | Self-producing systems that continuously regenerate their own material basis and boundary, versus other-producing systems such as computers and factories (`seth2025`, C §5, via Maturana & Varela). |
| **Mortal vs immortal computation** | Standard computation is *immortal* — software outlives any hardware instance, at a constant error-correction cost. Brains, being energy-efficient, would be running *mortal* computations inseparable from the wetware (`seth2025`, C §5, via Hinton). |
| **Causal / informational closure** | Measures of whether observing or intervening on a coarse-grained variable suffices to predict the higher-level outcome, so that lower-level detail adds nothing. The only proposal in the corpus that could *measure* how far a system abstracts from its substrate (`seth2025`, C §5 §3.5). |
| **Generic / digital / analog computation** | Generic computation is "the processing of vehicles … in accordance with rules that are sensitive to … differences between different portions of the vehicles"; digital adds strings of discrete digits, analog adds continuous variables (`piccinini2013`, A2 §6, p. 458). |
| **Medium independence** | A computation's defining rule is "sensitive only to differences between portions of the vehicles along specific dimensions of variation … insensitive to any more concrete physical properties" — which is why cooking and exploding are not computations (`piccinini2013`, A2 §6, p. 458). |
| **Semantic task** | An input–output regularity "specified in terms of the representational content of the arguments (inputs) and values (outputs)" — Shagrir's answer to why we call brains computers and planets not (`shagrir2006`, A2 §2, p. 403). |
| **The received view (on representation)** | "Computation essentially involves representational content", with no restriction on the type of content (`sprevak2010`, A2 §4, PDF p. 3). |
| **Integrated information (Φ)** | "Conceptual information that is specified by a system above and beyond the conceptual information specified by its (minimal) parts … a non-negative number" (`tononi2015`, D §1, p. 8). A **complex** is a set of elements at a *local maximum* of Φ; only maxima exist as entities. |
| **Unfolding** | The transformation of a recurrent network into a feedforward one with the same input–output function, used to show that causal structure and every possible experiment are doubly dissociated (`doerig2019`, D §4). |
| **Global availability (C1) / self-monitoring (C2)** | Information selected and broadcast so the whole system can use it; and a system's representation of its own states, confidence and errors (`dehaene2017`, D §2, pp. 486–87). |
| **Attention schema** | A schematic, physically inaccurate internal model of the system's own attention; "consciousness is, in a sense, a cartoon sketch of attention" (`graziano2017`, D §3, p. 5). |
| **Indicator properties** | Computational conditions extracted from several theories at once, used to score a system: "systems that have more of these features are better candidates for consciousness" (`butlin2023`, D §6, p. 45). |
| **Sentience candidate** | A system with "an evidence base that (a) implies a realistic possibility of sentience that it would be irresponsible to ignore … and (b) is rich enough to allow the identification of welfare risks" (`birch2024`, E §6, p. 6). Paired with **investigation priority** for systems that fall short but could be brought up to it. |
| **Gaming problem** | "When an artificial agent can intelligently draw upon huge amounts of human-generated training data, it is well placed to game our criteria for sentience … Criteria lose their usefulness once gamed" (`birch2024`, E §6, p. 13). |
| **Specificity problem** | "The challenge of how to spell out the cognitive mechanisms identified as constitutive of consciousness … in such a way as to make them applicable beyond the human case" (`shevlin2021`, E §2, p. 300). |
| **Umwelt / affordances** | The slice of the world an organism can perceive, and the action-relevant information within it; used to argue a language model's input stream "is more different from the one presented to humans than ours is from bats" (`aru2023`, C §4, PDF p. 6). |
| **"Skin in the game"** | A system with no real stake in its own continuation: shutting down a language model has no consequence for it, whereas an organism "has to keep going, because to be going is its very existence" (`aru2023`, C §4, Box 1). |
| **Epistemic vs instrumental inference** | Acting to find out more about the world, versus acting to keep the body's essential variables in range; the second is proposed as the primary job of interoception (`seth2018beast`, C §2). |
| **Being a model vs having a model** | Behaving as if model-based versus explicitly encoding a generative model's sufficient statistics (`seth2018beast`, C §2, Box 4). |
| **Counterfactually loaded** | A property that depends on what a system *would* do, not only on what it does. Computation is counterfactually loaded; an occurrent experience appears not to be. That mismatch is the whole of the Olympia argument (`maudlin1989`, F §1; `klein_maudlin`, F §2). |
| **Olympia** | Maudlin's machine, named after the clockwork automaton in Hoffmann's *The Sandman*: an armature sweeps a row of water troughs while the entire counterfactual-supporting apparatus sits inert, "gears hang[ing] motionless in the air, not touching" (F §1, p. 423). |
| **Inconsistent triad** | Maudlin's structure: computational sufficiency, computational necessity, and the supervenience of occurrent experience on concurrent physical activity cannot all hold (F §1, p. 413). |
| **Architecture / computational process** | A set of primitive operations and basic resources realised by causally interacting parts; and a temporally extended series of those operations. Klein's replacement for individuation by function (F §2, PDF pp. 9–16). |
| **Implementation vs emulation** | Acting like a Turing machine versus *being* one. "On Maudlin's view of computation, there is no space between 'acting like a Turing machine' and 'being a Turing machine'" (`klein_maudlin`, F §2, PDF p. 15). |
| **Blockhead** | A machine that passes the Turing test by looking up pre-computed replies: "It is just a huge list-searcher plus a tape recorder" (`block1978`, A1 §3, pp. 281–82). Revived as the standing null hypothesis for language models (`milliere2024`, E §7). |
| **Psychologism** | "Intelligence does not merely depend on the observable behavioral dispositions of a system, but also on the nature and complexity of internal information processing mechanisms" (`milliere2024`, E §7, p. 2). |
| **Redescription Fallacy** | Arguing that a system cannot model a capacity "simply because its operations can be explained in less abstract and more deflationary terms" — as if a piano could not produce harmony because it is hammers striking strings (`milliere2024`, E §7, p. 9). |
| **Swamp LLM** | A randomly initialised model that by coincidence has exactly the parameters of a trained one. It computes the same function and represents nothing, because content requires a selection history (`mollo2023vector`, E §4, §7.1). |
| **Referential grounding** | An internal state is grounded when it stands in causal-informational relations to the world *and* has "a history of selection that has endowed [it] with the function of carrying this information" (`mollo2023vector`, E §4, abstract). |
| **Theory-heavy / theory-light / theory-balanced** | Assess a system by assuming a complete theory; by weak theory-independent behavioural markers; or by averaging across competing theories weighted by their acceptance (`shevlin2021`, E §2, via Birch; `chalmers2023llm`, E §3 n. 30). |
| **PARC tests** | Permissibility-in-principle, adequacy, reasonable necessity, consistency — applied in sequence by a citizens' panel to decide which precautions are proportionate (`birch2024`, E §6, p. 9). |
| **Excluded Middle Policy** | "A policy of only creating AIs whose moral status is clear, one way or the other" (`schwitzgebel2015`, E §1, ms. p. 32). |
| **ASIMO Problem** | Our moral reactions to machines track cuteness, eyes and contingent responsiveness rather than anything conferring moral status — and they err in both directions (`schwitzgebel2015`, E §1, ms. pp. 24–29). |
| **Simulation / implementation / realisation** | Run an abstraction of a mechanism; realise its finer-grained aspects in another medium; or actually produce the property. "Nothing gets wet in a weather forecasting computer" (`seth2025`, C §5 §3.7). |
| **Nociception** | The neural encoding of damage signals, distinct from pain. This project's own vocabulary, not the corpus's; see [§8](#8-relevance-to-this-project-interpretive). |

---

## 2. Eras

The corpus supports five eras. Boundaries fall where the questions being asked changed, and are approximate. Era membership of every work is in `field_history_data/works.csv`.

| Era | Years | Works | Reviewed | The new question |
|---|---|---|---|---|
| Functionalism stated, and attacked from inside | 1967–1978 | 4 | 3 | What makes two mental states the same kind, and is the machine table the right currency? |
| Is running the right program sufficient? | 1979–1995 | 8 | 6 | Does instantiating a program suffice for understanding, at which neuron would the lights go out — and is there a fact of the matter at all? |
| What is it to run a computation at all? | 1996–2013 | 8 | 6 | Is the implementation relation non-trivial, which computation is being run, and what does the brain compute? |
| Theories of consciousness become machine tests | 2014–2021 | 12 | 11 | Can a theory of consciousness decide the machine case, and can such a theory be tested at all? |
| Systems that talk back | 2022–2026 | 10 | 10 | Are the systems in front of us candidates, how would we tell, and what should be done meanwhile? |

### 2.1 Functionalism stated, and attacked from inside (1967–1978)

**Live questions.** What makes two mental states the same *type* of state? Behaviourism said sameness of behavioural disposition; type physicalism said sameness of brain state. Is there a third answer, and does it have to be computational?

**Who asked.** Philosophers of mind — and, decisively, two of functionalism's own architects.

**Key works.**
- **Putnam 1967** (`putnam1967`; named-only) is the target and the source for everything that follows: mental states as machine-table states of a probabilistic automaton. No PDF is held, so this document reports only what the citing papers say about it.
- **Block & Fodor 1972** (`blockfodor1972`; A1 §1) accept the move to functionalism and accept multiple realizability, then give six arguments that the machine table is the wrong level. The individuation criterion is absurdly fine-grained — "if you and I differ only in the respect that your most probable response to the pain of stubbing your toe is to say 'damn' and mine is to say 'darn'", our pains are different types (p. 174) — and simultaneously too coarse, because a machine is in one state at a time and its states are a finite list. Their argument 3 is the ancestor of the corpus: two systems might share functional organisation while one feels nothing. They flag it as "a deeper problem … than any of the other arguments" and then explicitly set it aside (pp. 173–74).
- **Fodor 1974** (`fodor1974`; A1 §2) converts multiple realizability from a claim about minds into a claim about the architecture of science. Monetary exchanges can be wampum, dollar bills or a signature on a cheque; no physical description covers all and only those. The line that matters here: the unity of science "is at the mercy of progress in the field of computer simulation" (p. 106). He does *not* argue that the autonomous psychological level is computational.
- **Block 1978** (`block1978`; A1 §3) cashes out the deferred argument. The population of China, wired by radio, would have your functional organisation for an hour; a sheik could manipulate Bolivia's economy into functional equivalence with himself. He names the two failure modes — **liberalism** and **chauvinism** — and argues every version falls into one. He is careful about what this is: "I do not claim that this is a conclusive argument against functionalism … it is best construed as a burden-of-proof argument" (p. 296).

**What changed by the end.** Multiple realizability was common ground; type physicalism was abandoned by everyone in the batch — a fact about four papers from one decade, not about the field, since the identity theory's revival rests on `bechtelmundale1999`, which is named-only ([§10](#10-known-works-not-held)), so this corpus cannot show the other side of it. The field's question had shifted from *what is a mental state?* to *how abstract may a description be before it stops describing a mind?* That is the grain question ([§3.4](#34-how-fine-must-functional-equivalence-be--open)), and it has never been answered.

### 2.2 Is running the right program sufficient? The thought-experiment era (1979–1995)

**Live questions.** Is instantiating a program *sufficient* for understanding? If you replace a brain one piece at a time with non-biological parts that do the same job, at what point — if ever — does experience go?

**Who asked.** Philosophers of mind, in the medium of the thought experiment.

**Key works.**
- **Searle 1980** (`searle1980`; B §1) is a full journal treatment: target article, 27 open peer commentaries (not reviewed here), and Searle's own reply. The Chinese Room is built to establish exactly one of his five numbered propositions — that instantiating a program is never by itself sufficient for intentionality. The other four are asserted or derived. A critic who grants that proposition but denies that brain processes are the *only* sufficient cause is untouched by the room, and both later replies in this batch take that route.
- **Cuda 1985** (`cuda1985`; B §2) invents the move the field still uses. Replace Fred's neurons one at a time with homunculi that read and write neuronal states, and run a matched control sequence of unoperated people so that "same state as its counterpart" can be stipulated. Anyone who says the end product is unconscious must name a single neuron at which a fully conscious system becomes an unconscious one. Cuda then argues that claim is counterintuitive, has inductive evidence against it from clinical neuron loss, and could never have evidence *for* it.
- **Chalmers 1993/2011** (`chalmers1994cfc`; A2 §5), written in this period though published much later, supplies the positive programme: implementation as causal mirroring, computation as an abstract specification of **causal topology**, and the claim that mental properties are **organizational invariants**.
- **Chalmers 1995** (`chalmers1995qualia`; B §3) supplies the arguments. **Fading Qualia** yields Joe, halfway along the replacement series, who "exclaims about the vivid bright red and yellow uniforms of the basketball players" while experiencing faded pink. **Dancing Qualia** adds a switch, so the change happens within one subject at one moment and provably cannot be noticed. He is explicit that this establishes *empirical* impossibility only and leaves his position "just as compatible with certain forms of property dualism about experience as with certain forms of physicalism" (§5).
- **Maudlin 1989** (`maudlin1989`; F §1) attacks from an unexpected angle, and the target is precisely the defence the pro-computationalist works rely on. Whether a system is *running a program* depends on what it would do in cases that never arise; what you feel over the next ten seconds seems to depend only on what your brain is actually doing. **Olympia** is built to prize those apart: an armature sweeps left to right along a row of water troughs while, behind it, the entire counterfactual-supporting apparatus — N + 2 frozen copies of a working machine, each held by a wooden block chained to a pre-set float — sits motionless, "gears hang[ing] in the air, not touching" (p. 423). Give her any other tape and a float moves, a chain pulls, a block drops and a real machine takes over. So she supports every counterfactual in the machine table, and does almost nothing. Two smaller variants make the point without the machinery: slide an inert metal sheet between the frozen gear teeth, touching nothing, and the counterfactuals fail; or let the chains rust past a threshold that no observation marks. Maudlin's concessions are unusually large and routinely dropped in citation: funny-instantiation intuitions carry no weight, Searle's Chinese Room inference fails, and "the silicon brain and the hydraulic brain may, for all we have said, be conscious" (p. 429). What dies is exactly one thesis — computational sufficiency.

- **Dennett 1988** (`dennett1988`; G §1) attacks not the machines but the thing they were supposed to be missing. Every argument above assumes there is a definite something — the felt quality, the *quale* — whose presence is in dispute. Dennett argues the pre-theoretical notion does not survive contact with careful cases: pressed, it pulls apart into an **epistemic** horn on which no subject can tell whether his own qualia have changed (so they are not directly apprehensible) and a **constitutive** horn on which one's reactions partly make the experience what it is (so they are not intrinsic), with nothing in folk psychology to settle which was meant. Two brain surgeries with identical results from the inside; two coffee tasters who cannot say whether the coffee changed or their taste did. **He does not deny that experience occurs** — "since I don't deny the reality of conscious experience, I grant that conscious experience has properties" — and his flat closing line is flagged in his own endnote as a tactical recommendation about vocabulary. What he denies is that any property is ineffable, intrinsic, private and directly apprehensible in the way the tradition requires. The dating matters: the paper is 1988, but its endnote 14 documents the argument circulating from December 1979 and presented in near-final form in April 1985, so it is contemporaneous with Block 1978/1980 and Cuda 1985 rather than a late response to them.

Chalmers saw the problem and said so, in the footnote that names Maudlin as raising a challenge that "requires an in-depth treatment in its own right" (A2 §1 n. 3) — conceding both that the intuition is plausible and that the conditionals are constitutive, and then deferring. **No reviewed work in this corpus takes the deferral up until Part F**, which is why that batch exists.

**What changed by the end.** The debate acquired its standard form — gradual replacement, and the demand to locate the discontinuity — and its standard concession: three of the four participants restrict themselves to *contingent, actual-world* claims rather than modal ones, which is what makes the dispute tractable rather than a clash of intuitions (B cross-paper note 6). It also acquired a hidden parameter nobody fixed: Searle says whatever level "reproduces the causes", Cuda says each neuron's role, Chalmers says whatever fixes behavioural dispositions, and Bostrom says synapses.

### 2.3 What is it to run a computation at all? (1996–2013)

**Live questions.** Does everything implement every computation? If a system computes, *which* computation is it running, and does that depend on what its states mean? And what kind of computation does the brain actually perform?

**Who asked.** Philosophers of computation, and — in one case — a philosopher working with a physicist.

**Key works.**
- **Chalmers 1996** (`chalmers1996rock`; A2 §1) answers the triviality challenge: Putnam's construction reproduces only an automaton's *trace*, not its structure, because implementation requires transitions that would have held had things gone otherwise. He then argues against himself, showing a clock and a dial recover a weakened version of Putnam's result, and concludes that the *formalism* was wrong: replace finite-state automata with combinatorial state automata whose vector components vary independently and occupy distinct physical regions. He leaves two gaps open himself (§7).
- **Shagrir 2006** (`shagrir2006`; A2 §2) concedes the triviality point and relocates the answer: we take the computational stance toward brains because the regularities we want explained are specified by what the signals are *about*. His brown–cow cell is one pattern of electrical activity that is an AND gate and an OR gate at once; only content picks one.
- **Piccinini 2010** (`piccinini2010`; A2 §3) pulls apart two claims welded together for forty years: that the mind is the functional organisation of the brain, and that this organisation is computational. Neither entails the other once function is explained mechanistically. The effect is to strip the doctrine of a priori standing: whether the brain is a computing mechanism "can only be done by studying the functional organization of the brain empirically" (p. 302).
- **Sprevak 2010** (`sprevak2010`; A2 §4) presses the opposite case: nothing physical decides whether a circuit is an AND gate or an OR gate, and non-semantic realization functions are so cheap that they make every system compute everything.
- **Piccinini & Bahar 2013** (`piccinini2013`; A2 §6) is the corpus's one data-driven verdict. Neural processes are computations in a *generic* sense but neither digital (spikes cannot be typed into finitely many unambiguous types, and spike sets cannot be assembled into strings) nor analog (what matters is spike presence and timing, not continuous magnitudes). Neural computation is **sui generis**.
- **Coelho Mollo 2017/2018** (`mollo2018`; A2 §7) reframes: *which* computation is a functional, medium-independent question; *how* a system manages to run it is a material, mechanistic one. The two never had to conflict. **(Dated 2017, so `works.csv` places it in era 4. It is narrated here because it closes the era-3 debate; a timeline drawn from the data will show it one era later than this prose does.)**
- **Bostrom 2003** (`bostrom2003`; B §4) sits sideways to all of this. He imports substrate independence as an undefended premise, weakens it to its minimum, and uses it to found an argument in a different field entirely — which is itself evidence about how settled the thesis looked by then.

**What changed by the end.** Two challenges that could have ended the doctrine on technical grounds did not. But the price of answering them was that computational identity became a contested, possibly content-dependent matter, and the brain-as-digital-computer analogy — which most arguments for substrate independence had quietly assumed — was removed on empirical grounds by its own defenders.

### 2.4 Theories of consciousness become machine tests, and the testability crisis opens (2014–2021)

**Live questions.** Can a scientific theory of consciousness decide the machine case? Can such a theory be tested at all? Does biology matter after all? And what do we owe a machine whose status we cannot settle?

**Who asked.** Consciousness scientists, neuroscientists, philosophers of mind and — for the first time here — ethicists.

**Key works.**
- **Tononi & Koch 2015** (`tononi2015`; D §1) is the moment the leading physically-grounded theory states in one sentence that it contradicts functionalism: "in sharp contrast to widespread functionalist beliefs, IIT implies that digital computers, even if their behaviour were to be functionally equivalent to ours … would experience next to nothing" (p. 1). Endnote 15 exempts neuromorphic hardware, so the rejection targets computation, not non-biological substrates.
- **Dehaene, Lau & Kouider 2017** (`dehaene2017`; D §2) gives the opposite answer from the same starting point: consciousness is two computations — global availability and self-monitoring — and "the empirical evidence is compatible with the possibility that consciousness arises from nothing more than specific computations" (p. 492).
- **Graziano 2017** (`graziano2017`; D §3) changes the explanandum: the attention schema explains why a machine *claims* to have subjective experience, and "emphatically does not explain how we have a subjective experience" (p. 5).
- **Doerig et al. 2019** (`doerig2019`; D §4) turns a philosophical worry into a construction recipe. Because recurrent and feedforward networks are both universal function approximators, any experimental result supporting a causal-structure theory can be reproduced by a system with opposite structure. Either such theories are falsified or they are "outside the realm of science" (p. 49).
- **Kleiner & Hoel 2021** (`kleiner2021`; D §5) generalise: the problem is the testing scheme itself, and it catches both camps. Independence of prediction and inference data means the theory is already falsified; strict dependence means it is unfalsifiable.
- **Godfrey-Smith 2016** (`godfreysmith2016`; C §1) and **Seth & Tsakiris 2018** (`seth2018beast`; C §2) bring biology back — but as an *immanent* correction. Metabolism is part of a human's functional profile; perception exists in order to regulate the body. Neither says a machine could never qualify.
- **Schwitzgebel & Garza 2015** (`schwitzgebel2015`; E §1) opens the ethics strand without committing to any theory: only psychological and social properties bear on moral status, so some possible AI deserves human-like consideration, and creating a mind would generate obligations exceeding those owed to a stranger.
- **Klein 2016** (`klein_maudlin`; F §2) is the corpus's only retrospective on Olympia, written from inside computationalism. He grants the argument's premises their force, denies the conclusion, and relocates the dispute: stated over input–output *functions*, computationalism collapses — any computable function can be made a single architectural primitive, so an extended conscious episode becomes one structureless step. Stated over *architectures* and the processes actually running in them, Olympia turns out to **emulate** a Turing machine rather than implement one, because her parts are not arranged as a Turing machine's parts are. The consequence he accepts without hedging: a virtual machine, "even the virtual machine that would arise from a simulation of my brain in all computationally relevant detail", is not a candidate for consciousness — a conclusion he notes is "suspiciously close to what Searle (1980) says", reached by a route that rejects Searle's argument.
- **The higher-order family** (higher-order thought theories and perceptual reality monitoring) is present in this corpus only inside the works that survey it — `butlin2023` draws four indicators from it, and `shevlin2021` and `seth2025` discuss it — because no primary statement of it was fetched. It is the fourth of the four theory families the indicator method uses, and **its absence as a node should be visible on any diagram of this era**.
- **Shevlin 2021** (`shevlin2021`; E §2) names the methodological problem that all of this shares: a substrate-neutral theory cannot be applied to a non-human system until its level of abstraction is fixed, and stating it abstractly enough to be substrate-neutral certifies network time protocol as global information sharing (p. 302).

**What changed by the end.** The thesis stopped being a background assumption and became something a paper had to declare. It also acquired a second role — as a filter on which theories get assessed at all ([§3.6](#36-can-theories-of-consciousness-be-tested-and-does-the-thesis-gate-which-theories-count--open)).

### 2.5 Systems that talk back: assessment, precaution, and the biological alternative (2022–2026)

**Live questions.** Are these systems candidates? How would we tell, when they are trained on us? What should be done while the question is open? And is there a positive alternative to computational functionalism, rather than only objections to it?

**Who asked.** Everyone. All six communities contribute, and several works are jointly authored across them.

**Key works.**
- **Butlin, Long et al. 2023** (`butlin2023`; D §6) makes the thesis load-bearing and visible: it is stated, adopted as a working hypothesis, and used to decide which theories are admitted — integrated information theory is excluded "because it is not compatible with computational functionalism" (p. 5). Fourteen indicator properties are extracted and applied to named systems; no current system is a strong candidate.
- **Chalmers 2023** (`chalmers2023llm`; E §3) converts every objection into an engineering challenge and attaches explicit, self-described "extremely rough" credences: under one in ten for current models, about one in four for successor systems within a decade.
- **Aru, Larkum & Shine 2023** (`aru2023`; C §4) answers from neuroscience: impoverished input stream, absent thalamocortical architecture, and organisation that may not be abstractable from life. Their actual position is a third option — "consciousness might be implementable in principle, but it might require a level of computational specificity that is beyond the present-day (and perhaps future) AI systems" (PDF pp. 9–10).
- **Albantakis et al. 2023** (`albantakis2023`; D §7) gives integrated information theory its full formalisation, with three functionally equivalent systems whose Φ values are 21.01, 3.64 and 0: "consciousness is about being, not doing" (p. 39).
- **Coelho Mollo & Millière 2023/2026** (`mollo2023vector`; E §4) attacks a level down: before asking whether a model feels, ask whether its states *mean* anything. Their answer is that meaning needs a selection history, which gives the corpus a restriction on computation that has nothing to do with biology.
- **Millière & Buckner 2024** (`milliere2024`; E §7) names the **Redescription Fallacy** and keeps Blockhead as the standing null hypothesis, making a certain kind of dismissal something a writer now has to defend.
- **Long et al. 2024** (`long2024welfare`; E §5) turns the open question into a governance programme, with an explicit credence assigned to the thesis itself as one term in a product.
- **Birch 2025** (`birch2024`; E §6) supplies the framework Long et al. lean on, and is the batch's outlier in two directions at once: more dismissive of chatbots than anyone ("no one is there") and more worried about machines nobody is watching — insect connectome emulations, evolved agents, minimal global workspaces.
- **Seth 2025** (`seth2025`; C §5) is the systematic statement of the alternative: conscious AI requires *both* computational functionalism *and* substrate flexibility extending to silicon, and both are assumed rather than established.

**What changed.** The evidential centre of gravity moved from behaviour to architecture, in six works independently ([§3.7](#37-is-what-a-system-says-or-does-evidence-about-whether-it-has-a-mind--leaning)). And the debate acquired institutions: a report to companies, a proposed corporate role, a proposed citizens' panel, and a methodology that had already changed a national statute in the animal case.

---

## 3. Debates

Nine debates cut across the eras. Statuses use the scale in [Reading conventions](#reading-conventions) and describe the *reviewed corpus*. Full position lists with keys are in `positions.csv` (68 rows).

### 3.1 Is running the right computation sufficient for a mind? — **open**

**In plain words.** If a machine ran exactly the computation your brain runs, would it have a mind, and would it feel anything?

**Positions.**
- *Yes, as a matter of natural law.* `chalmers1994cfc` (A2 §5), `chalmers1995qualia` (B §3), `chalmers1996rock` (A2 §1), `cuda1985` (B §2), `bostrom2003` (B §4). Mental properties are organizational invariants; the replacement arguments price the denial.
- *Yes, and here are the computations.* `dehaene2017` (D §2), `graziano2017` (D §3), `butlin2023` (D §6), `doerig2019` (D §4), `chalmers2023llm` (E §3).
- *No — semantics and causal powers are missing.* `searle1980` (B §1).
- *No — occurrent experience cannot turn on inert machinery.* `maudlin1989` (F §1). Sufficiency, necessity and supervenience form an inconsistent triad; only sufficiency dies.
- *No — consciousness is intrinsic cause-effect power, not computation.* `tononi2015` (D §1), `albantakis2023` (D §7).
- *No version of functionalism avoids both liberalism and chauvinism.* `block1978` (A1 §3), with `blockfodor1972` (A1 §1) as its first half.
- *Not a priori either way; it is an empirical question about the brain.* `piccinini2010` (A2 §3), `piccinini2013` (A2 §6).
- *Plausible but unearned; life may be doing work the thesis ignores.* `godfreysmith2016` (C §1), `seth2018beast` (C §2), `aru2023` (C §4), `seth2025` (C §5), `cleeremans2022` (C §3).
- *Computationalism survives, but only as a claim about architectures and actual processes.* `klein_maudlin` (F §2).
- *The question has no determinate answer.* `dennett1988` (G §1). Counted as *supporting* the thesis, but defensively and indirectly only: the paper removes a stumbling block and argues nothing about programs, substrate or implementation, and never says the machine has qualia.
- *Assign it a credence and proceed.* `long2024welfare` (E §5), `birch2024` (E §6), `schwitzgebel2015` (E §1), `kleiner2021` (D §5).

**Key exchanges, in order.**
1. Block & Fodor 1972 raise absent qualia and defer them; Block 1978 cashes the deferral and closes his own 1972 escape route in a footnote (A1 cross-paper note 2). Treat these as one developing position.
2. Searle 1980 against strong AI; Cuda 1985 against Searle, quoting the brain-simulator paragraph as his target (B §2, p. 111).
3. Searle answers the replacement scenario in 1992 — accepting fading but denying the subject is *mistaken* — and Chalmers quotes him and answers that the beliefs have nowhere to live (B §3). This is the closest the corpus comes to a directly quoted exchange between two principals about the same claim; Klein quoting Maudlin (F §2) and Kleiner & Hoel self-describing as correcting Doerig et al. (D §5) are the other two candidates.
4. Piccinini's dilemma against Chalmers's abstract causal organisation, in a footnote, with **Piccinini himself** conceding the point is "fair" while saying it "makes a difference only insofar as we have good evidence that computation is sufficient for mentation" (A2 §3 n. 8, p. 275).
5. Tononi & Koch 2015 state the contradiction; Dehaene et al. 2017 answer that "mere information-theoretic quantities do not suffice" (D §2, p. 492).
6. Maudlin 1989 attacks the counterfactual defence itself; Chalmers 1996 concedes the point in a footnote and defers it (A2 §1 n. 3); Klein 2016 finally takes it up and answers by re-stating what computationalism is a claim *about* (F §2).
7. Dennett 1988 denies that the thing being argued over is well defined. **This is not an exchange.** He predates Chalmers 1995 by seven years, does not cite Searle at all, and does not cite Cuda; Chalmers's defence of the reliability of introspection is not a reply to him. The two meet at exactly one premise, stated independently in the opposite time order (G cross-paper note 2).
8. Butlin et al. 2023 adopt the thesis and exclude integrated information theory; Seth 2025 flags that their conclusions depend on the assumption (C §5, PDF p. 6).

**What each side leans on.** Supporters: thought experiments (fading and dancing qualia, gradual replacement), a formal account of implementation, and the absence of any account of what else could matter. Opponents: a thought experiment (the Chinese Room), a formal identity claim plus a mathematical fact about feedforward reconstruction, and — from the biological side — accumulating detail about how neural function is entangled with metabolism. **Nobody collects data bearing directly on the question.**

**Status now: open.** No reviewed work concedes to another. **Of the 29 works that hold a position in *this debate*, 11 support, 9 restrict, 5 reject and 4 abstain.** That is not the corpus-wide stance tally (14/13/5/4 over 36 reviewed works): seven works carry a stance but hold no position here, because their argument is about individuation, grounding or specificity rather than sufficiency. **A figure drawn from `positions.csv` shows 29 nodes and must not be captioned with 36.** Neither figure is a vote — the corpus was assembled to trace this thesis. *Corpus limit:* the works most likely to change the count — Putnam 1988, Searle 1990/1992, Bechtel & Mundale 1999, Thompson 2007, Block 1995 — are all named-only.

### 3.2 Does every ordinary object implement every computation? — **leaning**

**In plain words.** If a rock can be described as running your brain's program, then saying a mind is a program says nothing. Does that follow?

**Positions.**
- *Yes.* Putnam 1988 and Searle 1990/1992. Both are **named-only**: the corpus contains only their critics' reconstructions.
- *No, once implementation requires counterfactual-supporting transitions.* `chalmers1996rock` (A2 §1), `chalmers1994cfc` (A2 §5).
- *The counterfactual requirement is met cheaply, so it does not do the work claimed.* `sprevak2010` (A2 §4, PDF p. 10 n. 9).
- *Concede perspectivalism and relocate the answer to scientific practice.* `shagrir2006` (A2 §2).
- *The Putnam–Searle problem is not serious; a different multiplicity problem survives.* `piccinini2010` (A2 §3, p. 281).
- *Grant that counterfactual restrictions work, and you inherit a different problem.* `maudlin1989` (F §1), `klein_maudlin` (F §2). Maudlin presupposes for argument's sake that they block explosions, which makes his argument a dilemma: "either one accepts explosion, or else one accepts a modal mismatch between computation and consciousness" (F §2, PDF p. 8).
- *Restrict computing systems to teleofunctional mechanisms.* `mollo2018` (A2 §7).

**Key exchanges, in order.** Chalmers's reply (1996) → his own clock-and-dial and input-memory constructions conceding weakened versions → Shagrir's concession and relocation (2006) → Piccinini's refusal to fight this battle and substitution of a different one (2010) → Sprevak's reading of Chalmers's concession (2010) → Coelho Mollo's teleofunctional restriction (2017).

**What each side leans on.** Formal constructions, on both sides — Putnam's mapping, Chalmers's clock and dial, Chalmers's exponential-explosion counterexample, and Coelho Mollo's equivalence classes. No empirical content at all.

**Status now: leaning**, and the direction must be stated narrowly. What no reviewed work contests is that **Putnam's mapping construction reproduces only a trace, so some modal constraint is required**. What *is* contested is whether a **non-semantic** modal constraint suffices: Sprevak holds that non-semantic realization functions stay cheap enough to return universal realization (A2 §4, PDF pp. 10–11), which is exactly the further claim a broader lean would assert. Piccinini calls the Putnam–Searle problem "not very serious" but for a different reason, and Maudlin accepts the constraint and argues it is bought at a price. *Corpus limit:* the objection's sources are not held, and **neither is any of the post-1996 triviality literature** (Godfrey-Smith 2009; Scheutz; Rescorla; Schweizer). This debate is more live in the field than the corpus makes it look.

### 3.3 Which computation is a system running, and does meaning decide? — **open**

**In plain words.** One circuit can be called an AND gate or an OR gate depending on which voltage you call "1". What fixes which computation a system is running?

**Positions.**
- *Syntactically, with no appeal to content.* `chalmers1994cfc` (A2 §5, PDF p. 6): building semantic content into implementation conditions would ground computation on a notion that "desperately needs a foundation itself".
- *Mechanistically — digits, strings, rule-governed manipulation.* `piccinini2010` (A2 §3), `piccinini2013` (A2 §6).
- *By mathematical content only.* `shagrir2006` (A2 §2, pp. 411–12).
- *By representational content of any type, including broad content.* `sprevak2010` (A2 §4).
- *Functionally, over equivalence classes of physical states — with logical indeterminacy left standing one level up.* `mollo2018` (A2 §7).
- *By architecture and by the process actually running, individuated mechanistically.* `klein_maudlin` (F §2, PDF pp. 9–16).
- *By selection history, not by present computation at all.* `mollo2023vector` (E §4, §7.1).

**Key exchanges, in order.** Shagrir's brown–cow cell (2006) and Sprevak's AND/OR circuit (2010) are the same argument, written independently within four years (A2 §4). Piccinini rejects the semantic view outright, naming Shagrir (2010, p. 282); Piccinini & Bahar name Shagrir again as committing an "information processing" fallacy (2013, p. 477); Coelho Mollo grants the semanticists' structural point and denies them the conclusion by relocating mechanism to implementation (2017, §5, §7). Coelho Mollo & Millière then add a constraint nobody in the earlier debate had: parameter-identical systems can differ in content because of history.

**What each side leans on.** Cases and engineering practice. Piccinini's strongest argument is deference: "computability theorists and computer designers … individuate computational states without appealing to their semantic properties" (A2 §3, p. 282). Sprevak's is symmetry: nothing physical breaks the tie. Both are claims about practice that could be surveyed and are not.

**Status now: open.** Five incompatible accounts stand; the most recent (selection history) is orthogonal to the rest rather than a rival within the old frame. *Corpus limit:* Egan, Dewhurst, Haimovici and Piccinini's own 2008 and 2015 statements are known only through the papers answering them, and Marr 1982 is read three incompatible ways inside the corpus ([§6](#6-corrections-and-mis-statements)).

### 3.4 How fine must functional equivalence be? — **open**

**In plain words.** Copy a brain at what level of detail — the computations it performs, single neurons, individual synapses, sub-neuronal receptors? Everyone needs an answer, nobody gives the same one, and some say the question is the wrong shape.

This is the field's unresolved axis, and it has its own data file (`grain.csv`, 31 rows). **Two cautions before the table.** First, `grain.csv` (31 keys, earliest 1972) and this debate's position list (17 keys, earliest 1980) are *different sets*: the data file records every reviewed work that commits to or comments on a level, while the debate records only those the reviews place in the dispute. Any figure must say which set it is drawing. Second, the table below reads as a single ordered scale, and **nine of the 31 rows deny that it is one** — see the last line.

| Setting | Who | Locus |
|---|---|---|
| Unspecified — whatever "reproduces the causes and not merely describes them" | `searle1980` | Author's Response, pp. 452–53 |
| Each neuron's functional role ("circuit functional equivalence") | `cuda1985` | pp. 124–25 |
| Fine enough to fix behavioural dispositions; for brains, probably neural | `chalmers1995qualia`, `chalmers1994cfc` | §1; PDF p. 7 |
| Individual synapses | `bostrom2003` | p. 244 |
| Marr's algorithmic and representational level | `butlin2023` | pp. 13–14 |
| Sub-neuronal: dual-compartment pyramidal neurons, metabotropic receptors | `aru2023` | PDF pp. 9–12 |
| No bottom at all; metabolism does not stop anywhere | `seth2025`, `godfreysmith2016` | §4.1; PDF pp. 11–12 |
| The input–output level: what it does, not how | `doerig2019` | p. 56 |
| An architecture's primitive operations, not the function computed | `klein_maudlin` | PDF pp. 9–16 |
| Four rungs, of which only the counterfactual top rung is denied | `maudlin1989` | pp. 426–29 |
| A definite grain, derived from the exclusion postulate | `tononi2015`, `albantakis2023` | pp. 9–10; p. 10 |
| **Not a setting at all: nine rows are about the parameter rather than points on it** | `shevlin2021`, `birch2024`, `long2024welfare`, `blockfodor1972`, `block1978`, `sprevak2010`, `mollo2023vector`, `seth2018beast`, `maudlin1989` | see `grain.csv` |

**One work maps the axis explicitly.** Maudlin's ladder of abstraction has four rungs, and he concedes the first three: any substrate carrying the same pattern of activity, any causal process with the same pattern of interaction, and the physical processes themselves. He denies only the fourth — a connection that is merely counterfactual or informational, with no causal chain (F §1, pp. 426–29). **A synthesis that presents Olympia as an argument against substrate independence is misreading it**; the paper's own words are that it "does not purport to establish that things with minds must be wet and squishy". Klein then relocates the axis again: not how finely you copy, but which *architecture* the copy has, since a virtual machine with the same organizational invariants is not a process that actually has that architecture (F §2, PDF p. 16).

**Key exchanges, in order.** Cuda's note 1 complains that Searle never cashes out "causal powers" beyond gesturing at biochemistry (B §2, p. 126). Cuda then states his own limit explicitly — sufficiency at circuit grain and at no coarser level. Chalmers leaves it at "likely the neural level". Bostrom fixes it at synapses without argument. Shevlin 2021 makes the omission the topic: conservatism restricts consciousness to humans, liberalism certifies network time protocol. Birch places the scale of functional organisation inside the zone of reasonable disagreement and advises routing around it. Seth 2025 is the only reviewed work proposing an *empirical* route — causal and informational closure measures — and it is proposed, not run.

**What each side leans on.** Nothing, in the sense that matters. No reviewed work argues that another's setting is wrong; they simply assume different ones. The two constructions that could in principle discriminate — Chalmers's dancing-qualia switch and Seth's closure measures — are described as pointless to perform and not yet performed, respectively.

**A relation between arguments, not a citation.** Maudlin addresses the gradual-replacement argument form directly and does *not* refute it: he calls it a *tu quoque* (it rests on the same supervenience intuition he is using) and then concedes that it needs a *stronger* supervenience thesis than his, since a silicon brain is physically distinguishable from an organic one in a way that Olympia with and without the extra blocks is not (F cross-paper note 3). The two arguments are aimed at different rungs, and neither touches the other. Maudlin predates Chalmers 1995 and does not cite Cuda 1985, so `edges.csv` records no link here.

**Status now: open.** *The curator's reading, offered as a reading:* this is the debate whose openness plausibly explains the others', since sufficiency, biology and the language-model question each turn on a setting of it and none can be settled while it is unfixed. **No reviewed work states this ordering.** The closest support is the three meta-positions (`shevlin2021`, `birch2024`, `long2024welfare`), which say only that the parameter cannot be fixed from the human case. *Corpus limit:* no reviewed work proposes an experiment that has been run, and the meta-position is stated but not itself contested.

### 3.5 Does being alive matter, and in which of its three senses? — **open**

**In plain words.** Is a mind something only a living thing can have — and if so, is it metabolism, bodily self-regulation, or specific brain wiring that does the work?

**Three claims, not equivalent** (C cross-paper note 4). Merging them is the commonest error in citing this literature.
1. *Metabolism and self-maintenance.* `godfreysmith2016` (C §1), `seth2025` (C §5). "Metabolic activity is part of the 'functional' profile of a human agent" (PDF pp. 11–12) — an immanent correction that grants functionalism's framework and contests the inventory of functions.
2. *Allostatic regulation and interoception.* `seth2018beast` (C §2), `seth2025` §4.1, touched by `cleeremans2022` (C §3). Perception exists to keep the body viable, and that shapes what experience is like.
3. *Specific neural architecture.* `aru2023` (C §4). Thalamocortical loops, ascending arousal, dual-compartment layer 5 pyramidal neurons. **This third claim is compatible with substrate flexibility** — a machine with the right circuits would qualify.

**On the other side.** `chalmers2023llm` (E §3, PDF p. 7): the biology requirement is "a sort of biological chauvinism … silicon is just as apt as carbon". `tononi2015` and `albantakis2023` draw the line elsewhere entirely — computation versus physical causal organisation, with neuromorphic hardware exempted by name (D cross-paper note 7). `searle1980` sits between: brains cause minds, but "only a machine could think", and silicon is an empirical question.

**Key exchanges, in order.** Godfrey-Smith 2016 → cited by Seth 2025 §3.3 as the "differences on the inside" objection to neural replacement. Aru et al. 2023 → Seth 2025 §4.1 borrows "skin in the game" by name. Seth & Tsakiris 2018 → Cleeremans & Tallon-Baudry 2022 for the visceral grounding of the subject, and → Seth 2025 §4.5. Thompson 2007, the hub all three cite, is not held. Against: Chalmers sets the objection aside rather than arguing it. **The one-in-three figure is not his own credence.** He writes that "on mainstream assumptions, it wouldn't be unreasonable to hold that there's at least a one-in-three chance … that biology is required", and his note 29 says his own credences for the various requirements are *lower* than the mainstream ones he computes with (E §3, PDF pp. 14–15).

**What each side leans on.** The biological side leans on detail: nanoscale molecular dynamics, homeostatic spiking that protects neurons from reactive oxygen species, anaesthetic decoupling of apical and basal dendritic compartments, the energetics of error correction. None of it bears *directly* on whether consciousness requires life; it lowers a prior. The other side leans on the replacement arguments and on the absence of a stated alternative mechanism.

**Status now: open**, with one fact about the corpus that must not be read as a fact about the field: **nobody in the reviewed biological batch rejects computational functionalism.** Four of five are recorded as `restricts`, each declining the stronger claim in their own words; Aru et al. carry three explicit disclaimers and Seth writes "the arguments so far do not disprove computational functionalism" (C cross-paper note 1). The biological challenge in its 2016–2025 form is a challenge to an *assumption*, framed in credences. *Corpus limit:* Thompson 2007 is the batch's missing hub, and the multiple-realizability literature is not argued with on its own terms anywhere.

### 3.6 Can theories of consciousness be tested, and does the thesis gate which theories count? — **open**

**In plain words.** Every measurement of consciousness runs through a report. Can any theory survive that? And is "computation suffices" now being used to decide which theories get assessed at all?

**Positions on testability.**
- *Causal-structure theories are falsified or outside science.* `doerig2019` (D §4), with three appendices giving explicit constructions.
- *The testing scheme itself is the problem, and it catches both camps.* `kleiner2021` (D §5). Independence → already falsified; strict dependence → unfalsifiable.
- *The same fact shows behaviour is a bad guide, not that the theory is untestable.* `tononi2015` (D §1), `albantakis2023` (D §7).
- *Proceed by architectural indicators drawn from several theories at once.* `butlin2023` (D §6).
- *Operationalise the theory and measure it.* `dehaene2017` (D §2), `graziano2017` (D §3).
- *Nothing can be applied until the theory's level of specificity is calibrated.* `shevlin2021` (E §2).
- *The higher-order family* (higher-order thought; perceptual reality monitoring) is a live position in this dispute but **has no primary statement in this corpus** — it appears only inside `butlin2023`, which derives four indicators from it, and in discussions by `shevlin2021` and `seth2025` ([§10](#10-known-works-not-held)).

**Positions on the gate.** `butlin2023` excludes integrated information theory from its survey "because it is not compatible with computational functionalism" (p. 5, with the fuller statement at p. 33). `seth2025` flags that the report's conclusions depend on the assumption, and `long2024welfare` answers the same problem differently, by assigning the thesis a credence rather than adopting it. This is the cleanest evidence in the corpus that the thesis now functions as a methodological gate as well as a metaphysical claim.

**Key exchanges, in order.** Tononi & Koch 2015 state the recurrent-to-feedforward fact themselves (p. 13, with a bounded-time-step qualification) → Doerig et al. 2019 build a construction recipe on it and draw the opposite conclusion, naming the convergence explicitly (p. 56) → Kleiner & Hoel 2021 describe their own paper as "both a generalization and correction" of Doerig et al. and expose the functionalist theories the unfolding argument protects → Albantakis et al. 2023 restate the fact citing Krohn & Rhodes and restate the opposite inference → Butlin et al. 2023 build a method that sidesteps the whole dispute by excluding the theory that generates it.

**What each side leans on.** Formal results: universal approximation theorems, prime decomposition, Φ-increasing devices from the Aaronson–Tononi exchange, and Kleiner & Hoel's two theorems. On the other side, clinical measures — the perturbational complexity index falling across sleep, anaesthesia and disorders of consciousness — which Doerig et al. explicitly accept as *markers* while denying the identity (p. 54).

**Status now: open.** Doerig's and Kleiner's results stand unanswered in the corpus and are not accepted either; the published replies (Kleiner 2020; Tsuchiya, Andrillon & Haun 2019) are named but not held. *Corpus limit:* one side of this exchange is absent by construction, so the debate reads more one-sided here than it is.

### 3.7 Is what a system says or does evidence about whether it has a mind? — **leaning**

**In plain words.** A chatbot trained on human talk can say it feels things. Is that evidence, and if not, what is?

**Positions.**
- *Downgrade behaviour, upgrade architecture.* `chalmers2023llm` (E §3), `long2024welfare` (E §5), `birch2024` (E §6), `shevlin2021` (E §2), `milliere2024` (E §7).
- *Human reactions to machines are unreliable in both directions.* `schwitzgebel2015` (E §1).
- *Only the internal causal organisation counts.* `tononi2015` (D §1), `albantakis2023` (D §7), `aru2023` (C §4).
- *Signatures of the right computations do count.* `dehaene2017` (D §2), `doerig2019` (D §4), `butlin2023` (D §6).
- *What a machine says is a readout of its self-model's format, not of an underlying fact.* `graziano2017` (D §3, p. 5).
- *First-person report cannot settle even the subject's own case.* `dennett1988` (G §1). **This is about human introspection, not machine behaviour**, and no reviewed work connects the two. It is listed here because it is the corpus's most radical claim about report as evidence, and because it attacks the premise Chalmers's argument leans on hardest — "that rational conscious beings are generally correct in their judgments about their experiences", restricted to rational, unimpaired systems. Dennett's cases are rational and unimpaired by construction.

**Key exchanges, in order.** Block 1978's list-searcher makes the point first, against a *reply* to his own argument. Dennett 1988 makes the sharper, human-side version and is not picked up. Schwitzgebel & Garza 2015 state it symmetrically (the ASIMO Problem). Shevlin 2021 generalises it (the gerrymandered robot). Chalmers 2023 applies it to self-report, citing a one-word prompt change that reverses a model's answer. Birch supplies the name — the **gaming problem** — and pushes it further than anyone else with the greenwashing analogy: "immaculately ticking off all the boxes can become evidence *against*" (E §6, p. 13). Millière & Buckner reach the same place from psychologism: behavioural indistinguishability is compatible with mere retrieval.

**What each side leans on.** One measured demonstration (the prompt-reversal experiment), one survey of user attributions, developmental psychology on why people over-attribute, and otherwise argument. The architecture side leans on architectures being inspectable — which Millière & Buckner note is "outright impossible for closed models whose weights are not released" (E §7, p. 19).

**Status now: leaning**, toward architectural rather than behavioural evidence for trained systems. This is the strongest convergence in the corpus — **but it is five works in one position plus Schwitzgebel & Garza's symmetric version, and it is not independent.** Long et al. share two authors (Chalmers, Birch) with works they cite for it; separately, Butlin is a main author of Long et al. while Long is joint first author of Butlin et al. (E cross-paper note 1; [§4](#4-how-the-communities-relate)). *Corpus limit:* Dennett's version of the worry, about human introspection rather than machine behaviour, has no successor here and is connected to the machine case by nobody.

### 3.8 Are today's language models candidates for minds? — **leaning**

**In plain words.** Does anything in a large language model make it a serious candidate for having experiences?

**Positions.**
- *Not yet, but the obstacles are temporary.* `chalmers2023llm` (E §3): five of six objections describe things ordinary engineering is already removing. His stated figures are "somewhere under 10 percent" now and "25 percent **or more**" for extended systems within a decade, both offered as "extremely rough numbers for illustrative purposes".
- *No, and the reasons are architectural.* `aru2023` (C §4), `birch2024` (E §6), `dehaene2017` (D §2). Birch's reason is the sharpest: "no sub-network anywhere in the world [is] dedicated to your conversation" — "no one is there" (p. 13).
- *No current system is a strong candidate on any theory's indicators.* `butlin2023` (D §6), `long2024welfare` (E §5). Long et al.'s 30–50% for the thesis is explicitly an *illustrative* range; their own stated estimate is ~50%, giving ~22.5% for near-future moral patienthood via the sentience route. **Butlin et al. and Long et al. are not two independent assessments**: Butlin is a main author of the second, Long joint first author of the first.
- *Unlikely along current trajectories; more plausible as systems become life-like.* `seth2025` (C §5), `cleeremans2022` (C §3).
- *Ask about meaning before asking about experience.* `mollo2023vector` (E §4), `milliere2024` (E §7).
- *The credible routes do not run through chatbots at all.* `birch2024` (E §6): connectome-based insect emulation, evolved agents converging without gaming, deliberate minimal global workspaces — because sentience and intelligence may decouple.

**Key exchanges, in order.** The Lemoine/LaMDA episode of 2022 is the trigger cited by both Chalmers and Long et al. Chalmers 2023 sets the frame with two explicit credences. Aru et al. 2023 answer from neuroscience the same year. Butlin et al. 2023 score real architectures. Birch 2025 disagrees with Chalmers in two directions simultaneously — more dismissive of chatbots, more worried about other machines — and since both authored Long et al. 2024, that report is *not* evidence that they agree (E cross-paper notes 4–5).

**What each side leans on.** Interpretability results (Othello board-state probes), benchmark and Turing-test rates, architectural inspection, and two opinion surveys used by Chalmers to set his credences. Also one piece of the corpus's rare quantitative honesty: Chalmers states that his own views lean *more* toward widespread consciousness than the numbers he computes with (E §3 n. 29).

**Status now: leaning**, toward no current system being a strong candidate — every work that gives a verdict says so, including the most permissive. The trajectory question is wide open, and the disagreement between Chalmers and Birch about *where to look* is the sharpest live disagreement in the corpus. *Corpus limit:* no reviewed work argues at length against AI moral status from inside the AI-minds literature; opponents appear only as reported objections inside works that answer them.

### 3.9 What should be done while the question stays open? — **open**

**In plain words.** If nobody can settle whether a machine feels anything, who decides how to treat it, and on what evidence?

**Four recommendations, and they do not compose** (E cross-paper note 4).
- *Do not build the uncertain cases.* `schwitzgebel2015` (E §1): the **Excluded Middle Policy**, paired with **Emotional Alignment** — build machines that evoke the reactions their real status warrants.
- *Assume they will be built; acknowledge, assess, prepare.* `long2024welfare` (E §5), including an appointed corporate **AI welfare officer**.
- *Shift to sentience candidature and let citizens decide precautions.* `birch2024` (E §6): a deliberately low bar as a criterion for negligence, four sequential **PARC tests** applied by a panel of at least 150 ordinary people, and a **run-ahead principle** for AI regulation.
- *Publish the challenge list as a roadmap and equally as red flags.* `chalmers2023llm` (E §3): "One person's barrage of objections is another person's research program" — with the author declining to say the programme should be pursued.

Two further positions sit alongside. `seth2025` (C §5 §6.1): real artificial consciousness "should not be an explicit goal", and conscious-*seeming* AI is far likelier and raises its own forced choice between distorting the circle of moral concern and "brutalising our own minds". `aru2023` (C §4, Box 1) predicts current systems cannot suffer in any morally relevant sense, because a system with no stake in its own continuation has no personal investment.

**Where they conflict.** Birch's framework exists to *govern* exactly the borderline class Schwitzgebel & Garza would forbid creating; he keeps Metzinger's moratorium "on the table" while judging it foreclosed — "frankly, the moment has probably gone". Birch and Long et al. compose on substance and conflict on governance: Birch's central worry is the "tyranny of expert values", and a framework in which a company's appointed expert assesses the company's own systems is close to the arrangement he is warning against.

**What each side leans on.** Analogies and precedent: farmed animals for under-attribution, the Lemoine episode for over-attribution, greenwashing for gaming, and — uniquely — an actual legislative outcome, since Birch's methodology applied to cephalopods and decapods fed into the UK's Animal Welfare (Sentience) Act 2022.

**Status now: open.** Four live procedures, no adjudication, and one of them (do not build) is arguably already foreclosed by events. *Corpus limit:* Birch's framework is read here from the published précis, not the book, and the policy proposals the works assess — Bryson, Metzinger — are named only.

---

## 4. How the communities relate

Links below come only from what the reviews record (`edges.csv`, 110 documented engagements). A missing link means none was recorded among the 36 reviewed works. It does not mean none exists in the wider literature.

**`edges.csv` is not a citation census.** An edge records a documented *engagement*, which is not the same as a citation of the node's own document. The `cites_held_document` column says which: **84 of 110 edges cite the held document (`yes`), 23 cite a sibling statement of the same theory or author (`sibling`), and 3 cite a different document entirely (`other`)** — 26 in all. The gap is largest at the integrated-information node: **of the 13 engagements into `tononi2015`, only 4 cite the held 2015 paper**; the rest cite Oizumi et al. 2014, Tononi 2004, Tononi 2008, Tononi et al. 2016, Albantakis & Tononi 2019 or Koch 2019. That node is best captioned as *`tononi2015` standing for the integrated-information programme*, not as a paper drawing 13 citations.

**Who engages whom.** Of the 110 engagements the relation types are: builds-on 40, critiques 37, reinterprets 14, uses-as-evidence 7, names-as-opponent 6, replies-to 4, excludes 1, flags-as-open 1. Philosophy of mind is the most-engaged destination: `searle1980` draws 14 incoming edges and `block1978` 9, from every era including the last, and the integrated-information node draws 13, most of them critical.

**The field is unusually well connected across communities.** Unlike the sibling imperativism corpus, where philosophy and neuroscience barely meet, here neuroscientists read philosophers and philosophers read neuroscientists. Aru et al. (neuroscience) cite Nagel, von Uexküll and Gibson and are cited in turn by Seth; Butlin et al. is co-authored across AI, consciousness science and philosophy; Long et al. spans philosophy, consciousness science and AI-safety organisations. Two structural reasons: the object of study is shared and concrete, and several people appear in more than one community's papers.

**Where a debate is carried by one community.**
- **Implementation and individuation** ([§3.2](#32-does-every-ordinary-object-implement-every-computation--leaning), [§3.3](#33-which-computation-is-a-system-running-and-does-meaning-decide--open)) is almost entirely philosophy of computation. Six reviewed works, no consciousness scientist engages it, and only Seth 2025 imports any of it into the machine-consciousness debate.
- **The deflationary strand** ([§3.1](#31-is-running-the-right-computation-sufficient-for-a-mind--open)) is carried by **one work, from 1988, with nothing after it.** Every work in Parts D and E presupposes there is a determinate fact about whether a given system is conscious — the thing Dennett denies — and none of them engages the denial.
- **The Olympia argument** ([§3.1](#31-is-running-the-right-computation-sufficient-for-a-mind--open)) is carried by two works, 27 years apart (on a compile date, [§11](#11-scope-and-provenance)), with nothing in between in this corpus. Klein records why: the argument "remains relatively obscure, in part because the bulk of his paper is devoted to constructing an elaborate example that is easily misinterpreted" (F §2).
- **Testability** ([§3.6](#36-can-theories-of-consciousness-be-tested-and-does-the-thesis-gate-which-theories-count--open)) is entirely consciousness science. No philosopher of computation in this corpus engages Doerig or Kleiner, and no AI paper does either.
- **Precaution** ([§3.9](#39-what-should-be-done-while-the-question-stays-open--open)) is carried by ethics-and-policy, with one consciousness scientist (Seth) and one neuroscience team (Aru et al., in a box) contributing.

**Where agreement is an artefact of co-authorship.** This is the single most important caution in this document.
- **Long et al. 2024 is not independent of Chalmers 2023 or Birch 2025.** Chalmers and Birch are contributing authors, and the report quotes Chalmers's credence verbatim as evidence (E cross-paper note 5).
- **Chalmers and Birch disagree about language models**, sharply and in two directions, despite co-authoring that report. The apparent convergence between entries 3 and 5 of Part E is co-authorship, not corroboration.
- **Birch co-authored Butlin et al. 2023**, the report he cites for the risk of building sentient machines.
- **Coelho Mollo appears in two communities** under two different arguments (A2 §7 on individuation, E §4 on grounding) and Millière co-authors both E §4 and E §7.
- **Butlin et al. 2023 and Long et al. 2024 overlap directly.** Butlin is a main author of Long et al.; Long is joint first author of Butlin et al. Any figure showing both as sources for the indicator method, or both scoring current systems as weak candidates, is showing **one author group twice**. (Butlin et al. has 19 authors; the overlap beyond Butlin and Long was not verified here — **check the title pages before the page uses the word "independent" anywhere**.)
- **The behaviour-to-architecture convergence** ([§3.7](#37-is-what-a-system-says-or-does-evidence-about-whether-it-has-a-mind--leaning)) is the place where this matters most, because it is the corpus's strongest apparent consensus.

**Where agreement is an artefact of corpus construction.** The corpus contains no work in these fields that ignores computational functionalism, so the thesis looks more central to each community than it is. The biological batch was assembled around a challenge to it, and therefore contains no biologist who simply accepts it. The AI-minds batch contains no sustained opponent of AI moral status. Multiple realizability appears unchallenged because its challenger is named-only.

**Two non-links worth recording.**
- Seth & Tsakiris 2018 cite Godfrey-Smith — but for his 1996 book, not the 2016 metabolism paper (C cross-paper note 3). There is no edge between them here.
- Several works cite a *sibling* statement of a theory rather than the paper held in this corpus: Dehaene et al. engage Tononi et al. 2016, Chalmers engages Tononi 2004, Shevlin engages Dehaene 2014, Butlin et al. engage Baars 1988. Every such case is flagged in the `evidence` column of `edges.csv`. A diagram drawing these as arrows between held works is drawing a real intellectual link through a citation that names a different document.

---

## 5. What the arguments and evidence do and do not show

The field is mostly argument, not data. This section is explicit about which is which.

### 5.1 What rests on thought experiments

These are the corpus's load-bearing devices, and none of them is an observation.

| Device | Work | What it is meant to establish |
|---|---|---|
| The Chinese nation; the Bolivian economy; the elementary-particle people | `block1978` (A1 §3) | That no version of functionalism avoids both liberalism and chauvinism — offered as burden-of-proof |
| The list-searcher (later "Blockhead") | `block1978` (A1 §3) | **Not** that functionalism fails. It is aimed at a *reply* to Block's own argument — "this is just crude behaviorism" (pp. 281–82). See [§6](#6-corrections-and-mis-statements) |
| Alternative neurosurgery; Chase and Sanborn; thirteen further intuition pumps | `dennett1988` (G §1) | That the pre-theoretical notion of a felt quality answers to no well-defined property — used "in place of formal argument" by design |
| The Chinese Room; the water-pipe brain; internalisation | `searle1980` (B §1) | That instantiating a program is not *sufficient* for intentionality |
| Gradual homunculus replacement with a matched control sequence | `cuda1985` (B §2) | That denying consciousness to the endpoint commits one to an indefensible discontinuity |
| Fading Qualia; Dancing Qualia (the backup circuit and switch) | `chalmers1995qualia` (B §3) | That absent and inverted qualia are *empirically* impossible |
| The Ana-and-Vijay child case; the Sim-as-god case; the fission-fusion monster | `schwitzgebel2015` (E §1) | That existential debt is not a callable debt, and that intuitive ethics may not survive weird minds |
| The Swamp LLM; Lucky Pre-Training; the Chroma game | `mollo2023vector` (E §4) | That content is fixed by selection history, not by present structure |
| The gerrymandered robot | `shevlin2021` (E §2) | That behavioural markers cannot settle machine cases without architectural calibration |
| Olympia; the argument by addition (an inert metal sheet); the argument by subtraction (rusting chains) | `maudlin1989` (F §1) | That computational identity can turn entirely on machinery that does nothing during the run |
| Ms W the silent viola player; the Action Max replay console; Theodore and Alvin | `klein_maudlin` (F §2) | That computation is counterfactually loaded — and that Alvin computes only by virtue of a bolted-on spare |

Chalmers is explicit that his arguments are "a plausibility argument … by showing that the alternatives have implausible consequences", and that an opponent "can still" hold the line at a higher cost (B §3 §2). Block says the same of his. **Neither the strongest argument for the thesis nor the strongest argument against it claims to be a proof.**

### 5.2 What rests on formal results

| Result | Work | What it shows, exactly |
|---|---|---|
| Putnam's construction fails; clock-and-dial and input-memory recover weakened versions | `chalmers1996rock` (A2 §1) | That implementation conditions must be modal, and that inputless finite-state automata are the wrong formalism |
| The exponential-explosion false implementation | `chalmers1996rock` §7 | That the CSA account is "imperfect as it stands" — the author's own verdict |
| Universal approximation + the unfolding construction (three appendices) | `doerig2019` (D §4) | That causal structure and every report-based experiment are doubly dissociated |
| Two theorems on substitution and falsification | `kleiner2021` (D §5) | That independence of prediction and inference data implies already-falsified, strict dependence implies unfalsifiable |
| The formalisation of Φ, with three functionally equivalent systems at Φ = 21.01, 3.64 and 0 | `albantakis2023` (D §7) | That functional equivalence does not entail phenomenal equivalence *on that theory's own definitions* |

**The one thing every party accepts.** That any recurrent system's bounded input–output behaviour can be reproduced by a feedforward system. Tononi & Koch state it in 2015 (p. 13), Doerig et al. call it "uncontroversial and widely accepted (including by proponents of IIT)" (p. 52), and Albantakis et al. restate it in 2023 citing Krohn & Rhodes (p. 37). **The disagreement is entirely about what follows.** A synthesis that presents this as a factual dispute misreads the corpus.

### 5.3 What rests on empirical work — which is very little

- **`piccinini2013` (A2 §6) is the only reviewed work whose verdict turns on data.** Its evidence base is published neurophysiology: spike-timing precision in vitro versus in vivo, variable synaptic delay, stochastic ion channels and transmitter release, rate coding in the crayfish photoreceptor, the failure of precisely-timed spike-pattern analyses, minimal signalling units of 50–100 neurons, spontaneous activity as roughly 75% of brain energy use. And its verdict is narrower than it looks: **it does not test whether the right computation suffices for a mind. It tests what kind of computation the brain performs, and answers "neither digital nor analog".**
- **Empirical support, not empirical verdicts.** Aru et al. cite anaesthetic decoupling of apical and basal dendritic compartments and the persistence of thalamocortical structure through unconsciousness. Tononi & Koch cite the perturbational complexity index falling across sleep, anaesthesia and disorders of consciousness. Dehaene et al. cite ignition, the attentional blink, the psychological refractory period and infant error-related negativity. Cleeremans & Tallon-Baudry cite micro-valence work and call their own evidence "scant" (p. 4). Chalmers cites Othello board-state probes and two opinion surveys. All of this supports a premise; none of it bears on the thesis.
- **Maudlin's one empirically shaped claim** is a reductio he offers against the computationalist, and it is worth stating as a claim: a computationalist must allow that two intervals of *identical recorded neural firing* — every neuron, same rate, same pattern — could differ in whether consciousness is present, because a synapse that never fired in either interval was severed in between (F §1, p. 426). As stated, that is a disagreement about what a sufficiently complete recording of neural activity would settle.
- **Cuda 1985 is the corpus's one genuine two-sided empirical appeal.** He stakes his claim on clinical neuron loss and states the falsifier in both directions: if neuron loss always produced all-or-nothing changes in conscious ability, "we would be justified in believing (2)" (B §2, pp. 123–24). It is second-hand and unquantified, but it is offered as a real test.
- **Nothing in the corpus measures the grain parameter.** Seth's causal and informational closure measures are the only proposal that could, and they are proposed rather than run (C §5 §3.5).

### 5.4 What rests on assumption

- **Bostrom 2003** states substrate independence and declines to defend it: "Arguments for this thesis have been given in the literature, and although it is not entirely uncontroversial, I shall here take it as given" (B §4, p. 244). He is the clearest case, and he is honest about it.
- **Butlin et al. 2023** adopt the thesis as the first of three stated assumptions and name what would follow if it were false (D §6, pp. 11–14).
- **Long et al. 2024** assign it a credence — 30–50% — and design a method that works either way (E §5, p. 15).
- **Multiple realizability** is assumed by every reviewed work and contested by none, because the work that contests it is named-only.
- **Godfrey-Smith's charge** is that the *thought experiment* rests on an assumption: holding function fixed while removing life may be ill-formed, because "metabolic activity is part of the 'functional' profile of a human agent" (C §1, PDF pp. 11–12).

### 5.5 Version caveats that change what may be cited

These are collected from the reviews. Each changes what a citation of the work can claim.

| Work | Held version | What changes |
|---|---|---|
| `chalmers1994cfc` | Author web version; text 1993, **one footnote added 2011**; the headnote says "forthcoming in the *Journal of Cognitive Science* (2012)" while the manifest DOI is `jcs.2011` — `works.csv` uses 2011 for `year_print` | The added footnote restricts computational sufficiency and organizational invariance to *nomological* rather than metaphysical necessity, leaving zombies metaphysically possible. **Any quotation of "computational sufficiency" from this paper must carry it.** Body footnote markers also misalign from note 5 onward. |
| `block1978` | Author-revised anthology reprint (ch. 22, pp. 268–305), **image-only scan** | Page cites do not match the Minnesota Studies original; quotations were transcribed by eye from rendered pages and should be re-verified before publication. |
| `chalmers1995qualia` | Author web version, no pagination, cited by section | The file's header names *Conscious Experience* (ed. Metzinger, 1995); the manifest says JCS 1995. The venue should be checked. Its reference list disagrees with its own body on two dates. |
| `searle1980` | Full BBS treatment | Contains 27 open peer commentaries that were **not reviewed**. Nothing here may be attributed to Block, Dennett, Fodor, Hofstadter or Pylyshyn on this document's authority; only Searle's characterisations of them are reported. |
| `bostrom2003` | Published, but the **text layer dropped superscripts** | Every power of ten was reconstructed from context and footnote 9. Re-verify any figure that will be load-bearing. |
| `godfreysmith2016` | The 2014 NYU talk, later **split into two publications** | Sections 1–4 became the *Journal of Philosophy* paper the DOI points at; section 5 (biopsychism, the latecomer-versus-transformation argument) went elsewhere. Page cites are talk pages. |
| `seth2025` | Accepted, not copyedited BBS target article | **Target article only** — no commentaries, no author response. Table 1 is an unextractable image; its five scenarios were reconstructed from the body text. |
| `aru2023` | Author preprint of the *Trends in Neurosciences* paper | Figures present as captions only; no journal pagination. |
| `butlin2023` | arXiv v3 | A title-page footnote records a **post-v1 softening**: the earlier closing sentence "there are no obvious barriers to building conscious AI systems" was revised. |
| `kleiner2021` | arXiv v3 | Preprint of the *Neuroscience of Consciousness* paper; no journal pagination. |
| `mollo2023vector` | **The 2026 published version**, not the 2023 preprint named in the manifest | It cites and replies to work from 2024 and 2025; §7.2 is a reply to Grindrod 2024 and does not exist in the preprint. Citing "Coelho Mollo & Millière 2023" for §7.2 content is an error. |
| `chalmers2023llm` | Author version of the published *Boston Review* text **plus a July 2023 afterword** | Not the arXiv preprint named in the manifest; the afterword is absent from the preprint. |
| `schwitzgebel2015` | Accepted manuscript with its own pagination | Does not match *Midwest Studies in Philosophy* 39: 98–119. |
| `birch2024` | The published **précis**, not the assigned book | Birch flags omissions and simplifications. Claims about how the book *argues* cannot be checked here. But §12 (AI) is **newer** than the book, updated for 2025. |
| `long2024welfare`, `milliere2024` | arXiv v1 preprints | — |
| `dennett1988` | A **2009 browser printout of the author's own web page**, not a published scan | **No book pagination**, so PDF-page citations cannot be converted. **Figure 1 is missing** ("INSERT FIGURE 1 ABOUT HERE"). The file's header names the source volume *Consciousness in **Modern** Science* while the standard citation gives *Consciousness in **Contemporary** Science*; both are recorded and neither adjudicated. Endnote 14 documents the argument circulating from December 1979 and presented near-final in April 1985, so **1988 understates its currency** relative to Block 1978/1980 and Cuda 1985. |
| `maudlin1989` | Published (JSTOR scan) | The scan **garbles Greek letters throughout**: π, τ and φ appear variously as `ir`, `7r`, `-r`, `r`, `0`, `4`, `X` and `k`. Any quotation lifted from a raw text extraction will contain them. The review states the readings it adopts. |
| `klein_maudlin` | Author web version of a **draft chapter**, with **no publication year** | The PDF names only a venue ("*Routledge Handbook of the Computational Mind*, ed Mark Sprevak and Matteo Columbo") and a compile date ("Draft 1D, compiled October 8, 2016"). **Anything needing a citable published reference must verify it independently**; the review deliberately supplies none from memory, and the PDF misspells the second editor's surname. |
| `mollo2018` | Open-access typeset, deposited as advance online, paginated 1–21 | No volume or page numbers; article year 2017, print issue 2018. |
| `sprevak2010` | Author-typeset postprint paginated 1–29 | Not the journal's 260–270. |
| `fodor1974` | The *Synthese* journal article | The manifest note "chapter" is **wrong**; chapter-based page cites will not match. |
| `piccinini2013` | Published | The running footer prints "Cognitive Science 34 (2013) 453–488"; printed page = PDF page + 452. |
| `doerig2019` | Published, via a repository copy | Two cover pages precede the article. |

### 5.6 Where papers mis-state each other

Recorded, not adjudicated. The full table is [§6](#6-corrections-and-mis-statements); the three that most change how a citation should be read:

1. **Doerig et al. on integrated information theory.** Their gloss is that "φ is always greater than zero in recurrent systems (they are always conscious)" (p. 51). The theory's own statement requires a *maximum* of integrated information, not merely positive Φ (`albantakis2023`, p. 10). Their construction nevertheless respects maximality, so the gloss and the construction come apart (D cross-paper note 3).
2. **Sprevak on Chalmers.** He cites Chalmers 1996 *not* as the solution to universal realization but as showing how cheaply the counterfactual requirement is met (A2 §4, PDF p. 10 n. 9). That is a reading of Chalmers's own §4 concession, not a disagreement with his conclusion (A2 cross-paper note 4).
3. **Marr 1982, read three incompatible ways inside the corpus.** Shagrir: explanatory only via correspondence to represented structure. Sprevak, reporting Egan: purely function-theoretic, which Sprevak argues collapses into a representational reading. Piccinini & Bahar: an instance of a *fallacy* conflating computationalism with mechanistic explanation (A2 cross-paper note 2). Three papers, three uses of the same book, and Marr is not held.

### 5.7 A convergence that is not agreement

Three works in this corpus conclude that a detailed computer simulation of a brain would not be conscious, and **they share no premise**. (Tononi & Koch's endnote 14 claims kinship with Searle and with Leibniz's mill, and `edges.csv` records that as a `builds-on`; but **the kinship is asserted, not argued** — no shared premise is identified, and the routes below are the reasons each actually gives.)
- `tononi2015` (D §1, p. 15): a simulation is *virtual*, and consciousness is real intrinsic cause-effect power — "a computer simulation of a giant star will not bend space–time around the machine".
- `searle1980` (B §1, p. 424): intentionality is a biological phenomenon, and "no one would suppose that we could produce milk and sugar by running a computer simulation of the formal sequences in lactation and photosynthesis".
- `klein_maudlin` (F §2, PDF p. 16): a virtual machine is not a process that actually has an architecture — a conclusion Klein reaches *while defending computationalism*, and calls "suspiciously close to what Searle (1980) says".

Seth's simulation/implementation/realisation distinction (C §5 §3.7) is a fourth route to the same place. **Agreement on this verdict is not evidence of a shared underlying view**, and a diagram that merges these nodes will imply a consensus that does not exist. The routes should be drawn separately (F cross-paper note 5).

---

## 6. Corrections and mis-statements

Claims commonly attributed to a work, against what the reviewed work says. Full table (41 rows) in `field_history_data/corrections.csv`; verdicts are `holds` / `partly` / `does-not-hold` / `misattributed` / `disputed`. Counts: does-not-hold 25, partly 9, misattributed 5, disputed 2.

| Work | Commonly attributed | What the reviewed work says | Verdict |
|---|---|---|---|
| `searle1980` | Searle argues machines cannot think | "Only a machine could think, and indeed only very special kinds of machines" (p. 424). He rejects only the *sufficiency* of running a program (B §1) | does-not-hold |
| `searle1980` | Searle rules out silicon | "I offer no a priori proof that a system of integrated circuit chips couldn't have intentionality. That is … an empirical question" (p. 453) | does-not-hold |
| `searle1980` | Searle concedes nothing to the replacement arguments | Author's Response: "if the stimulation of the causes is at a low enough level to reproduce the causes … the 'simulation' will reproduce the effects" (pp. 452–53) | does-not-hold |
| `maudlin1989` | Maudlin argues against substrate independence, or that machines cannot be conscious | He grants that silicon and hydraulic brains "may, for all we have said, be conscious" (p. 429) and that computational structure may be *necessary* (p. 431); only sufficiency dies (F §1) | does-not-hold |
| `maudlin1989` | Olympia is a funny-instantiation argument like the Chinese Nation | He rejects those intuitions outright — "I cannot think of one reason to accord those intuitions any weight" (p. 414); Klein separates the two families (F §2, PDF p. 8) | does-not-hold |
| `maudlin1989` | Olympia is a triviality or exploding-implementation argument | He presupposes, for argument's sake, that counterfactual restrictions *do* block explosions; the argument is best read as a dilemma (F §2, PDF p. 8) | misattributed |
| `klein_maudlin` | Klein refutes computationalism about consciousness | "I do not think Maudlin's argument succeeds" (PDF p. 7); he defends it while narrowing it to architectures and actual processes (F §2) | does-not-hold |
| `dennett1988` | Dennett denies that conscious experience exists | "Since I don't deny the reality of conscious experience, I grant that conscious experience has properties"; what is denied is that any property is ineffable, intrinsic, private *and* directly apprehensible. The flat closing line is flagged in his own endnote 2 as tactical (G §1) | does-not-hold |
| `dennett1988` | "Quining Qualia" replies to the fading and dancing qualia arguments | It predates Chalmers 1995 by seven years and does not cite him. The two meet at one premise about introspection, stated independently in the opposite time order (G cross-paper note 2) | misattributed |
| `dennett1988` | It is a general reply to the anti-functionalist literature | Block's liberalism/chauvinism dilemma and the input-output problem are untouched, and **Searle 1980 is not in the bibliography at all**; the homunculi-head and Chinese nation are never discussed (G cross-paper note 5) | does-not-hold |
| `dennett1988` | Dennett concludes that a functional duplicate *does* have qualia | He never says the wine-tasting machine has qualia; the conclusion withholds the affirmative verdict as much as the negative (G §1) | does-not-hold |
| `dennett1988` | Dennett and the replacement arguments clash over whether subjects are in error | His conclusion is that there is **no determinate fact**; Cuda's step 2 and Chalmers's Joe are built against a *systematic-error* hypothesis. Whether either reaches the no-fact case is addressed by **no reviewed work** — a gap, not a settled clash (G cross-paper note 3) | disputed |
| `aru2023` | Aru et al. deny that machines could be conscious | Three explicit disclaimers: not only mammalian brains, not only living systems, not impossible in software. The claim is about present systems and specificity (C §4) | does-not-hold |
| `piccinini2010` | Piccinini is an anti-triviality theorist answering Putnam and Searle | He calls their problem "not very serious" (p. 281) and raises a *different* surviving problem about bona fide descriptions (A2 cross-paper note 1) | misattributed |
| `block1978` | Blockhead is an argument against computational functionalism | The list-searcher is offered against a *reply* to Block's own argument — "this is just crude behaviorism" (pp. 281–82) — not against functionalism (A1 cross-paper note 5) | partly |
| `block1978` | Block refutes functionalism | "I do not claim that this is a conclusive argument … it is best construed as a burden-of-proof argument" (p. 296) | partly |
| `chalmers1994cfc` | Chalmers established that the right computation is *metaphysically* sufficient | The 2011 footnote restricts sufficiency and organizational invariance to nomological necessity, leaving zombies metaphysically possible (A2 §5 §2.8) | partly |
| `chalmers1995qualia` | The fading and dancing qualia arguments prove functional duplicates are conscious | §5 states the conclusion is empirical impossibility only, and that the position is compatible with property dualism | partly |
| `cuda1985` | Cuda established that functional organisation suffices for consciousness | Only at *circuit functional equivalence*, and he says so; what he claims more broadly is to disqualify material as a ground of objection (B §2) | partly |
| `blockfodor1972` | Block and Fodor concluded against a computational theory of mind | "It may be both true and important that organisms are probabilistic automata"; the target is the machine-table level (A1 §1) | does-not-hold |
| `tononi2015` | Integrated information theory is carbon chauvinism | Endnote 15: "there is no reason why hardware-level, neuromorphic models … could not approximate, one day, our level of consciousness" | does-not-hold |
| `tononi2015` | On IIT, recurrent systems are always conscious (Doerig's gloss) | IIT requires a *maximum* of integrated information, not merely positive Φ (`albantakis2023`, p. 10); gloss and construction come apart (D cross-paper note 3) | partly |
| `schwitzgebel2015` | They run the Cuda–Chalmers replacement argument | n. 5 (ms. p. 11): they *assume* consciousness is preserved and argue something ethical; Cuda and Chalmers try to *establish* the preservation | does-not-hold |
| `chalmers2023llm` | Chalmers and Birch agree about language models, as their joint report shows | They disagree. Birch: "no one is there" (p. 13). Co-authorship is not corroboration (E cross-paper notes 4–5) | does-not-hold |
| `butlin2023` | The report found no obvious barriers to building conscious AI | A title-page footnote records the revision: satisfying the indicators "would not mean that such an AI system would definitely be conscious" | partly |
| `butlin2023` | The indicator list states necessary or sufficient conditions | "Systems that have more of these features are better candidates … We do not endorse these stronger claims" (p. 45) | does-not-hold |
| `sprevak2010` | Sprevak cites Chalmers 1996 as the solution to universal realization | He cites it to show the counterfactual requirement is cheaply met (PDF p. 10 n. 9) | misattributed |
| `fodor1974` | Fodor argued the autonomous psychological level is computational | He argues only that psychology does not *reduce*; the step is taken by others (A1 §2) | does-not-hold |
| `seth2025` | Seth refutes computational functionalism | "The arguments so far do not disprove computational functionalism. But they do render it less plausible, and less appealing" (§3.6) | partly |
| `cleeremans2022` | *Consciousness Matters* is an anti-functionalist paper | It argues consciousness *has a function*, and its anti-epiphenomenalism runs through multiple realizability (C cross-paper note 2) | does-not-hold |
| `kleiner2021` | Kleiner and Hoel restate the unfolding argument | Self-described "generalization and correction"; the second horn hits the theories the unfolding argument exempts (D cross-paper note 5) | does-not-hold |
| `graziano2017` | The attention schema theory explains subjective experience | "The theory emphatically does not explain how we have a subjective experience. It explains how a machine claims to have a subjective experience" (p. 5) | does-not-hold |
| `dehaene2017` | Dehaene, Lau and Kouider answer the question of experience | Declared beyond scope (p. 492); what is offered is a covariation observation about blindsight | does-not-hold |
| `piccinini2013` | Piccinini and Bahar refute computationalism | They *defend* generic computationalism and reject only its digital and analog species | does-not-hold |
| `mollo2023vector` | The paper shows that language models understand language | The scope restriction is stated twice: not about understanding, knowledge, linguistic acts or mental properties | does-not-hold |
| `bostrom2003` | Bostrom offers a fourth position on substrate independence | He imports it undefended; his value here is as evidence about the thesis's *status* in 2003 (B cross-paper note 9) | misattributed |
| `shagrir2006` | Marr's computational level shows computation is individuated non-representationally | Three reviewed works read Marr incompatibly (A2 cross-paper note 2) | disputed |
| `block1978` | Block's 1972 and 1978 papers are two independent data points | He closes his own 1972 escape route in 1978 (n. 14, p. 300); present them as one developing position | does-not-hold |
| `doerig2019` | The unfolding argument is a version of the zombie argument | §2.5 distinguishes both scope (it *favours* functionalism) and modality (a construction recipe, not a conceivability claim) | does-not-hold |

---

## 7. Current status in one page

Statuses describe the reviewed corpus (see the scale in [Reading conventions](#reading-conventions) and `status_scope` in `debates.csv`).

| Debate | Status (2026) | Why, in one line | What the field itself says is open |
|---|---|---|---|
| Is the right computation sufficient? | open | No reviewed work concedes to another; of 29 works positioned here, 11 support, 9 restrict, 5 reject, 4 abstain | Chalmers: "it is not implausible that minds arise in virtue of causal organization, but neither is it obvious" (A2 §1, pp. 332–33). His deferral of Maudlin — "requires an in-depth treatment in its own right" — is taken up only in Part F |
| Does anything implement every computation? | leaning, toward *no* | Chalmers's modal diagnosis is not contested; his critics say it is insufficient or beside the point | Chalmers's own §7 leaves a uniformity clause and an independence condition unworked-out |
| Which computation is a system running? | open | Five incompatible accounts, with the newest (selection history) orthogonal to the old frame | Sprevak: computation must also be "mechanical" in a sense "yet to be defined"; Coelho Mollo: whether objective teleological functions exist |
| How fine must functional equivalence be? | open | At least eight settings, plus nine works whose claim is about the parameter rather than a setting of it; no reviewed work argues another's setting is wrong | Seth proposes closure measures could "empirically determine … whether neural dynamics can be abstracted away from finer-grained levels" |
| Does being alive matter? | open | The biological works lower a prior rather than refuting; nobody in that batch rejects the thesis | Seth: what distinguishes conscious from non-conscious living systems is "questions for another time" |
| Can theories be tested, and is the thesis a gate? | open | Two formal results stand unanswered, and Butlin et al. proceed by excluding the theory that generates them | Kleiner & Hoel: no current theory or paradigm achieves "lenient dependency" |
| Is behaviour evidence? | leaning, toward architecture | Six works converge independently — but two of them share authors with the work citing them | Millière & Buckner: internal analysis is "outright impossible for closed models whose weights are not released" |
| Are language models candidates? | leaning, toward *not now* | Every work with a verdict says no current system is a strong candidate; they split on trajectory | Chalmers's challenge 12: if all eleven are met and someone still disagrees, "what is the X that is missing?" |
| What should be done meanwhile? | open | Four live procedures that do not compose | Birch: the moratorium "should be on the table, but … frankly, the moment has probably gone" |

**The two things the corpus agrees on.** That any recurrent system's bounded behaviour can be reproduced feedforward ([§5.2](#52-what-rests-on-formal-results)) — and that multiple realizability is true, which is unanimous *by absence*, because the work that challenges it is not held ([§10](#10-known-works-not-held)).

**One thing that looks like agreement and is not.** Three works with no shared premise conclude that a simulated brain would not be conscious ([§5.7](#57-a-convergence-that-is-not-agreement)).

**One question the corpus never asks.** Every work from 2015 on presupposes that there is a determinate fact about whether a given system is conscious. `dennett1988` denies exactly that, and no reviewed work written after it engages the denial. Whether the replacement arguments reach the no-fact hypothesis, as opposed to the systematic-error hypothesis they were built against, is unaddressed anywhere in this corpus.

---

## 8. Relevance to this project (interpretive)

> **Interpretive, not a finding.** Nothing here is about this project's agents, and nothing shows that an artificial agent has experiences. The agents' damage signal is **nociception**, never "pain". Experiment ideas are out of scope and belong to **`research-postdoc`** (triage) and **`professor-pain-modeling`** (construct validity for any "pain-like" claim).

The corpus is about consciousness in machines. This project trains reinforcement-learning agents with a nociception channel and studies how their behaviour changes when that channel is active — a behavioural description, and "pain-like" in that descriptive sense only, never a claim about experience. Three points bear on how that work is described.

1. **The corpus supplies the vocabulary for saying what is *not* being claimed.** Seth's three-way split between *simulating*, *implementing* and *realising* a mechanism (C §5 §3.7) is the cleanest way to state that a model of a damage signal is a model, not an instance. "Nothing gets wet in a weather forecasting computer."
2. **The behaviour-to-architecture shift is a caution about behavioural evidence generally.** Reviewed works converge on the view that a trained system's behaviour is weak evidence about its internal states ([§3.7](#37-is-what-a-system-says-or-does-evidence-about-whether-it-has-a-mind--leaning)). The argument is about consciousness; the structure of the worry transfers to any behavioural signature read off a trained agent.
3. **The corpus offers no ladder these agents could be climbing.** The grain debate ([§3.4](#34-how-fine-must-functional-equivalence-be--open)) asks how finely a *brain* must be copied before the copy inherits its mental properties. This project's agents are not copies of any nervous system, so that debate does not place them anywhere on its scale — high or low. Adding biological detail to a nociception model therefore does not move an agent along any axis this literature recognises, and the reason is not that the threshold is far away; it is that **no threshold in this corpus is defined for a system of this kind**.

This corpus licenses no claim about this project's agents in either direction. Its value here is terminological discipline, not evidence.

---

## 9. Data files for diagrams

All in `field_history_data/`, UTF-8 CSV with a header row, using manifest keys throughout. They were generated from one transcription of the reviews and validated against the manifest by `build_field_history_data.py`, which exits non-zero on any mismatch.

| File | Rows | Contents |
|---|---|---|
| `works.csv` | 42 | Every manifest key: label, plot year, print year, community, era, review status, stance, one-line role, evidence type, debates |
| `eras.csv` | 5 | Era id, label, start and end year, summary |
| `debates.csv` | 9 | Debate id, title, plain question, status, reason, direction, corpus-limit scope, first and latest year of positioned works |
| `positions.csv` | 68 | Positions per debate with keys and a one-line summary |
| `edges.csv` | 110 | Documented engagements: relation, **`cites_held_document`**, and the review locus |
| `grain.csv` | 31 | Every reviewed work that commits to or comments on a level of functional equivalence: level named, page or section, direction code, note |
| `corrections.csv` | 41 | Commonly attributed claim → what the reviewed work says → verdict |
| `not_held.csv` | 40 | Works and strands named in the reviews but not held, with why they matter and which reviewed works cite them |

**Legend and conventions for the figures.**
- **`positions.csv` is authoritative** for which works belong to which debate; `works.csv`'s `debates` column is derived from it. Works with no position have an empty `debates` cell — that is true of `fodor1974`, the named-only keys and the two pending keys.
- **`works.csv` `status`** takes three values here. `reviewed-full` (22) and `reviewed-short` (14) are the two review tiers; `named-only` (6) means no PDF is held. Named-only works carry `stance = unknown`, `evidence_type = unknown`, and a `role` beginning "Not reviewed". **The page should render them differently — greyed, dashed or in a separate lane — and must not attribute a position to them.** The schema also permits a fourth value, `pending-review`, for a held PDF whose review does not yet exist; no work carries it at present ([§11](#11-scope-and-provenance)).
- **`works.csv` `stance`** is the reviewer's own field-history-record judgement, carried over unchanged: `supports` (14), `restricts` (13), `rejects` (5), `neutral` (4), `unknown` (6). This is the **corpus-wide** tally; per-debate tallies are smaller and are computed from `positions.csv` (see `debates.csv` `status_reason`). "Restricts" does **not** mean "rejects" — see [§3.5](#35-does-being-alive-matter-and-in-which-of-its-three-senses--open). Two `supports` values need their role text read with them: `fodor1974` supports only indirectly, and `dennett1988` only defensively.
- **`edges.csv` `relation`** takes eight values: `builds-on` (40), `critiques` (37), `reinterprets` (14), `uses-as-evidence` (7), `names-as-opponent` (6), `replies-to` (4), `excludes` (1), `flags-as-open` (1). Every edge's `from_key` is a reviewed work; named-only works can only *receive*.
- **`edges.csv` `cites_held_document`** is the column that keeps an engagement graph from being read as a citation count: `yes` (84), `sibling` (23), `other` (3). The generator refuses a `sibling` value whose `evidence` cell does not name the document actually cited.
- **Three edges point forward in time** by the `year` column and are deliberate: `mollo2023vector` → `milliere2024` (the held version of record is 2026), and `long2024welfare` → `birch2024` and → `seth2025` (the citations are to the 2024 book and to Seth 2021/2024 respectively, while the keys are dated by later restatements). The generator whitelists exactly these three.
- **`grain.csv` `direction`** was recoded in this revision and now takes seven values: `fine` (7 — at or finer than the neural level), `coarse` (3 — above it), `derived` (2 — the level falls out of the theory's own postulate rather than being chosen: `tononi2015`, `albantakis2023`), `no-bottom` (2 — denies there is a bottom level: `godfreysmith2016`, `seth2025`), `assumed` (1 — commits without argument: `schwitzgebel2015`), `unspecified` (7 — commits to a level but does not locate it on that scale), `meta` (9 — the claim is *about* the parameter rather than a setting of it). **Only the 10 `fine`/`coarse` rows belong on an ordered axis**; the other 21 must be shown off-axis. `grain.csv` (31 keys, from 1972) and the grain debate's position list (17 keys, from 1980) are different sets — say which a figure uses.
- **`debates.csv` `status`** follows the scale in [Reading conventions](#reading-conventions). `status_direction` is filled only for `leaning`; `status_scope` states the corpus limit and should be rendered with the status rather than hidden.
- **Communities.** `unknown` is a permitted lane and is currently empty; every work has a community.
- **Era membership is by `year`, not `year_print`.** Five works differ; see [§11](#11-scope-and-provenance). `mollo2018` is also narrated in era 3 and placed in era 4 — the timeline will disagree with [§2.3](#23-what-is-it-to-run-a-computation-at-all-19962013) on purpose.
- **The appended reviewer-feedback sections are not part of the neutral history.** They are signed working notes on this document. If the page renders the synthesis, it must exclude them or mark them clearly as external commentary.

**Caption caveats every planned figure needs.** These come from the two reviewer gates and are not optional.

| Figure | Caption must say |
|---|---|
| **Stance distribution** | Never a vote and never a pie. `restricts` is not `rejects`; 6 of 42 works have no stance; the corpus was assembled to trace this thesis, so the distribution is a fact about the corpus. `fodor1974` supports only indirectly and `dennett1988` only defensively. |
| **Sufficiency debate** | 29 positioned works (11/9/5/4), **not** the 36-work corpus tally. State which file the nodes come from. |
| **Grain axis** | Only the 10 `fine`/`coarse` rows sit on an axis; show the other 21 off it as derived, assumed, unspecified or unfixable. Say whether the nodes are `grain.csv` (31 keys, from 1972) or the grain debate (17 keys, from 1980). |
| **Engagement graph** | "Documented engagements", not citations. 26 of 110 edges name a document other than the node. The integrated-information node is `tononi2015` *standing for the programme* — only 4 of its 13 incoming edges cite the held 2015 paper. Named-only nodes greyed, and receive-only. |
| **Timeline / works** | Show the works-vs-reviewed gap. `bechtelmundale1999` being named-only is why multiple realizability looks unopposed; `block1995` being named-only is why Block reads as a 1970s figure. |
| **Community lanes** | `biology-and-neuroscience` has exactly **one** work (`aru2023`). Say so or merge the lane; do not let one paper look like a field. |
| **Status badges** | Render `status_scope` beside the badge, never hidden. The two `leaning` badges are the contestable ones, and `triviality`'s direction is deliberately narrow. |
| **Triviality debate bar** | It starts at 1989 only because the 1988 and 1990 sources are named-only. |
| **Any "independent convergence" claim** | Butlin/Long and Chalmers/Birch author overlaps ([§4](#4-how-the-communities-relate)); the 19-author Butlin list was not checked beyond those two. |
| **Any Dennett node** | Label "denies that the felt qualities the debate argues about are a well-defined target" — **never** "denies consciousness". A single pro/anti-functionalism axis puts Dennett and Chalmers on the same side and loses what divides them. |

---

## 10. Known works not held

The reviews cite many works that are not in the corpus. The 40 that matter most for the history are in `field_history_data/not_held.csv`, so their absence is visible rather than silent. **None of them carries a claim in this document.**

**The six named in the manifest but not held.**
- **Putnam 1967** (`putnam1967`), the founding statement both Block papers target. Two different paginations are in play and neither should be treated as canonical (A1 cross-paper note 8).
- **Bechtel & Mundale 1999** (`bechtelmundale1999`), the standard challenge to multiple realizability. Its absence is the single most consequential gap: **multiple realizability is unchallenged in this corpus purely by absence**, and every reviewed work assumes it. The synthesis should say so rather than presenting the premise as settled.
- **Searle 1990** (`searle1990`), the compressed restatement and the source of the wall-runs-WordStar claim Chalmers answers. Its absence means the corpus holds only the 1980 form of Searle's argument.
- **Schneider 2019** (`schneider2019`), source of the AI Consciousness Test that Chalmers, Birch, Butlin et al. and Long et al. all assess. Its absence leaves a 16-year gap between Bostrom 2003 and the AI-minds works.
- **Thompson 2007, *Mind in Life*** (`thompson2007`), cited by all three biological works as the tradition they belong to. The highest-value single addition if the corpus is extended.
- **Block 1995, "On a confusion about a function of consciousness"** (`block1995`), added to the manifest in this round; the fetch failed. It is the **access/phenomenal distinction** the later corpus reaches for whenever it separates global availability from experience — used in Parts C, D and E as a distinction rather than as a work. Without it, Block is represented by 1972 and 1978 alone, so a reader takes "burden-of-proof argument" for his position and never meets his later, substantive anti-computationalism.

**Sources of arguments the corpus only answers.** Putnam 1988 (*Representation and Reality*, the universal-realization appendix); Searle 1992 (*The Rediscovery of the Mind*, containing the fading-qualia passage Chalmers quotes); Egan 1991–95 (the function-theoretic view of computational content); Marr 1982; McCulloch & Pitts 1943 and von Neumann 1951/1958; Haimovici 2013 and Dewhurst 2016; Piccinini 2008 and 2015; Block 1981 (the standalone Blockhead paper); Shoemaker 1975/1982; Lewis 1972 and Armstrong 1968; Harnad 1990; Bender & Koller 2020; Oizumi, Albantakis & Tononi 2014 (IIT 3.0 — the version the unfolding argument actually attacks); Lamme 2006/2010; Baars 1988 and Dehaene 2014; the Aaronson–Tononi exchange of 2014; Maturana & Varela 1980; Hinton 2022 on mortal computation; Barnett & Seth 2023 and Rosas et al. 2024 on closure measures; Cao 2022; Metzinger 2021; Chalmers 1996 (*The Conscious Mind*); Michel & Lau 2021, Wiese 2024, Shiller 2024, Arvan & Maley 2022.

**A second challenge hidden inside a single citation.** `not_held.csv` now carries *Representation and Reality* as two rows, because the book does two separate things. The appendix is the universal-realization argument that [§3.2](#32-does-every-ordinary-object-implement-every-computation--leaning) is about. The book is *also* where functionalism's founder abandons it, on externalist grounds — that content is not fixed by internal functional organisation, so mental states cannot be individuated the way functionalism needs. **That second challenge bears on [§3.3](#33-which-computation-is-a-system-running-and-does-meaning-decide--open), not §3.2, and this corpus holds no trace of it.**

**Three absences that make a debate look one-sided.**
- The published replies to the unfolding argument — Kleiner 2020 and Tsuchiya, Andrillon & Haun 2019 — are named but not held. The testability debate therefore reads as if the formal results stand unopposed. They stand *unanswered in this corpus*, which is not the same thing.
- **The reply literature on the Chinese Room** — the Systems and Robot Replies in their developed forms, and Churchland & Churchland 1990 — is held nowhere, and the 27 BBS commentaries were not reviewed. `searle1980` is the most-engaged work in this corpus and the only reviewed reply to it is `cuda1985`, five years later and aimed at one paragraph. The argument therefore reads here as **less answered than it is**.
- The whole reply literature on Olympia — Barnes 1991, Klein's own 2008/2012/2013/2015 papers, Bishop 2009a,b and Bartlett 2012 — is mapped by Klein and held nowhere. The corpus therefore contains one argument and one retrospective on it, with 27 years and an entire exchange in between, visible only as a bibliography. **Bartlett 2012 is described by Klein as the existing survey of the responses, "albeit in a Maudlin-sympathetic way"**, and is the obvious next fetch for this thread.

**One absence that makes a batch look unanimous.** No work in the AI-minds batch argues at length against AI moral status; opponents appear only as reported objections inside works that answer them. The corpus's opposition to computational functionalism lives in Parts B and C and has to be imported.

**One strand that stops in 1988.** The deflationary line — that there is no determinate fact for the thought experiments to be about — is represented by `dennett1988` and by nothing after it. Its successors (*Consciousness Explained* 1991; Frankish on illusionism) are not held, and **no work in this corpus presses the deflationary objection against the contemporary proposals**, every one of which presupposes a determinate fact about whether a given system is conscious: indicator-property checklists, theory-heavy assessments, credence arithmetic and welfare arguments alike. That is a thirty-seven-year silence in the record, not a settled question, and a 1988 paper should not be left to carry it.

**And one whose absence is a synthesis-level gap, not a corpus one.** The **higher-order family** (higher-order thought; perceptual reality monitoring) has no primary statement here, though `butlin2023` draws four of its fourteen indicators from it. It is the fourth of the four theory families the indicator method uses and should be visible as a missing node ([§2.4](#24-theories-of-consciousness-become-machine-tests-and-the-testability-crisis-opens-20142021), [§3.6](#36-can-theories-of-consciousness-be-tested-and-does-the-thesis-gate-which-theories-count--open)).

---

## 11. Scope and provenance

- **Counts** (from `references_manifest.csv`): **42 references. 22 reviewed in full, 14 reviewed as short summaries, 6 named-only.**
- **The corpus grew twice while this synthesis was being written, and both rounds are integrated.** The brief named 39 works (33 reviewed, 6 named-only). Batch F added Maudlin's Olympia argument and a Klein retrospective (`maudlin1989` upgraded from `named-only` to `pdf`; `klein_maudlin` new), and is the reason [§5.7](#57-a-convergence-that-is-not-agreement) exists. Batch G then added the deflationary strand — `dennett1988` reviewed at full tier, and `block1995` added as `named-only` because the fetch failed. Both rounds carry stances, roles, positions, edges, corrections and, where applicable, grain rows. The `pending-review` status value remains in the generator's schema for a future in-flight batch, but no work carries it.
- **Two counts that must not be confused, and were.** An earlier draft used the corpus-wide stance tally inside the sufficiency debate's `status_reason`. They are different quantities: 36 reviewed works carry a stance, 29 hold a position in that debate. The generator now computes every per-debate tally from `positions.csv` + `works.csv` and **refuses to build if any count written into a `status_reason` disagrees with it**.
- **Ambiguous years.** In each case `works.csv` gives the first public year in `year` and the print year in `year_print`. Era membership follows `year`.

  | Key | year | year_print | Why |
  |---|---|---|---|
  | `chalmers1994cfc` | 1993 | 2011 | Text written 1993 and widely cited from then; one footnote added 2011; journal publication 2012 (A2 §5 headnote) |
  | `mollo2018` | 2017 | 2018 | Advance online 2017; print issue 2018 (A2 §7) |
  | `mollo2023vector` | 2023 | 2026 | arXiv preprint 2023; **the held file is the 2026 published version**, which is substantially expanded (E §4) |
  | `birch2024` | 2025 | 2025 | The manifest key says 2024 (the book); the held file is the 2025 *Animal Sentience* précis (E §6) |
  | `klein_maudlin` | 2016 | 2016 | **The PDF states no publication year.** The date is the compile date printed on the draft ("Draft 1D, compiled October 8, 2016"), confirmed by the file's own metadata (F §2). Every "27 years" statement in this document inherits that compile date |
  | `dennett1988` | 1988 | 1988 | Dated by the published volume, but endnote 14 documents the same argument circulating from December 1979 and presented near-final in April 1985 (G §1). **The timeline position understates its currency** relative to Block 1978/1980 and Cuda 1985; a figure may want to draw a lead-in bar |

  Two cases were considered and left at the reviewer's own year. `godfreysmith2016` is held as the 2014 NYU talk but is dated 2016 here, because the talk is not a publication and the reviewer's field-history record says 2016. `shevlin2021` was accepted in 2019 and printed in 2021; the reviewer's record says 2021.
- **Recodings.** Every `stance` value is the batch reviewer's own field-history-record judgement, carried over unchanged — including `maudlin1989` as `rejects` and `dennett1988` as `supports`, both of which are correct but narrow and must be read with the role text and [§6](#6-corrections-and-mis-statements). `grain.csv` `direction` was **recoded in this revision** after a reviewer found it inconsistent: "no bottom" had been `fine` for one work and `meta` for another, and a grain derived from a theory's own postulate had been coded as unspecified. The seven current values are defined in [§9](#9-data-files-for-diagrams). Communities were assigned from the reviewers' records; two were normalised — `chalmers1994cfc` and `piccinini2010`, whose records read "philosophy-of-mind (with philosophy-of-computation)", are coded `philosophy-of-mind`, and `piccinini2013`, whose record reads "philosophy-of-computation (jointly with biology-and-neuroscience)", is coded `philosophy-of-computation`. Communities for named-only works were assigned only where a citing review describes the work's field.
- **Era boundaries** are the curator's, chosen where the questions being asked changed, and are stated as approximate. The 1996 boundary follows the publication of the implementation reply; the 2014 boundary precedes the first work in which a leading theory states its incompatibility with the thesis; the 2022 boundary follows the arrival of systems the debate is now about. Two placements are worth naming: `chalmers1994cfc` sits in era 2 because its text is 1993, so the positive programme predates the implementation reply that is usually read as its foundation; and `klein_maudlin` sits in era 4 by its 2016 compile date, 27 years after the argument it answers.
- **What the generator validates.** That the manifest key set and the works table match exactly; that any count of the form "N supporting / restricting / rejecting / abstaining" in a debate's `status_reason` matches the tally computed from `positions.csv` and `works.csv`; that every `cites_held_document` value is from its allowed set and that a `sibling` value has an `evidence` cell naming the document actually cited, and that no `CITES` entry refers to a non-existent edge; that every community, stance, evidence type, work status and debate status is from its allowed set; that unreviewed works carry `stance = unknown` and a role beginning "Not reviewed", and that reviewed works do not carry `unknown`; that no `role` exceeds 160 characters and no debate, position, grain or correction cell exceeds its limit; that every position id is unique and every position key is known; that every edge's endpoints are known keys, that every edge's source is a reviewed work, that relations are from the allowed set, that there are no duplicate edges, and that no edge points forward in time except the three whitelisted cases; that every `grain.csv` and `corrections.csv` row names a reviewed work and that grain keys are unique; and that every `not_held.csv` `cited_by` entry is a reviewed key. It exits non-zero and prints every failure.
- **Generator.** `field_history_data/build_field_history_data.py`. Run it with the project interpreter at `/home/vncuser/miniconda3/envs/grid_world_pain/bin/python`. Edit it and rerun; **do not hand-edit the CSVs.**
- **One inference removed.** An earlier draft carried an edge `maudlin1989 → block1978` on the strength of Maudlin rejecting "the ploy of funny instantiation". Checking Part F's responds-to record, **Block is not named there** — the water pipes and beer cans Maudlin dismisses are Searle's examples. The edge was the curator's inference, not a documented engagement, and has been deleted. (Klein's re-diagnosis of Block's Chinese Nation *is* documented and stands.)
- **What is deliberately absent from the data files.** No credence, probability or Φ value is reproduced as a data column, because in every case the author attaches hedges that a bare number would drop — Chalmers calls his "extremely rough numbers for illustrative purposes", Long et al. call theirs illustrative, and Tononi & Koch's Φ figures are computed on three-unit toy systems. Where such numbers matter they are quoted in prose with their hedges attached.

---

## Feedback from research-postdoc — 2026-09-21

**What this section is.** A domain sanity check of the sections above, written by standing in for a philosophy-of-mind / consciousness-science reader, because the project has no professor agent for this area. It is **appended, not integrated**: nothing above has been edited. Overall judgement — the synthesis is broadly sound. Positions are stated at or near their strongest, the corrections table (§6) is unusually good and would itself be citable, and the corpus-construction caveats (§4, §10) are more honest than most published reviews. The findings below are one data inconsistency that will print wrong numbers on the page, a terminology gap that a specialist reader will notice immediately, and five omissions that bend the field's shape.

### Blocking

1. **§3.1 / §9 vs `debates.csv`.** The prose (line "13 supporting, 13 restricting, 5 rejecting, 4 abstaining", matching `works.csv`, 35 reviewed) contradicts `debates.csv` `sufficiency.status_reason` ("Thirteen … support … twelve restrict it, four reject it, four decline" = 33). The CSV row is stale from before Part F was folded in. Since the page's diagrams are drawn from the CSVs, the figure and the text will disagree. Fix in `build_field_history_data.py` and rerun; add a generator check that any count stated in a `status_reason` string matches the `works.csv` tally.

2. **§1 Vocabulary — four terms the reader is assumed to already hold apart.** The table defines *computational functionalism* but not *machine functionalism*, *computationalism*, or *the computational theory of mind*, while the body uses "computationalism" (Klein), "minimal computationalism" (Chalmers), and "generic computationalism" (Piccinini) as if the differences were established. It also has no entry for *consciousness*, *phenomenal consciousness* or *sentience*, yet "sentience" (Birch's term, which in his usage means *valenced* experience specifically — capacity for states that feel good or bad, narrower than phenomenal consciousness) is used alongside "consciousness" in §3.8, §3.9 and §4 without a gloss. Four rows to add:

   | **Machine functionalism** | Putnam's original version: a mental state type is a machine-table state of a probabilistic automaton. The target of Block & Fodor 1972 and Block 1978; the later works reject *this* version while keeping functionalism (A1 §1). |
   | **Computationalism / the computational theory of mind** | The claim that cognition is computation. Distinct from computational functionalism, which adds that the computation is what *makes* the state mental. Piccinini's central move is to prise the two apart (`piccinini2010`, A2 §3); "generic computationalism" (`piccinini2013`) is a claim about cognition only, not about experience. |
   | **Consciousness / phenomenal consciousness** | Used in this corpus for *there being something it is like* to be the system. Distinct from a system's merely having information globally available for use, which several reviewed works take to be the easier and separable question (`dehaene2017`, D §2, declares experience beyond scope). |
   | **Sentience** | Birch's term, and narrower than phenomenal consciousness: the capacity for *valenced* experience — states that feel good or bad. A system could in principle be phenomenally conscious without being sentient in this sense. Where this document says "sentience" it is reporting `birch2024` and `long2024welfare`, not restating "consciousness" (E §6). |

3. **§1 Vocabulary, *Substrate independence* row.** Multiple realizability, substrate independence and organizational invariance are each defined but never ordered, and the commonest error in this literature is treating the first as establishing the second. Append to the row: "Stronger than multiple realizability, which it is often confused with: multiple realizability says the same state type has many physical realizers, and is satisfied by a world in which every realizer is nonetheless carbon-based. Substrate independence additionally says the realizers may be drawn from a *broad* class. Organizational invariance (`chalmers1994cfc`) is more specific again: it names *causal topology* as the invariant. Every reviewed work assumes multiple realizability ([§5.4](#54-what-rests-on-assumption)); assuming substrate independence is a further step, and `bostrom2003` is the corpus's clearest case of taking it without argument."

### Omissions that bend the shape

4. **Dennett is absent from the whole document and from `not_held.csv`** (the only mention is the §5.5 caveat that nothing may be attributed to him). The deflationary strand — that the absent/inverted-qualia framing is itself confused, that there is no further fact for the thought experiments to be about — is one of the two or three most influential positions in this debate, and it is the reason the intuition pumps in §5.1 are *contested* rather than merely inconclusive. As the document stands, absent qualia reads as a datum. **Recommend: name the gap now, fetch later.** Add to `not_held.csv` and to §10; fetching "Quining Qualia" (1988) or the relevant chapters of *Consciousness Explained* would be the single best next addition after Thompson 2007.

5. **Block is represented only by 1972 and 1978.** He draws 9 incoming edges and is the corpus's second-most-cited work, so a reader will take "burden-of-proof argument" as his position. Missing are the access/phenomenal distinction (Block 1995) — which is the device the whole later corpus uses when it separates "global availability" from "experience" — and Block's own later, substantive anti-computationalism. **Recommend: fetch Block 1995**; it is cheap, it repairs finding 2, and it is cited (as a distinction, not a work) throughout Parts C, D and E.

6. **The higher-order family is missing from §2.4 and §3.6**, though the reviews hold it (higher-order theory appears 13 times in Part D and 8 in Part E). Era 4 names integrated information, global workspace and attention-schema theories as the theories that became machine tests, and omits higher-order thought / perceptual reality monitoring, which is one of the four families `butlin2023` actually draws indicators from. **This is a synthesis-level omission, not a corpus one — no fetch needed.** In §2.4 "Live questions", after the Graziano bullet, add: "- **The higher-order family** (higher-order thought theories and perceptual reality monitoring) is present in this corpus only inside the works that survey it — `butlin2023` draws indicators from it and `shevlin2021` and `seth2025` discuss it — because no primary statement of it was fetched. It is the fourth of the four theory families the indicator method uses, and its absence as a node should be visible on any diagram of era 4."

7. **The Chinese Room reply literature is absent as a strand.** `searle1980` draws 14 incoming edges, the most in the corpus, and the only reviewed reply to him is `cuda1985`. The Systems Reply, the Robot Reply and Churchland & Churchland 1990 are not in `not_held.csv`. §5.5 correctly forbids attributing anything to the 27 commentators, but the effect at the level of the whole document is that Searle's argument appears to stand with one answer. **Recommend: name the gap** in §10 under "Two absences that make a debate look one-sided", as a third bullet: "- **The reply literature on the Chinese Room** — the Systems and Robot Replies in their developed forms, and Churchland & Churchland 1990 — is held nowhere, and the 27 BBS commentaries were not reviewed. `searle1980` is the most-cited work in this corpus and the only reviewed reply to it is `cuda1985`, 5 years later and aimed at one paragraph. The argument therefore reads here as less answered than it is."

8. **`not_held.csv`, `Putnam 1988` row, mischaracterises the book.** It is listed only as "the universal-realization argument itself (appendix, pp. 120–25)". *Representation and Reality* is also where Putnam abandons functionalism on externalist grounds — that content is not fixed by internal functional organisation, so mental states cannot be individuated the way functionalism needs. That is a second, independent challenge, it is the founder recanting, and it bears on §3.3 (individuation) rather than §3.2 (triviality). Replace the `why_relevant` cell with: "The universal-realization argument (appendix, pp. 120-25), reconstructed here only from Chalmers 1996 section 2 - and, separately, the book in which functionalism's founder abandons it on externalist grounds, that content is not fixed by internal functional organisation. The corpus holds the first challenge's critics and no trace of the second." Also add a line to §10 so the second challenge is visible in prose.

### Positions and statuses

9. **Searle, Maudlin, IIT, Seth and Chalmers's nomological claim are all stated at or near their strongest, and the corrections table catches the standard straw men in both directions.** Particular credit: the nomological-not-metaphysical restriction on `chalmers1994cfc` is caught in §5.5, §6 and the vocabulary; Maudlin's concessions (§2.2, §6) are the ones citation normally drops; `tononi2015` endnote 15 is used to block the carbon-chauvinism reading; `seth2025` is quoted declining the stronger claim. No straw-manning found.

10. **Entry point, third bullet — "The loudest disagreement is not the real one."** This is the curator's adjudication, in a document whose header says "It adjudicates nothing." The supporting facts are correct; the framing is a verdict. Replace with: "**The loudest disagreement may not be the load-bearing one.** Almost nobody in this corpus says machines could never have minds — John Searle, the most-cited opponent, writes that "only a machine could think" and that whether a silicon system could is "an empirical question". On the reading taken here, the live question is narrower: is organisation *by itself* enough? Readers who weight integrated information theory's rejection more heavily will draw the line differently."

11. **§3.4, "Status now" — "this is the debate whose openness explains the others'."** The strongest interpretive claim in the document, and it is the curator's, not the corpus's: no reviewed work says the grain question is prior. Replace with: "**Status now: open.** *The curator's reading, offered as a reading:* this is the debate whose openness plausibly explains the others', since sufficiency, biology and the language-model question each turn on a setting of it and none can be settled while it is unfixed. No reviewed work states this ordering; the closest are the three meta-positions (`shevlin2021`, `birch2024`, `long2024welfare`), which say only that the parameter cannot be fixed from the human case."

12. **§3.2 `status_scope` is too narrow.** It names only Putnam 1988 and Searle 1990/1992 as missing. The triviality literature did not stop in 1996 — Godfrey-Smith 2009, Scheutz, Rescorla and Schweizer all press it after Chalmers's reply, and none is held or named. "Leaning toward the objection failing" is defensible *for this corpus* and would be contested in the field. Replace the `status_scope` cell in `debates.csv` with: "Putnam 1988 and Searle 1990/1992, the sources of the objection, are not held, and neither is any of the post-1996 triviality literature (Godfrey-Smith 2009; Scheutz; Rescorla; Schweizer). The corpus contains Chalmers's reply and its critics, and stops there; this debate is more live in the field than the corpus makes it look."

13. **§2.1, "type physicalism was abandoned by everyone in the batch."** True of the batch and misleading about the field, since the identity theory's revival is exactly the not-held challenge. Append: " — a fact about four papers from one decade, not about the field. The revival of the identity theory rests on `bechtelmundale1999`, which is named-only ([§10](#10-known-works-not-held)), so this corpus cannot show the other side of it."

### Project relevance (§8)

14. **§8 avoids implying the project's agents are candidates for consciousness, and the nociception discipline is correctly stated and repeated.** One fix and one tightening.

    - **MUST-FIX — §8 point 3.** "The grain question is why 'pain-like' cannot be upgraded by adding detail" imports a debate about *how finely to copy a brain* into a claim about agents that are not copies of any brain, which quietly places them on the gradual-replacement ladder. Replace with: "**3. The corpus offers no ladder these agents could be climbing.** The grain debate ([§3.4](#34-how-fine-must-functional-equivalence-be--open)) asks how finely a *brain* must be copied before the copy inherits its mental properties. This project's agents are not copies of any nervous system, so that debate does not place them anywhere on its scale — high or low. Adding biological detail to a nociception model therefore does not move an agent along any axis this literature recognises, and the reason is not that the threshold is far away; it is that no threshold in this corpus is defined for a system of this kind."
    - **SUGGEST — §8, second paragraph.** "studies pain-*like* behaviour" leans on the italic hedge to do all the work. Replace with: "This project trains reinforcement-learning agents with a nociception channel and studies how their behaviour changes when that channel is active — a behavioural description, and "pain-like" in that descriptive sense only, never a claim about experience."

*Signed: research-postdoc, 2026-09-21. Appended only; no text above was altered. Findings 1–3 should be cleared before the page is published, because they will print wrong numbers or invite a specialist's first objection. Findings 4–8 are for the topic's next fetch round and are routed to `literature-curator` (naming the gaps) and `academic-pdf-fetch` (Block 1995, then Dennett).*

---

## Revision log — literature-curator — 2026-09-21

One revision pass, applying two reviewer gates and integrating a seventh review batch. Nothing above this line in §§1–11 predates it unchanged where a finding applied; the appended feedback section is untouched.

**Inputs.** `research-postdoc` domain read (verdict *broadly sound*), signed and appended above. `plan-reviewer` evidence check (verdict *SOUND WITH CONCERNS*, no Critical findings), at `reports/gate_planreviewer.md` in the job's working directory — not appended here, because appending another agent's report in my own edit would put words in its voice; its findings are applied and attributed below. Batch G (`dennett1988`, `block1995`) landed during the pass.

**Applied from `plan-reviewer`** — all eight Major and all ten Minor.

| # | Finding | Where fixed |
|---|---|---|
| 1 | Corpus-wide stance tally conflated with the sufficiency debate's positioned works | Reading conventions, §3.1, §7, §9, `debates.csv` (now generator-computed) |
| 2 | The one-in-three biology credence is a mainstream figure Chalmers says exceeds his own | §3.5, `debates.csv` `biology.status_reason` |
| 3 | The triviality lean over-reached and mis-stated Sprevak, its one reviewed dissenter | §3.2, `debates.csv` `triviality` direction and scope |
| 4 | "Independently" contradicted the co-authorship caveat beside it | §3.7 (three places), §3.8, §4, `debates.csv` `evidence.status_reason` |
| 5 | Edges were readable as a citation census | New `cites_held_document` column; §4 retitled and rewritten; §9 |
| 6 | `grain.csv` `direction` inconsistent | Recoded to seven values incl. `no-bottom`; §3.4, §9, §11 |
| 7 | The grain dial listed a setting nobody takes and hid the works denying the scale | Entry point, §3.4 |
| 8 | `mollo2018` narrated in era 3, placed in era 4 | §2.3 flagged explicitly; §9 |
| 9–18 | Scoping of "most-cited opponent"; ambiguous agent in §3.1 exchange 4; "one directly quoted exchange" overclaimed; Chalmers's "25% **or more**"; Long et al.'s illustrative 30–50%; the list-searcher row contradicting §6; the asserted-not-argued kinship in §5.7; the `chalmers1994cfc` 2011/2012 discrepancy | Entry point, §3.1, §3.8, §5.1, §5.5, §5.7 |

**Applied from `research-postdoc`** — MUST-FIX 1, 2, 3, 6, 8, 10, 11, 14a and SUGGEST 4, 7, 12, 13, 14b. The stale counts (1) and the entry-point verdict (10) overlap with the plan-reviewer and were fixed once. New vocabulary rows for machine functionalism, computationalism, the computational theory of mind, and consciousness / phenomenal consciousness / sentience with Birch's narrower sense (2); the three-claim ladder now ordered and explained (3); the higher-order family named as a missing node (6); *Representation and Reality* split into two `not_held` rows so the externalist abandonment is visible (8); §3.4's priority claim marked as the curator's reading (11); the triviality scope widened to the post-1996 literature (12); the type-physicalism remark scoped to the batch (13); §8 point 3 rewritten so the grain debate is not imported onto agents that are not copies of any nervous system, and the "pain-like" hedge made explicit (14a, 14b). The Chinese Room reply literature and the deflationary successors are now `not_held` rows and §10 bullets (7, 4).

**Batch G integrated.** `dennett1988` reviewed-full, era 2, stance `supports` — **defensively and indirectly only**, and the role text and §6 say so: the paper removes a stumbling block, argues nothing about programs, substrate or implementation, and never says the machine has qualia. Two positions (`suf-deflate`, `ev-introspect`), two edges (Block 1978, Block & Fodor 1972 — **Searle is not in his bibliography and no edge was drawn**), five corrections, no grain row. New prose in the entry point, §1, §2.2, §3.1, §3.7, §5.1, §5.5, §6, §7, §10. `block1995` added as `named-only` in `works.csv` *and* as a `not_held.csv` row, matching how the other five named-only works are already carried; §10 now lists six.

**One thing deleted rather than added.** The edge `maudlin1989 → block1978` was my inference and is not in Part F's record; it is gone ([§11](#11-scope-and-provenance)).

**Declined, with reasons.**
- *Fetching Block 1995 and the Dennett successors* (postdoc SUGGEST 5, and the residue of 4). Out of scope for a curator — I organise what has been extracted. Both are named in §10 and in `not_held.csv` so the next fetch round can see them; `block1995` is already a manifest key.
- *Appending the plan-reviewer's report to the synthesis.* Its findings are applied and attributed above, but writing a signed section in another agent's voice would misrepresent authorship. The report stays at its own path.
- *Setting the triviality debate to `open`* — the plan-reviewer offered this or a narrowed direction. I took the narrowing, because a real convergence exists on the narrow claim (Putnam's construction reproduces only a trace) and collapsing it to `open` would lose that. Both readings are now visible in §3.2, and a reader who prefers `open` has the evidence to say so.

**Two places where the reviewers' emphases pull apart, left visible rather than merged.** The postdoc wants the deflationary strand named as the reason absent qualia should not read as a datum; the plan-reviewer warns that a single pro/anti axis would put Dennett and Chalmers on the same side. Both are recorded — the first in §2.2 and §10, the second in the §9 caption table — and they constrain a diagram in different directions.

**Not verified here, and flagged rather than asserted:** the 19-author overlap between Butlin et al. and Long et al. beyond Butlin and Long themselves; Klein's 2016 date, which is a compile date that every "27 years" statement inherits; and the reviewers' own premise that the per-paper reviews are faithful to the PDFs, which this document takes on trust throughout.

*Signed: literature-curator, 2026-09-21. Data regenerated and validated; not committed.*
