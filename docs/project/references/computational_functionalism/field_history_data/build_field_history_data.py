"""Build the computational-functionalism field-history data files from the reviewed corpus.

Canonical location: docs/project/references/computational_functionalism/field_history_data/.
Written 2026-09-21 by literature-curator.

Every value below was transcribed from the per-batch reviews at the topic root
(Parts A1, A2, B, C, D, E). Section references use the part letter + entry number
(e.g. "B 1" = Searle 1980, entry 1 of Part B; "A2 5" = Chalmers 1993/2011, entry 5
of Part A2). Cross-paper sections are cited as "A2 notes 1", "E notes 4", etc.

Run:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python build_field_history_data.py

The script validates against references_manifest.csv and exits non-zero on any
mismatch. Edit this file and rerun; do not hand-edit the CSVs.
"""
import csv
import os
import re
import sys

ROOT = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/docs/project/references/computational_functionalism"
OUT = os.path.join(ROOT, "field_history_data")

COMMUNITIES = {
    "philosophy-of-mind",
    "philosophy-of-computation",
    "consciousness-science",
    "AI-and-ML",
    "ethics-and-policy",
    "biology-and-neuroscience",
    "unknown",
}

STANCES = {"supports", "restricts", "rejects", "neutral", "unknown"}

EVIDENCE_TYPES = {
    "thought experiment",
    "conceptual analysis",
    "formal proof",
    "empirical study",
    "review",
    "position piece",
    "unknown",
}

# status values used in works.csv. "pending-review" is NOT one of the three the
# brief named; it exists because the corpus grew while this synthesis was being
# written (batch F: Maudlin 1989 upgraded from named-only to pdf, plus a new
# context piece), and neither had a review at build time. See synthesis section 11.
WORK_STATUSES = {"reviewed-full", "reviewed-short", "named-only", "pending-review"}

# Keys whose PDF is held but whose per-paper review does not exist. Batch F (Maudlin
# 1989 and the Klein retrospective) landed on 2026-09-21 and is fully integrated, so
# this set is now empty; it is kept so a future in-flight batch can be marked.
PENDING = set()

# Edges that point forward in time by the `year` column but are genuine, because the
# citing work's version of record post-dates the cited work, or because the cited key
# is dated by a later restatement than the one actually cited. Reason is in `evidence`.
FORWARD_OK = {
    ("mollo2023vector", "milliere2024"),
    ("long2024welfare", "birch2024"),
    ("long2024welfare", "seth2025"),
}

ERAS = [
    ("e1_founding", "Functionalism stated, and attacked from inside", 1967, 1978,
     "A mental state is defined by its role, not its material. Within a decade two of functionalism's own architects argue the machine-table version fails and that no version avoids both liberalism and chauvinism."),
    ("e2_sufficiency", "Is running the right program sufficient? The thought-experiment era", 1979, 1995,
     "Searle's Chinese Room denies sufficiency; Cuda and Chalmers reply with gradual neuron-by-neuron replacement and demand the opponent name the step at which the lights go out."),
    ("e3_implementation", "What is it to run a computation at all? Implementation, individuation, mechanism", 1996, 2013,
     "Triviality and individuation nearly end the doctrine on technical grounds. Implementation conditions are tightened, content-based individuation is pressed, and the question of what the brain computes becomes empirical."),
    ("e4_theories", "Theories of consciousness become machine tests, and the testability crisis opens", 2014, 2021,
     "Integrated information, global workspace and attention-schema theories deliver explicit machine verdicts; formal results argue such theories are untestable; biology returns as a rival; ethics enters."),
    ("e5_systems", "Systems that talk back: assessment, precaution, and the biological alternative", 2022, 2026,
     "Language models make the question concrete. Behavioural evidence is downgraded, architectural indicators are proposed, precautionary frameworks are built, and biological naturalism is stated systematically."),
]

DEBATES = [
    # id, title, plain question, status, status_reason, status_direction, status_scope
    ("sufficiency",
     "Is running the right computation sufficient for a mind?",
     "If a machine ran exactly the computation your brain runs, would it have a mind, and would it feel anything?",
     "open",
     "Of the {tally} works positioned in this debate, {supports} supporting, {restricts} restricting, {rejects} rejecting and {neutral} abstaining; no reviewed work concedes to another.",
     "",
     "The corpus was built to trace this thesis, so both camps are over-represented relative to authors who never address it."),
    ("triviality",
     "Does every ordinary object implement every computation?",
     "If a rock can be described as running your brain's program, then saying a mind is a program says nothing. Does that follow?",
     "leaning",
     "No reviewed work contests that Putnam's construction reproduces only a trace; Sprevak contests whether a NON-SEMANTIC modal constraint suffices, holding that realization functions stay cheap.",
     "toward Putnam's mapping construction failing and some modal constraint being required; whether a non-semantic modal constraint suffices is disputed (Sprevak: no)",
     "Putnam 1988 and Searle 1990/1992, the sources, are not held, nor is any post-1996 triviality work (Godfrey-Smith 2009; Scheutz; Rescorla; Schweizer). More live in the field than here."),
    ("individuation",
     "Which computation is a given system running, and does meaning decide?",
     "One circuit can be called an AND gate or an OR gate depending on which voltage you call '1'. What fixes which computation a system is running?",
     "open",
     "Non-semantic, mathematical-content, any-content, functional-equivalence-class and selection-history accounts all stand unreconciled in the corpus.",
     "",
     "Egan, Dewhurst, Haimovici and Piccinini 2008/2015 are known only through the papers that answer them."),
    ("grain",
     "How fine must functional equivalence be before it counts?",
     "Copy a brain at what level of detail - whole regions, single neurons, synapses, molecules? Everyone needs an answer and nobody gives the same one.",
     "open",
     "The corpus records at least eight distinct settings and two meta-positions saying the parameter cannot be fixed from human experiments; no reviewed work argues another's setting is wrong.",
     "",
     "This is the axis on which the field's disagreements actually turn, and no reviewed work proposes a run experiment that would settle it."),
    ("biology",
     "Does being alive matter, and in which of its three non-equivalent senses?",
     "Is a mind something only a living thing can have - and if so, is it metabolism, bodily self-regulation, or specific brain wiring that does the work?",
     "open",
     "The biological works lower plausibility without rejecting; Chalmers calls the requirement 'biological chauvinism' while using a mainstream credence he says exceeds his own.",
     "",
     "Nobody in the reviewed biological batch rejects computational functionalism; Thompson 2007, the hub all three biological works cite, is not held."),
    ("testability",
     "Can theories of consciousness be tested at all, and does the thesis gate which theories count?",
     "Every measurement of consciousness runs through a report. Can any theory survive that, and is 'computation suffices' now used to decide which theories get assessed?",
     "open",
     "Doerig's and Kleiner's formal results stand unanswered in the corpus, while Butlin et al. proceed by excluding the theory that denies the thesis (p. 5, p. 33).",
     "",
     "The published replies to the unfolding argument (Kleiner 2020; Tsuchiya, Andrillon & Haun 2019) are named but not held."),
    ("evidence",
     "Is what a system says or does evidence about whether it has a mind?",
     "A chatbot trained on human talk can say it feels things. Is that evidence, and if not, what is?",
     "leaning",
     "Five reviewed works take this position and Schwitzgebel & Garza state a symmetric version; but two of the five share authors, so the agreement is not independent.",
     "toward architectural rather than behavioural evidence, at least for trained systems",
     "Long et al. share two authors (Chalmers, Birch) with works they cite for this, so the convergence is partly co-authorship rather than independent agreement."),
    ("llm",
     "Are today's language models candidates for minds?",
     "Does anything in a large language model make it a serious candidate for having experiences?",
     "leaning",
     "Every reviewed work that gives a verdict says no current system is a strong candidate; they split sharply on whether the obstacles are temporary.",
     "toward no current system being a strong candidate, with the trajectory question wide open",
     "The corpus holds no work arguing at length against AI moral status from inside the AI-minds literature; opponents appear only as reported objections."),
    ("precaution",
     "What should be done while the question stays open?",
     "If nobody can settle whether a machine feels anything, who decides how to treat it, and on what evidence?",
     "open",
     "Four procedural recommendations are on the table and they do not compose: do-not-build, corporate assess-and-prepare, a roadmap-or-red-flags list, and citizen-panel precaution.",
     "",
     "Birch's framework is read here from the published precis, not the book; the assessed policy proposals (Bryson, Metzinger) are named only."),
]

