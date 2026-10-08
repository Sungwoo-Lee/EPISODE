"""Build the AI-consciousness field-data CSV files from the reviewed corpus.

Canonical location: docs/project/references/ai_consciousness/field_data/.
Written 2026-10-07 by literature-curator.

What is read from the reviews (parsed, not transcribed):
  * Parts C1-C4: for each of the 50 BBS commentaries, the manifest key, title, PDF pages,
    the "Field" line, the "Which of Seth's claims it addresses" line and the
    "Verdict on Seth's thesis" line.
  * Part D, closing table: Seth's response section(s), engagement level and
    concede / partly / holds / holds (in agreement) treatment for all 50 commentaries.
  * references_manifest.csv: keys, batch, tier, authors.

What is hand-coded below (curator judgement, labelled as such in the CSVs):
  * community codes, theme clusters, stance codes for the 50 commentaries,
  * the questions, positions and cautions.
For the nine core works the stance codes follow each review's own field record.

Run:
  /home/vncuser/miniconda3/envs/grid_world_pain/bin/python build_field_data.py

The script exits non-zero on any key that is not in references_manifest.csv, on any
commentary missing from Parts C or D, on any duplicate, and if the treatment counts
disagree with the count line printed under Part D's table. Edit this file and rerun;
do not hand-edit the CSVs.
"""
import csv
import os
import re
import sys
from collections import Counter, OrderedDict

ROOT = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/docs/project/references/ai_consciousness"
OUT = os.path.join(ROOT, "field_data")
MANIFEST = os.path.join(ROOT, "references_manifest.csv")
C_PARTS = ["C1", "C2", "C3", "C4"]
D_FILE = os.path.join(ROOT, "ai_consciousness_lit_review_D_seth_response.md")

# Part D's own count line: "Count: 0 not addressed; 1 concede (Kleiner); 20 partly ...;
# 12 holds against; 17 holds in agreement. Total 50."
EXPECTED_TREATMENT = {"concede": 1, "partly": 20, "holds": 12, "holds-in-agreement": 17}

COMMUNITIES = {
    "philosophy-of-mind", "philosophy-of-computation", "consciousness-science",
    "AI-and-ML", "ethics-and-policy", "biology-and-neuroscience", "other",
}
STANCE_CF = {"supports", "restricts", "rejects", "neutral"}
STANCE_AI = {"likely", "possible", "unlikely-now", "very-unlikely", "no-verdict", "question-reframed"}
VERDICTS = ["supports", "extends", "qualifies", "rejects"]
# Seth's version-of-record sections (Part B, "Section numbering and page mapping").
VALID_SECTIONS = {"1", "2", "3", "4", "5", "6", "7", "1.0", "1.1", "2.0", "3.0", "4.0", "5.0",
                  "6.0", "7.0"} | {f"3.{i}" for i in range(1, 10)} | {f"4.{i}" for i in range(1, 6)} \
    | {f"5.{i}" for i in range(1, 9)} | {"6.1", "6.2"}


def die(msg):
    sys.stderr.write("ERROR: " + msg + "\n")
    sys.exit(1)


# --------------------------------------------------------------------------- manifest
with open(MANIFEST, newline="", encoding="utf-8") as fh:
    MAN = OrderedDict((r["key"], r) for r in csv.DictReader(fh))
if len(MAN) != 59:
    die(f"manifest has {len(MAN)} rows, expected 59")


def check_keys(keys, where):
    for k in keys:
        if k not in MAN:
            die(f"key '{k}' in {where} is not in references_manifest.csv")


def short_label(key):
    r = MAN[key]
    year = {"seth2025": "2025", "seth2026response": "2026"}.get(key)
    authors = [a.strip() for a in r["authors"].split(";") if a.strip() and a.strip() != "..."]
    if not authors:  # core works without an authors column
        return {"aru2023": "Aru, Larkum & Shine 2023", "butlin2025": "Butlin et al. 2025",
                "damasio2022": "Damasio & Damasio 2022", "bengio2025": "Bengio & Elmoznino 2025",
                "seth2025": "Seth 2025 (target article)"}[key]
    if year is None:
        year = re.search(r"(\d{4})", key).group(1)
    if key == "seth2026response":
        return "Seth 2026 (Author's Response)"
    if len(authors) == 1:
        return f"{authors[0]} {year}"
    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]} {year}"
    return f"{authors[0]} et al. {year}"


# --------------------------------------------------------------------------- Parts C
def norm_sections(text):
    found = set()
    t = text.replace("sect. ", "§").replace("section ", "§").replace("Section ", "§")
    # explicit range expansion: §3.1–§3.2 or §4.1–4.2
    for maj, lo, hi in re.findall(r"§\s*(\d)\.(\d)\s*[–-]\s*§?\s*\d\.(\d)", t):
        for i in range(int(lo), int(hi) + 1):
            found.add(f"{maj}.{i}")
    for s in re.findall(r"§\s*(\d(?:\.\d)?)", t):
        found.add(s)
    return sorted(found, key=lambda s: [int(x) for x in s.split(".")])


VERDICT_OVERRIDE = {
    "silberstein2026bbs": ("qualifies", "verdict line 'supports the conclusion, rejects the positive grounds': "
                           "coded qualifies under the stated rule (accepts conclusion, rejects grounds)"),
}
FRAMING_REJECTERS = {"shanahan2026bbs", "fields2026bbs", "gomezmarin2026bbs"}

COMM = OrderedDict()
for part in C_PARTS:
    path = os.path.join(ROOT, f"ai_consciousness_lit_review_{part}_seth_commentaries.md")
    text = open(path, encoding="utf-8").read()
    chunks = re.split(r"\n## (e3\d\d)\. ", text)
    for i in range(1, len(chunks), 2):
        enum, body = chunks[i], chunks[i + 1].split("\n## Cross-commentary")[0]
        head = body.split("\n")[0]
        m = re.search(r"\*\*Manifest key:\*\* `([^`]+)`\s*·\s*\*\*PDF pages:\*\*\s*([^·]+)·\s*\*\*Field:\*\*\s*(.*)", body)
        if not m:
            die(f"{part} {enum}: no manifest/pages/field line")
        key = m.group(1)
        check_keys([key], f"Part {part} {enum}")
        if key in COMM:
            die(f"duplicate commentary key {key}")

        def field(label):
            mm = re.search(r"^- \*\*" + re.escape(label) + r"[^*]*:\*\*\s*(.*)$", body, re.M)
            if not mm:
                die(f"{part} {enum} {key}: missing '{label}'")
            return mm.group(1).strip()

        verdict_text = field("Verdict on Seth's thesis")
        first = re.search(r"\b(supports|extends|qualifies|rejects)\b", verdict_text)
        if not first:
            die(f"{key}: verdict line has none of {VERDICTS}")
        verdict = first.group(1)
        verdict_note = ""
        # Stated rule: the verdict is the first of the four words in the reviewer's verdict line,
        # EXCEPT that a line which accepts Seth's conclusion but rejects his grounds is coded
        # 'qualifies' (as Godfrey-Smith and Nave already are). Any 'supports'/'extends' line that
        # also contains 'rejects' must be listed in VERDICT_OVERRIDE, or the build fails.
        if key in VERDICT_OVERRIDE:
            verdict, verdict_note = VERDICT_OVERRIDE[key]
        elif verdict in ("supports", "extends") and "rejects" in verdict_text:
            die(f"{key}: verdict line both supports and rejects; add it to VERDICT_OVERRIDE")
        rejects_what = ""
        if verdict == "rejects":
            rejects_what = "shared-framing" if "framing" in verdict_text else "seth-argument"
        title = re.sub(r"\s*\[commentary\]\s*$", "", head)
        title = re.sub(r"^.*?\(2026\)\s*—\s*", "", title)
        addressed = field("Which of Seth's claims it addresses")
        COMM[key] = {
            "e": enum, "part": part, "title": title, "pages": m.group(2).strip(),
            "field_text": m.group(3).strip(), "addressed": addressed,
            "sections": norm_sections(addressed),
            "verdict_text": verdict_text, "verdict": verdict, "verdict_note": verdict_note,
            "rejects_what": rejects_what,
        }

