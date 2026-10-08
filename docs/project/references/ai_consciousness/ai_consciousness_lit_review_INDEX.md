# AI Consciousness — Master Index

**Topic folder:** `docs/project/references/ai_consciousness/`
**Curator:** literature-curator, 2026-10-07
**Counts computed from:** `references_manifest.csv` (59 rows)

## What this index is for (plain-language entry point)

This folder reviews the current debate about one question: **could an AI system be conscious** — could there be something it feels like to be it — and if nobody can be sure, what should we do? The works come from consciousness science, neuroscience, philosophy, AI research and ethics, and date from 2022 to 2026.

The collection has two parts. **Seven core papers** set out the main approaches: a checklist of features to look for inside AI systems, a method for trusting tests of consciousness, a warning about what happens when people *believe* AI is conscious, an argument for moral caution under uncertainty, and two neuroscience papers on why living bodies may matter. **One full published debate** makes up the rest: the neuroscientist Anil Seth argues in *Behavioral and Brain Sciences* that consciousness may need a living body, fifty researchers reply, and Seth answers them.

Each work has its own review in one of nine part files. The **synthesis** ties them together by question — could any AI be conscious, what would have to be copied, how could anyone tell, are today's systems candidates, what follows for ethics — and states each side at its strongest without choosing a winner. Start there for the field as a whole; open a part for one paper.

## Start here