# key: (short_label, year, year_print, community, role, evidence_type, stance)
W = {
    "putnam1967": ("Putnam 1967", 1967, 1967, "philosophy-of-mind",
                   "Not reviewed (no PDF). The target and the source for both Block papers: mental states as machine-table states of a probabilistic automaton.",
                   "unknown", "unknown"),
    "blockfodor1972": ("Block & Fodor 1972", 1972, 1972, "philosophy-of-mind",
                       "Six arguments that the Turing-machine table is the wrong level; separates machine-table from computational states; first statement of the absent-qualia worry.",
                       "conceptual analysis", "restricts"),
    "fodor1974": ("Fodor 1974", 1974, 1974, "philosophy-of-mind",
                  "Makes non-neural realisation the standard case: special-science kinds cross-classify physical kinds. Does not itself say the autonomous level is computational.",
                  "conceptual analysis", "supports"),
    "block1978": ("Block 1978", 1978, 1978, "philosophy-of-mind",
                  "The Chinese-nation absent-qualia argument, the liberalism/chauvinism pair, and the input-output dilemma - framed as burden-of-proof, not refutation.",
                  "thought experiment", "rejects"),
    "bechtelmundale1999": ("Bechtel & Mundale 1999", 1999, 1999, "philosophy-of-mind",
                           "Not reviewed (no PDF). The standard challenge to the multiple-realizability premise every reviewed work assumes; its absence leaves that premise unopposed here.",
                           "unknown", "unknown"),
    "maudlin1989": ("Maudlin 1989", 1989, 1989, "philosophy-of-mind",
                    "Olympia: a machine whose entire counterfactual apparatus sits inert during the run, so computational identity and actual physical activity come apart.",
                    "thought experiment", "rejects"),
    "klein_maudlin": ("Klein 2016 (draft)", 2016, 2016, "philosophy-of-computation",
                      "Answers Olympia by re-stating computationalism over mechanistically individuated architectures and actual processes, so Olympia emulates rather than implements.",
                      "conceptual analysis", "restricts"),
    "chalmers1994cfc": ("Chalmers 1993/2011", 1993, 2011, "philosophy-of-mind",
                        "The canonical positive statement: causal topology, organizational invariance, minimal computationalism. A 2011 footnote makes sufficiency nomological only.",
                        "conceptual analysis", "supports"),
    "chalmers1996rock": ("Chalmers 1996", 1996, 1996, "philosophy-of-computation",
                         "Answers triviality: Putnam reproduces an automaton's trace, not its structure. Introduces strong conditionals and combinatorial state automata; admits two gaps.",
                         "conceptual analysis", "supports"),
    "piccinini2010": ("Piccinini 2010", 2010, 2010, "philosophy-of-mind",
                      "Separates functionalism from computationalism by cashing out function mechanistically; strips the doctrine of a priori standing and hands it to neuroscience.",
                      "conceptual analysis", "restricts"),
    "piccinini2013": ("Piccinini & Bahar 2013", 2013, 2013, "philosophy-of-computation",
                      "The corpus's one data-driven verdict: neural computation is generic but neither digital nor analog, so it is sui generis and needs its own mathematics.",
                      "review", "restricts"),
    "shagrir2006": ("Shagrir 2006", 2006, 2006, "philosophy-of-computation",
                    "Concedes that being a computer is perspectival, and locates explanatory force in a correspondence between representing and represented structure.",
                    "conceptual analysis", "restricts"),
    "sprevak2010": ("Sprevak 2010", 2010, 2010, "philosophy-of-computation",
                    "Defends the view that computation essentially involves content; the AND/OR gate shows nothing physical decides which computation a circuit runs.",
                    "conceptual analysis", "restricts"),
    "mollo2018": ("Coelho Mollo 2018", 2017, 2018, "philosophy-of-computation",
                  "Splits computational individuation (functional, medium-independent) from implementation (mechanistic, material), dissolving the conflict between them.",
                  "conceptual analysis", "supports"),
    "searle1980": ("Searle 1980", 1980, 1980, "philosophy-of-mind",
                   "The Chinese Room: a program has syntax but no semantics, so running one cannot suffice for understanding. Explicitly allows machine minds; silicon left open.",
                   "thought experiment", "rejects"),
    "searle1990": ("Searle 1990", 1990, 1990, "philosophy-of-mind",
                   "Not reviewed (no PDF). The compressed three-axiom restatement, and the source of the wall-runs-WordStar claim that Chalmers 1996 answers.",
                   "unknown", "unknown"),
    "chalmers1995qualia": ("Chalmers 1995", 1995, 1995, "philosophy-of-mind",
                           "Fading and Dancing Qualia: denying organizational invariance costs either a brute discontinuity in law or subjects irreparably wrong about their own experience.",
                           "thought experiment", "supports"),
    "cuda1985": ("Cuda 1985", 1985, 1985, "philosophy-of-mind",
                 "Gradual homunculus replacement with a matched control sequence, converting the question into 'at which single neuron?'. Sufficiency only at circuit-level grain.",
                 "thought experiment", "supports"),
    "bostrom2003": ("Bostrom 2003", 2003, 2003, "philosophy-of-mind",
                    "Imports substrate independence undefended and states its weakest useful form: contingent, non-behavioural, at roughly the level of individual synapses.",
                    "conceptual analysis", "supports"),
    "schneider2019": ("Schneider 2019", 2019, 2019, "philosophy-of-mind",
                      "Not reviewed (no PDF). Source of the AI Consciousness Test that Chalmers and Birch both assess; its absence leaves 16 years after Bostrom 2003.",
                      "unknown", "unknown"),
    "seth2025": ("Seth 2025", 2025, 2025, "consciousness-science",
                 "The systematic statement of biological naturalism: conscious AI needs computational functionalism and silicon substrate flexibility, both of which are assumed.",
                 "position piece", "restricts"),
    "godfreysmith2016": ("Godfrey-Smith 2016", 2016, 2016, "philosophy-of-mind",
                         "Re-describes living matter at the nanoscale and argues metabolic activity belongs inside a human's functional profile - an immanent correction, not a rejection.",
                         "conceptual analysis", "restricts"),
    "aru2023": ("Aru, Larkum & Shine 2023", 2023, 2023, "biology-and-neuroscience",
                "Three arguments against language-model consciousness: impoverished Umwelt, no thalamocortical architecture, organisation perhaps not abstractable from life.",
                "review", "restricts"),
    "cleeremans2022": ("Cleeremans & Tallon-Baudry 2022", 2022, 2022, "consciousness-science",
                       "Argues consciousness has a function because every experience carries intrinsic value; what machines lack is rewards that are rewarding for them.",
                       "position piece", "restricts"),
    "seth2018beast": ("Seth & Tsakiris 2018", 2018, 2018, "consciousness-science",
                      "Selfhood as control-oriented interoceptive inference serving allostasis: we perceive ourselves because of, not in spite of, being flesh machines.",
                      "position piece", "restricts"),
    "thompson2007": ("Thompson 2007", 2007, 2007, "philosophy-of-mind",
                     "Not reviewed (no PDF). The hub all three biological works cite for continuity between life and mind; the highest-value addition if the corpus is extended.",
                     "unknown", "unknown"),
    "butlin2023": ("Butlin, Long et al. 2023", 2023, 2023, "AI-and-ML",
                   "Adopts computational functionalism as a working hypothesis, derives fourteen indicator properties from five theories, and scores real systems against them.",
                   "review", "supports"),
    "dehaene2017": ("Dehaene, Lau & Kouider 2017", 2017, 2017, "consciousness-science",
                    "Splits consciousness into global availability (C1) and self-monitoring (C2), and holds a machine with both conscious in every sense science can address.",
                    "review", "supports"),
    "tononi2015": ("Tononi & Koch 2015", 2015, 2015, "consciousness-science",
                   "States that integrated information theory contradicts functionalism: a feedforward duplicate has zero Phi, and a brain simulation is virtual, not causally real.",
                   "review", "rejects"),
    "doerig2019": ("Doerig et al. 2019", 2019, 2019, "consciousness-science",
                   "The unfolding argument: since recurrent behaviour is reproducible feedforward, causal-structure theories are either falsified or outside empirical science.",
                   "formal proof", "supports"),
    "kleiner2021": ("Kleiner & Hoel 2021", 2021, 2021, "consciousness-science",
                    "Generalises the unfolding argument into a dilemma catching both camps: independence means already falsified, strict dependence means unfalsifiable.",
                    "formal proof", "neutral"),
    "albantakis2023": ("Albantakis et al. 2023", 2023, 2023, "consciousness-science",
                       "The full formalisation of integrated information theory, with three functionally equivalent systems of different Phi: 'consciousness is about being, not doing'.",
                       "formal proof", "rejects"),
    "graziano2017": ("Graziano 2017", 2017, 2017, "consciousness-science",
                     "The attention schema: a deliberately inaccurate self-model of attention explains the claim of experience. Declared buildable with current technology.",
                     "position piece", "supports"),
    "chalmers2023llm": ("Chalmers 2023", 2023, 2023, "consciousness-science",
                        "Converts each objection to language-model consciousness into an engineering challenge; credence under 10% now, about 25% for successor systems within a decade.",
                        "position piece", "supports"),
    "long2024welfare": ("Long et al. 2024", 2024, 2024, "ethics-and-policy",
                        "Turns the open question into a governance programme - acknowledge, assess, prepare - with an explicit credence assigned to computational functionalism itself.",
                        "position piece", "neutral"),
    "schwitzgebel2015": ("Schwitzgebel & Garza 2015", 2015, 2015, "ethics-and-policy",
                         "Only psychological and social properties bear on moral status, so some possible AIs merit human-like consideration; adds the Excluded Middle Policy.",
                         "conceptual analysis", "neutral"),
    "birch2024": ("Birch 2025 (precis)", 2025, 2025, "ethics-and-policy",
                  "Replaces 'is it sentient?' with 'is it a sentience candidate?' at a low bar, hands proportionality to a citizens' panel, names the gaming problem.",
                  "conceptual analysis", "neutral"),
    "milliere2024": ("Milliere & Buckner 2024", 2024, 2024, "AI-and-ML",
                     "Names the Redescription Fallacy - inferring from a deflationary description that a system cannot implement a capacity - and keeps Blockhead as the null.",
                     "review", "supports"),
    "mollo2023vector": ("Coelho Mollo & Milliere 2023/2026", 2023, 2026, "philosophy-of-mind",
                        "The Vector Grounding Problem: content needs causal-informational relations plus a selection history, so parameter-identical systems can differ in content.",
                        "conceptual analysis", "restricts"),
    "dennett1988": ("Dennett 1988", 1988, 1988, "philosophy-of-mind",
                    "Quining Qualia: the felt quality these debates argue about pulls apart under pressure into two incompatible things, so the question has no determinate answer.",
                    "thought experiment", "supports"),
    "block1995": ("Block 1995", 1995, 1995, "philosophy-of-mind",
                  "Not reviewed (no PDF; the fetch failed). The access/phenomenal distinction that the later corpus uses whenever it separates global availability from experience.",
                  "unknown", "unknown"),
    "shevlin2021": ("Shevlin 2021", 2021, 2021, "consciousness-science",
                    "Names the specificity problem: a substrate-neutral theory cannot be applied until its level of abstraction is fixed, and human experiments do not fix it.",
                    "conceptual analysis", "restricts"),
}