c_keys_manifest = [k for k, r in MAN.items() if r["batch"] == "C"]
if set(COMM) != set(c_keys_manifest) or len(COMM) != 50:
    die(f"Parts C hold {len(COMM)} commentaries; manifest batch C has {len(c_keys_manifest)}; "
        f"missing={sorted(set(c_keys_manifest) - set(COMM))} extra={sorted(set(COMM) - set(c_keys_manifest))}")

if {k for k, d in COMM.items() if d["rejects_what"] == "shared-framing"} != FRAMING_REJECTERS:
    die("the replies that reject the shared framing are not exactly " + str(sorted(FRAMING_REJECTERS)))

for k, d in COMM.items():
    bad = [s for s in d["sections"] if s not in VALID_SECTIONS]
    if bad:
        die(f"{k}: section(s) {bad} parsed from the review are not version-of-record sections")

# --------------------------------------------------------------------------- Part D
dtext = open(D_FILE, encoding="utf-8").read()
DTAB = {}
for line in dtext.split("\n"):
    m = re.match(r"\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|", line)
    if not m:
        continue
    key = m.group(2)
    check_keys([key], "Part D table")
    tr = m.group(6).strip()
    if tr.startswith("concede"):
        code = "concede"
    elif tr.startswith("partly"):
        code = "partly"
    elif tr.startswith("holds (in agreement"):
        code = "holds-in-agreement"
    elif tr.startswith("holds"):
        code = "holds"
    else:
        die(f"Part D: unknown treatment '{tr}' for {key}")
    DTAB[key] = {"seth_calls": m.group(3).strip(), "sections": m.group(4).strip(),
                 "engagement": m.group(5).strip(), "treatment": code, "treatment_text": tr}
if set(DTAB) != set(COMM):
    die(f"Part D table and Parts C disagree: {sorted(set(DTAB) ^ set(COMM))}")
tcount = Counter(v["treatment"] for v in DTAB.values())
if dict(tcount) != EXPECTED_TREATMENT:
    die(f"treatment counts {dict(tcount)} differ from Part D's count line {EXPECTED_TREATMENT}")

# --------------------------------------------------------------------------- hand coding
# Community codes. Commentaries: from the review's "Field" line. Core works: from the
# reviews' field records.
COMMUNITY = {
    "seth2025": "consciousness-science", "seth2026response": "consciousness-science",
    "aru2023": "biology-and-neuroscience", "damasio2022": "biology-and-neuroscience",
    "butlin2023": "consciousness-science", "butlin2025": "consciousness-science",
    "bayne2024": "consciousness-science", "bengio2025": "AI-and-ML", "sebolong2025": "ethics-and-policy",
    "allen2026bbs": "philosophy-of-mind", "larkum2026bbs": "biology-and-neuroscience",
    "baltieri2026bbs": "AI-and-ML", "bayne2026bbs": "philosophy-of-mind",
    "birch2026bbs": "philosophy-of-mind", "blackburne2026bbs": "consciousness-science",
    "block2026bbs": "philosophy-of-mind", "blum2026bbs": "AI-and-ML",
    "bowes2026bbs": "philosophy-of-mind", "cao2026bbs": "philosophy-of-mind",
    "chiang2026bbs": "other", "chrisley2026bbs": "consciousness-science",
    "clark2026bbs": "philosophy-of-mind", "dolega2026bbs": "philosophy-of-mind",
    "debrigard2026bbs": "philosophy-of-mind", "dung2026bbs": "philosophy-of-mind",
    "evers2026bbs": "ethics-and-policy", "feinberg2026bbs": "biology-and-neuroscience",
    "fields2026bbs": "biology-and-neuroscience", "fleming2026bbs": "consciousness-science",
    "friston2026bbs": "biology-and-neuroscience", "godfreysmith2026bbs": "philosophy-of-mind",
    "gomezmarin2026bbs": "biology-and-neuroscience", "hohwy2026bbs": "philosophy-of-mind",
    "jablonka2026bbs": "biology-and-neuroscience", "kleiner2026bbs": "consciousness-science",
    "lane2026bbs": "biology-and-neuroscience", "legg2026bbs": "AI-and-ML",
    "lerchner2026bbs": "AI-and-ML", "levin2026bbs": "biology-and-neuroscience",
    "mcgilchrist2026bbs": "philosophy-of-mind", "metzinger2026bbs": "philosophy-of-mind",
    "michel2026bbs": "philosophy-of-mind", "mitchell2026bbs": "biology-and-neuroscience",
    "nave2026bbs": "philosophy-of-mind", "overgaard2026bbs": "consciousness-science",
    "parr2026bbs": "biology-and-neuroscience", "piccinini2026bbs": "philosophy-of-computation",
    "ramstead2026bbs": "biology-and-neuroscience", "richards2026bbs": "AI-and-ML",
    "rodriguez2026bbs": "ethics-and-policy", "roelofs2026bbs": "philosophy-of-mind",
    "schlicht2026bbs": "philosophy-of-mind", "schneider2026bbs": "philosophy-of-mind",
    "schwitzgebel2026bbs": "philosophy-of-mind", "shanahan2026bbs": "AI-and-ML",
    "shevlin2026bbs": "philosophy-of-mind", "silberstein2026bbs": "philosophy-of-mind",
    "solms2026bbs": "biology-and-neuroscience", "wiese2026bbs": "philosophy-of-mind",
}

