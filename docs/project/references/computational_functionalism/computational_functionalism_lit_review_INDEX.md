# Computational Functionalism — Master Index

**Topic folder:** `docs/project/references/computational_functionalism/`
**Curator:** literature-curator, 2026-09-21
**Counts computed from:** `references_manifest.csv`

## What this index is for (plain-language entry point)

This folder reviews sixty years of argument about one idea: that what makes something a mind is the
**computation** it carries out rather than the stuff it is made of — so that a machine running the
right program would have a mind, and might feel things. Philosophers call it **computational
functionalism**. The work here comes from philosophy of mind, philosophy of computation,
consciousness science, neuroscience, AI research and ethics, and runs from 1967 to 2026.

The per-paper reviews are split into eight parts. Each part covers one theme. Each paper gets a
plain overview, a reconstruction of its argument, a section-by-section outline (or, at the short
tier, a structured summary), and a fixed machine-readable record block that the diagram data is
built from.

The **synthesis** ties the parts together: five eras, nine debates with their current status and
what this corpus cannot show about each, how the communities relate, what the arguments rest on,
and forty-one claims commonly attributed to these works checked against what they say. Start there
for the field as a whole; open a part for one paper.

## Start here

- **Web page:** [Running the Right Program](https://claude.ai/artifact/YFbbuZWRXHCfNEfrXdDp2b) — the
  diagram-heavy field review built from the synthesis and the data files; source, template and figure
  scripts in `page/` (`build_page.py`), which republishes to that same URL.
- **Synthesis:** [[computational_functionalism_field_history_synthesis]]. A neutral history. It
  adjudicates nothing and states each position at its strongest.
- **Diagram data:** `field_history_data/`. Eight CSV files: works, eras, debates, positions,
  engagement edges, the grain of functional equivalence, corrections, and known works not held. The
  generator `build_field_history_data.py` sits beside them and refuses to write on any mismatch with
  the manifest. **Do not hand-edit the CSVs.**
- **Corpus list:** `references_manifest.csv`, all 42 references. Source PDFs are in `sources/`.

## Counts

**Tier legend.**
- *Reviewed full*: read from the PDF, with overview, argument reconstruction and section-by-section outline.
- *Reviewed short*: read from the PDF as a structured summary.
- *Named-only*: in the manifest, no PDF held, not reviewed — carries no claim anywhere in this topic.

| | Reviewed full | Reviewed short | Named-only | Total |
|---|---|---|---|---|
| **All parts** | **22** | **14** | **6** | **42** |

## Parts

| Part | Theme | Papers (manifest keys) | Full / short / named-only | File |
|---|---|---|---|---|
| A1 | Classical functionalism and multiple realizability | blockfodor1972, fodor1974, block1978; named-only: putnam1967, bechtelmundale1999 | 2 / 1 / 2 | [[computational_functionalism_lit_review_A1_functionalism_origins]] |
| A2 | Computation and implementation: triviality, individuation, mechanism | chalmers1994cfc, chalmers1996rock, piccinini2010, piccinini2013, shagrir2006, sprevak2010, mollo2018 | 4 / 3 / 0 | [[computational_functionalism_lit_review_A2_computation_and_implementation]] |
| B | Substrate independence and its thought experiments | searle1980, chalmers1995qualia, cuda1985, bostrom2003; named-only: searle1990, schneider2019 | 3 / 1 / 2 | [[computational_functionalism_lit_review_B_substrate_independence]] |
| C | The biological challenge | seth2025, godfreysmith2016, aru2023, cleeremans2022, seth2018beast; named-only: thompson2007 | 4 / 1 / 1 | [[computational_functionalism_lit_review_C_biological_naturalism]] |
| D | Theories of consciousness as machine tests, and the testability crisis | butlin2023, dehaene2017, tononi2015, doerig2019, kleiner2021, albantakis2023, graziano2017 | 4 / 3 / 0 | [[computational_functionalism_lit_review_D_theories_and_tests]] |
| E | AI minds, moral status and precaution | chalmers2023llm, long2024welfare, schwitzgebel2015, birch2024, milliere2024, mollo2023vector, shevlin2021 | 3 / 4 / 0 | [[computational_functionalism_lit_review_E_ai_minds_and_ethics]] |
| F | Maudlin's Olympia argument and the field's one retrospective on it | maudlin1989, klein_maudlin | 1 / 1 / 0 | [[computational_functionalism_lit_review_F_olympia_and_replies]] |
| G | The deflationary strand: "Quining Qualia" | dennett1988; named-only: block1995 | 1 / 0 / 1 | [[computational_functionalism_lit_review_G_deflationary_strand]] |

## Three things to know before citing anything here

1. **Named-only means not read.** Six keys have no PDF. They are named as works other papers cite,
   never as the source of a claim. Two of the six matter structurally: the standard challenge to
   multiple realizability is one, which is why that premise looks unanimous in this corpus, and
   Block 1995 is another, which is why Block reads here as a 1970s figure.
2. **Several held files are not the version of record.** One is an author web text carrying a
   footnote added eighteen years later that narrows its central claim; one is the 2026 published
   version behind a key dated 2023; one is a published précis rather than the book; one is a draft
   chapter with no publication year, dated by its compile date. Section 5.5 of the synthesis lists
   every case and what each changes about a citation.
3. **Statuses describe this corpus.** "Open", "leaning" and "nobody argues X" are claims about 36
   reviewed works, never about the literature. Each debate carries its own corpus-limit note.