POSITIONS = [
    # debate_id, position_id, label, keys (';'), summary
    ("sufficiency", "suf-yes", "The right computation suffices, as a matter of natural law",
     "chalmers1994cfc;chalmers1996rock;chalmers1995qualia;cuda1985;bostrom2003",
     "Mental properties are organizational invariants; deny it and you owe either a brute discontinuity in law or a subject irreparably wrong about its own experience"),
    ("sufficiency", "suf-func", "Consciousness is a specific set of computations, so build them",
     "dehaene2017;graziano2017;butlin2023;doerig2019;chalmers2023llm",
     "Identify consciousness with named functional or computational conditions (C1/C2, an attention schema, indicator properties) that a machine could satisfy"),
    ("sufficiency", "suf-no-sem", "Running a program is not sufficient; semantics and causal powers are missing",
     "searle1980",
     "A person can instantiate any formal program for Chinese and understand nothing; intentionality is a biological product of the brain's causal powers"),
    ("sufficiency", "suf-no-iit", "Consciousness is intrinsic cause-effect power, not computation",
     "tononi2015;albantakis2023",
     "Functional equivalence does not entail phenomenal equivalence: a feedforward duplicate has zero Phi, and a simulation is virtual rather than causally real"),
    ("sufficiency", "suf-nolevel", "No version of functionalism avoids both liberalism and chauvinism",
     "block1978;blockfodor1972",
     "Stated abstractly the theory certifies the Chinese nation and the Bolivian economy; stated concretely it excludes Martians - offered as a burden-of-proof case"),
    ("sufficiency", "suf-notapriori", "Whether the doctrine is true is an empirical question about the brain",
     "piccinini2010;piccinini2013",
     "Functionalism does not entail computationalism once function is mechanistic; whether the brain is a computing mechanism is settled by neuroscience"),
    ("sufficiency", "suf-bio", "Plausible but unearned: life may be doing work the thesis ignores",
     "godfreysmith2016;seth2018beast;aru2023;seth2025;cleeremans2022",
     "Each lowers the thesis's plausibility from biological detail while declining to disprove it: 'the arguments so far do not disprove computational functionalism'"),
    ("sufficiency", "suf-modal", "Occurrent experience cannot turn on inert machinery, so a program cannot suffice",
     "maudlin1989",
     "Sufficiency, necessity and the supervenience of occurrent experience on concurrent physical activity form an inconsistent triad; only sufficiency dies"),
    ("sufficiency", "suf-architecture", "Computationalism survives, but only as a claim about architectures and actual processes",
     "klein_maudlin",
     "Stated over input-output functions it collapses a conscious episode into one primitive step; stated over mechanisms, a simulated brain is not a candidate"),
    ("sufficiency", "suf-deflate", "The question has no determinate answer, because its subject matter is not well defined",
     "dennett1988",
     "Supports functionalism defensively only, by removing a stumbling block: no argument that a program suffices, nothing on substrate, no verdict on the machine"),
    ("sufficiency", "suf-credence", "Neither settled; assign it a credence and proceed",
     "long2024welfare;birch2024;schwitzgebel2015;kleiner2021",
     "Treat the thesis as one uncertain term in a decision problem rather than as a premise to be established or refuted before acting"),

    ("triviality", "triv-yes", "Every ordinary open system realizes every finite automaton",
     "",
     "Putnam 1988 and Searle 1990/1992, both named-only here, are the source; the corpus contains only their critics' reconstructions"),
    ("triviality", "triv-no", "No, once implementation requires counterfactual-supporting transitions",
     "chalmers1996rock;chalmers1994cfc",
     "Putnam reproduces only a trace; strong conditionals plus vector states over distinct physical regions make implementation non-trivial and objective"),
    ("triviality", "triv-cheap", "The counterfactual requirement is met cheaply, so it does not do the work claimed",
     "sprevak2010",
     "Reads Chalmers's own clock-and-dial concession as showing how easily the condition is satisfied - a reading of section 4, not a denial of his conclusion"),
    ("triviality", "triv-perspectival", "Concede perspectivalism and relocate the answer to scientific practice",
     "shagrir2006",
     "Everything can be conceived as a computer; what is discoverable is what the brain represents and which operations it performs over those representations"),
    ("triviality", "triv-different", "The Putnam-Searle problem is not serious; a different multiplicity problem survives",
     "piccinini2010",
     "Their mappings are anomalous because the mapping does the descriptive work; the surviving problem is indefinitely many bona fide computational descriptions"),
    ("triviality", "triv-dilemma", "Grant that counterfactuals block triviality and you inherit a modal mismatch",
     "maudlin1989;klein_maudlin",
     "Maudlin presupposes for argument's sake that counterfactual restrictions work: 'either one accepts explosion, or else one accepts a modal mismatch'"),
    ("triviality", "triv-teleo", "Restrict computing systems to teleofunctional mechanisms",
     "mollo2018",
     "Pancomputationalism is blocked by requiring that performing the computation be one of the system's teleological functions"),

    ("individuation", "ind-syntactic", "Computational identity is fixed syntactically, with no appeal to content",
     "chalmers1994cfc;chalmers1996rock",
     "Building semantic content into implementation conditions would ground computation on a notion that itself desperately needs a foundation"),
    ("individuation", "ind-mechanistic", "Fixed by mechanism: digits, strings, and rule-governed manipulation",
     "piccinini2010;piccinini2013",
     "Computability theorists and computer designers individuate computational states without semantic properties, and we should defer to them"),
    ("individuation", "ind-math", "Fixed by mathematical content, which picks one structure out of many",
     "shagrir2006",
     "The brown-cow cell is an AND gate and an OR gate at once; only content picks AND, because AND corresponds to set intersection among the represented objects"),
    ("individuation", "ind-any", "Fixed by representational content of any type, including broad content",
     "sprevak2010",
     "Nothing physical decides whether a circuit is an AND or an OR gate; non-semantic realization functions are cheap enough to make everything compute everything"),
    ("individuation", "ind-classes", "Fixed functionally, over equivalence classes of physical states",
     "mollo2018",
     "Individuation is functional and medium-independent, implementation mechanistic; logical indeterminacy (AND versus OR) survives one level above, by design"),
    ("individuation", "ind-architecture", "Fixed by architecture and by the process actually running, individuated mechanistically",
     "klein_maudlin",
     "An architecture is a set of primitive operations realised by causally interacting parts; Olympia has a lookup primitive, so she emulates a Turing machine"),
    ("individuation", "ind-history", "What a state is about is fixed by selection history, not by present computation",
     "mollo2023vector",
     "The Swamp LLM is parameter-identical to a trained model and computes the same function, yet represents nothing: function comes from a selection history"),

    ("grain", "grain-causes", "Whatever level reproduces the causes rather than merely describing them",
     "searle1980",
     "Left unspecified; Cuda's note 1 complains that 'causal powers' is never cashed out beyond a gesture at biochemistry"),
    ("grain", "grain-neuron", "Each neuron's functional role - circuit functional equivalence",
     "cuda1985",
     "Explicitly the finest grain, and explicitly the only one at which the paper claims to have established sufficiency"),
    ("grain", "grain-behaviour", "Fine enough to fix behavioural dispositions; for brains, probably neural",
     "chalmers1995qualia;chalmers1994cfc",
     "Causal topology at a level fine enough to determine the causation of behaviour; 'in the brain, it is likely that the neural level suffices'"),
    ("grain", "grain-synapse", "Individual synapses",
     "bostrom2003",
     "The weakest version anyone needs: structural replication 'in suitably fine-grained detail, such as on the level of individual synapses'"),
    ("grain", "grain-algorithm", "Marr's algorithmic and representational level",
     "butlin2023",
     "Neither the implementation level nor the abstract input-output level, so systems computing the same function need not be alike in consciousness"),
    ("grain", "grain-subneuronal", "Sub-neuronal, or no bottom at all",
     "aru2023;seth2025;godfreysmith2016",
     "Dual-compartment pyramidal neurons and metabotropic receptors; metabolic self-maintenance that does not bottom out at any implementation level"),
    ("grain", "grain-iit", "A definite spatio-temporal grain, the one at which integrated information is maximal",
     "tononi2015;albantakis2023",
     "Fixed by the exclusion postulate rather than chosen; for human experience, roughly 100 ms rather than 1 ms or 10 s"),
    ("grain", "grain-io", "The input-output level: what it does, not how it does it",
     "doerig2019",
     "The conclusion drawn from unfolding - consciousness must be described more abstractly than neural wiring if it is to stay inside empirical science"),
    ("grain", "grain-rung4", "Four rungs of abstraction; only the topmost, counterfactual rung is attacked",
     "maudlin1989",
     "Substrate, causal process and pattern of activity are all conceded; what fails is a merely counterfactual or informational connection, with no causal chain"),
    ("grain", "grain-primitive", "The level of an architecture's primitive operations, not the function computed",
     "klein_maudlin",
     "Any computable function can be a single primitive, so function-level computationalism collapses an extended conscious episode into one structureless step"),
    ("grain", "grain-meta", "The parameter cannot be fixed from the human case, and that is the problem",
     "shevlin2021;birch2024;long2024welfare",
     "Conservatism yields false negatives, liberalism certifies network time protocol; Birch puts the scale of functional organization inside reasonable disagreement"),

    ("biology", "bio-metabolism", "Metabolism and self-maintenance are part of the functional profile",
     "godfreysmith2016;seth2025",
     "A non-living functional duplicate may be incoherent, because metabolism is itself one of the functions an autopoietic system performs on itself"),
    ("biology", "bio-allostasis", "Perception exists to regulate the body, and that shapes what experience is like",
     "seth2018beast;seth2025;cleeremans2022",
     "Instrumental interoceptive inference serving allostasis; what machines lack is that anything matters to them at all"),
    ("biology", "bio-architecture", "Specific neural architecture, not life as such",
     "aru2023",
     "Thalamocortical loops, ascending arousal, dual-compartment layer 5 neurons - compatible with substrate flexibility for a machine with the right circuits"),
    ("biology", "bio-powers", "Brains cause minds; whether other materials can is an empirical question",
     "searle1980",
     "Intentionality is as causally dependent on its biochemistry as lactation is; but 'only a machine could think', and silicon is not ruled out a priori"),
    ("biology", "bio-no", "Substrate is irrelevant; the biology requirement is chauvinism",
     "chalmers2023llm;chalmers1995qualia;cuda1985",
     "What matters is how the parts are hooked up, not what they are made of; the replacement arguments are built to make that cost visible"),
    ("biology", "bio-orthogonal", "Not biology versus machine, but computation versus physical causal organisation",
     "tononi2015;albantakis2023",
     "Neuromorphic hardware is exempted by name; animals unlike us may be highly conscious if their architecture is compatible"),

    ("testability", "test-unfold", "Causal-structure theories are falsified or outside science",
     "doerig2019",
     "Any behavioural or report-based result is reproducible by a system with opposite causal structure and arbitrary Phi, so the two are doubly dissociated"),
    ("testability", "test-dilemma", "The testing scheme itself is the problem, and it catches both camps",
     "kleiner2021",
     "Independent prediction and inference data means already falsified; strict dependence means unfalsifiable; no current theory is leniently dependent"),
    ("testability", "test-behaviourbad", "The same fact shows behaviour is a bad guide, not that the theory is untestable",
     "tononi2015;albantakis2023",
     "Both accept that recurrent behaviour is reproducible feedforward and conclude that internal circuitry, not behaviour, is what must be examined"),
    ("testability", "test-indicators", "Proceed by architectural indicators drawn from several theories at once",
     "butlin2023",
     "Score systems by how many computational conditions they meet; behavioural tests are rejected because trained systems can game them"),
    ("testability", "test-operational", "Operationalise the theory and measure it",
     "dehaene2017;graziano2017",
     "Ignition, the attentional blink, confidence and error signals; or the prediction that attention without awareness is less stable and less correctable"),
    ("testability", "test-specificity", "Nothing can be applied until the theory's level of specificity is calibrated",
     "shevlin2021",
     "Use theory-light behavioural markers to fix the grain, then apply the calibrated theory to cases the markers cannot reach"),
    ("testability", "test-gate", "The thesis now works as an admission criterion for which theories get assessed",
     "butlin2023;seth2025",
     "Butlin et al. exclude integrated information theory solely because it denies the thesis (p. 5, p. 33); Seth flags that their conclusions depend on it"),

    ("evidence", "ev-arch", "Downgrade behaviour, upgrade architecture",
     "chalmers2023llm;long2024welfare;birch2024;shevlin2021;milliere2024",
     "Self-reports are fragile and training-contaminated; published criteria get gamed; behavioural indistinguishability is compatible with mere retrieval"),
    ("evidence", "ev-symmetric", "Human reactions to machines are unreliable in both directions",
     "schwitzgebel2015",
     "The ASIMO Problem: concern tracks cuteness, eyes and contingent responsiveness, so a boxy or simulated mind attracts too little and a cute robot too much"),
    ("evidence", "ev-circuit", "Only the internal causal organisation counts",
     "tononi2015;albantakis2023;aru2023",
     "There cannot be an ultimate Turing test for consciousness; the compelling conversation is a simulation of the signatures, not the thing"),
    ("evidence", "ev-function", "Behavioural and neural signatures of the right computations do count",
     "dehaene2017;doerig2019;butlin2023",
     "Consciousness must be described in terms of what it does; the signatures of C1 and C2 are measurable in humans, animals and pre-verbal infants"),
    ("evidence", "ev-introspect", "First-person report cannot settle even the subject's own case",
     "dennett1988",
     "About HUMAN introspection, not machine behaviour: rational, unimpaired subjects cannot tell whether their own qualia shifted. No reviewed work links the two"),
    ("evidence", "ev-claim", "What a machine says about its experience is a readout of its self-model's format",
     "graziano2017",
     "A system with a different internal architecture would build a different self-model and need not lay claim to consciousness in the sense humans understand"),

    ("llm", "llm-candidate", "Not yet, but the obstacles are temporary",
     "chalmers2023llm",
     "Five of the six best objections describe things ordinary engineering is already removing; under 10% now, about 25% for extended systems within a decade"),
    ("llm", "llm-no-arch", "No, and the reasons are architectural",
     "aru2023;birch2024;dehaene2017",
     "No thalamocortical loops or arousal systems; no sub-network persists across a conversation, so 'no one is there'; and the computations are the unconscious kind"),
    ("llm", "llm-scored", "No current system is a strong candidate on any theory's indicators",
     "butlin2023;long2024welfare",
     "Transformers have only a weak case for any global-workspace indicator; Perceiver comes closer but lacks global broadcast"),
    ("llm", "llm-notrajectory", "Unlikely along current trajectories; more plausible as systems become life-like",
     "seth2025;cleeremans2022",
     "Conscious AI would need to be living AI; and the obstacle is not computational power but that nothing is rewarding for the system itself"),
    ("llm", "llm-prior", "Ask about meaning before asking about experience",
     "mollo2023vector;milliere2024",
     "Referential grounding is within reach through selection history; but the Blockhead null hypothesis stands, and only internal evidence could reject it"),
    ("llm", "llm-elsewhere", "The credible routes to machine sentience do not run through chatbots",
     "birch2024",
     "Connectome-based insect emulation, evolved agents converging without gaming, and deliberate minimal global workspaces - sentience may decouple from intelligence"),

    ("precaution", "prec-dontbuild", "Do not build systems whose moral status is genuinely disputable",
     "schwitzgebel2015",
     "The Excluded Middle Policy, paired with Emotional Alignment: build machines that evoke the reactions their real status warrants"),
    ("precaution", "prec-govern", "Assume they will be built; acknowledge, assess, and prepare",
     "long2024welfare",
     "Corporate machinery including an AI welfare officer, probabilistic architectural assessment, and not training systems to simply deny they could be conscious"),
    ("precaution", "prec-candidate", "Shift the question to sentience candidature and let citizens decide precautions",
     "birch2024",
     "A deliberately low bar as a criterion for negligence; four sequential PARC tests applied by a citizens' panel; a run-ahead principle for AI regulation"),
    ("precaution", "prec-roadmap", "Publish the challenge list as a roadmap and equally as red flags",
     "chalmers2023llm",
     "Twelve challenges, with the author declining to say the programme should be pursued and warning against stumbling on AI consciousness unreflectively"),
    ("precaution", "prec-dontpursue", "Do not pursue real artificial consciousness for its own sake",
     "seth2025",
     "Real artificial consciousness risks a mass inauguration of unrecognised suffering; conscious-seeming AI is far likelier and raises its own forced choice"),
    ("precaution", "prec-nosuffering", "Predict that current systems cannot suffer in any morally relevant sense",
     "aru2023",
     "Without skin in the game - a real stake in its own continuation - a system has no personal investment and so nothing that could count as suffering"),
    ("precaution", "prec-both", "Both errors are costly, and the science is the bottleneck",
     "butlin2023;schwitzgebel2015",
     "Under-attribution risks harm at scale; over-attribution misallocates concern and discredits better claims; a good theory of consciousness is a moral imperative"),
]