# Theme clusters for the 50 commentaries: one primary cluster each.
CLUSTERS = [
    ("cl1_computation_not_refuted", "Functionalism defended: the case against computation is not made",
     "Seth shows that brains and computers differ, not that the difference matters for consciousness; "
     "functionalism stays the better or the only bet.",
     ["michel2026bbs", "dung2026bbs", "overgaard2026bbs", "legg2026bbs", "blum2026bbs", "debrigard2026bbs"]),
    ("cl2_computation_broadened", "Computation is wider than Seth's Turing sense",
     "Embodied, mortal, multiscale or self-constructing kinds of computation could do the work Seth gives to life.",
     ["richards2026bbs", "bowes2026bbs", "chrisley2026bbs", "larkum2026bbs", "hohwy2026bbs"]),
    ("cl3_simulation_realisation", "Is a simulation the real thing?",
     "Whether running a model of a process produces the process itself, or only a description of it.",
     ["dolega2026bbs", "wiese2026bbs", "ramstead2026bbs"]),
    ("cl4_machine_life", "Could a machine be alive, and what does 'life' mean?",
     "Self-repairing robots, virtual self-organising agents and engineered cells test whether Seth's line "
     "between living and non-living can be drawn and defined.",
     ["schwitzgebel2026bbs", "solms2026bbs", "levin2026bbs", "kleiner2026bbs", "chiang2026bbs"]),
    ("cl5_prediction_doubts", "Prediction and free energy do not single out life",
     "Predictive processing and the free energy principle fit thermostats, sponges and steam engines too, "
     "so they cannot by themselves carry a life-based theory.",
     ["baltieri2026bbs", "birch2026bbs", "godfreysmith2026bbs", "allen2026bbs", "nave2026bbs", "silberstein2026bbs"]),
    ("cl6_biological_mechanisms", "Beyond computation: physical and biological candidates",
     "Candidate physical or biological properties: brain rhythms, membrane potentials, energy cost of "
     "inference, emergence, arousal systems, evolved affordances, intrinsic meaning. Not all of them need "
     "life (Piccinini).",
     ["block2026bbs", "lane2026bbs", "friston2026bbs", "parr2026bbs", "blackburne2026bbs", "feinberg2026bbs",
      "jablonka2026bbs", "piccinini2026bbs", "lerchner2026bbs"]),
    ("cl7_subject_value", "Subjects and value",
     "What is missing may be a subject with its own good or its own interests, which may or may not need biology.",
     ["cao2026bbs", "mitchell2026bbs"]),
    ("cl8_reframe", "Change the question or the worldview",
     "Illusionism, Wittgensteinian language use, non-Western ontologies, consciousness as fundamental, "
     "a collapse of biology into physics or eliminativism, or asking what a system could be aware of.",
     ["clark2026bbs", "shanahan2026bbs", "gomezmarin2026bbs", "mcgilchrist2026bbs", "fields2026bbs",
      "metzinger2026bbs"]),
    ("cl9_different_not_absent", "Different, not absent",
     "Even if biology matters for human consciousness, other materials might give other forms of "
     "consciousness rather than none.",
     ["roelofs2026bbs", "shevlin2026bbs"]),
    ("cl10_evidence_ethics", "Biases, tests, evidence and ethics",
     "How bias, testing and governance should work while the question stays open, and whether conscious "
     "AI is desirable at all.",
     ["bayne2026bbs", "schlicht2026bbs", "schneider2026bbs", "fleming2026bbs", "rodriguez2026bbs", "evers2026bbs"]),
]
CLUSTER_OF = {}
for cid, _, _, members in CLUSTERS:
    check_keys(members, f"cluster {cid}")
    for k in members:
        if k in CLUSTER_OF:
            die(f"{k} is in two clusters")
        CLUSTER_OF[k] = cid
if set(CLUSTER_OF) != set(COMM):
    die(f"clusters do not cover the 50 commentaries: {sorted(set(COMM) ^ set(CLUSTER_OF))}")

STANCE_NOTE = {
    "damasio2022": "computational functionalism: rejects, by implication only (the essay never mentions "
                   "computation or machines); AI: no view stated, though it says consciousness cannot be found "
                   "in inanimate objects",
    "butlin2025": "computational functionalism: 'neutral to supportive as a working focus' (field record)",
    "seth2025": "computational functionalism: restricts in the target article; see seth2026response",
    "seth2026response": "computational functionalism: rejects (Part D field record); firmer than the target article",
}

# Stance codes. Core works: the review's field record. Commentaries: curator coding from
# the review's verdict and argument lines.
CORE = OrderedDict([
    # key: (year, year_print, part, kind, stance_cf, stance_ai, one_line)
    ("butlin2023", (2023, 2023, "A1", "report (arXiv v3, not peer reviewed)", "supports", "possible",
                    "If computational functionalism holds, 14 indicators from leading theories give a rubric; no current "
                    "system is a strong candidate, no obvious technical barrier to building one that meets them.")),
    ("butlin2025", (2025, 2025, "A1", "opinion article (in press)", "neutral", "possible",
                    "Turns the indicators into a general Bayesian method; no verdicts on systems; warns that indicators "
                    "can be gamed; biological and IIT views to be weighed in the final credence.")),
    ("bayne2024", (2024, 2024, "A2", "review article", "neutral", "no-verdict",
                   "Describes tests by population, specificity, sensitivity and rational confidence; validate them step "
                   "by step outward from humans who can report; AI sits at the far end.")),
    ("bengio2025", (2025, 2025, "A2", "perspective", "supports", "possible",
                    "Belief in AI consciousness will spread whether or not it is true; acting on it (rights, "
                    "self-preservation) is dangerous; build AI that seems and functions like a tool.")),
    ("sebolong2025", (2023, 2025, "A2", "original research (ethics)", "neutral", "possible",
                      "A 1-in-1,000 chance of consciousness is enough for some moral consideration, and even a "
                      "deliberately sceptical model gives some AI that chance by 2030.")),
    ("aru2023", (2023, 2023, "A3", "opinion article", "restricts", "unlikely-now",
                 "Language models are very unlikely to be conscious: thin input, missing brain architecture, and "
                 "living organisation that software leaves out; software not ruled out in principle.")),
    ("damasio2022", (2022, 2022, "A3", "essay", "rejects", "no-verdict",
                     "Consciousness is felt ownership of mental contents, supplied by homeostatic feelings from a "
                     "nervous system physically intertwined with the body; never discusses machines.")),
    ("seth2025", (2025, 2026, "B", "target article", "restricts", "unlikely-now",
                  "Conscious AI needs computational functionalism and silicon substrate flexibility, both doubtful; "
                  "consciousness may depend on life, so conscious AI would need to be 'living' AI.")),
    ("seth2026response", (2026, 2026, "D", "author's response", "rejects", "very-unlikely",
                          "Restates the case after 50 commentaries: biological naturalism, not computational "
                          "functionalism, should be the default; conscious AI is 'vanishingly unlikely' for AI as we know it.")),
])
check_keys(CORE, "CORE")

COMM_STANCE = {
    # key: (stance_cf, stance_ai)
    "allen2026bbs": ("neutral", "no-verdict"), "larkum2026bbs": ("restricts", "unlikely-now"),
    "baltieri2026bbs": ("neutral", "no-verdict"), "bayne2026bbs": ("neutral", "no-verdict"),
    "birch2026bbs": ("neutral", "no-verdict"), "blackburne2026bbs": ("restricts", "no-verdict"),
    "block2026bbs": ("restricts", "unlikely-now"), "blum2026bbs": ("supports", "likely"),
    "bowes2026bbs": ("supports", "possible"), "cao2026bbs": ("restricts", "unlikely-now"),
    "chiang2026bbs": ("supports", "possible"), "chrisley2026bbs": ("neutral", "possible"),
    "clark2026bbs": ("restricts", "no-verdict"), "dolega2026bbs": ("neutral", "no-verdict"),
    "debrigard2026bbs": ("supports", "unlikely-now"), "dung2026bbs": ("supports", "possible"),
    "evers2026bbs": ("neutral", "no-verdict"), "feinberg2026bbs": ("rejects", "very-unlikely"),
    "fields2026bbs": ("neutral", "question-reframed"), "fleming2026bbs": ("neutral", "no-verdict"),
    "friston2026bbs": ("restricts", "unlikely-now"), "godfreysmith2026bbs": ("restricts", "no-verdict"),
    "gomezmarin2026bbs": ("neutral", "question-reframed"), "hohwy2026bbs": ("restricts", "possible"),
    "jablonka2026bbs": ("rejects", "unlikely-now"), "kleiner2026bbs": ("neutral", "no-verdict"),
    "lane2026bbs": ("rejects", "very-unlikely"), "legg2026bbs": ("supports", "possible"),
    "lerchner2026bbs": ("rejects", "very-unlikely"), "levin2026bbs": ("rejects", "possible"),
    "mcgilchrist2026bbs": ("neutral", "question-reframed"), "metzinger2026bbs": ("neutral", "possible"),
    "michel2026bbs": ("supports", "possible"), "mitchell2026bbs": ("neutral", "unlikely-now"),
    "nave2026bbs": ("rejects", "very-unlikely"), "overgaard2026bbs": ("neutral", "no-verdict"),
    "parr2026bbs": ("restricts", "unlikely-now"), "piccinini2026bbs": ("rejects", "no-verdict"),
    "ramstead2026bbs": ("neutral", "no-verdict"), "richards2026bbs": ("supports", "likely"),
    "rodriguez2026bbs": ("neutral", "no-verdict"), "roelofs2026bbs": ("neutral", "likely"),
    "schlicht2026bbs": ("neutral", "no-verdict"), "schneider2026bbs": ("neutral", "unlikely-now"),
    "schwitzgebel2026bbs": ("supports", "possible"), "shanahan2026bbs": ("neutral", "question-reframed"),
    "shevlin2026bbs": ("neutral", "possible"), "silberstein2026bbs": ("rejects", "unlikely-now"),
    "solms2026bbs": ("supports", "possible"), "wiese2026bbs": ("restricts", "unlikely-now"),
}
check_keys(COMM_STANCE, "COMM_STANCE")
if set(COMM_STANCE) != set(COMM):
    die("COMM_STANCE does not cover exactly the 50 commentaries")