- **Web page:** [Could a Machine Be Conscious?](https://claude.ai/artifact/K7ySKSdvM9LhtPNwrkzyAc) — the field review built from the synthesis; source in `page/` (`build_page.py`), which republishes to the same URL.

- **Synthesis:** [[ai_consciousness_synthesis]]. A neutral map of the questions, the positions and the arguments, with the Seth debate as a worked example, common misreadings, and declared interests on all sides. Sections 1–6, 8 and 9 are written for the public page; §7 (corrections the sibling topic needs), §10 (data files) and §11 (provenance) are marked internal. Revised 2026-10-07 after a domain review; the review and the revision log are appended to the synthesis.
- **Diagram data:** `field_data/`. Six CSV files — questions, positions, commentaries, works, theme clusters, cautions — written by `field_data/build_field_data.py`, which reads the commentary fields and Seth's response table straight from the reviews and stops with an error on any key not in the manifest. **Do not hand-edit the CSVs.**
- **Corpus list:** `references_manifest.csv`, 59 rows. Source PDFs are in `sources/`.
- **Sibling topic (history and background):** [[computational_functionalism_lit_review_INDEX]] and [[computational_functionalism_field_history_synthesis]] — sixty years of argument about whether running the right computation is enough for a mind.

## Counts

**Tier legend.**
- *Reviewed full*: read from the PDF, with a plain overview, the argument step by step, and a section-by-section outline.
- *Reviewed short*: read from the PDF as a structured entry (sections addressed, verdict, argument, what it adds, quotes).
- *Named-only*: in the manifest, no PDF held, not reviewed. This topic has none.

| | Reviewed full | Reviewed short | Named-only | Total |
|---|---|---|---|---|
| Core papers (batch A) | 7 | 0 | 0 | 7 |
| Seth target article (batch B) | 1 | 0 | 0 | 1 |
| BBS commentaries (batch C) | 0 | 50 | 0 | 50 |
| Seth Author's Response (batch D) | 1 | 0 | 0 | 1 |
| **All parts** | **9** | **50** | **0** | **59** |

## Parts

| Part | Theme | Papers (manifest keys) | Full / short / named-only | File |
|---|---|---|---|---|
| A1 | Indicator properties: looking inside AI for features theories link to consciousness | butlin2023, butlin2025 | 2 / 0 / 0 | [[ai_consciousness_lit_review_A1_indicators]] |
| A2 | Tests, beliefs and moral status | bayne2024, bengio2025, sebolong2025 | 3 / 0 / 0 | [[ai_consciousness_lit_review_A2_tests_illusions_moral_status]] |
| A3 | Biology and feeling | aru2023, damasio2022 | 2 / 0 / 0 | [[ai_consciousness_lit_review_A3_biology_and_feeling]] |
| B | Seth's target article (version of record), with a numbered list of 90 claims (T1–T90) and the changes from the preprint | seth2025 | 1 / 0 / 0 | [[ai_consciousness_lit_review_B_seth_target_article]] |
| C1 | BBS commentaries e316–e327 | allen2026bbs, larkum2026bbs, baltieri2026bbs, bayne2026bbs, birch2026bbs, blackburne2026bbs, block2026bbs, blum2026bbs, bowes2026bbs, cao2026bbs, chiang2026bbs, chrisley2026bbs | 0 / 12 / 0 | [[ai_consciousness_lit_review_C1_seth_commentaries]] |
| C2 | BBS commentaries e328–e340 | clark2026bbs, dolega2026bbs, debrigard2026bbs, dung2026bbs, evers2026bbs, feinberg2026bbs, fields2026bbs, fleming2026bbs, friston2026bbs, godfreysmith2026bbs, gomezmarin2026bbs, hohwy2026bbs, jablonka2026bbs | 0 / 13 / 0 | [[ai_consciousness_lit_review_C2_seth_commentaries]] |
| C3 | BBS commentaries e341–e353 | kleiner2026bbs, lane2026bbs, legg2026bbs, lerchner2026bbs, levin2026bbs, mcgilchrist2026bbs, metzinger2026bbs, michel2026bbs, mitchell2026bbs, nave2026bbs, overgaard2026bbs, parr2026bbs, piccinini2026bbs | 0 / 13 / 0 | [[ai_consciousness_lit_review_C3_seth_commentaries]] |
| C4 | BBS commentaries e354–e365 | ramstead2026bbs, richards2026bbs, rodriguez2026bbs, roelofs2026bbs, schlicht2026bbs, schneider2026bbs, schwitzgebel2026bbs, shanahan2026bbs, shevlin2026bbs, silberstein2026bbs, solms2026bbs, wiese2026bbs | 0 / 12 / 0 | [[ai_consciousness_lit_review_C4_seth_commentaries]] |
| D | Seth's Author's Response, with a table mapping all 50 commentaries to response sections and concede / partly / holds | seth2026response | 1 / 0 / 0 | [[ai_consciousness_lit_review_D_seth_response]] |
| — | **Synthesis** across all parts | all 59 | — | [[ai_consciousness_synthesis]] |

## Things to know before citing anything here

1. **Cite Seth's version of record, not the preprint.** Cite it as Seth (2026), *Behavioral and Brain Sciences* 49, e315 (manuscript online 2025; the manifest key is `seth2025`). The sibling topic reviewed the preprint. Two sentences changed meaning: §5.8 now calls biological naturalism a claim about **necessary** conditions (the preprint said "sufficient"), and in §3.3 the neural-replacement aside now reads "this seems **plausible**" (the preprint said "unlikely"). Page numbers differ throughout; Part B has a conversion table.
2. **Cite Aru et al.'s published version.** The published *Trends in Neurosciences* text drops the preprint's "not only living systems" disclaimer and weakens its software disclaimer to "not necessarily subscribing". The sibling topic's statement that the paper carries "three explicit disclaimers" relies on the preprint.
3. **Sebo & Long is a 2023 paper with a 2025 issue date.** It went online on 11 December 2023. Citing it as 2025 reverses its order relative to Bayne et al. (2024), Long et al. (2024) and Bengio & Elmoznino (2025).
4. **Butlin et al. come in two versions with different claims.** The 2023 arXiv report (v3) gives verdicts on named systems and assumes computational functionalism; its abstract was softened after v1. The 2025 article drops the verdicts, calls many of its authors "agnostic", and is an article-in-press with no volume or pages yet.
5. **Section numbers §3.9, §4.0, §4.5 and §5.0 are real.** They are the Summary and opening headings of Seth's article. The reviewers' brief listed sections incompletely; a commentator who cites them was *not* reading a different draft.
6. **Part D reports Seth's account of the commentaries.** Its concede / partly / holds table records how Seth answered each reply; the replies were not re-read for Part D. The verdicts (supports / extends / qualifies / rejects) in Parts C1–C4 are the readings of four different reviewers, not calibrated against each other. The synthesis codes them by a stated rule (5 supports, 9 extends, 21 qualifies, 15 rejects, of which 3 reject the framing both sides share rather than Seth's argument).
7. **Agreement is often not independent.** Bengio, Elmoznino and Long co-wrote the 2023 indicator report; Seth is second author of Bayne et al. 2024; Bayne and Fleming also wrote replies to Seth; Larkum et al.'s reply is the Aru et al. team. The synthesis (§5.3) lists these.
8. **Bengio & Elmoznino's description of the indicators is a conditional, not a misreading.** "Individually necessary and jointly sufficient … if that theory is true" is accurate about what each theory claims; Butlin et al. themselves do not endorse the stronger claim.
9. **Statuses and counts describe this collection.** 52 of the 59 works belong to one debate. "Open", "leaning" and "15 rejecting replies" are claims about these works, not about the field.
10. **Project vocabulary.** This project's agents receive a damage signal called *nociception*, never "pain". Nothing in this topic is a finding about those agents.