RELATIONS = {
    "builds-on",
    "critiques",
    "replies-to",
    "reinterprets",
    "uses-as-evidence",
    "excludes",
    "names-as-opponent",
    "flags-as-open",
}

# plan-reviewer MAJOR 5: an edge records a documented ENGAGEMENT, which is not the same
# as a citation of the node's own document. `cites_held_document` says which:
#   yes     - the citing work cites the held document itself
#   sibling - it cites a different statement of the same theory or by the same author
#   other   - it cites a different document entirely (named in `evidence`)
#   unknown - the reviews do not record which document was cited
# Default is "yes"; only departures are listed here.
CITES = {
    ("dehaene2017", "tononi2015"): "sibling",
    ("graziano2017", "tononi2015"): "sibling",
    ("graziano2017", "dehaene2017"): "sibling",
    ("piccinini2013", "shagrir2006"): "sibling",
    ("butlin2023", "dehaene2017"): "sibling",
    ("shevlin2021", "dehaene2017"): "sibling",
    ("shevlin2021", "graziano2017"): "sibling",
    ("cleeremans2022", "block1978"): "sibling",
    ("aru2023", "dehaene2017"): "sibling",
    ("seth2025", "tononi2015"): "sibling",
    ("seth2025", "piccinini2013"): "sibling",
    ("chalmers2023llm", "tononi2015"): "sibling",
    ("chalmers2023llm", "dehaene2017"): "sibling",
    ("long2024welfare", "seth2025"): "sibling",
    ("long2024welfare", "piccinini2010"): "sibling",
    ("long2024welfare", "tononi2015"): "sibling",
    ("doerig2019", "tononi2015"): "sibling",
    ("kleiner2021", "tononi2015"): "sibling",
    ("kleiner2021", "dehaene2017"): "sibling",
    ("kleiner2021", "graziano2017"): "sibling",
    ("klein_maudlin", "piccinini2010"): "sibling",
    ("klein_maudlin", "chalmers1994cfc"): "sibling",
    ("godfreysmith2016", "tononi2015"): "sibling",
    ("klein_maudlin", "tononi2015"): "other",
    ("milliere2024", "block1978"): "other",
    ("schwitzgebel2015", "chalmers1995qualia"): "other",
}

EDGES = [
    # from, to, relation, evidence (review locus; notes where the cited work is a sibling, not this key)
    ("blockfodor1972", "putnam1967", "critiques", "A1 1: the machine-table version of functionalism is the paper's target"),
    ("fodor1974", "putnam1967", "builds-on", "A1 2: 'equivalent automata can be made out of practically anything'"),
    ("block1978", "putnam1967", "critiques", "A1 3: the decomposition stipulation and 'specified only implicitly'"),
    ("block1978", "blockfodor1972", "critiques", "A1 3 n. 14 p. 300: computational-state functionalism does not escape the absent-qualia argument"),
    ("cuda1985", "searle1980", "critiques", "B 2 p. 111: quotes the brain-simulator passage as its target"),
    ("cuda1985", "block1978", "critiques", "B 2 p. 125: Block's coarse-grained counterexamples must now turn on level, not material"),
    ("chalmers1995qualia", "searle1980", "critiques", "B 3 s. 2 and s. 3: water-pipes and wind-machines; Searle's Rediscovery passage quoted and answered"),
    ("chalmers1995qualia", "block1978", "critiques", "B 3 s. 2: the Chinese population stated at full strength, then answered by the homunculi chain"),
    ("chalmers1995qualia", "cuda1985", "builds-on", "B 3 s. 3 footnote: credited among prior neural-replacement scenarios"),
    ("chalmers1994cfc", "searle1980", "critiques", "A2 5 s. 2.5: the Chinese Room answered by gradual demon replacement (Systems Reply)"),
    ("chalmers1994cfc", "putnam1967", "builds-on", "A2 5 note 1: the implementation definition described as the standard one"),
    ("chalmers1996rock", "searle1990", "critiques", "A2 1 s. 2.9: the wall does not satisfy the strong conditionals"),
    ("chalmers1996rock", "searle1980", "critiques", "A2 1 s. 2.9: two distinct automata in the Chinese Room, so expect two minds"),
    ("chalmers1996rock", "chalmers1994cfc", "builds-on", "A2 1 s. 2.10: 'the harder part' explicitly deferred to the companion paper"),
    ("chalmers1996rock", "maudlin1989", "flags-as-open", "A2 1 n. 3: 'This argument requires an in-depth treatment in its own right'"),
    ("shagrir2006", "chalmers1996rock", "builds-on", "A2 2: cited as a refinement of the implementation relation"),
    ("shagrir2006", "fodor1974", "critiques", "A2 2 s. 3: rejects multiple realizability as the source of computational explanatory force"),
    ("piccinini2010", "chalmers1994cfc", "critiques", "A2 3 s. 2.7 (n. 8, p. 275): the dilemma against abstract causal organisation; concedes the point is 'fair'"),
    ("piccinini2010", "shagrir2006", "critiques", "A2 3 s. 3 p. 282: the semantic view of computational states 'is incorrect'"),
    ("piccinini2010", "blockfodor1972", "builds-on", "A2 3 s. 2.1 p. 283: cited for the route by which functionalism came to entail computationalism"),
    ("piccinini2010", "putnam1967", "critiques", "A2 3 s. 2.2: pancomputationalism makes the weak reading nearly trivial"),
    ("piccinini2010", "block1978", "reinterprets", "A2 3 s. 2.6 pp. 300-301: shows at most that computationalism is insufficient, leaving functionalism untouched"),
    ("piccinini2010", "searle1980", "reinterprets", "A2 3 s. 2.6 pp. 300-301: same rereading applied to the Chinese Room"),
    ("piccinini2010", "maudlin1989", "reinterprets", "A2 3 s. 2.6 pp. 300-301: listed with Block and Searle among thought-experiment objections"),
    ("piccinini2010", "bechtelmundale1999", "names-as-opponent", "A2 3 s. 2.6 p. 297: named among the 'foes of multiple realizability' whose position strong computationalism would overturn"),
    ("sprevak2010", "chalmers1996rock", "reinterprets", "A2 4 (PDF p. 10 n. 9): cited to show the clock-and-dial conditions are easily satisfied, not as the solution"),
    ("sprevak2010", "shagrir2006", "builds-on", "A2 4: Shagrir cited within the semantic-individuation camp"),
    ("sprevak2010", "searle1990", "uses-as-evidence", "A2 4 s. 2.2: the brick wall used to show non-semantic realization functions yield universal realization"),
    ("piccinini2013", "shagrir2006", "critiques", "A2 6 s. 2.7 p. 477: names Shagrir 2010, a sibling paper, as equating computation with information processing"),
    ("piccinini2013", "piccinini2010", "builds-on", "A2 6: the mechanistic account of computation carried into the neuroscience"),
    ("mollo2018", "piccinini2010", "critiques", "A2 7 s. 5: granting Piccinini's reply to Haimovici collapses the mechanistic view into the functional view"),
    ("mollo2018", "sprevak2010", "replies-to", "A2 7 s. 7: the dual-gate multiplicity case answered by relocating indeterminacy to the logical level"),
    ("mollo2018", "shagrir2006", "replies-to", "A2 7 s. 7: grants that no non-semantic theory tells AND from OR, and denies this was ever about individuation"),
    ("mollo2018", "chalmers1994cfc", "builds-on", "A2 7 (PDF pp. 14-15): mechanism offered as the successor to causal topology, under tighter constraints"),
    ("maudlin1989", "searle1980", "critiques", "F 1 pp. 414-415: rejects Searle's Chinese Room inference, siding with the BBS commentators that a disjoint mentality could arise"),
    ("dennett1988", "block1978", "critiques", "G 1: quoted twice by name - the Louis Armstrong deflection (p. 281) as the exhibit of the presumption attacked, and 'immediate phenomenological qualities'"),
    ("dennett1988", "blockfodor1972", "critiques", "G 1: quoted at p. 172 on verificationist counterarguments, as the rehabilitation of the inverted-spectrum hypothesis he attacks"),
    ("klein_maudlin", "maudlin1989", "replies-to", "F 2 (PDF pp. 6-16): 'I do not think Maudlin's argument succeeds', then relocates the dispute to architecture"),
    ("klein_maudlin", "chalmers1996rock", "critiques", "F 2 (PDF pp. 8, 15): the triviality family separated from Maudlin's argument; the isomorphism account departed from, naming Chalmers 2011"),
    ("klein_maudlin", "chalmers1994cfc", "critiques", "F 2 (PDF p. 16): organizational invariants do not show a virtual machine is the same as a process with that architecture; cites Chalmers 1996a, a sibling statement"),
    ("klein_maudlin", "block1978", "reinterprets", "F 2 (PDF pp. 8, 12): the Chinese Nation and the lookup-table objection both re-diagnosed as failures of computational structure"),
    ("klein_maudlin", "searle1980", "reinterprets", "F 2 (PDF pp. 8, 16): Searle's interpretation worry distinguished, then the simulation verdict conceded as 'suspiciously close'"),
    ("klein_maudlin", "tononi2015", "critiques", "F 2 (PDF p. 4): cites Fekete & Edelman 2011 against the view that inactive elements contribute to experience"),
    ("klein_maudlin", "piccinini2010", "builds-on", "F 2 (PDF p. 15): architectures as sets of mechanisms; cites Piccinini 2007 and 2015, sibling statements"),
    ("tononi2015", "searle1980", "builds-on", "D 1 endnote 14: the same conclusion credited to the Chinese Room and to Leibniz's mill"),
    ("dehaene2017", "tononi2015", "critiques", "D 2 s. 2.2: 'mere information-theoretic quantities do not suffice'; the cited reference is Tononi et al. 2016, a sibling statement"),
    ("graziano2017", "tononi2015", "critiques", "D 3 p. 7: integrated information called non-explanatory and unfalsifiable; cites Tononi 2008, a sibling statement"),
    ("graziano2017", "dehaene2017", "critiques", "D 3 p. 7: global workspace judged incomplete; cites Baars 1988 and Dehaene 2014, sibling statements"),
    ("doerig2019", "tononi2015", "critiques", "D 4 s. 1.2: the unfolding argument's primary target; cites Oizumi et al. 2014 as the formal statement"),
    ("kleiner2021", "doerig2019", "replies-to", "D 5 (PDF p. 2): self-described 'generalization and correction' of the unfolding argument"),
    ("kleiner2021", "tononi2015", "critiques", "D 5: the independence horn; cites Oizumi et al. 2014, Albantakis & Tononi 2019, Koch 2019"),
    ("kleiner2021", "dehaene2017", "critiques", "D 5 (PDF p. 14): global workspace listed under strict dependence; cites Baars 1997, Dehaene & Changeux 2004"),
    ("kleiner2021", "graziano2017", "critiques", "D 5 (PDF p. 14): the attention schema listed among theories exposed to the strict-dependence horn; cites the theory, not this 2017 paper"),
    ("albantakis2023", "tononi2015", "builds-on", "D 7: supersedes the earlier formulation; cited as ref. 19"),
    ("butlin2023", "tononi2015", "excludes", "D 6 s. 2.3 (p. 5, p. 33): excluded from the survey because incompatible with computational functionalism"),
    ("butlin2023", "graziano2017", "builds-on", "D 6 s. 2.4: AST-1 derived from the attention schema theory"),
    ("butlin2023", "dehaene2017", "builds-on", "D 6 s. 2.2: GWT-1 to GWT-4 derived; cites Baars, Dehaene 2014 and Mashour et al. 2020"),
    ("butlin2023", "searle1980", "names-as-opponent", "D 6 s. 1.2.1 p. 12: named, with Seth 2021, as the rejection case for the report's working assumption"),
    ("shevlin2021", "block1978", "builds-on", "E 2 p. 300: the specificity problem presented as a descendant of liberalism versus chauvinism"),
    ("shevlin2021", "dehaene2017", "critiques", "E 2 p. 300: global workspace used as the worked illustration; quotes Dehaene 2014, a sibling statement"),
    ("shevlin2021", "tononi2015", "uses-as-evidence", "E 2 p. 303: quoted for the claim that consciousness is widespread even in simple systems"),
    ("shevlin2021", "searle1980", "reinterprets", "E 2 p. 310: the Chinese Room recast as a weak candidate his method would exclude"),
    ("shevlin2021", "graziano2017", "builds-on", "E 2 p. 299: the attention schema listed among the cognitive theories at issue; cites Graziano 2013"),
    ("schwitzgebel2015", "searle1980", "reinterprets", "E 1 s. 2.4 and s. 2.6: read as an epistemic rather than metaphysical problem, and shown to overshoot its source"),
    ("schwitzgebel2015", "block1978", "reinterprets", "E 1 s. 2.6 (ms. p. 30): the lookup-table mannequin recast as an epistemic problem"),
    ("schwitzgebel2015", "cuda1985", "reinterprets", "E 1 n. 5 (ms. p. 11): explicitly distinguishes its own slippery slope, which assumes rather than proves preserved consciousness"),
    ("schwitzgebel2015", "chalmers1995qualia", "reinterprets", "E 1 n. 5 (ms. p. 11): same distinction; cited there as 'Chalmers 1996'"),
    ("schwitzgebel2015", "bostrom2003", "uses-as-evidence", "E 1 s. 2.1 (ms. p. 5): simulated worlds cited as a case strengthening premise 2"),
    ("godfreysmith2016", "thompson2007", "builds-on", "C 1 n. 1: 'Thompson's book has influenced this paper'"),
    ("godfreysmith2016", "tononi2015", "critiques", "C 1 s. 5 (PDF p. 13): characterised as near-panpsychist; the held PDF is the 2014 talk, so it cites an earlier Tononi-Koch statement, not this 2015 paper"),
    ("seth2018beast", "thompson2007", "builds-on", "C 2 (PDF p. 13): cited for strong continuity between life, mind and consciousness"),
    ("cleeremans2022", "seth2018beast", "builds-on", "C 3 s. 8 (pp. 7-8): cited for the visceral grounding of the experiencing subject"),
    ("cleeremans2022", "block1978", "critiques", "C 3 s. 2: the access/phenomenal distinction called fundamentally misleading; cites Block 1995, a sibling paper"),
    ("aru2023", "tononi2015", "uses-as-evidence", "C 4 s. 2.2: cited for the claim that software lacks real cause-effect power"),
    ("aru2023", "dehaene2017", "uses-as-evidence", "C 4 s. 2.2: global neuronal workspace summarised as one of the converging theories; cites Dehaene and Baars"),
    ("seth2025", "godfreysmith2016", "builds-on", "C 5 s. 3.3: the 'differences on the inside' objection to neural replacement"),
    ("seth2025", "aru2023", "builds-on", "C 5 s. 4.1: 'skin in the game' borrowed by name"),
    ("seth2025", "seth2018beast", "builds-on", "C 5 s. 4.5: the beast-machine formulation carried forward"),
    ("seth2025", "searle1980", "builds-on", "C 5 s. 4.0: the term biological naturalism taken from Searle and redefined"),
    ("seth2025", "butlin2023", "critiques", "C 5 s. 3.1 (PDF p. 6): flags that the report's conclusions depend on an assumption it acknowledges"),
    ("seth2025", "chalmers1995qualia", "critiques", "C 5 s. 3.3 footnote: the plausibility objections extended to the dancing-qualia argument"),
    ("seth2025", "tononi2015", "reinterprets", "C 5 s. 5.6: if IIT is right, conventional AI is off the path but nothing is special about life; cites Tononi et al. 2016, a sibling statement"),
    ("seth2025", "albantakis2023", "reinterprets", "C 5 s. 5.6: cited alongside Tononi et al. 2016 for IIT's sufficient conditions"),
    ("seth2025", "piccinini2013", "builds-on", "C 5 s. 3.4: neural computation as a broader notion; cites Piccinini 2018/2020/2023, sibling statements"),
    ("seth2025", "chalmers2023llm", "names-as-opponent", "C 5 references: cited among the works arguing that current systems are serious candidates"),
    ("seth2025", "bostrom2003", "uses-as-evidence", "C 5 s. 2.0: the simulation argument cited as part of the technophilic framing"),
    ("seth2025", "schneider2019", "builds-on", "C 5 s. 7.0 footnote: cited as one proposal for a Garland test"),
    ("chalmers2023llm", "butlin2023", "builds-on", "E 3 references: cited as the indicator-properties report"),
    ("chalmers2023llm", "tononi2015", "critiques", "E 3 s. 2.3: IIT's zero-Phi prediction for feedforward systems; cites Tononi 2004, a sibling statement"),
    ("chalmers2023llm", "dehaene2017", "builds-on", "E 3 s. 2.3: global workspace used as an objection source; cites Baars 1988 and Dehaene 2014"),
    ("chalmers2023llm", "schneider2019", "builds-on", "E 3 s. 2.2: the AI Consciousness Test, which motivates the untrained-description challenge"),
    ("mollo2023vector", "searle1980", "builds-on", "E 4 n. 5: the symbol grounding problem taken as an elaboration of the Chinese Room"),
    ("mollo2023vector", "milliere2024", "builds-on", "E 4 n. 1: cited as the general introduction to language models"),
    ("mollo2023vector", "chalmers2023llm", "builds-on", "E 4 references: Chalmers 2023 and 2025 cited in the 2026 published version"),
    ("milliere2024", "block1978", "builds-on", "E 7: Blockhead as the standing null hypothesis; cites Block 1981, whose list-searcher appears in the held 1978 reprint at pp. 281-282"),
    ("milliere2024", "mollo2023vector", "builds-on", "E 7 s. 3: cited for the vector grounding problem"),
    ("milliere2024", "searle1980", "reinterprets", "E 7: cited only to note that some take understanding to require consciousness, deferred to Part II"),
    ("long2024welfare", "butlin2023", "builds-on", "E 5 p. 16: the indicator list reproduced in full"),
    ("long2024welfare", "chalmers2023llm", "uses-as-evidence", "E 5 p. 18: Chalmers's credence quoted verbatim at length"),
    ("long2024welfare", "birch2024", "builds-on", "E 5: the marker method and precautionary framing; Birch is a contributing author"),
    ("long2024welfare", "shevlin2021", "builds-on", "E 5: cited on criteria for AI moral patienthood"),
    ("long2024welfare", "godfreysmith2016", "names-as-opponent", "E 5 p. 27: listed among in-practice biology views; cites Godfrey-Smith 2016, 2020, 2024"),
    ("long2024welfare", "seth2025", "names-as-opponent", "E 5 p. 27: listed among in-practice biology views; cites Seth 2021 and 2024, sibling statements"),
    ("long2024welfare", "tononi2015", "names-as-opponent", "E 5 p. 27: integrated information listed among views requiring absent computational features; cites Koch 2019"),
    ("long2024welfare", "putnam1967", "builds-on", "E 5 p. 15: cited in the definition of computational functionalism"),
    ("long2024welfare", "piccinini2010", "builds-on", "E 5 p. 15: cited in the same definition; the citation is Piccinini 2018, a sibling statement"),
    ("long2024welfare", "schneider2019", "builds-on", "E 5: the AI Consciousness Test discussed, with Udell & Schwitzgebel's worries noted"),
    ("birch2024", "butlin2023", "builds-on", "E 6 s. 12: 'we must not be complacent about the risks of developing new kinds of sentient being'"),
    ("birch2024", "schneider2019", "critiques", "E 6 s. 12: regular sentience testing judged 'currently unfeasible' because of gaming"),
    ("birch2024", "chalmers2023llm", "critiques", "E notes 4: the decoupling of sentience from intelligence, and 'no one is there' against a live chatbot credence"),
]