# --------------------------------------------------------------------------- questions
QUESTIONS = [
    # id, title, plain question, status, why open
    ("q1_possible", "Could any AI be conscious at all?",
     "Is there anything about machines, as a kind of thing, that rules out experience — or could the right machine have it?",
     "open",
     "Every side rests on an assumption the others reject: that computation suffices, that life is required, or that "
     "physical causal structure decides; no experiment yet separates them."),
    ("q2_what_copied", "What exactly would have to be copied?",
     "If a machine were to be conscious, which features of a brain or body would it need: the computation, the fine "
     "physical detail, the energy flow, life itself, or a subject with its own good?",
     "open",
     "Candidate lists differ by author and none has been tested as necessary; several proposals are already being "
     "engineered, which turns the question into a moving target."),
    ("q3_how_tell", "How could anyone tell?",
     "What evidence could show that a machine is, or is not, conscious, when the machine was trained on human talk "
     "about experience?",
     "open",
     "Tests are validated on humans and do not transfer cleanly; behaviour can be imitated and internal indicators can "
     "be 'gamed'; any test presupposes a contested theory."),
    ("q4_llms", "Are today's systems candidates?",
     "Do current large language models, or other present AI systems, have a serious chance of being conscious?",
     "leaning",
     "Leans toward 'no current system is a strong candidate': every work that gives a verdict on present systems says so, "
     "except one commentary (Richards & Aguera y Arcas) that speculates some current AI may be partly conscious; the "
     "reasons for the 'no' differ sharply, and the future trajectory is wide open."),
    ("q5_ethics", "What follows for ethics and policy?",
     "While no one knows, what should companies, scientists and governments do — about AI that might be conscious and "
     "about AI that only seems to be?",
     "open",
     "The recommendations rest on different weightings of two errors (over- and under-attribution) and do not combine "
     "into one policy."),
    ("q6_body", "What role do the living body, interoception and feeling play?",
     "Does consciousness start from a living body regulating itself — feelings such as hunger and well-being — and if "
     "so, can anything non-living do the same?",
     "open",
     "Body-first accounts disagree with each other about mechanism (prediction versus physical mixing of nerve and "
     "body), and critics say the formal tools fit non-living systems too."),
    ("q7_fact", "Is there a fact to find?",
     "Is 'is this machine conscious?' a question with a hidden yes-or-no answer, or is it partly a question about how "
     "we choose to use words, or about what the system can respond to?",
     "open",
     "Most of the corpus assumes a factual answer; a minority argues the framing itself misleads, and the two sides "
     "rarely engage directly."),
]

