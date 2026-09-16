# Imperativism Field History — Master Index

**Topic folder:** `docs/project/references/imperativism/`
**Curator:** literature-curator, 2026-09-17
**Counts computed from:** `references_manifest.csv`

## What this index is for (plain-language entry point)

This folder reviews research on the side of pain that is not plain sensation: why pain *feels bad* and why it *pushes* us to act. The work comes from philosophy, human brain imaging, animal circuit studies, clinical psychology, neurology and computational modelling, and runs from 1962 to 2026.

The per-paper reviews are split into thirteen parts, A to I. Each part covers one theme or period. Each paper gets a plain summary, a technical deep dive or short summary, and a section-by-section outline.

The **synthesis** ties the parts together. It sets out the eras of the field, eight debates with their current status, how the research communities relate, what the evidence does and does not show, and corrections to the survey that seeded the corpus. Start there if you want the field as a whole. Open a part if you want one paper.

## Start here

- **Synthesis:** [[imperativism_field_history_synthesis]]. A neutral history of the field, with eras, debates, evidence ledger and survey corrections.
- **Diagram data:** `field_history_data/`. Nine CSV files: works, eras, debates, positions, citation edges, dissociation evidence, dimension models, survey corrections, and known works not held. The generator `build_field_history_data.py` sits beside them.
- **Corpus list:** `references_manifest.csv`, with all 89 references. Source PDFs are in `sources/`.

## Counts

**Tier legend.**
- *Reviewed full*: reviewed from PDF with overview, deep dive and section-by-section outline.
- *Reviewed short*: reviewed from PDF as a structured summary.
- *Named-only*: listed in the manifest, no PDF held, not reviewed.

| | Reviewed full | Reviewed short | Named-only | Total |
|---|---|---|---|---|
| **All parts** | **46** | **19** | **24** | **89** |

## Parts

| Part | Theme | Papers (manifest keys) | Full / short / named-only | File |
|---|---|---|---|---|
| A | Imperative vs evaluative theories of pain and valence (philosophy) | klein2007, carruthers2018, bh2019, barlassina2020, carruthers2023 | 5 / 0 / 0 | [[imperativism_lit_review_A_imperative_theories]] |
| B1 | First imperative accounts and first evaluativist replies, 2008–2013 | martinez2011, cuttertye2011, bain2013, jacobson2013; named-only: hall2008, tumulty2009, klein2010 | 4 / 0 / 3 | [[imperativism_lit_review_B1_imperativism_evaluativism_origins]] |
| B2 | Imperativism and evaluativism mature, 2015–2019 | martinez2015, klein2015, mk2016, bain2017, bainreview2017, km2018, bain2019, loopy2019 | 6 / 2 / 0 | [[imperativism_lit_review_B2_imperativism_evaluativism_maturity]] |
| B3 | Where the valence debate stands, 2020s | kauppinen2021, mb2026, barlassina_reflection | 3 / 0 / 0 | [[imperativism_lit_review_B3_valence_debate_current]] |
| C | Pain asymbolia and lesion cases | klein2015asym, griffithkind2023, duvalklein2025; named-only: foltz1962, berthier1988, ploner1999 | 3 / 0 / 3 | [[imperativism_lit_review_C_asymbolia_and_lesions]] |
| D | How pain was split into dimensions | melzackwall1965, price2000, leknestracey2008, talbot2019; named-only: melzackcasey1968, fernandezturk1992, treede1999, auvray2010, raja2020 | 2 / 2 / 5 | [[imperativism_lit_review_D_dimensions_of_pain]] |
| E1 | Separating intensity from unpleasantness in the human brain, 1997–2014 | rainville1997, hofbauer2001, zubieta2001, kulkarni2005, tiemann2014; named-only: bentley2004 | 5 / 0 / 1 | [[imperativism_lit_review_E1_sensory_affective_neuroimaging]] |
| E2 | Recent human and animal dissociation studies, 2017–2024 | hayen2017, singh2020, stankewitz2023, zidda2024; named-only: nickel2017 | 4 / 0 / 1 | [[imperativism_lit_review_E2_sensory_affective_recent]] |
| F | Pain as need state, defensive system and driver of avoidance (fear-avoidance, homeostatic emotion) | claes2015 (full); vlaeyen2000, craig2003, leeuw2006, crombez2012, vlaeyen2016 (short); named-only: wall1979, bolles1980, eccleston1999, fields2006, vandamme2008, hasenbring2010, vlaeyen2012 | 1 / 5 / 7 | [[imperativism_lit_review_F_motivation_fear_avoidance]] |
| G1 | Unpleasantness and avoidance in animal circuits, 2001–2022 | johansen2001, johansen2004, corder2019, lee2022 | 4 / 0 / 0 | [[imperativism_lit_review_G1_avoidance_circuits]] |
| G2 | Pain as a learning and decision signal, 2013–2024 | seymour2019, gandhi2021, jepma2022 (full); wiech2013, wang2018, becker2018, le2024 (short) | 3 / 4 / 0 | [[imperativism_lit_review_G2_computational_avoidance]] |
| H | Measuring unpleasantness, avoidance and valence separately | lee2024, flury2025; named-only: vase2003, vase2005 | 2 / 0 / 2 | [[imperativism_lit_review_H_valence_avoidance_dissociation]] |
| I | Where pain meets action in cortex, 2011–2023 | perini2013, tolomeo2016, perini2020, koppel2022 (full); shackman2011, misra2014, budell2015, procyk2014, han2017, gordon2023 (short); named-only: vogt1992, budell2010 | 4 / 6 / 2 | [[imperativism_lit_review_I_pain_and_action_cortex]] |
| — | Cross-part synthesis | all of the above | — | [[imperativism_field_history_synthesis]] |

## Notes

- **Year labels.** Some key years differ from first publication. `gandhi2021` was published in 2022. `misra2014` and `procyk2014` are the 2015 and 2016 print papers, first online in 2014. Details are in synthesis §11.
- **Other material in this folder.** The `intro_page/` folder holds the introductory web page built from Part A. It is not part of this index's counts.