GRAIN = [
    # key, level_named, locus, direction, note
    ("searle1980", "Unspecified - whatever level 'reproduces the causes and not merely describes them'",
     "Author's Response, pp. 452-453", "unspecified",
     "Cuda's n. 1 (p. 126) complains Searle never says what components must share with neurons beyond 'something to do with biochemistry'"),
    ("cuda1985", "Circuit functional equivalence: the functional role of each neuron",
     "pp. 124-125", "fine",
     "Stated as the finest grain and the only one at which sufficiency is claimed; explicitly does not establish sufficiency at any coarser level"),
    ("chalmers1995qualia", "Fine enough to determine the system's behavioural dispositions; 'in the brain, it is likely that the neural level suffices'",
     "section 1", "fine",
     "A coarser level 'might also work'; the grain is set by what fixes behaviour, not by biology"),
    ("chalmers1994cfc", "Causal topology at a level 'fine enough to determine the causation of behavior'; for the brain 'probably the neural level or higher'",
     "PDF p. 7", "fine",
     "The notion is conceded to be 'necessarily informal for now'"),
    ("chalmers1996rock", "Combinatorial-state-automaton substates, each corresponding to 'a distinct physical region in the system'",
     "p. 325", "fine",
     "Section 7 admits the distinct-region requirement may be too strong (virtual memory) while dropping independence collapses CSA implementation into FSA implementation"),
    ("bostrom2003", "Individual synapses: structural replication 'in suitably fine-grained detail, such as on the level of individual synapses'",
     "p. 244", "fine",
     "The weakest version anyone needs; chemicals affect experience only via their influence on computational activity"),
    ("blockfodor1972", "Machine-table individuation, rejected as simultaneously too coarse and too fine",
     "pp. 170-175", "meta",
     "One state at a time and a finite list on one side; 'damn' versus 'darn' making two pains type-distinct on the other"),
    ("block1978", "Functional equivalence declared relative to a level of abstractness, with the fatal step located at the input-output interface",
     "p. 274; section 3.1", "meta",
     "Physical descriptions of inputs and outputs are chauvinist; descriptions purely as inputs and outputs are liberal; disjunction and mental vocabulary are both barred"),
    ("piccinini2010", "Mechanistic: components with functions, organised - with a stored program a physical part of the machine",
     "pp. 285-297", "unspecified",
     "The grain is whatever neuroscience finds; the paper's point is that the question is empirical rather than settled in advance"),
    ("piccinini2013", "Medium-independent vehicles whose functionally relevant properties are spike rate and spike timing - neither digits nor continuous magnitudes",
     "p. 476", "fine",
     "Neural computation is sui generis, so a digital or analog abstraction of it is the wrong grain by construction"),
    ("mollo2018", "Equivalence classes of physical states, defined by 'input values that lead to uniform behaviour of the whole device'",
     "PDF p. 20", "unspecified",
     "Chosen to make cushion intervals and noise bands irrelevant while preserving equivalence across electronic and hydraulic media"),
    ("shagrir2006", "The level at which a semantic task is specified - content-bearing inputs and outputs",
     "pp. 403, 411-412", "unspecified",
     "Only mathematical or formal content individuates; a brown-cow cell and a black-dog cell share a computational identity"),
    ("sprevak2010", "Whatever level fixes representational content, which may be broad and environment-involving",
     "PDF pp. 22-25", "meta",
     "If content is broad, two intrinsic duplicates in different environments are not running the same computation, so grain cannot be read off the system alone"),
    ("mollo2023vector", "No synchronic level suffices: content is fixed by selection history, not by present structure",
     "PDF p. 21 (Swamp LLM)", "meta",
     "Parameter-identical systems computing the same function differ in whether their states represent; an orthogonal constraint rather than a finer or coarser setting"),
    ("tononi2015", "A definite spatio-temporal grain - the one at which integrated information is maximal; for human experience roughly 100 ms",
     "pp. 9-10", "derived",
     "The grain is derived from the exclusion postulate rather than chosen; a mechanism cannot have effects at a fine grain and additional effects at a coarser one"),
    ("albantakis2023", "The maximal substrate: the definite set of units and grain maximising system integrated information",
     "p. 10", "derived",
     "Many overlapping sets may have positive integrated information; only the maximum counts, which is stricter than the gloss used by some critics"),
    ("dehaene2017", "The level of information-processing computations: global availability (C1) and self-monitoring (C2)",
     "p. 486", "coarse",
     "Explicitly 'resolutely computational'; information-theoretic quantities alone are said not to suffice without the nature and depth of what is processed"),
    ("graziano2017", "The level of an internal model of attention - a deliberately inaccurate schema, not the attention mechanism itself",
     "pp. 4-5", "coarse",
     "Declared buildable with current technology; a differently architected system would build a different self-model and need not claim consciousness"),
    ("doerig2019", "The input-output level: 'consciousness must be described in terms of what it does, and not how it does it'",
     "p. 56", "coarse",
     "The conclusion drawn from the unfolding construction; global workspace, higher-order and predictive-processing theories are exempted by name"),
    ("butlin2023", "Marr's algorithmic and representational level - neither the implementation level nor the input-output function",
     "pp. 13-14", "unspecified",
     "Explicitly denies that systems computing the same input-output function are alike in consciousness, citing Sprevak 2007"),
    ("aru2023", "Sub-neuronal: dual-compartment layer 5 pyramidal neurons and metabotropic receptors 'not usually modeled in artificial neural networks'",
     "PDF pp. 9-12", "fine",
     "The stated position is that consciousness may be implementable but at a specificity beyond present and perhaps future AI"),
    ("seth2025", "No bottom: 'the imperative to stay alive doesn't bottom out at any particular implementation level in our biology'",
     "section 4.1", "no-bottom",
     "Proposes causal and informational closure measures to determine empirically how far neural dynamics can be abstracted from finer levels (section 3.5)"),
    ("godfreysmith2016", "Metabolic activity counted as part of a human agent's functional profile",
     "PDF pp. 11-12", "no-bottom",
     "Aimed at the thought experiment rather than the thesis: holding function fixed while removing life may be ill-formed"),
    ("seth2018beast", "Distinguishes being a model from having a model - whether a generative model must be explicitly encoded or only behaved as if",
     "Box 4, PDF p. 20", "meta",
     "Framed as possibly mattering for what selfhood is like; the paper poses it as an outstanding question rather than answering it"),
    ("maudlin1989", "A four-rung ladder of abstraction; only the top rung - a counterfactual or informational connection with no causal chain - is denied",
     "pp. 426-429", "meta",
     "Substrate independence at the level of causal processes is conceded: 'the silicon brain and the hydraulic brain may, for all we have said, be conscious' (p. 429)"),
    ("klein_maudlin", "An architecture's primitive operations and the process actually running, not the mathematical function computed",
     "PDF pp. 9-16", "unspecified",
     "Any computable function can be made a single primitive, so a function-level criterion makes an extended conscious episode a structureless one-step computation"),
    ("shevlin2021", "The specificity problem: the grain cannot be read off the human experiments the theory was built on",
     "pp. 300-306", "meta",
     "Conservatism restricts consciousness to humans; liberalism certifies network time protocol as global information sharing"),
    ("birch2024", "Places 'the scale of functional organization that matters' inside the zone of reasonable disagreement and routes around it",
     "p. 5", "meta",
     "Advises looking for ways forward that do not rely on controversial assumptions about the grain; his third AI pathway nonetheless uses a minimal global workspace"),
    ("chalmers2023llm", "Organisational: 'what matters is how neurons or silicon chips are hooked up to each other, not what they are made of'",
     "PDF p. 7", "unspecified",
     "The grain is left open; the paper works instead through six architectural features and assigns each a credence"),
    ("schwitzgebel2015", "A small artificial component 'that contributes identically to the entity's psychology'",
     "ms. p. 10", "assumed",
     "Assumed rather than argued: n. 5 distinguishes this from Cuda and Chalmers, who try to establish that consciousness survives replacement"),
    ("long2024welfare", "Assigns a credence to computational functionalism itself rather than naming a grain",
     "p. 15", "meta",
     "Illustrative arithmetic: a 30-50% chance the thesis holds times a 30-50% chance a given system qualifies gives 9-25%"),
]