POSITIONS = [
    # (question, position id, label, holders, summary)
    ("q1_possible", "q1_cf", "Yes in principle: the right computation is enough",
     ["butlin2023", "bengio2025", "blum2026bbs", "michel2026bbs", "richards2026bbs", "debrigard2026bbs", "legg2026bbs"],
     "Computational functionalism is the working default or the best bet; consciousness depends on what is computed, "
     "not on the material."),
    ("q1_possible", "q1_other_route", "Yes in principle, whether or not computation alone is enough",
     ["chrisley2026bbs", "dung2026bbs", "bowes2026bbs", "mitchell2026bbs", "shevlin2026bbs", "hohwy2026bbs",
      "silberstein2026bbs", "levin2026bbs"],
     "Rejecting biological naturalism does not require computational functionalism: embodiment, relations of a "
     "subject, self-organisation or adaptability could be built in non-living material. Holders differ on whether "
     "computation alone would be enough."),
    ("q1_possible", "q1_life_buildable", "Yes: even life's self-production can be built or computed",
     ["chiang2026bbs", "schwitzgebel2026bbs", "solms2026bbs"],
     "Accept that something life-like may be needed, then argue it can be met in software or robots: digital "
     "organisms, a self-repairing robot, virtual self-organising agents."),
    ("q1_possible", "q1_more_biology", "Possible in principle, but may need far more biological detail than any current AI",
     ["aru2023", "larkum2026bbs"],
     "Consciousness might be implementable, but only with a level of computational specificity (multiscale, dendritic, "
     "thalamocortical) beyond present and perhaps future AI."),
    ("q1_possible", "q1_hardware", "Depends on physical properties of the hardware, not on computation or life as such",
     ["block2026bbs", "friston2026bbs", "piccinini2026bbs", "metzinger2026bbs"],
     "Fields, electrochemical rhythms, in-memory processing or arousal-set global states may be needed; on some of these "
     "views (Friston, Piccinini, Metzinger) non-living hardware might have them. (Integrated information theory is the "
     "best-known view of this kind; no IIT author is in this collection.)"),
    ("q1_possible", "q1_life", "Only if the machine is, in a relevant sense, alive",
     ["seth2025", "seth2026response", "lane2026bbs", "nave2026bbs", "lerchner2026bbs", "jablonka2026bbs",
      "feinberg2026bbs", "cao2026bbs", "damasio2022"],
     "Consciousness depends on properties of living systems (metabolism, self-production, valuation, evolved "
     "affordances); conscious AI would need to be living AI. Damasio & Damasio hold the life requirement but never "
     "apply it to machines."),
    ("q1_possible", "q1_undecided", "Undecided: neither side has earned the default",
     ["allen2026bbs", "birch2026bbs", "kleiner2026bbs", "schlicht2026bbs", "rodriguez2026bbs", "overgaard2026bbs",
      "bayne2024"],
     "Both camps beg the question or lack decisive evidence; keep pluralism and look for tests."),
    ("q1_possible", "q1_abundant", "Consciousness is widespread in nature, so the question is what kind a machine has",
     ["roelofs2026bbs", "mcgilchrist2026bbs"],
     "Roelofs: a different material should be taken to give a different consciousness, not none. McGilchrist: "
     "a chip has minimal experience just by being matter, but any AI consciousness 'would always lack what we "
     "most highly value in our own'."),

    ("q2_what_copied", "q2_computation", "The computation: algorithm and representation format",
     ["butlin2023", "butlin2025", "blum2026bbs", "michel2026bbs"],
     "Copy the right functional architecture (workspace, recurrence, metacognition, attention model, agency) and you "
     "copy what matters."),
    ("q2_what_copied", "q2_multiscale", "Fine-grained, multiscale brain organisation",
     ["aru2023", "larkum2026bbs", "blackburne2026bbs", "silberstein2026bbs", "feinberg2026bbs", "piccinini2026bbs"],
     "Scale-free dynamics, dendritic coupling, emergence across levels or arousal-set global states — features that "
     "resist separation from the substrate."),
    ("q2_what_copied", "q2_time_energy", "Physical dynamics: time, energy and fields",
     ["friston2026bbs", "parr2026bbs", "block2026bbs", "hohwy2026bbs", "seth2026response"],
     "Inference that costs real energy ('mortal computation'), electrochemical rhythms, and continuous physical time; "
     "a program that only cares about step order lacks these."),
    ("q2_what_copied", "q2_life", "Life itself: metabolism and self-production",
     ["seth2025", "seth2026response", "lane2026bbs", "nave2026bbs", "lerchner2026bbs", "jablonka2026bbs"],
     "A system that continually rebuilds its own physical basis; computers are built and repaired from outside."),
    ("q2_what_copied", "q2_feeling_value", "Feeling and value: a body that matters to itself",
     ["damasio2022", "cao2026bbs", "aru2023"],
     "Homeostatic feelings from a nervous system intertwined with the body, or a 'valuing subject' with skin in the game."),
    ("q2_what_copied", "q2_subject", "A subject: relations to world, to itself and through time",
     ["mitchell2026bbs", "metzinger2026bbs"],
     "What must be copied is a subject defined by relations, or a self-model of one's own capacity to know; these may "
     "be buildable in other materials."),
    ("q2_what_copied", "q2_buildable", "Whatever it is, it can be built or simulated",
     ["chiang2026bbs", "schwitzgebel2026bbs", "solms2026bbs", "richards2026bbs", "dolega2026bbs"],
     "Life-like properties are functional: a self-repairing robot, a virtual organism or a self-constructing program "
     "would have them."),

    ("q3_how_tell", "q3_indicators", "Look inside: indicators derived from theories",
     ["butlin2023", "butlin2025", "bengio2025"],
     "Check a system's architecture for properties that leading theories link to consciousness; update credence in a "
     "Bayesian way."),
    ("q3_how_tell", "q3_iterative", "Validate tests step by step, outward from humans",
     ["bayne2024", "fleming2026bbs", "seth2026response"],
     "Treat consciousness as a natural kind; calibrate tests in reporting humans, then extend to nearer and then "
     "more distant populations."),
    ("q3_how_tell", "q3_not_behaviour", "Behaviour from systems trained on human text is not evidence",
     ["schneider2026bbs", "aru2023", "evers2026bbs", "seth2025", "butlin2025"],
     "Language models recycle human talk about experience ('error theory'); behavioural and even internal markers can "
     "be gamed. Behaviour is at most weak first-sight evidence."),
    ("q3_how_tell", "q3_self_report", "Accept self-reports by default, unless defeated",
     ["roelofs2026bbs"],
     "Under theoretical uncertainty, a system that says it is conscious should be believed unless its design history "
     "explains the report away."),
    ("q3_how_tell", "q3_attribute_only", "We can only attribute, not assess",
     ["schlicht2026bbs", "fields2026bbs", "friston2026bbs"],
     "Without a test for whether the material matters, we can only take a stance toward a system, or ask what it "
     "can respond to."),
    ("q3_how_tell", "q3_experiment", "Test the underlying assumption directly",
     ["rodriguez2026bbs", "birch2026bbs", "blackburne2026bbs", "solms2026bbs"],
     "Organoid and neuroprosthesis experiments, comparisons across species, emergence measures, or building agents "
     "against agreed criteria."),
    ("q3_how_tell", "q3_specificity_limit", "Even a detailed understanding may not settle it",
     ["butlin2025", "rodriguez2026bbs"],
     "Whether a system has an indicator can turn on where its boundary is drawn; finding indicators may increase, "
     "not reduce, expert disagreement."),

    ("q4_llms", "q4_no_strong_candidate", "No current system is a strong candidate; no fundamental barrier",
     ["butlin2023", "bengio2025"],
     "Current systems meet few indicators (transformers are weak on workspace indicators), but systems that meet them "
     "could be built."),
    ("q4_llms", "q4_neuro_no", "Very unlikely, for neuroscience reasons",
     ["aru2023", "larkum2026bbs"],
     "Thin text-only input, no thalamocortical or arousal architecture, no living self-maintenance."),
    ("q4_llms", "q4_bio_no", "Very unlikely, because they are not alive",
     ["seth2025", "seth2026response", "lane2026bbs", "nave2026bbs"],
     "Digital language models lack the biological properties consciousness may require; they 'beguile our biases by design'."),
    ("q4_llms", "q4_error_theory", "Their talk of experience is recycled human data",
     ["schneider2026bbs", "roelofs2026bbs", "mcgilchrist2026bbs"],
     "The reason to doubt them is training history, not material: they were built to imitate human talk."),
    ("q4_llms", "q4_boundary", "Unclear even in principle: depends on where the system's boundary is drawn",
     ["butlin2025"],
     "A transformer is feedforward, but generation feeds each token back; whether it is 'recurrent' is a judgement call."),
    ("q4_llms", "q4_maybe_yes", "Conscious AI is likely; some current AI may already be partly conscious",
     ["richards2026bbs", "blum2026bbs"],
     "Consciousness is functional and buildable in information (Richards & Aguera y Arcas, who speculate about current "
     "AI); on a formal model, conscious AI is 'inevitable' (Blum & Blum, about AI in general)."),
    ("q4_llms", "q4_chance_2030", "A non-negligible chance for some AI by 2030",
     ["sebolong2025"],
     "Even on sceptical inputs, at least about 1 in 1,000 that some AI system is conscious by 2030 (not a claim about "
     "today's systems)."),

    ("q5_ethics", "q5_consideration", "Extend some moral consideration under uncertainty",
     ["sebolong2025", "roelofs2026bbs"],
     "A non-negligible chance of consciousness triggers a duty of consideration; under-attribution may be the worse error."),
    ("q5_ethics", "q5_two_sided", "Weigh both errors explicitly",
     ["butlin2023", "butlin2025", "bayne2024"],
     "Missing consciousness risks harm at scale; wrongly attributing it wastes resources and distorts priorities."),
    ("q5_ethics", "q5_do_not_build", "Do not set out to build conscious AI",
     ["seth2025", "seth2026response", "evers2026bbs", "metzinger2026bbs"],
     "Real artificial consciousness risks new, possibly unrecognised suffering and unaligned interests; it should "
     "not be a goal."),
    ("q5_ethics", "q5_build_to_test", "Build it carefully, to understand it, with agreed stop criteria",
     ["solms2026bbs"],
     "Consciousness science needs falsifiable tests, best obtained by trying to build conscious agents in pure-science settings."),
    ("q5_ethics", "q5_tool_like", "Avoid conscious-seeming designs; resist AI rights and self-preservation",
     ["bengio2025", "seth2025", "seth2026response"],
     "Conscious-seeming AI is coming regardless of the truth; rights or survival goals for it would undermine human "
     "control and safety."),
    ("q5_ethics", "q5_govern_by_evidence", "Govern by evidence and respect all mainstream theories meanwhile",
     ["rodriguez2026bbs", "allen2026bbs"],
     "Turn the dispute into experiments; no camp should 'force hegemony' over policy early."),
    ("q5_ethics", "q5_hypothetical", "Worries about present systems are more hypothetical than real",
     ["aru2023"],
     "Language models have no stake in their continuation, so do not suffer in any sense that should matter to society."),
    ("q5_ethics", "q5_beyond_ai", "Look beyond AI: organoids and hybrids",
     ["metzinger2026bbs", "levin2026bbs", "rodriguez2026bbs", "schneider2026bbs", "seth2026response"],
     "Lab-grown neural tissue and bio-machine hybrids share biological material without triggering our biases, so "
     "false negatives become the main worry."),
    ("q5_ethics", "q5_gradual", "Digital moral status, if it comes, will come slowly",
     ["chiang2026bbs"],
     "Digital life would develop from reflexes upwards, giving time to avoid catastrophe."),

    ("q6_body", "q6_homeostatic_feeling", "Feeling starts in the living body's self-regulation",
     ["damasio2022"],
     "Homeostatic feelings (hunger, pain, well-being) are conscious by nature and arise from a two-way physical mixing "
     "of interoceptive nerves and the body."),
    ("q6_body", "q6_beast_machine", "Interoceptive prediction for staying alive grounds experience",
     ["seth2025", "seth2026response"],
     "The brain predicts and controls bodily states to stay alive; this ties perception and emotion to life "
     "('beast machine')."),
    ("q6_body", "q6_mortal_inference", "The physics of inference ties prediction to metabolism",
     ["friston2026bbs", "parr2026bbs", "wiese2026bbs", "hohwy2026bbs"],
     "In living systems, belief updating has a real thermodynamic cost; a simulation lacks the causal relations "
     "(with differences on whether this is substrate or function)."),
    ("q6_body", "q6_metabolism_not_fep", "Metabolism matters, but not via prediction or free energy",
     ["godfreysmith2026bbs", "nave2026bbs", "lane2026bbs", "silberstein2026bbs"],
     "Membrane potentials, metabolic closure or multiscale self-organisation do the work; 'surprise minimisation' "
     "does not fit how organisms behave."),
    ("q6_body", "q6_fep_too_general", "Prediction and free energy fit non-living systems too",
     ["baltieri2026bbs", "birch2026bbs", "michel2026bbs", "fields2026bbs", "allen2026bbs"],
     "Kalman filters, Watt governors, sponges and any 'thing' with a boundary satisfy the formalism; it cannot single "
     "out life or consciousness."),
    ("q6_body", "q6_valuing", "What matters is a subject with skin in the game",
     ["cao2026bbs", "aru2023", "mitchell2026bbs"],
     "A being for whom things go well or badly, whose existence depends on what it does."),
    ("q6_body", "q6_buildable_body", "Bodies and self-maintenance can be engineered or virtual",
     ["schwitzgebel2026bbs", "chiang2026bbs", "solms2026bbs", "bowes2026bbs", "legg2026bbs", "butlin2023"],
     "A robot that recharges and repairs itself, or a virtual body, meets the functional description; the 2023 "
     "indicator report defines embodiment so that a virtual avatar can count."),

    ("q7_fact", "q7_realism", "Yes: there is a fact of the matter",
     ["seth2025", "bayne2024", "roelofs2026bbs", "wiese2026bbs", "rodriguez2026bbs"],
     "Whether a system is conscious is a fact not settled by social or linguistic agreement."),
    ("q7_fact", "q7_illusionism", "The puzzle is an illusion to be explained",
     ["clark2026bbs"],
     "Experience has no extra intrinsic properties beyond what can be discriminated, reported and reacted to; "
     "what needs explaining is why it seems puzzling."),
    ("q7_fact", "q7_belief_forecast", "A prediction, not a view: the hard problem will lose its hold on more people",
     ["bengio2025"],
     "New explanations keep being proposed that 'will inevitably convince some'; whether any one convinces is "
     "'beside the point'. This forecasts belief; it does not endorse illusionism."),
    ("q7_fact", "q7_use", "It is partly a matter of how we use the words",
     ["shanahan2026bbs", "shevlin2026bbs"],
     "Ask how 'consciousness' is used; society will extend the word to AI by public criteria; 'deep realism' invites dualism."),
    ("q7_fact", "q7_aware_of", "Ask what a system could be aware of, not whether it is conscious",
     ["fields2026bbs"],
     "Computation is interpretation-relative; science can only find what a system responds to differentially."),
    ("q7_fact", "q7_beyond_naturalism", "Step outside the naturalist framing",
     ["gomezmarin2026bbs", "mcgilchrist2026bbs"],
     "Both computation and biology views share one Western ontology; animism or consciousness-as-fundamental changes "
     "the question."),
    ("q7_fact", "q7_attribution", "We can attribute but not assess",
     ["schlicht2026bbs"],
     "Without a test for medium dependence, AI consciousness is a matter of taking a stance."),
]
# Label-versus-coding checks: where a position label implies a stance, every holder's coded
# stance must fit it, or the build fails. ('cf' = stance_cf, 'ai' = stance_ai.)
POSITION_CONSTRAINTS = {
    "q1_cf": ("cf", {"supports"}),
    "q1_life_buildable": ("cf", {"supports", "neutral"}),
    "q1_more_biology": ("cf", {"restricts"}),
    "q1_hardware": ("cf", {"restricts", "rejects", "neutral"}),
    "q1_life": ("cf", {"restricts", "rejects"}),
    "q1_undecided": ("cf", {"neutral"}),
    "q2_computation": ("cf", {"supports", "neutral"}),
    "q2_multiscale": ("cf", {"restricts", "rejects"}),
    "q2_time_energy": ("cf", {"restricts", "rejects"}),
    "q2_life": ("cf", {"restricts", "rejects"}),
    "q2_buildable": ("cf", {"supports", "neutral"}),
    "q6_buildable_body": ("cf", {"supports"}),
    "q6_beast_machine": ("cf", {"restricts", "rejects"}),
    "q4_maybe_yes": ("ai", {"likely"}),
    "q4_bio_no": ("ai", {"unlikely-now", "very-unlikely"}),
    "q4_neuro_no": ("ai", {"unlikely-now", "very-unlikely"}),
    "q4_no_strong_candidate": ("ai", {"possible"}),
}

QIDS = {q[0] for q in QUESTIONS}
seen_pid = set()
for qid, pid, _, holders, _ in POSITIONS:
    if qid not in QIDS:
        die(f"position {pid} refers to unknown question {qid}")
    if pid in seen_pid:
        die(f"duplicate position id {pid}")
    seen_pid.add(pid)
    check_keys(holders, f"position {pid}")
    if len(set(holders)) != len(holders):
        die(f"position {pid} lists a holder twice")

def stance_of(key):
    if key in CORE:
        return {"cf": CORE[key][4], "ai": CORE[key][5]}
    return {"cf": COMM_STANCE[key][0], "ai": COMM_STANCE[key][1]}


for qid, pid, label, holders, _ in POSITIONS:
    if pid in POSITION_CONSTRAINTS:
        axis, allowed = POSITION_CONSTRAINTS[pid]
        for h in holders:
            if stance_of(h)[axis] not in allowed:
                die(f"position {pid} ('{label}') holder {h} has {axis} stance {stance_of(h)[axis]}, not in {allowed}")
for pid in POSITION_CONSTRAINTS:
    if pid not in seen_pid:
        die(f"constraint for unknown position {pid}")

# --------------------------------------------------------------------------- cautions
CAUTIONS = [
    # id, kind, keys, what one might say, what the text says, source, sibling topic needs correction
    ("v1", "version", ["seth2025"],
     "Seth calls biological naturalism a claim about sufficient conditions (§5.8).",
     "Version of record: 'false as an account of necessary conditions' (p. 13); the preprint said 'in terms of "
     "sufficient conditions' (preprint p. 27).",
     "Part B, Changes from the preprint", "yes: computational_functionalism Part C §5 (Self-assessment §5.8) quotes the preprint wording"),
    ("v2", "version", ["seth2025"],
     "In the neural-replacement argument Seth says it 'seems unlikely' that replacing one cell changes consciousness.",
     "Version of record: '– and this seems plausible –' (p. 4). The preprint aside 'seems unlikely' reversed the "
     "premise (preprint p. 8).",
     "Part B, Changes from the preprint", "yes: any citation of the preprint wording"),
    ("v3", "version", ["seth2025"],
     "Seth 2025 is a stand-alone paper; its Table 1 was reconstructed from the text.",
     "Cite the version of record as Seth (2026), BBS 49, e315, published with 50 commentaries and an Author's Response; "
     "Table 1 is now readable and lists IIT among scenario-4 examples with a caveat, while §5.6 says IIT does not fall "
     "on that continuum.",
     "Part B, Table 1; How to cite", "yes: computational_functionalism synthesis §5.5 (seth2025 row)"),
    ("v4", "version", ["aru2023"],
     "Aru et al. carry three explicit disclaimers: not only mammalian brains, not only living systems, not impossible in software.",
     "Published version: the 'not only living systems' sentence is not found; the software disclaimer is weakened to "
     "'not necessarily subscribing to the claim that consciousness cannot be captured within software at all' (p. 8). "
     "The mammalian-brain hedge remains (p. 5).",
     "Part A3, Published version versus the preprint",
     "yes: computational_functionalism synthesis §3.5 and §6 (aru2023 row) and Part C §4 rely on the preprint disclaimers"),
    ("v5", "version", ["aru2023"],
     "Aru et al. say conversation is no evidence of conscious agency.",
     "Published: conversations 'constitute only prima facie evidence for conscious agency' (p. 3); the preprint said "
     "they 'do not constitute' it.",
     "Part A3, Published version versus the preprint", "yes, where the preprint wording is quoted"),
    ("v6", "version", ["aru2023"],
     "On IIT, Aru et al. say software lacks real cause-effect power.",
     "Published: 'modern computers do not have the appropriate architecture to realise the cause-effect power' (p. 6) "
     "— the obstacle is moved to typical hardware.",
     "Part A3, Published version versus the preprint", "yes, where the preprint wording is quoted"),
    ("v7", "version", ["sebolong2025"],
     "Sebo & Long (2025) responds to later work such as Bayne et al. 2024 or Long et al. 2024.",
     "Published online 11 December 2023; the 2025 date is the journal issue. It predates Bayne et al. (2024), Long et "
     "al. (2024) and Bengio & Elmoznino (2025).",
     "Part A2, cross-paper note 6", "no"),
    ("v8", "version", ["butlin2023"],
     "Butlin et al. 2023 conclude there are no obvious barriers to building conscious AI systems.",
     "The amended abstract says no obvious barriers to building AI systems 'which satisfy these indicators'; a footnote "
     "records the change and its reason (p. 1).",
     "Part A1, Phase 1", "no (sibling records it)"),
    ("v9", "version", ["butlin2025"],
     "Butlin et al. 2025 is cited with volume and pages.",
     "The held file is an online article-in-press (header 'TICS 2797'); volume and pages were not yet assigned.",
     "Part A1, entry 2", "no"),
    ("m1", "misreading", ["bengio2025", "butlin2023"],
     "Bengio & Elmoznino misread Butlin et al. as treating indicators as necessary and sufficient.",
     "Their gloss is conditional — 'individually necessary and jointly sufficient … if that theory is true' — and is "
     "accurate as a statement about what each theory claims (Butlin et al. 2023 p. 46: 'GWT claims that these are "
     "necessary and jointly sufficient'). Butlin et al. themselves do not endorse the stronger claim (2023 p. 45; 2025 "
     "p. 3). Record as a conditional gloss, not a misreading.",
     "Coordinator settlement; Parts A1 and A2", "no"),
    ("m2", "misreading", ["bengio2025"],
     "Bengio & Elmoznino argue that AI only seems conscious and is not.",
     "The body never says belief in AI consciousness would be false; it calls AI consciousness 'plausible' and argues "
     "the risks hold 'whether or not' it is the correct approach. The 'illusion' on the literal reading is the hard "
     "problem itself.",
     "Part A2, reviewer's note on the title", "no"),
    ("m3", "misreading", ["damasio2022"],
     "Damasio & Damasio argue that AI cannot be conscious.",
     "The essay never mentions computers, machines or AI. It says consciousness 'cannot be found in inanimate "
     "objects, regardless of how complex they may be' (p. 4), without applying this to AI.",
     "Part A3, field record", "no"),
    ("m4", "misreading", ["seth2025"],
     "Seth claims to have refuted computational functionalism, or holds carbon chauvinism, vitalism or biopsychism.",
     "The target article says its arguments 'do not disprove computational functionalism' (p. 6) and disavows "
     "biopsychism, carbon chauvinism and neo-vitalism (§4.5, §5.8). The response is firmer: biological naturalism "
     "should be 'the default position' (p. 105).",
     "Part B claims T33, T62; Part D R7", "partly: the sibling records Seth as 'restricts'; the 2026 response is coded 'rejects'"),
    ("m5", "misreading", ["seth2025", "seth2026response", "chrisley2026bbs", "dung2026bbs"],
     "Seth holds that conscious AI strictly requires computational functionalism.",
     "Seth concedes the sentence was 'strictly incorrect' (R2.2, p. 94) and keeps the practical conclusion: 'without "
     "CF being true, there are no good reasons to believe it is plausible'.",
     "Part D, R2.2", "no"),
    ("m6", "misreading", ["sebolong2025"],
     "Sebo & Long estimate a 0.1% chance of AI consciousness by 2030.",
     "0.1% is a deliberately sceptical floor; the authors' own view is that the chance is far above it and the "
     "threshold far below. Their model includes only necessary conditions, and the numbers are illustrative.",
     "Part A2, entry 3", "no"),
    ("m7", "misreading", ["sebolong2025"],
     "Sebo & Long call for rights for AI systems.",
     "Their conclusion is about whether to treat AI as having moral standing and 'has no straightforward implications "
     "for how humans should treat AI systems' (p. 2).",
     "Part A2, entry 3", "no"),
    ("m8", "misreading", ["bayne2024", "bengio2025"],
     "Bayne et al.'s 'deflationary views' are the explaining-away accounts in Bengio & Elmoznino.",
     "Bayne et al. use 'deflationary' for views on which consciousness can be understood a priori, and reject them; "
     "the accounts Bengio & Elmoznino describe are empirical theories. Do not merge the two uses.",
     "Part A2, cross-paper note 2", "no"),
    ("m9", "misreading", ["sebolong2025"],
     "Sebo & Long (2023/2025) and Long et al. (2024) are the same argument.",
     "Same two authors and two-premise shape, but different routes to standing, different probability claims and "
     "different practical outputs (table in Part A2).",
     "Part A2, cross-reference to the sibling topic", "no"),
    ("s1", "section-artefact", ["chrisley2026bbs", "blum2026bbs", "wiese2026bbs"],
     "Commentators citing §3.9, §4.0, §4.5 or §5.0 worked from a different draft.",
     "These are real sections of the version of record (Summary and opening headings). The reviewers' brief listed "
     "sections incompletely; every commentary file carries a correction note.",
     "Coordinator correction in Parts C1-C4", "no"),
    ("a1", "shared-authorship", ["butlin2023", "butlin2025", "bengio2025", "sebolong2025", "bayne2024", "bayne2026bbs",
                                 "fleming2026bbs", "seth2025"],
     "The indicator report, the illusions paper and the moral-consideration paper independently agree that no current "
     "system is a strong candidate but nothing blocks one.",
     "Bengio, Elmoznino and Long are co-authors of Butlin et al. 2023; Bayne joined the 2025 article; Seth is second "
     "author of Bayne et al. 2024; Bayne and Fleming also wrote commentaries. Agreement is partly one research "
     "network's view repeated.",
     "Part A2, cross-paper note 4; Part A1, cross-paper notes", "no"),
    ("a2", "shared-authorship", ["aru2023", "larkum2026bbs", "damasio2022"],
     "Aru et al. 2023 and Larkum et al.'s commentary are two independent neuroscience voices; Aru et al. and the "
     "Damasios independently ground biology.",
     "Larkum et al. is the same author team as Aru et al. plus Whyte; Aru et al. cite the Damasios for their published "
     "Argument 1 lesson and Man & Damasio 2019 for 'skin in the game'.",
     "Part A3, cross-paper note 1; Part C1, e317", "no"),
    ("d1", "source-limit", ["seth2026response"],
     "Part D's table shows what each commentary argued.",
     "The table records Seth's account of each commentary; the commentaries were not re-read for Part D. Several are "
     "only named in lists ('name only' or 'brief').",
     "Part D, extraction notes", "no"),
    ("d2", "source-limit", ["seth2026response"],
     "Nobody disputed that conscious-seeming AI is coming.",
     "'There was no pushback on this point in the commentary set' (p. 104) is Seth's own statement about the set.",
     "Part D, R6.3", "no"),
    ("d3", "declared-interest", ["seth2025", "seth2026response", "solms2026bbs", "butlin2025", "sebolong2025",
                                 "richards2026bbs", "shanahan2026bbs", "legg2026bbs", "lerchner2026bbs",
                                 "rodriguez2026bbs", "bengio2025", "bayne2024", "friston2026bbs", "baltieri2026bbs"],
     "Positions here are free of commercial ties.",
     "Declared interests and affiliations, both sides: Seth advises Conscium Ltd and AllJoined Inc. (target article) "
     "and sits on the Conscium advisory board (response note 25); Solms sits on the Conscium and PRISM boards and is "
     "funded in part by Conscium. Butlin et al. 2025: Butlin consulted for Anthropic and Conscium, Long for Anthropic, "
     "J.B. received Google research funding, A.C. consulted for Verses AI, D.C. gives paid talks to technology "
     "companies, R.K. (Kanai) founded Araya, Inc. Sebo & Long funded by the Centre for Effective Altruism. Richards and "
     "Agüera y Arcas are Google employees; Shanahan is part-time at Google and an Alphabet shareholder; Legg and "
     "Lerchner work at Google DeepMind; Friston lists VERSES as an affiliation; Baltieri & Kanai write from Araya; "
     "Farahany sits on the OpenBCI board; Bengio leads LawZero; Massimini (Bayne et al. 2024) co-founded Intrinsic "
     "Powers. Butlin et al. 2023 declared no conflicts. Recorded for completeness, not as an argument.",
     "Parts A1, A2, B, C2, C3, C4, D", "no"),
]
for cid, kind, keys, *_ in CAUTIONS:
    check_keys(keys, f"caution {cid}")