CORRECTIONS = [
    # key, commonly_attributed_claim, what_the_reviewed_paper_says, verdict
    ("searle1980", "Searle argues that machines cannot think",
     "'Only a machine could think, and indeed only very special kinds of machines' (p. 424); he rejects only the sufficiency of running a program (B 1)",
     "does-not-hold"),
    ("searle1980", "Searle rules out silicon minds",
     "'I offer no a priori proof that a system of integrated circuit chips couldn't have intentionality. That is ... an empirical question' (p. 453) (B 1)",
     "does-not-hold"),
    ("searle1980", "Searle opposes artificial intelligence research",
     "'I am all in favor of weak AI, at least as a research program' (p. 453); the target is strong AI's claim that the program is the explanation (B 1)",
     "does-not-hold"),
    ("searle1980", "Searle concedes nothing to the replacement arguments",
     "Author's Response: 'if the stimulation of the causes is at a low enough level to reproduce the causes ... the simulation will reproduce the effects' (pp. 452-453) (B notes 4)",
     "does-not-hold"),
    ("dennett1988", "Dennett denies that conscious experience exists",
     "'Since I don't deny the reality of conscious experience, I grant that conscious experience has properties'; what is denied is that any property is ineffable, intrinsic, private or directly apprehensible (G 1)",
     "does-not-hold"),
    ("dennett1988", "Quining Qualia replies to the fading and dancing qualia arguments",
     "It predates Chalmers 1995 by seven years and does not cite him; the two meet at one premise about introspection, stated independently in the opposite time order (G 1)",
     "misattributed"),
    ("dennett1988", "Quining Qualia answers the anti-functionalist literature generally",
     "Block's liberalism/chauvinism dilemma and the input-output problem are untouched, and Searle 1980 is not in the bibliography at all; the target is one premise family (G notes 5)",
     "does-not-hold"),
    ("dennett1988", "Dennett concludes that a functional duplicate does have qualia",
     "He does not claim the wine-tasting machine has qualia; the conclusion withholds the affirmative verdict as much as the negative, and 'no qualia at all' is flagged as tactical (G 1, endnote 2)",
     "does-not-hold"),
    ("dennett1988", "Dennett and the replacement arguments disagree about whether subjects are in error",
     "His conclusion is that there is no determinate fact; Cuda's step 2 and Chalmers's Joe are built against a systematic-error hypothesis. Whether they reach the no-fact case is addressed by no reviewed work (G notes 3)",
     "disputed"),
    ("aru2023", "Aru et al. deny that machines could be conscious",
     "Three explicit disclaimers: not only mammalian brains, not only living systems, not impossible in software; the claim is about present systems and specificity (C 4)",
     "does-not-hold"),
    ("piccinini2010", "Piccinini is an anti-triviality theorist answering Putnam and Searle",
     "He calls their problem 'not very serious' (p. 281) because their mappings are anomalous, and raises a different surviving problem about bona fide descriptions (A2 notes 1)",
     "misattributed"),
    ("block1978", "Blockhead is an argument against computational functionalism",
     "The list-searcher is offered against a reply to Block's own argument - 'this is just crude behaviorism' (pp. 281-282) - not against functionalism itself (A1 notes 5)",
     "partly"),
    ("block1978", "Block refutes functionalism",
     "'I do not claim that this is a conclusive argument against functionalism ... it is best construed as a burden-of-proof argument' (p. 296) (A1 3)",
     "partly"),
    ("tononi2015", "Doerig et al.'s gloss: on IIT, recurrent systems are always conscious",
     "IIT requires a maximum of integrated information, not merely positive Phi (albantakis2023, p. 10); the unfolding construction respects maximality, so gloss and construction come apart (D notes 3)",
     "partly"),
    ("chalmers1994cfc", "Chalmers established that the right computation is metaphysically sufficient for a mind",
     "A footnote added in 2011 restricts computational sufficiency and organizational invariance to nomological necessity, leaving zombies metaphysically possible (A2 5 s. 2.8)",
     "partly"),
    ("chalmers1995qualia", "The fading and dancing qualia arguments prove that functional duplicates are conscious",
     "Section 5 states the conclusion is empirical (natural) impossibility only, and that the position is compatible with property dualism about experience (B 3)",
     "partly"),
    ("cuda1985", "Cuda established that functional organisation suffices for consciousness",
     "He establishes sufficiency only at circuit functional equivalence and says so; what he claims more broadly is to disqualify material as a ground of objection (B 2)",
     "partly"),
    ("blockfodor1972", "Block and Fodor concluded against a computational theory of mind",
     "'It may be both true and important that organisms are probabilistic automata'; the target is the machine-table level, and computational states are offered as the repair (A1 1)",
     "does-not-hold"),
    ("tononi2015", "Integrated information theory is carbon chauvinism",
     "Endnote 15: 'there is no reason why hardware-level, neuromorphic models ... could not approximate, one day, our level of consciousness' (D 1, D notes 7)",
     "does-not-hold"),
    ("schwitzgebel2015", "Schwitzgebel and Garza run the Cuda-Chalmers replacement argument",
     "n. 5 (ms. p. 11): they assume consciousness is preserved and argue something ethical; Cuda and Chalmers try to establish the preservation (E 1 s. 2.3)",
     "does-not-hold"),
    ("chalmers2023llm", "Chalmers and Birch agree about language models, as their joint report shows",
     "They disagree: Birch says of a chatbot conversation that 'no one is there' (p. 13) while Chalmers holds a live credence; co-authorship is not corroboration (E notes 4-5)",
     "does-not-hold"),
    ("butlin2023", "The report found no obvious barriers to building conscious AI systems",
     "A title-page footnote records that this sentence was revised: satisfying the indicators 'would not mean that such an AI system would definitely be conscious' (D 6)",
     "partly"),
    ("sprevak2010", "Sprevak cites Chalmers 1996 as the solution to universal realization",
     "He cites it to show how cheaply the counterfactual requirement is met given a clock and a dial (PDF p. 10 n. 9) - a reading of Chalmers's own concession (A2 notes 4)",
     "misattributed"),
    ("fodor1974", "Fodor argued that the autonomous psychological level is computational",
     "He argues only that psychology does not reduce; the step from irreducible to computational is taken by others (A1 2)",
     "does-not-hold"),
    ("seth2025", "Seth refutes computational functionalism",
     "'The arguments so far do not disprove computational functionalism. But they do render it less plausible, and less appealing' (section 3.6) (C 5)",
     "partly"),
    ("cleeremans2022", "Consciousness Matters is an anti-functionalist paper",
     "It argues that consciousness has a function, and its anti-epiphenomenalism runs through multiple realizability (List's realization insensitivity) (C notes 2)",
     "does-not-hold"),
    ("kleiner2021", "Kleiner and Hoel restate the unfolding argument",
     "Self-described 'generalization and correction'; its second horn hits the functionalist theories that the unfolding argument exempts (D 5, D notes 5)",
     "does-not-hold"),
    ("graziano2017", "The attention schema theory explains subjective experience",
     "'The theory emphatically does not explain how we have a subjective experience. It explains how a machine claims to have a subjective experience' (p. 5) (D 3)",
     "does-not-hold"),
    ("dehaene2017", "Dehaene, Lau and Kouider answer the question of experience",
     "The experiential question is declared beyond scope (p. 492); what is offered instead is a covariation observation about blindsight (D 2)",
     "does-not-hold"),
    ("piccinini2013", "Piccinini and Bahar refute computationalism",
     "They defend generic computationalism and reject only its digital and analog species; neural computation is sui generis (A2 6)",
     "does-not-hold"),
    ("mollo2023vector", "The Vector Grounding Problem paper shows that language models understand language",
     "The scope restriction is stated twice: not about understanding, knowledge, linguistic acts, or mental properties; grounding is a floor, not a ceiling (E 4)",
     "does-not-hold"),
    ("shagrir2006", "Shagrir argues that the brain is not really a computer",
     "He concedes that being a computer is perspectival while rescuing the empirical content of computational neuroscience; the restriction is on individuation (A2 2)",
     "partly"),
    ("bostrom2003", "Bostrom offers a fourth position on substrate independence",
     "He imports it as an undefended premise and states its weakest useful form; his value here is as evidence about the thesis's status in 2003 (B notes 9)",
     "misattributed"),
    ("shagrir2006", "Marr's computational level shows that computation is individuated non-representationally",
     "Three reviewed papers read Marr incompatibly: Shagrir (correspondence), Sprevak reporting Egan (function-theoretic, collapsing into representational), Piccinini & Bahar (a fallacy) (A2 notes 2)",
     "disputed"),
    ("block1978", "Block's 1972 and 1978 papers are two independent data points",
     "Block closes his own 1972 escape route in 1978 (n. 14, p. 300); the two should be presented as one developing position (A1 notes 2)",
     "does-not-hold"),
    ("doerig2019", "The unfolding argument is a version of the philosophical zombie argument",
     "Section 2.5 distinguishes both scope (only causal-structure theories; it favours functionalism) and modality (a construction recipe, not a conceivability claim) (D 4)",
     "does-not-hold"),
    ("maudlin1989", "Maudlin argues against substrate independence, or that machines cannot be conscious",
     "He grants that silicon and hydraulic brains may be conscious (p. 429) and that computational structure may be necessary (p. 431); only sufficiency dies (F 1)",
     "does-not-hold"),
    ("maudlin1989", "Olympia is a funny-instantiation argument like Block's Chinese Nation",
     "He rejects those intuitions outright - 'I cannot think of one reason to accord those intuitions any weight' (p. 414); Klein separates the two families (F 2, PDF p. 8)",
     "does-not-hold"),
    ("maudlin1989", "Olympia is a triviality or exploding-implementation argument",
     "He presupposes, for argument's sake, that counterfactual restrictions do block explosions; the argument is best read as a dilemma (F 2, PDF p. 8)",
     "misattributed"),
    ("klein_maudlin", "Klein refutes computationalism about consciousness",
     "'I do not think Maudlin's argument succeeds' (PDF p. 7); he defends computationalism while narrowing it to architectures and actual processes (F 2)",
     "does-not-hold"),
    ("butlin2023", "The indicator list states necessary or sufficient conditions for consciousness",
     "'Systems that have more of these features are better candidates ... We do not endorse these stronger claims' (p. 45) (D 6)",
     "does-not-hold"),
]