# --------------------------------------------------------------------------- write
os.makedirs(OUT, exist_ok=True)


def write(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")
    return len(rows)


write("questions.csv", ["question_id", "order", "title", "plain_question", "status", "why_open",
                        "n_positions", "n_distinct_holders"],
      [[q[0], i + 1, q[1], q[2], q[3], q[4],
        sum(1 for p in POSITIONS if p[0] == q[0]),
        len({h for p in POSITIONS if p[0] == q[0] for h in p[3]})] for i, q in enumerate(QUESTIONS)])

write("positions.csv", ["question_id", "position_id", "label", "holders", "n_holders", "summary"],
      [[p[0], p[1], p[2], ";".join(p[3]), len(p[3]), p[4]] for p in POSITIONS])

CL_LABEL = {c[0]: c[1] for c in CLUSTERS}
write("clusters.csv", ["cluster_id", "label", "summary", "members", "n_members",
                       "n_supports", "n_extends", "n_qualifies", "n_rejects", "n_rejects_shared_framing",
                       "n_concede", "n_partly", "n_holds", "n_holds_in_agreement"],
      [[cid, lab, summ, ";".join(m), len(m)]
       + [sum(1 for k in m if COMM[k]["verdict"] == v) for v in VERDICTS]
       + [sum(1 for k in m if COMM[k]["rejects_what"] == "shared-framing")]
       + [sum(1 for k in m if DTAB[k]["treatment"] == t) for t in ["concede", "partly", "holds", "holds-in-agreement"]]
       for cid, lab, summ, m in CLUSTERS])

comm_rows = []
for k, d in sorted(COMM.items(), key=lambda kv: kv[1]["e"]):
    comm_rows.append([
        k, d["e"], MAN[k]["authors"], short_label(k), d["title"], d["pages"], d["part"],
        d["field_text"], COMMUNITY[k], ";".join(d["sections"]), d["addressed"],
        d["verdict"], d["verdict_note"], d["rejects_what"], d["verdict_text"], CLUSTER_OF[k], CL_LABEL[CLUSTER_OF[k]],
        DTAB[k]["seth_calls"], DTAB[k]["sections"], DTAB[k]["engagement"],
        DTAB[k]["treatment"], DTAB[k]["treatment_text"],
    ])
write("commentaries.csv",
      ["key", "bbs_number", "authors", "short_label", "title", "pdf_pages", "review_part", "field",
       "community", "seth_sections_addressed", "addressed_text", "verdict", "verdict_note", "rejects_what",
       "verdict_text",
       "theme_cluster", "theme_label", "seth_calls_it", "response_sections", "response_engagement",
       "response_treatment", "response_treatment_text"], comm_rows)

works_rows = []
for k, r in MAN.items():
    if k in CORE:
        year, yprint, part, kind, scf, sai, line = CORE[k]
        basis = f"reviewer field record (Part {part})"
        cluster = verdict = treat = ""
    else:
        d = COMM[k]
        year, yprint, part, kind = 2026, 2026, d["part"], "open peer commentary"
        scf, sai = COMM_STANCE[k]
        basis = "curator coding from the review's verdict and argument"
        line = d["verdict_text"]
        cluster, verdict, treat = CLUSTER_OF[k], d["verdict"], DTAB[k]["treatment"]
    if COMMUNITY[k] not in COMMUNITIES or scf not in STANCE_CF or sai not in STANCE_AI:
        die(f"{k}: bad code {COMMUNITY[k]} / {scf} / {sai}")
    works_rows.append([k, short_label(k), year, yprint, r["batch"], r["tier"], part, COMMUNITY[k], kind,
                       scf, sai, basis, STANCE_NOTE.get(k, ""), cluster, verdict, treat, line])
if len(works_rows) != 59 or len({w[0] for w in works_rows}) != 59:
    die("works.csv must have one row per manifest key (59)")
write("works.csv", ["key", "short_label", "year", "year_print", "batch", "tier", "review_part", "community",
                    "kind", "stance_cf", "stance_ai", "stance_basis", "stance_note", "theme_cluster", "verdict",
                    "response_treatment", "one_line"], works_rows)

write("cautions.csv", ["caution_id", "kind", "keys", "what_one_might_say", "what_the_text_says", "source",
                       "sibling_topic_correction"],
      [[c[0], c[1], ";".join(c[2]), c[3], c[4], c[5], c[6]] for c in CAUTIONS])

# --------------------------------------------------------------------------- summaries
print("\nverdict counts:", dict(Counter(d["verdict"] for d in COMM.values())))
print("rejects split:", dict(Counter(d["rejects_what"] for d in COMM.values() if d["rejects_what"])))
print("treatment counts:", dict(tcount))
print("\nverdict x treatment:")
for v in VERDICTS:
    print(f"  {v:10s}", {t: sum(1 for k in COMM if COMM[k]["verdict"] == v and DTAB[k]["treatment"] == t)
                          for t in ["concede", "partly", "holds", "holds-in-agreement"]})
print("\nengagement:", dict(Counter(v["engagement"] for v in DTAB.values())))
print("communities (all 59):", dict(Counter(COMMUNITY[k] for k in MAN)))
print("stance_cf (all 59):", dict(Counter(w[9] for w in works_rows)))
print("stance_ai (all 59):", dict(Counter(w[10] for w in works_rows)))
sec = Counter(s for d in COMM.values() for s in d["sections"])
print("most-addressed sections:", sec.most_common(12))