NOT_HELD = [
    # label, year, community, why_relevant, cited_by (';' of reviewed keys)
    ("Putnam 1967, Psychological Predicates (The Nature of Mental States)", 1967, "philosophy-of-mind",
     "Named-only in the manifest. The founding statement both Block papers target and every later work inherits; two paginations are in play and neither is canonical here",
     "blockfodor1972;block1978;piccinini2010;chalmers1994cfc;long2024welfare"),
    ("Block 1995, On a confusion about a function of consciousness", 1995, "philosophy-of-mind",
     "Named-only; the fetch failed. The access/phenomenal distinction the later corpus uses whenever it separates global availability from experience, and Block's later anti-computationalism",
     "cleeremans2022;butlin2023;kleiner2021;chalmers2023llm;dennett1988"),
    ("The Chinese Room reply literature: the Systems and Robot Replies in developed form; Churchland & Churchland 1990", 1990, "philosophy-of-mind",
     "searle1980 is the most-engaged work here and the only reviewed reply is cuda1985, aimed at one paragraph. The 27 BBS commentaries were not reviewed, so the argument reads less answered than it is",
     "searle1980;cuda1985;chalmers1996rock;schwitzgebel2015"),
    ("The deflationary successors: Dennett 1991 Consciousness Explained; Frankish on illusionism", 2016, "philosophy-of-mind",
     "The strand dennett1988 opens has no successor here, while every AI-minds work presupposes a determinate fact about whether a system is conscious. Nothing presses the deflationary line against them",
     "dennett1988;cleeremans2022;graziano2017;birch2024"),
    ("Post-1996 triviality literature: Godfrey-Smith 2009; Scheutz; Rescorla; Schweizer", 2009, "philosophy-of-computation",
     "The triviality debate did not stop with Chalmers's reply. The corpus holds that reply and its critics and stops there, which makes the debate look more settled here than it is in the field",
     "chalmers1996rock;sprevak2010;piccinini2010"),
    ("Bechtel & Mundale 1999, Multiple realizability revisited", 1999, "philosophy-of-mind",
     "Named-only in the manifest. The standard challenge to multiple realizability, which every reviewed work assumes; its absence leaves that premise unopposed in this corpus",
     "piccinini2010;seth2025"),
    ("Searle 1990, Is the brain's mind a computer program?", 1990, "philosophy-of-mind",
     "Named-only in the manifest. The compressed three-axiom restatement and the source of the wall-runs-WordStar claim that Chalmers 1996 answers",
     "chalmers1996rock;sprevak2010"),
    ("Schneider 2019, Artificial You: AI and the Future of Your Mind", 2019, "philosophy-of-mind",
     "Named-only in the manifest. Source of the AI Consciousness Test that Chalmers, Birch, Butlin et al. and Long et al. all assess; leaves a 16-year gap after Bostrom 2003",
     "chalmers2023llm;birch2024;butlin2023;long2024welfare;seth2025"),
    ("Thompson 2007, Mind in Life", 2007, "philosophy-of-mind",
     "Named-only in the manifest. The hub cited by all three biological works for continuity between life and mind; the highest-value single addition to this corpus",
     "godfreysmith2016;seth2018beast;seth2025"),
    ("Putnam 1988, Representation and Reality - the universal-realization appendix (pp. 120-25)", 1988, "philosophy-of-computation",
     "The triviality argument itself, reconstructed here only from Chalmers 1996 section 2. The corpus holds its critics and not the source, which is why the triviality debate reads one-sided (section 3.2)",
     "chalmers1996rock;shagrir2006;piccinini2010;sprevak2010;mollo2018"),
    ("Putnam 1988, Representation and Reality - the externalist abandonment of functionalism", 1988, "philosophy-of-mind",
     "Also where functionalism's founder abandons it, on the ground that content is not fixed by internal functional organisation - a second challenge, bearing on individuation (3.3), untraced here",
     "chalmers1996rock;piccinini2010"),
    ("Searle 1992, The Rediscovery of the Mind", 1992, "philosophy-of-mind",
     "Contains the fading-qualia passage (pp. 66-67) that Chalmers 1995 quotes and answers, and the observer-relativity claims Shagrir contests",
     "chalmers1995qualia;shagrir2006;chalmers1996rock"),
    ("Egan 1991-1995, the function-theoretic view of computational content", 1995, "philosophy-of-computation",
     "The non-semantic, purely mathematical account of Marr's computational level; the direct target of Sprevak's individuation argument",
     "sprevak2010;piccinini2010;shagrir2006"),
    ("Marr 1982, Vision", 1982, "philosophy-of-computation",
     "Read three incompatible ways inside this corpus; the disagreement about what Marr's computational level shows is itself part of the field's history",
     "shagrir2006;sprevak2010;piccinini2013"),
    ("McCulloch & Pitts 1943, A logical calculus of the ideas immanent in nervous activity", 1943, "biology-and-neuroscience",
     "The origin of digital computationalism about the brain, and the source of the two assumptions Piccinini & Bahar show were never empirically supported",
     "piccinini2010;piccinini2013;seth2025"),
    ("von Neumann 1951 and 1958, on neural nets and the computer-and-brain analogy", 1958, "philosophy-of-computation",
     "The route by which pancomputationalism entered the literature, and the source of the spike-rates-as-digits proposal reported as still unsolved",
     "piccinini2010;piccinini2013"),
    ("Block 1981, Psychologism and Behaviorism (the giant lookup table)", 1981, "philosophy-of-mind",
     "The standalone Blockhead paper; the held 1978 reprint contains the list-searcher at pp. 281-282, but the argument's canonical home is not in this corpus",
     "chalmers1996rock;chalmers1994cfc;milliere2024;schwitzgebel2015"),
    ("Shoemaker 1975 and 1982, Functionalism and Qualia; The Inverted Spectrum", 1982, "philosophy-of-mind",
     "The argument that absent qualia are logically impossible, and the inverted-spectrum statement Chalmers answers; both known here only through citing papers",
     "block1978;cuda1985;chalmers1995qualia"),
    ("Lewis 1972 and Armstrong 1968, causal-role analyses of mental terms", 1972, "philosophy-of-mind",
     "The platitude and causal-role machinery Chalmers leans on for psychological properties and Block attacks with paralytics and brains in bottles",
     "block1978;chalmers1994cfc"),
    ("Haimovici 2013 and Dewhurst 2016, on mechanistic and physical-level individuation", 2016, "philosophy-of-computation",
     "The dilemma Coelho Mollo 2018 sets out to dissolve, and the physical-level proposal he rejects; both reconstructed only from that paper",
     "mollo2018"),
    ("Piccinini 2008 and 2015, Computation without representation; Physical Computation", 2015, "philosophy-of-computation",
     "The book-length mechanistic account and the anti-semantic paper; the held 2010 and 2013 papers are its sketch and its application",
     "sprevak2010;mollo2018"),
    ("Oizumi, Albantakis & Tononi 2014, IIT 3.0", 2014, "consciousness-science",
     "The formal statement the unfolding argument actually attacks, and the source of the Phi-additivity rule its construction uses",
     "doerig2019;kleiner2021;butlin2023;albantakis2023"),
    ("Lamme 2006 and 2010, recurrent processing theory", 2010, "consciousness-science",
     "The second causal-structure theory the unfolding argument targets, and the source of Butlin et al.'s RPT indicators; represented here only second-hand",
     "doerig2019;butlin2023;chalmers2023llm"),
    ("Baars 1988 and Dehaene 2014, global workspace statements", 2014, "consciousness-science",
     "The theory statements that several reviewed works actually cite when they say 'global workspace'; the held Dehaene et al. 2017 is a later and narrower paper",
     "butlin2023;chalmers2023llm;shevlin2021;kleiner2021;aru2023"),
    ("Aaronson 2014 and Tononi 2014, the unconscious-expander exchange", 2014, "consciousness-science",
     "Supplies the Phi-increasing devices that make Doerig et al.'s construction concrete; the exchange itself is not held",
     "doerig2019"),
    ("Kleiner 2020; Tsuchiya, Andrillon & Haun 2019, replies to the unfolding argument", 2020, "consciousness-science",
     "The published defences of causal-structure theories. Their absence is why the testability debate reads as one-sided in this corpus",
     "kleiner2021"),
    ("Maturana & Varela 1980, Autopoiesis and Cognition", 1980, "biology-and-neuroscience",
     "The source of autopoiesis, the concept doing the heaviest lifting in Seth's positive case; known here only through Seth's summary",
     "seth2025"),
    ("Hinton 2022 and Ororbia & Friston 2023, mortal computation", 2023, "AI-and-ML",
     "The argument against substrate flexibility from inside computationalism, which Seth says he finds the most provocative; not held",
     "seth2025"),
    ("Barnett & Seth 2023; Rosas et al. 2024, causal and informational closure measures", 2024, "consciousness-science",
     "The only proposal in the corpus that could measure how far a system's dynamics can be abstracted from its substrate; the measures themselves are not held",
     "seth2025"),
    ("Cao 2022, generative entrenchment in evolved mental function", 2022, "philosophy-of-mind",
     "One of the three plausibility arguments against neural replacement (nitric oxide diffusion; homeostatic spiking); reconstructed only from Seth 2025",
     "seth2025"),
    ("Harnad 1990, The Symbol Grounding Problem", 1990, "philosophy-of-mind",
     "The problem the Vector Grounding Problem restates, and the bridge from the Chinese Room to the language-model debate",
     "mollo2023vector;milliere2024;chalmers2023llm"),
    ("Bender & Koller 2020, Climbing towards NLU (the Octopus Test)", 2020, "AI-and-ML",
     "The strongest case against grounding in text-trained systems; appears here only inside the papers that answer it",
     "mollo2023vector;milliere2024;chalmers2023llm"),
    ("Metzinger 2021, a moratorium on synthetic phenomenology", 2021, "ethics-and-policy",
     "The most restrictive policy proposal in the debate; assessed by Birch, Butlin et al. and Seth but never stated in its own words here",
     "birch2024;butlin2023;seth2025"),
    ("Birch 2024, The Edge of Sentience (the book)", 2024, "ethics-and-policy",
     "The corpus holds the published precis, not the book; claims about how the framework is argued cannot be checked from the precis alone",
     "birch2024;long2024welfare"),
    ("Millière & Buckner, A Philosophical Introduction to Language Models, Part II", 2024, "AI-and-ML",
     "The companion paper reserved for interpretability methods and for consciousness, which Part I defers by design",
     "milliere2024"),
    ("Chalmers 1996, The Conscious Mind", 1996, "philosophy-of-mind",
     "The book whose views the 2011 footnote to A Computational Foundation was added to square with; the footnote is why sufficiency there is nomological, not metaphysical",
     "chalmers1994cfc;seth2025"),
    ("Barnes 1991; Klein 2008, 2012, 2013, 2015; Bishop 2009a,b; Bartlett 2012", 2012, "philosophy-of-computation",
     "The entire reply literature on Olympia, mapped by Klein but not held. Bartlett 2012 is described as the existing survey, 'albeit in a Maudlin-sympathetic way'",
     "klein_maudlin"),
    ("Fekete & Edelman 2011, on whether inactive elements contribute to experience", 2011, "consciousness-science",
     "The named dissent from the premise that experience supervenes on what a brain actually does, aimed at integrated information theory; reported only via Klein",
     "klein_maudlin"),
    ("Sprevak 2007 and Pylyshyn 1984, on program portability and architecture", 2007, "philosophy-of-computation",
     "The source of the claim that what programs a machine can run depends on its architecture - the hinge of Klein's reformulation, and cited by Butlin et al. on levels",
     "klein_maudlin;butlin2023"),
    ("Michel & Lau 2021; Wiese 2024; Shiller 2024; Arvan & Maley 2022", 2024, "philosophy-of-mind",
     "Recent restrictions on substrate flexibility - Swiss cheese, weak computational functionalism, constraints on parts, analog computation - all named but not held",
     "butlin2023;seth2025;long2024welfare"),
]


def main():
    manifest_path = os.path.join(ROOT, "references_manifest.csv")
    with open(manifest_path, newline="", encoding="utf-8") as fh:
        manifest = {r["key"]: r for r in csv.DictReader(fh)}

    errs = []
    if set(manifest) != set(W):
        errs.append(
            f"key mismatch: manifest-only={sorted(set(manifest) - set(W))} "
            f"works-only={sorted(set(W) - set(manifest))}"
        )
    debate_ids = [d[0] for d in DEBATES]

    def era_of(y):
        if y == "":
            return "unknown"
        for eid, _, s, e, _ in ERAS:
            if s <= y <= e:
                return eid
        raise ValueError(y)

    def status(k):
        m = manifest[k]
        if k in PENDING:
            return "pending-review"
        if m["status"] == "named-only":
            return "named-only"
        return "reviewed-full" if m["tier"] == "full" else "reviewed-short"

    # positions.csv is authoritative for debate membership; works.debates is derived.
    pos_rows = []
    deb_keys = {d: set() for d in debate_ids}
    key_debates = {k: [] for k in W}
    seen_pos = set()
    for d, pid, lab, keys, summ in POSITIONS:
        if d not in deb_keys:
            errs.append(f"position {pid}: unknown debate {d}")
            continue
        if pid in seen_pos:
            errs.append(f"dup position {pid}")
        seen_pos.add(pid)
        for kk in [x for x in keys.split(";") if x]:
            if kk not in W:
                errs.append(f"position {pid}: unknown key {kk}")
                continue
            deb_keys[d].add(kk)
            if d not in key_debates[kk]:
                key_debates[kk].append(d)
        for txt in (lab, summ):
            if len(txt) > 160:
                errs.append(f"position {pid}: cell too long ({len(txt)})")
        pos_rows.append([d, pid, lab, keys, summ])

    rows = []
    for k in manifest:  # manifest order
        label, y, yp, comm, role, ev, stance = W[k]
        if comm not in COMMUNITIES:
            errs.append(f"{k}: community {comm}")
        if stance not in STANCES:
            errs.append(f"{k}: stance {stance}")
        if ev not in EVIDENCE_TYPES:
            errs.append(f"{k}: evidence_type {ev}")
        st = status(k)
        if st not in WORK_STATUSES:
            errs.append(f"{k}: status {st}")
        if st in ("named-only", "pending-review") and not role.startswith("Not reviewed"):
            errs.append(f"{k}: unreviewed role must start 'Not reviewed'")
        if st in ("named-only", "pending-review") and stance != "unknown":
            errs.append(f"{k}: unreviewed work must have stance unknown")
        if st.startswith("reviewed") and stance == "unknown":
            errs.append(f"{k}: reviewed work has stance unknown")
        if len(role) > 160:
            errs.append(f"{k}: role too long ({len(role)})")
        ordered = [d for d in debate_ids if d in key_debates[k]]
        rows.append([k, label, y, yp, comm, era_of(y), st, stance, role, ev, ";".join(ordered)])
    write(
        "works.csv",
        ["key", "short_label", "year", "year_print", "community", "era",
         "status", "stance", "role", "evidence_type", "debates"],
        rows,
    )
    write("eras.csv", ["era_id", "label", "start_year", "end_year", "summary"],
          [list(e) for e in ERAS])
    write("positions.csv", ["debate_id", "position_id", "position_label", "keys", "summary"],
          pos_rows)

    statuses = {"settled", "leaning", "open", "stalled", "untested"}
    # Per-debate stance tally over the works POSITIONED in that debate. This is not the
    # corpus-wide stance column: a work can hold a stance and no position in a given debate.
    deb_tally = {}
    for did in debate_ids:
        t = {"supports": 0, "restricts": 0, "rejects": 0, "neutral": 0, "unknown": 0}
        for k in deb_keys[did]:
            t[W[k][6]] += 1
        t["tally"] = len(deb_keys[did])
        deb_tally[did] = t
    drows = []
    for did, title, q, st, reason, direction, scope in DEBATES:
        reason = reason.format(**deb_tally[did])
        # Any count of the form "N supporting/restricting/rejecting/abstaining" stated in a
        # status_reason must match the tally computed above from positions.csv + works.csv.
        words = {"supporting": "supports", "restricting": "restricts",
                 "rejecting": "rejects", "abstaining": "neutral"}
        for m in re.finditer(r"(\d+)\s+(supporting|restricting|rejecting|abstaining)", reason):
            if int(m.group(1)) != deb_tally[did][words[m.group(2)]]:
                errs.append(f"debate {did}: status_reason says {m.group(0)}, tally says "
                            f"{deb_tally[did][words[m.group(2)]]}")
        ys = [W[k][1] for k in deb_keys[did] if W[k][1] != ""]
        if st not in statuses:
            errs.append(f"debate {did}: status {st}")
        if (st == "leaning") != bool(direction):
            errs.append(f"debate {did}: status_direction must be set iff leaning")
        for txt in (q, reason, scope, direction):
            if len(txt) > 200:
                errs.append(f"debate {did}: text too long ({len(txt)})")
        if not ys:
            errs.append(f"debate {did}: no dated works")
            ys = [0]
        drows.append([did, title, q, st, reason, direction, scope, min(ys), max(ys)])
    write(
        "debates.csv",
        ["debate_id", "title", "question", "status", "status_reason",
         "status_direction", "status_scope", "first_year", "latest_year"],
        drows,
    )

    seen = set()
    erows = []
    for f, t, r, ev in EDGES:
        if f not in W or t not in W:
            errs.append(f"edge unknown key {f}->{t}")
            continue
        if f in PENDING or manifest[f]["status"] != "pdf":
            errs.append(f"edge from unreviewed key {f}")
        if r not in RELATIONS:
            errs.append(f"edge relation {r}")
        if (f, t, r) in seen:
            errs.append(f"dup edge {f}->{t} {r}")
        if (W[f][1] != "" and W[t][1] != "" and W[t][1] > W[f][1]
                and (f, t) not in FORWARD_OK):
            errs.append(f"edge {f}({W[f][1]})->{t}({W[t][1]}) points forward in time")
        seen.add((f, t, r))
        cites = CITES.get((f, t), "yes")
        if cites not in {"yes", "sibling", "other", "unknown"}:
            errs.append(f"edge {f}->{t}: cites_held_document {cites}")
        if cites == "sibling" and "sibling" not in ev and "cites" not in ev:
            errs.append(f"edge {f}->{t}: marked sibling but evidence does not say which document")
        erows.append([f, t, r, cites, ev])
    for k in CITES:
        if k not in {(e[0], e[1]) for e in EDGES}:
            errs.append(f"CITES entry for non-existent edge {k}")
    write("edges.csv", ["from_key", "to_key", "relation", "cites_held_document", "evidence"], erows)

    directions = {"fine", "coarse", "derived", "no-bottom", "assumed", "unspecified", "meta"}
    grows = []
    seen_g = set()
    for k, level, locus, direction, note in GRAIN:
        if k not in W:
            errs.append(f"grain unknown key {k}")
            continue
        if k in PENDING or manifest[k]["status"] != "pdf":
            errs.append(f"grain row for unreviewed key {k}")
        if direction not in directions:
            errs.append(f"grain {k}: direction {direction}")
        if k in seen_g:
            errs.append(f"dup grain key {k}")
        seen_g.add(k)
        for c in (level, locus, note):
            if len(c) > 200:
                errs.append(f"grain {k}: cell too long ({len(c)})")
        grows.append([k, W[k][1], level, locus, direction, note])
    write("grain.csv", ["key", "year", "level_named", "locus", "direction", "note"], grows)

    verdicts = {"holds", "partly", "does-not-hold", "misattributed", "disputed"}
    crows = []
    for k, claim, finding, verdict in CORRECTIONS:
        if k not in W:
            errs.append(f"correction unknown key {k}")
            continue
        if k in PENDING or manifest[k]["status"] != "pdf":
            errs.append(f"correction for unreviewed key {k}")
        if verdict not in verdicts:
            errs.append(f"correction {k}: verdict {verdict}")
        for c in (claim, finding):
            if len(c) > 220:
                errs.append(f"correction {k}: cell too long ({len(c)})")
        crows.append([k, claim, finding, verdict])
    write("corrections.csv", ["key", "commonly_attributed_claim", "what_the_paper_says", "verdict"],
          crows)

    nrows = []
    for lab, y, comm, why, cited in NOT_HELD:
        if comm not in COMMUNITIES:
            errs.append(f"not_held {lab}: community {comm}")
        for kk in [c for c in cited.split(";") if c]:
            if kk not in W:
                errs.append(f"not_held {lab}: cited_by {kk} unknown")
            elif kk in PENDING or manifest[kk]["status"] != "pdf":
                errs.append(f"not_held {lab}: cited_by {kk} is not a reviewed key")
        if len(why) > 200:
            errs.append(f"not_held {lab}: why too long ({len(why)})")
        nrows.append([lab, y, comm, why, cited])
    write("not_held.csv", ["label", "year", "community", "why_relevant", "cited_by"], nrows)

    if errs:
        print("ERRORS:")
        print("\n".join(errs))
        sys.exit(1)
    print(
        "rows: works", len(rows),
        "eras", len(ERAS),
        "debates", len(drows),
        "positions", len(pos_rows),
        "edges", len(erows),
        "grain", len(grows),
        "corrections", len(crows),
        "not_held", len(nrows),
    )
    counts = {}
    for r in rows:
        counts[r[6]] = counts.get(r[6], 0) + 1
    print("work status:", counts)
    scount = {}
    for r in rows:
        scount[r[7]] = scount.get(r[7], 0) + 1
    print("stance:", scount)
    ecount = {}
    for r in rows:
        ecount[r[5]] = ecount.get(r[5], 0) + 1
    print("era:", ecount)
    ccount = {}
    for r in rows:
        ccount[r[4]] = ccount.get(r[4], 0) + 1
    print("community:", ccount)


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    main()
