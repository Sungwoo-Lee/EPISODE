"""Build the imperativism field-history data files from the reviewed corpus.

Canonical location: docs/project/references/imperativism/field_history_data/.
Revised 2026-09-17 after professor-pain-modeling and plan-reviewer gates.

Every value below was transcribed from the per-batch reviews in
docs/project/references/imperativism/ (Parts A-I). Section references use
Part letter + entry number (e.g. "D §2" = Price 2000 in Part D).
Run: /home/vncuser/miniconda3/envs/grid_world_pain/bin/python build_field_history_data.py
"""
import csv
import os
import sys

ROOT = "/media/nas01/projects/Interoceptive-AI/grid_world_pain/docs/project/references/imperativism"
OUT = os.path.join(ROOT, "field_history_data")

COMMUNITIES = {"philosophy", "human-neuroscience", "animal-circuits", "clinical-psychology",
               "computational", "neurology-neurosurgery", "unknown"}
ERAS = [
    ("e1_gate", "Clinical dissociations and the gate", 1962, 1989,
     "Pain stops being a fixed line from receptor to brain; surgery and lesion cases show pain can persist without bothering the patient."),
    ("e2_dimensions", "Mapping the dimensions", 1990, 2006,
     "Imaging, opioid PET and rodent place-avoidance assays look for separate homes for intensity and unpleasantness; fear-avoidance model consolidates."),
    ("e3_badness", "Pain's badness and pull on behaviour become explicit problems", 2007, 2013,
     "Imperativism and evaluativism are founded; neuroscience recasts pain as a motivator; fear-avoidance turns to goals; cingulate linked to action."),
    ("e4_elaboration", "Elaboration, formal models and the turn to valence", 2014, 2019,
     "Books and formal models; the painkiller question; debate widens to all feelings; RL framing of pain; circuit silencing; a critical systematic review."),
    ("e5_valence", "Revised IASP definition, all-affect valence and graded dissociations", 2020, 2026,
     "Metasemantic dispute over learning and decision science; asymbolia reframed as taxonomy; graded human dissociations; conflicting avoidance-learning results."),
]

DEBATES = [
    # id, title, question, status, status_reason, status_direction, status_scope
    ("dimensions", "How many components, and can they be moved separately?",
     "Is pain one experience or separable parts (how strong vs how bad), and can one part be changed without the other?",
     "open",
     "Same asymmetry read as seriality (price2000) or near-unitary (talbot2019); 2023-24 studies call it graded; no E1-E2 primary study moves intensity alone.",
     "",
     "Talbot's review covered cognitive manipulations only; drug and lesion evidence enters through a few small separate studies."),
    ("valence-nature", "What is the non-sensory component: evaluation, command, or something else?",
     "What makes pain (and other feelings) bad: a perception of badness, a command, a desire, or something else?",
     "open",
     "Latest exchange (mb2026 reply to carruthers2023) has no counter-reply in the corpus; imperativists also split among themselves (kauppinen2021 vs bh2019).",
     "",
     "Seed survey favoured imperativism: imperativist authors wrote 14 reviewed works, evaluativists 7; several evaluativist replies are not held."),
    ("relief-seeking", "Why take painkillers? The direction of pain's motivation",
     "Does unpleasantness itself push us to get rid of the feeling, or only to protect the body, with relief-seeking coming from elsewhere?",
     "open",
     "Four rival accounts persist (martinez2015, bain2019, loopy2019, kauppinen2021) and carruthers2023 presses a hedonism charge; no side concedes in the corpus.",
     "",
     "Replies directly on this question (Cutter & Tye 2014, Jacobson 2019) are not held."),
    ("asymbolia", "Is asymbolic pain pain, and what does it show?",
     "When patients say a pinprick hurts but do not mind it, are they in pain, and does this show pain has separable parts?",
     "stalled",
     "No clinical evidence newer than 1999 enters the record; the active 2023-25 exchange moves only by reinterpretation of old case reports.",
     "",
     "Case reports are known only second-hand; Grahek 2007 and Bain 2014, central to the exchange, are not held."),
    ("unpleasantness-vs-avoidance", "Is felt unpleasantness separable from avoidance and motivation?",
     "Is how bad pain feels the same thing as the push to avoid or escape it, or can the two be measured and moved apart?",
     "open",
     "Behaviour moved without ratings (claes2015, flury2025) but across phases or probe trials; no reviewed study rates own unpleasantness and avoidance per trial.",
     "",
     "Placebo and desire-for-relief work that rated desire beside pain is largely outside the corpus (vase2003, vase2005 named-only)."),
    ("cingulate-action", "Where does pain meet action in cortex?",
     "Is cingulate activity during pain about feeling bad, about general control, or about preparing an action?",
     "open",
     "Integration (shackman2011) and action-dependence (perini2013, koppel2022) readings coexist unadjudicated; the one lesion study did not measure pain.",
     "",
     "The action-dependence line is mostly one lab's studies; counter-evidence such as Kragel 2018 is cited but not held."),
    ("learning-signal", "Is pain's felt badness the learning signal, and how is learning from pain structured?",
     "Nociceptive input supports aversive learning; is pain's felt badness itself that teaching signal, and do people learn more from pain received or avoided?",
     "open",
     "Identity claims (seymour2019; johansen2004 one-circuit) are untested against felt badness; learning asymmetry conflicts (jepma2022 vs le2024).",
     "",
     "The reviewed computational papers were selected for this framing; that nociceptive input drives aversive learning is treated as uncontested background."),
    ("avoidance-drivers", "What drives pain-related avoidance and disability?",
     "Do people avoid painful activity because of fear, because of pain itself, or because avoiding pain wins out over other goals?",
     "leaning",
     "The originators' 2016 model keeps the fear loop and adds a goal-priority fork (crombez2012, vlaeyen2016); causal tests remain few (leeuw2006, claes2015).",
     "toward fear plus goal competition",
     "Only the fear-avoidance originators' programme is reviewed; rival clinical models (e.g. endurance responses, hasenbring2010) are named-only."),
]

# key: (short_label, year, year_print, community, era, role, debates)
# status is derived from the manifest (pdf+tier -> reviewed-full/short; named-only).
W = {
 # ---------- Part A ----------
 "klein2007": ("Klein 2007", 2007, 2007, "philosophy", "Founds imperativism: pain's content is a negative command against using a body part; intensity is command strength", "valence-nature"),
 "carruthers2018": ("Carruthers 2018", 2017, 2018, "philosophy", "Evaluativism for all affect: valence is a nonconceptual representation of value; argued against the hedonic account", "valence-nature;relief-seeking;asymbolia"),
 "bh2019": ("Barlassina & Hayward 2019", 2019, 2019, "philosophy", "Reflexive imperativism: unpleasant experience commands 'less of me!'; rejects first-order and higher-order imperativism", "valence-nature;relief-seeking;asymbolia;learning-signal"),
 "barlassina2020": ("Barlassina 2020", 2020, 2020, "philosophy", "Reflexive imperativism judged better than Carruthers's evaluativism on phenomenology and imagination-based choice", "valence-nature;relief-seeking"),
 "carruthers2023": ("Carruthers 2023", 2023, 2023, "philosophy", "Valence represents adaptive value; commands idle in learning, choice, brain location and attention", "valence-nature;relief-seeking;learning-signal;unpleasantness-vs-avoidance"),
 # ---------- Part B1 ----------
 "hall2008": ("Hall 2008", 2008, 2008, "philosophy", "Not reviewed. Cited by martinez2011, cuttertye2011, bain2013 as source of imperative itch/hunger content", "valence-nature"),
 "martinez2011": ("Martínez 2011", 2010, 2011, "philosophy", "Unpleasantness is imperative content 'don't have this bodily disturbance'; rejects evaluative reading and action commands", "valence-nature"),
 "cuttertye2011": ("Cutter & Tye 2011", 2011, 2011, "philosophy", "Pain represents damage as bad for the subject to a degree; imperatives fail on intensity and polarity", "valence-nature;unpleasantness-vs-avoidance"),
 "bain2013": ("Bain 2013", 2012, 2013, "philosophy", "Names evaluativism; commands cannot give reasons or explain painkillers; asymbolia lacks the evaluative layer", "valence-nature;relief-seeking;asymbolia"),
 "jacobson2013": ("Jacobson 2013", 2013, 2013, "philosophy", "'Killing the messenger': rational painkiller use shows painfulness is not a representation of bodily badness", "valence-nature;relief-seeking"),
 "tumulty2009": ("Tumulty 2009", 2009, 2009, "philosophy", "Not reviewed. Manifest lists it as a critique of Klein 2007; no reviewed paper summarises it", "valence-nature"),
 "klein2010": ("Klein 2010", 2010, 2010, "philosophy", "Not reviewed. Response to Tumulty 2009; listed among works Klein 2015 consolidates", "valence-nature"),
 # ---------- Part B2 ----------
 "martinez2015": ("Martínez 2015", 2014, 2015, "philosophy", "Pains as 'benevolent-dictator' commands; relief-seeking is extrinsic avoidance of 'spammy' requests", "valence-nature;relief-seeking"),
 "klein2015": ("Klein 2015 (book)", 2015, 2015, "philosophy", "Book: pains are pure commands to protect a body part; unpleasantness handled separately (12-page preview only)", "valence-nature;asymbolia"),
 "mk2016": ("Martínez & Klein 2016", 2016, 2016, "philosophy", "Signalling-game model: pain messages carry more information about protective acts than world states", "valence-nature"),
 "bain2017": ("Bain 2017 (chapter)", 2017, 2017, "philosophy", "Handbook evaluativism: unpleasant pain represents the bodily condition as bad and is itself motivating", "valence-nature;relief-seeking;asymbolia"),
 "bainreview2017": ("Bain 2017 (review)", 2017, 2017, "philosophy", "Review of Klein 2015: an account of pain per se; objections on neutral-pain motivation, authority, asymbolia", "valence-nature;asymbolia"),
 "km2018": ("Klein & Martínez 2018", 2018, 2018, "philosophy", "Command intensity as a ranking over possible worlds (written c. 2014); answers the intensity objection", "valence-nature"),
 "bain2019": ("Bain 2019", 2017, 2019, "philosophy", "Unpleasantness is non-instrumentally bad; relief-seeking comes from separate desires (self-elimination denied)", "valence-nature;relief-seeking"),
 "loopy2019": ("Barlassina & Hayward 2019 (Loopy)", 2019, 2020, "philosophy", "World-directed theories fail (moods, experts, rat liking/wanting); relief-seeking intrinsic to reflexive commands", "valence-nature;relief-seeking;unpleasantness-vs-avoidance"),
 # ---------- Part B3 ----------
 "kauppinen2021": ("Kauppinen 2021", 2021, 2021, "philosophy", "Relational imperativism: indicative content plus background concern plus command; denies reflexive motivation", "valence-nature;relief-seeking;asymbolia"),
 "barlassina_reflection": ("Barlassina c. 2020 (essay)", 2020, "", "philosophy", "Short essay for reflexive imperativism citing rat salt liking/wanting dissociation; function of valence unexplained", "valence-nature;relief-seeking;unpleasantness-vs-avoidance"),
 "mb2026": ("Martínez & Barlassina 2026", 2026, 2026, "philosophy", "Reply to Carruthers 2023: valence informs more about behaviour than world, so imperative (accepted 2023)", "valence-nature;learning-signal"),
 # ---------- Part C ----------
 "foltz1962": ("Foltz & White 1962", 1962, 1962, "neurology-neurosurgery", "Not reviewed. Cingulumotomy reports cited as background by rainville1997, kulkarni2005, johansen2001", "cingulate-action;dimensions"),
 "berthier1988": ("Berthier et al. 1988", 1988, 1988, "neurology-neurosurgery", "Not reviewed. Asymbolia case series (insular lesions) known via price2000 and the Part C papers", "asymbolia;dimensions"),
 "ploner1999": ("Ploner et al. 1999", 1999, 1999, "neurology-neurosurgery", "Not reviewed. One patient reporting unpleasantness without pain sensation, as quoted by bh2019, klein2015asym, carruthers2023", "asymbolia;dimensions;valence-nature"),
 "klein2015asym": ("Klein 2015 (asymbolia)", 2015, 2015, "philosophy", "Asymbolics lost a general capacity to care about bodily integrity; pain's command persists but is not binding", "asymbolia;unpleasantness-vs-avoidance"),
 "griffithkind2023": ("Griffith & Kind 2023", 2023, 2024, "philosophy", "Clinical record does not show asymbolia is pain; standard reading incoherent under essentialism; a symptom", "asymbolia"),
 "duvalklein2025": ("Duval & Klein 2025", 2025, 2026, "philosophy", "Reply: objections weak if pain is a cluster kind; the real open question is how to classify asymbolia", "asymbolia"),
 # ---------- Part D ----------
 "melzackwall1965": ("Melzack & Wall 1965", 1965, 1965, "human-neuroscience", "Gate control: pain is modulated, not a fixed line; names sensory and affective components, no dimensional model", "dimensions;avoidance-drivers"),
 "melzackcasey1968": ("Melzack & Casey 1968", 1968, 1968, "human-neuroscience", "Not reviewed. Cited across Parts D, E, G, H as origin of the sensory / motivational-affective / evaluative split", "dimensions;unpleasantness-vs-avoidance"),
 "fernandezturk1992": ("Fernandez & Turk 1992", 1992, 1992, "clinical-psychology", "Not reviewed. Framework that talbot2019 followed for testing whether the two components separate", "dimensions"),
 "treede1999": ("Treede et al. 1999", 1999, 1999, "human-neuroscience", "Not reviewed. Cited by talbot2019 and johansen2001 for lateral (sensory) vs medial (affective) pathways", "dimensions"),
 "price2000": ("Price 2000", 2000, 2000, "human-neuroscience", "Serial model intensity -> unpleasantness -> secondary affect, converging on ACC; motivation given no dimension", "dimensions;unpleasantness-vs-avoidance;cingulate-action;asymbolia"),
 "leknestracey2008": ("Leknes & Tracey 2008", 2008, 2008, "human-neuroscience", "Pain and pleasure share opioid/dopamine currency; hedonic and motivational aspects named but hard to separate", "unpleasantness-vs-avoidance;dimensions"),
 "auvray2010": ("Auvray et al. 2010", 2010, 2010, "unknown", "Not reviewed. Cited by flury2025 for the claim that sensory and affective components can dissociate", "dimensions"),
 "talbot2019": ("Talbot et al. 2019", 2019, 2019, "clinical-psychology", "Systematic review: intensity not selectively modifiable; unpleasantness possibly, slightly; leans unitary", "dimensions;unpleasantness-vs-avoidance"),
 "raja2020": ("Raja et al. 2020", 2020, 2020, "unknown", "Not reviewed. Revised IASP pain definition; zidda2024 reads it as implying separable dimensions", "dimensions"),
 # ---------- Part E1 ----------
 "rainville1997": ("Rainville et al. 1997", 1997, 1997, "human-neuroscience", "Hypnotic suggestion moved unpleasantness, not significantly intensity; ACC followed, S1 did not (N=8)", "dimensions;cingulate-action"),
 "hofbauer2001": ("Hofbauer et al. 2001", 2001, 2001, "human-neuroscience", "Intensity suggestions moved S1 not ACC, but unpleasantness moved too (r=0.81); rejects a simple dichotomy", "dimensions;cingulate-action"),
 "zubieta2001": ("Zubieta et al. 2001", 2001, 2001, "human-neuroscience", "Regional opioid release correlated with sensory vs affective questionnaire scores across people", "dimensions"),
 "bentley2004": ("Bentley et al. 2004", 2004, 2004, "human-neuroscience", "Not reviewed. Laser-evoked potential attention study, described only by kulkarni2005", "dimensions"),
 "kulkarni2005": ("Kulkarni et al. 2005", 2005, 2005, "human-neuroscience", "Attending to location vs unpleasantness engaged lateral vs medial regions; attention, not percept, manipulated", "dimensions;cingulate-action"),
 "tiemann2014": ("Tiemann et al. 2014", 2014, 2014, "human-neuroscience", "Dopamine-precursor depletion raised unpleasantness (one rating, p=.048), not intensity or EEG responses", "dimensions"),
 # ---------- Part E2 ----------
 "nickel2017": ("Nickel et al. 2017", 2017, 2017, "human-neuroscience", "Not reviewed. Oscillations paper; a different 'Nickel 2017' from the one stankewitz2023 cites", "dimensions"),
 "hayen2017": ("Hayen et al. 2017", 2017, 2017, "human-neuroscience", "Opioid lowered unpleasantness but not significantly intensity of breathlessness (not a pain study)", "dimensions"),
 "singh2020": ("Singh et al. 2020", 2020, 2020, "animal-circuits", "Rat S1->ACC input amplifies noxious ACC responses and regulates place aversion; no sensory test under manipulation", "dimensions;unpleasantness-vs-avoidance;cingulate-action"),
 "stankewitz2023": ("Stankewitz et al. 2023", 2023, 2023, "human-neuroscience", "7T fMRI: single-trial signals track unpleasantness slightly more than intensity; graded, not distinct", "dimensions"),
 "zidda2024": ("Zidda et al. 2024", 2024, 2024, "human-neuroscience", "Emotional picture primes shifted unpleasantness, not intensity main effect; P2 change predicted it", "dimensions"),
 # ---------- Part F ----------
 "wall1979": ("Wall 1979", 1979, 1979, "unknown", "Not reviewed. Cited by vlaeyen2000 and leeuw2006 for short-term avoidance being adaptive", "avoidance-drivers"),
 "bolles1980": ("Bolles & Fanselow 1980", 1980, 1980, "unknown", "Not reviewed. Perceptual-defensive-recuperative model; no reviewed paper cites it (Part F notes)", "avoidance-drivers"),
 "eccleston1999": ("Eccleston & Crombez 1999", 1999, 1999, "clinical-psychology", "Not reviewed. Cited for 'pain demands attention' and intense pain as itself threatening", "avoidance-drivers"),
 "vlaeyen2000": ("Vlaeyen & Linton 2000", 2000, 2000, "clinical-psychology", "Fear-avoidance state of the art: catastrophizing -> fear -> avoidance -> disability; evidence mostly correlational", "avoidance-drivers"),
 "craig2003": ("Craig 2003", 2003, 2003, "animal-circuits", "Pain as homeostatic emotion: sensation in insula, motivational drive in ACC; primate-specific claim", "dimensions;avoidance-drivers;cingulate-action"),
 "fields2006": ("Fields 2006", 2006, 2006, "unknown", "Not reviewed. Motivation-decision model as described by leknestracey2008 and seymour2019", "avoidance-drivers;learning-signal"),
 "leeuw2006": ("Leeuw et al. 2006", 2006, 2007, "clinical-psychology", "Evidence audit: fear links supported, disuse weak, intensity matters more, causal claims untested", "avoidance-drivers"),
 "vandamme2008": ("Van Damme et al. 2008", 2008, 2008, "clinical-psychology", "Not reviewed. Motivational coping perspective cited by crombez2012, claes2015, becker2018", "avoidance-drivers"),
 "hasenbring2010": ("Hasenbring & Verbunt 2010", 2010, 2010, "clinical-psychology", "Not reviewed. Fear-avoidance and endurance responses; cited by crombez2012", "avoidance-drivers"),
 "vlaeyen2012": ("Vlaeyen & Linton 2012", 2012, 2012, "clinical-psychology", "Not reviewed. '12 years on' update to which vlaeyen2016 is anchored", "avoidance-drivers"),
 "crombez2012": ("Crombez et al. 2012", 2012, 2012, "clinical-psychology", "'Next generation': fear-avoidance recast as goal competition and futile problem-solving; intensity underplayed", "avoidance-drivers"),
 "claes2015": ("Claes et al. 2015", 2015, 2015, "clinical-psychology", "Reward raised choice of a painful movement while fear, intensity and unpleasantness ratings stayed put", "avoidance-drivers;unpleasantness-vs-avoidance"),
 "vlaeyen2016": ("Vlaeyen et al. 2016", 2016, 2016, "clinical-psychology", "One-page diagram: threat plus priority to pain control vs valued life goals, with learning panels", "avoidance-drivers"),
 # ---------- Part G1 ----------
 "johansen2001": ("Johansen et al. 2001", 2001, 2001, "animal-circuits", "Rostral ACC lesions abolished formalin place avoidance; acute paw behaviours not reduced (rats)", "unpleasantness-vs-avoidance;cingulate-action"),
 "johansen2004": ("Johansen & Fields 2004", 2004, 2004, "animal-circuits", "Rostral ACC glutamate activity necessary and sufficient for pain avoidance learning: 'aversive teaching signal'", "learning-signal;unpleasantness-vs-avoidance;cingulate-action"),
 "corder2019": ("Corder et al. 2019", 2019, 2019, "animal-circuits", "Amygdala nociceptive ensemble needed for tending, escape and avoidance, not reflexes (mice)", "unpleasantness-vs-avoidance"),
 "lee2022": ("Lee et al. 2022", 2022, 2022, "animal-circuits", "Mouse ACC->PAG activation raised reflex heat sensitivity and shock-zone distance together; necessity untested", "cingulate-action;avoidance-drivers;unpleasantness-vs-avoidance"),
 # ---------- Part G2 ----------
 "wiech2013": ("Wiech & Tracey 2013", 2013, 2013, "human-neuroscience", "Review: pain and motivation shape each other in both directions; names RL tools as the next step", "learning-signal;avoidance-drivers"),
 "wang2018": ("Wang et al. 2018", 2018, 2018, "computational", "Pain avoidance fits planning/habit arbitration; pain-vs-reward difference provisional (N=15)", "learning-signal"),
 "becker2018": ("Becker et al. 2018", 2018, 2018, "clinical-psychology", "Translational review: chronic pain shifts reward, learning, goal regulation and avoidance", "avoidance-drivers;unpleasantness-vs-avoidance"),
 "seymour2019": ("Seymour 2019", 2019, 2019, "computational", "Pain as a reinforcement and control signal in a controller hierarchy; behaviour, not report, as measure", "learning-signal;avoidance-drivers;unpleasantness-vs-avoidance"),
 "gandhi2021": ("Gandhi et al. 2022", 2022, 2022, "human-neuroscience", "Avoidance vigour fell after failure, more with migraine and helplessness; parietal (not PAG) activity tracked it", "learning-signal;avoidance-drivers"),
 "jepma2022": ("Jepma et al. 2022", 2022, 2022, "computational", "Faster learning from received than avoided pain; levodopa and naltrexone raised learning from avoided pain", "learning-signal"),
 "le2024": ("Le et al. 2024", 2024, 2024, "computational", "Faster learning after avoided shock (opposite to jepma2022); avoidance parameters had cingulate correlates", "learning-signal"),
 # ---------- Part H ----------
 "vase2003": ("Vase et al. 2003", 2003, 2003, "unknown", "Not reviewed and not cited by the reviewed Part H papers; title names desire in placebo effects", "unpleasantness-vs-avoidance"),
 "vase2005": ("Vase et al. 2005", 2005, 2005, "unknown", "Not reviewed and not cited by the reviewed Part H papers", ""),
 "lee2024": ("Lee et al. 2024", 2024, 2024, "human-neuroscience", "Signed valence and unsigned affective intensity decoded from largely distinct voxels; no action measure", "dimensions;unpleasantness-vs-avoidance"),
 "flury2025": ("Flury et al. 2025", 2025, 2026, "clinical-psychology", "Reward improved pain avoidance without changing intensity or unpleasantness ratings; no differential claim", "unpleasantness-vs-avoidance;dimensions"),
 # ---------- Part I ----------
 "vogt1992": ("Vogt et al. 1992", 1992, 1992, "human-neuroscience", "Not reviewed. Cingulate functional heterogeneity; named in the Part I manifest only", "cingulate-action"),
 "budell2010": ("Budell et al. 2010", 2010, 2010, "human-neuroscience", "Not reviewed. Observation-only precursor that budell2015 replicates and extends", "cingulate-action"),
 "shackman2011": ("Shackman et al. 2011", 2011, 2011, "human-neuroscience", "Meta-analysis: negative affect, pain and cognitive control overlap in aMCC; adaptive control hypothesis", "cingulate-action"),
 "perini2013": ("Perini et al. 2013", 2013, 2013, "human-neuroscience", "Midcingulate responded to pain only with a button press; urge ratings did not dissociate from intensity", "cingulate-action;unpleasantness-vs-avoidance"),
 "misra2014": ("Misra & Coombes 2015", 2014, 2015, "human-neuroscience", "Grip-force control and pain overlap in aMCC within the same individuals", "cingulate-action"),
 "procyk2014": ("Procyk et al. 2016", 2014, 2016, "human-neuroscience", "Reward-feedback activity sits in cingulate motor maps (humans, monkeys); pain only as a hypothesis", "cingulate-action"),
 "budell2015": ("Budell et al. 2015", 2015, 2015, "human-neuroscience", "Observed pain faces: cingulate responses with attention to meaning, favouring affective meaning over mirroring", "cingulate-action"),
 "tolomeo2016": ("Tolomeo et al. 2016", 2016, 2016, "neurology-neurosurgery", "Cingulotomy lesion overlap predicted emotion-recognition and Stroop errors; pain not measured", "cingulate-action"),
 "han2017": ("Han et al. 2017", 2017, 2017, "human-neuroscience", "Watching others' pain raised instructed press force with observer unpleasantness; pressing damped responses", "cingulate-action"),
 "perini2020": ("Perini et al. 2020", 2020, 2020, "human-neuroscience", "Low C-fibre mutation carriers: normal thresholds, weaker urge to withdraw; insula-MCC coupling tracked urge", "cingulate-action;unpleasantness-vs-avoidance"),
 "koppel2022": ("Koppel et al. 2022", 2022, 2022, "human-neuroscience", "Cingulate/insula tracked predicted, not current, pain; action dependence only in exploratory tests", "cingulate-action"),
 "gordon2023": ("Gordon et al. 2023", 2023, 2023, "human-neuroscience", "Somato-cognitive action network in motor cortex; link to pain by citation only", "cingulate-action"),
}

POSITIONS = [
 ("dimensions", "dim-serial", "Separable and serially ordered", "price2000;rainville1997", "Intensity causes unpleasantness, which feeds secondary suffering; ACC tracks unpleasantness (partial segregation)"),
 ("dimensions", "dim-lateral-medial", "Distinct lateral (sensory) and medial (affective) systems", "kulkarni2005;zidda2024;craig2003", "Attention, primes or anatomy separate a sensory route from an affective/motivational one"),
 ("dimensions", "dim-affect-selective", "Manipulation shifts unpleasantness, intensity not significantly", "tiemann2014;hayen2017", "Drug manipulations moved unpleasantness without a significant intensity change; hayen2017 is breathlessness, a non-pain analogue"),
 ("dimensions", "dim-graded", "Relative specialisation or graded difference", "hofbauer2001;zubieta2001;stankewitz2023;singh2020", "Regions lean toward one dimension, but ratings co-move and streams integrate; no simple dichotomy"),
 ("dimensions", "dim-unitary", "Evidence favours one unitary experience", "talbot2019", "Intensity not selectively modifiable; unpleasantness maybe, tentatively and slightly; dissociations vulnerable to demand"),
 ("dimensions", "dim-valence-intensity", "Signed valence vs unsigned affective intensity", "lee2024;leknestracey2008", "Recasts the axis: pain shares valence and intensity codes with pleasure rather than a sensory/affective split"),
 ("valence-nature", "vn-body-imperative", "Body-protection imperativism", "klein2007;klein2015;mk2016;km2018", "Pain is a command about using or protecting a body part; intensity is command strength or ranking"),
 ("valence-nature", "vn-state-imperative", "First-order imperativism about bodily state", "martinez2011;martinez2015", "Unpleasantness commands that a bodily disturbance not exist; how to achieve it is left open"),
 ("valence-nature", "vn-reflexive", "Reflexive imperativism", "bh2019;loopy2019;barlassina2020;barlassina_reflection", "An unpleasant experience commands 'less of me!'; world-directed motivation is derived by decision-making"),
 ("valence-nature", "vn-relational", "Relational imperativism", "kauppinen2021", "Indicative content bearing on a standing concern plus an authoritative command about the world"),
 ("valence-nature", "vn-any-imperative", "Any imperativism beats evaluativism (metasemantic)", "mb2026", "Valence informs more about behaviour than world and sits late in processing, so its content is imperative"),
 ("valence-nature", "vn-body-evaluativism", "Evaluativism about bodily badness", "cuttertye2011;bain2013;bain2017;bain2019", "Unpleasant pain represents the bodily condition as bad for the subject; the experience itself motivates"),
 ("valence-nature", "vn-value-evaluativism", "Evaluativism about adaptive value", "carruthers2018;carruthers2023", "Valence is a nonconceptual representation of (adaptive) value for all affect; commands add nothing science needs"),
 ("valence-nature", "vn-against-representation", "Evaluative representation cannot be the whole story", "jacobson2013", "Rational relief shows painfulness is not exhausted by evaluative content; hints at a conative (desire-like) view"),
 ("relief-seeking", "rs-imperatives-fail", "Commands cannot explain relief-seeking", "bain2013", "Receiving a command is no reason to obey; silencing it with painkillers should then make no sense"),
 ("relief-seeking", "rs-messenger", "Evaluations cannot explain relief-seeking", "jacobson2013", "Removing a report of bodily badness without fixing the body would be 'killing the messenger'"),
 ("relief-seeking", "rs-spam", "Relief-seeking is extrinsic spam avoidance", "martinez2015", "Pain commands about the body only; we silence insistent, useless ('spammy') pains"),
 ("relief-seeking", "rs-separate-desires", "Two motivational routes", "bain2017;bain2019", "Unpleasant experience itself motivates protecting the body; relief-seeking comes from separate desires"),
 ("relief-seeking", "rs-reflexive", "Relief-seeking is intrinsic", "loopy2019;bh2019;barlassina_reflection", "Unpleasantness is about the experience, so wanting it gone is built in; body care is derived"),
 ("relief-seeking", "rs-separate-displeasure", "No reflexive motivation", "kauppinen2021", "Grief or fear do not motivate pills; painkillers answer a separate displeasure at being in an unpleasant state"),
 ("relief-seeking", "rs-hedonism-charge", "Experience-directed views imply motivational hedonism", "carruthers2023;carruthers2018", "If valence targets experiences and drives all choice, every choice aims at one's own experiences"),
 ("asymbolia", "as-standard", "Pain without painfulness", "bain2013;price2000;bh2019;carruthers2018", "Asymbolia keeps sensation and loses the affective/evaluative/command part (Grahek's reading, not in corpus)"),
 ("asymbolia", "as-lost-capacity", "Lost capacity to care about the body", "klein2015asym", "Indifference extends to all bodily threats; the command persists but is not treated as binding"),
 ("asymbolia", "as-concern", "Command without authority", "kauppinen2021;bain2017", "Without concern for bodily integrity, the command or evaluation no longer makes pain unpleasant"),
 ("asymbolia", "as-deflation", "Not shown to be pain; set aside", "griffithkind2023", "Testimony inconsistent and confounded; standard reading incoherent under essentialism; a symptom, not syndrome"),
 ("asymbolia", "as-taxonomy", "Probably still pain; taxonomy is the question", "duvalklein2025", "If pain is a cluster kind the objections fail; dispute turns on specific deficit vs symptom cluster"),
 ("unpleasantness-vs-avoidance", "uva-accompaniment", "Escape desire accompanies unpleasantness", "price2000;talbot2019", "Motivation gets no dimension of its own; talbot2019 explicitly equates unpleasantness with protective motivation"),
 ("unpleasantness-vs-avoidance", "uva-operational", "Avoidance as the readout of affect", "johansen2001;johansen2004;singh2020;corder2019", "Animal work infers unpleasantness from learned or ongoing avoidance, never measured independently of it"),
 ("unpleasantness-vs-avoidance", "uva-hard-to-separate", "Hedonic and motivational hard to disentangle", "leknestracey2008;cuttertye2011", "Avoidance tracks aversiveness; represented badness is carried by a state defined by avoidance role"),
 ("unpleasantness-vs-avoidance", "uva-behaviour-moves", "Behaviour moves while ratings do not", "claes2015;flury2025;becker2018", "Competing rewards change avoidance choices or performance without changing fear, intensity or unpleasantness ratings"),
 ("unpleasantness-vs-avoidance", "uva-behaviour-primary", "Control behaviour as the ultimate measure", "seymour2019", "Pain is a control signal, so behaviour rather than self-report should measure it"),
 ("unpleasantness-vs-avoidance", "uva-liking-wanting", "Liking and wanting come apart", "loopy2019;barlassina_reflection;carruthers2023", "Both camps accept dissociations of pleasure from motivation; they disagree what they show about valence"),
 ("unpleasantness-vs-avoidance", "uva-urge", "Urge to withdraw rated beside action", "perini2013;perini2020", "Urge did not dissociate from intensity (perini2013); insula-cingulate coupling tracked urge in controls (perini2020 only)"),
 ("cingulate-action", "ca-affect", "Cingulate as the seat of unpleasantness", "rainville1997;price2000;johansen2001;craig2003", "ACC activity tracks or is needed for pain's unpleasantness or motivational drive"),
 ("cingulate-action", "ca-integration", "Adaptive control integration", "shackman2011;misra2014;tolomeo2016", "One aMCC region integrates pain, negative affect and control to choose actions under uncertainty"),
 ("cingulate-action", "ca-action-dependence", "Pain response depends on action", "perini2013;perini2020;koppel2022;lee2022", "Midcingulate responses follow action requirements or consequences; ACC output is sensorimotor, not sensory"),
 ("cingulate-action", "ca-observed", "Observed pain: meaning and vigour", "budell2015;han2017", "Others' pain engages cingulate when meaning is attended and makes instructed actions more forceful"),
 ("cingulate-action", "ca-motor-maps", "Effector-specific action maps (not pain studies)", "procyk2014;gordon2023", "Cingulate and motor cortex organise feedback and whole-body action planning in motor maps"),
 ("learning-signal", "ls-teaching", "ACC as aversive teaching signal", "johansen2004", "Rostral ACC activity necessary and sufficient to teach avoidance (one dose; authors: not conclusive); same circuit as unpleasantness"),
 ("learning-signal", "ls-rl-control", "Pain is the reinforcement and control signal", "seymour2019;wiech2013", "Pain is the internal reinforcement signal in a controller hierarchy (seymour2019 identity claim); wiech2013 frames it as a motivator"),
 ("learning-signal", "ls-arbitration", "Planning and habit systems for pain avoidance", "wang2018", "Pain avoidance draws on model-based and model-free control with reliability-based switching"),
 ("learning-signal", "ls-received", "Learn more from pain received", "jepma2022", "Learning rate higher after received than avoided pain; separate threat and safety systems"),
 ("learning-signal", "ls-avoided", "Learn more from pain avoided", "le2024", "Learning rate higher after avoided shock in a go/no-go task mixing money and shock"),
 ("learning-signal", "ls-value", "Learning describable as value updating", "carruthers2023", "Prediction-error learning of stored values needs no commands"),
 ("learning-signal", "ls-command", "Learning function supports commands", "bh2019;mb2026", "Affect evolved as reward/punishment for trial-and-error learning; learning models favour imperative content"),
 ("learning-signal", "ls-vigour", "Avoidance vigour adapts to failure", "gandhi2021", "Failing to avoid lowers next-trial vigour, more with helplessness; parietal attention not PAG"),
 ("avoidance-drivers", "ad-fear", "Fear drives avoidance", "vlaeyen2000;vlaeyen2016", "Catastrophizing leads to fear, avoidance and disability; the 2016 diagram keeps this fear loop as its core"),
 ("avoidance-drivers", "ad-intensity", "Intense pain is itself threatening", "leeuw2006", "High pain intensity itself drives escape and avoidance; model underplayed it"),
 ("avoidance-drivers", "ad-goals", "Goal competition", "crombez2012;claes2015;vlaeyen2016;becker2018", "Avoiding pain is one goal among many; protective behaviour yields when another goal is valued more"),
 ("avoidance-drivers", "ad-homeostatic", "Homeostatic drive", "craig2003", "Pain is a feeling plus behavioural drive like hunger or thermal discomfort"),
 ("avoidance-drivers", "ad-decision", "Motivation and learned decision", "seymour2019;wiech2013;gandhi2021", "Avoidance is learned and weighed against other outcomes; vigour falls after failure and helplessness"),
 ("avoidance-drivers", "ad-defence-circuit", "Active-defence circuit", "lee2022", "Increased ACC->PAG signalling might contribute to excessive fear-avoidance (stated as speculation)"),
]

# (from, to, relation, evidence)
EDGES = [
 ("martinez2011","klein2007","critiques","B1 §1 Argument 3"),
 ("martinez2011","hall2008","critiques","B1 §1 backbone: Klein's command model"),
 ("cuttertye2011","klein2007","critiques","B1 §2 Against imperative content"),
 ("cuttertye2011","martinez2011","critiques","B1 §2 Against imperative content"),
 ("cuttertye2011","hall2008","critiques","B1 §2 backbone §4 (fn. 13)"),
 ("bain2013","klein2007","critiques","B1 §3 Argument 2"),
 ("bain2013","martinez2011","critiques","B1 §3 Argument 2"),
 ("bain2013","hall2008","critiques","B1 §3 backbone §5"),
 ("bain2013","cuttertye2011","builds-on","B1 §5 who answers whom"),
 ("jacobson2013","cuttertye2011","critiques","B1 §4 main argument"),
 ("carruthers2018","cuttertye2011","critiques","A §2 naturalisation problem"),
 ("bh2019","martinez2011","critiques","A §3 Argument 1"),
 ("bh2019","martinez2015","critiques","A §3 Argument 1 table (spam)"),
 ("bh2019","klein2015","critiques","A §3 Argument 2"),
 ("bh2019","klein2007","critiques","A §3 critical assessment (ankle reply); A §6"),
 ("bh2019","bain2013","critiques","A §3 diagnostic step (§4.3)"),
 ("bh2019","cuttertye2011","critiques","A §3 diagnostic step (§4.3)"),
 ("bh2019","ploner1999","uses-as-evidence","A §3 Argument 2 (pure affect)"),
 ("barlassina2020","carruthers2018","critiques","A §4 argument reconstruction"),
 ("barlassina2020","bh2019","builds-on","A §4 technical analysis (token to type)"),
 ("carruthers2023","barlassina2020","replies-to","A §5 Argument 7; A §6 reply ledger"),
 ("carruthers2023","bh2019","replies-to","A §5 Argument 7"),
 ("carruthers2023","loopy2019","replies-to","A §5 citation-key warning; B2 §8 attribution check"),
 ("carruthers2023","carruthers2018","builds-on","A §5 technical analysis"),
 ("carruthers2023","martinez2011","critiques","A §5 technical analysis (world-directed imperativism)"),
 ("carruthers2023","ploner1999","reinterprets","A §5 Argument 7 (fn. 11)"),
 ("martinez2015","bain2013","replies-to","B2 §1 argument reconstruction (P7, conclusion)"),
 ("martinez2015","martinez2011","builds-on","B2 §1 field-history record"),
 ("martinez2015","km2018","builds-on","B2 §1 technical analysis (fn. 2-3)"),
 ("klein2015","klein2007","builds-on","B2 §2 place in history"),
 ("klein2015","klein2010","builds-on","B2 §2 place in history; field-history record"),
 ("mk2016","bain2013","critiques","B2 §3 argument reconstruction (4.3)"),
 ("mk2016","klein2015","builds-on","B2 §3 backbone 1"),
 ("mk2016","martinez2015","builds-on","B2 §3 argument reconstruction (4.3, reasons)"),
 ("bain2017","klein2007","critiques","B2 §4 argument reconstruction 3(d)"),
 ("bain2017","martinez2011","critiques","B2 §4 four positions table"),
 ("bain2017","cuttertye2011","builds-on","B2 §4 argument reconstruction 1-2"),
 ("bain2017","jacobson2013","replies-to","B2 §4 challenges table (messenger-shooting)"),
 ("bain2017","bain2013","builds-on","B2 §4 introduction"),
 ("bain2017","berthier1988","uses-as-evidence","B2 §4 backbone 3 (asymbolia and care)"),
 ("bainreview2017","klein2015","critiques","B2 §5 worries"),
 ("km2018","cuttertye2011","replies-to","B2 §6 introduction"),
 ("bain2019","martinez2015","critiques","B2 §7 strategies table (row 1)"),
 ("bain2019","klein2015","critiques","B2 §7 strategies table (row 1)"),
 ("bain2019","jacobson2013","replies-to","B2 §7 backbone §2 and §8"),
 ("bain2019","bain2013","builds-on","B2 §7 field-history record"),
 ("loopy2019","martinez2015","critiques","B2 §8 §3.3.1"),
 ("loopy2019","bain2019","critiques","B2 §8 §3.3.2"),
 ("loopy2019","bain2013","critiques","B2 §8 §3.2 Thinking Otherwise Problem"),
 ("loopy2019","carruthers2018","critiques","B2 §8 map of intentionalist theories"),
 ("loopy2019","martinez2011","critiques","B2 §8 map of intentionalist theories"),
 ("loopy2019","bh2019","builds-on","B2 §8 relation to Part A"),
 ("kauppinen2021","martinez2011","builds-on","B3 §1 key finding 3"),
 ("kauppinen2021","bh2019","critiques","B3 §1 Shooting the Officer, reply 2"),
 ("kauppinen2021","km2018","critiques","B3 §1 intensity"),
 ("kauppinen2021","cuttertye2011","critiques","B3 §1 key finding 2"),
 ("kauppinen2021","bain2019","builds-on","B3 §1 Shooting the Officer, reply 1"),
 ("kauppinen2021","carruthers2018","critiques","B3 §1 key finding 1"),
 ("kauppinen2021","klein2015","builds-on","B3 §1 asymbolia"),
 ("barlassina_reflection","carruthers2018","critiques","B3 §3 key finding 1"),
 ("barlassina_reflection","bain2013","critiques","B3 §3 key finding 1"),
 ("barlassina_reflection","cuttertye2011","critiques","B3 §3 key finding 1"),
 ("barlassina_reflection","martinez2011","critiques","B3 §3 key finding 2"),
 ("barlassina_reflection","bh2019","builds-on","B3 §3 initial takeaway"),
 ("mb2026","carruthers2023","replies-to","B3 §2 reply table"),
 ("mb2026","mk2016","builds-on","B3 §2 metasemantic framework"),
 ("mb2026","bh2019","builds-on","B3 §2 the divide"),
 ("mb2026","martinez2011","builds-on","B3 §2 the divide"),
 ("klein2015asym","klein2007","builds-on","C §1 revision of Klein 2007 (fn. 12)"),
 ("klein2015asym","ploner1999","critiques","C §1 technical analysis (fn. 4)"),
 ("klein2015asym","berthier1988","uses-as-evidence","C §1 key finding 2"),
 ("klein2015asym","craig2003","builds-on","C §1 neural framing"),
 ("klein2015asym","price2000","critiques","C §1 backbone §2.1 (degraded input model)"),
 ("griffithkind2023","klein2015asym","critiques","C §2 §6 alternatives"),
 ("griffithkind2023","berthier1988","reinterprets","C §2 threshold detail"),
 ("duvalklein2025","griffithkind2023","replies-to","C §3"),
 ("duvalklein2025","klein2015asym","builds-on","C §3 introduction"),
 ("duvalklein2025","ploner1999","critiques","C §3 technical analysis"),
 ("duvalklein2025","berthier1988","uses-as-evidence","C §3 Argument A (A2)"),
 ("price2000","rainville1997","uses-as-evidence","D §2 evidence table"),
 ("price2000","berthier1988","uses-as-evidence","D §2 evidence table"),
 ("price2000","melzackcasey1968","builds-on","D §2 backbone 2"),
 ("leknestracey2008","craig2003","builds-on","D §3 key result"),
 ("leknestracey2008","fields2006","builds-on","D §3 key result"),
 ("talbot2019","price2000","reinterprets","D §4 terminology; D cross-paper note 2"),
 ("talbot2019","fernandezturk1992","builds-on","D §4 key findings (method)"),
 ("talbot2019","rainville1997","uses-as-evidence","D §4 included studies"),
 ("talbot2019","hofbauer2001","uses-as-evidence","D §4 included studies"),
 ("talbot2019","treede1999","builds-on","D §4 terminology"),
 ("rainville1997","melzackcasey1968","builds-on","E1 §1 introduction"),
 ("rainville1997","foltz1962","uses-as-evidence","E1 §1 backbone background"),
 ("hofbauer2001","rainville1997","builds-on","E1 §2 introduction"),
 ("hofbauer2001","ploner1999","uses-as-evidence","E1 §2 further points"),
 ("hofbauer2001","berthier1988","uses-as-evidence","E1 §2 further points (insula); record"),
 ("hofbauer2001","price2000","builds-on","E1 §2 inferential step 4"),
 ("zubieta2001","rainville1997","uses-as-evidence","E1 §3 backbone (affective correlations)"),
 ("kulkarni2005","rainville1997","critiques","E1 §4 further points"),
 ("kulkarni2005","hofbauer2001","critiques","E1 §4 inferential step 3; backbone abstract"),
 ("kulkarni2005","bentley2004","builds-on","E1 §4 further points"),
 ("kulkarni2005","ploner1999","uses-as-evidence","E1 §4 backbone introduction"),
 ("kulkarni2005","foltz1962","uses-as-evidence","E1 §4 backbone introduction"),
 ("tiemann2014","leknestracey2008","builds-on","E1 §5 inferential step 5"),
 ("hayen2017","zubieta2001","uses-as-evidence","E2 §1 backbone discussion (rACC/NAcc)"),
 ("hayen2017","leknestracey2008","uses-as-evidence","E2 §1 backbone discussion (emotional state)"),
 ("singh2020","rainville1997","builds-on","E2 §2 introduction"),
 ("singh2020","melzackcasey1968","builds-on","E2 §2 introduction"),
 ("singh2020","johansen2001","builds-on","E2 §2 critical assessment (CPA lineage)"),
 ("singh2020","price2000","builds-on","E2 §2 backbone discussion"),
 ("stankewitz2023","rainville1997","critiques","E2 §3 introduction"),
 ("stankewitz2023","hofbauer2001","critiques","E2 §3 introduction"),
 ("stankewitz2023","wiech2013","uses-as-evidence","E2 §3 inferential step"),
 ("zidda2024","hofbauer2001","builds-on","E2 §4 backbone discussion (sources)"),
 ("zidda2024","price2000","builds-on","E2 §4 backbone discussion (sources)"),
 ("zidda2024","melzackcasey1968","builds-on","E2 §4 backbone introduction"),
 ("vlaeyen2000","wall1979","uses-as-evidence","F §1 place in history"),
 ("craig2003","melzackwall1965","critiques","F §2 place in history"),
 ("leeuw2006","vlaeyen2000","builds-on","F §3 key result"),
 ("leeuw2006","eccleston1999","builds-on","F §3 revision on intensity"),
 ("leeuw2006","wall1979","uses-as-evidence","F §3 adaptiveness"),
 ("crombez2012","vlaeyen2000","builds-on","F §4 field-history record"),
 ("crombez2012","leeuw2006","builds-on","F §4 field-history record"),
 ("crombez2012","eccleston1999","builds-on","F §4 place in history"),
 ("crombez2012","vandamme2008","builds-on","F §4 field-history record"),
 ("crombez2012","hasenbring2010","builds-on","F §4 field-history record"),
 ("claes2015","crombez2012","builds-on","F §5 place in history"),
 ("claes2015","vandamme2008","builds-on","F §5 place in history"),
 ("claes2015","vlaeyen2000","critiques","F §5 inferential step 3"),
 ("vlaeyen2016","vlaeyen2012","builds-on","F §6 claim"),
 ("vlaeyen2016","crombez2012","builds-on","F §6 place in history"),
 ("johansen2001","rainville1997","uses-as-evidence","G1 §1 introduction"),
 ("johansen2001","price2000","builds-on","G1 §1 technical analysis (framework)"),
 ("johansen2001","melzackcasey1968","builds-on","G1 §1 technical analysis (framework)"),
 ("johansen2001","treede1999","builds-on","G1 §1 technical analysis (framework)"),
 ("johansen2001","foltz1962","uses-as-evidence","G1 §1 field-history record"),
 ("johansen2004","johansen2001","builds-on","G1 §2 introduction; G1 §5 note 1"),
 ("johansen2004","rainville1997","uses-as-evidence","G1 §2 bridge to human affect"),
 ("corder2019","price2000","builds-on","G1 §3 framing"),
 ("corder2019","ploner1999","uses-as-evidence","G1 §3 framing"),
 ("corder2019","melzackcasey1968","builds-on","G1 §3 framing"),
 ("lee2022","johansen2004","builds-on","G1 §5 note 1"),
 ("lee2022","vlaeyen2016","builds-on","G1 §4 framing"),
 ("lee2022","melzackcasey1968","builds-on","G1 §4 framing"),
 ("wiech2013","vlaeyen2000","builds-on","G2 §1 field-history record"),
 ("wiech2013","eccleston1999","builds-on","G2 §1 field-history record"),
 ("becker2018","claes2015","uses-as-evidence","G2 §3 key result (competing goals)"),
 ("becker2018","crombez2012","builds-on","G2 §3 field-history record"),
 ("becker2018","vandamme2008","builds-on","G2 §3 field-history record"),
 ("becker2018","leeuw2006","builds-on","G2 §3 field-history record"),
 ("becker2018","leknestracey2008","builds-on","G2 §3 field-history record"),
 ("seymour2019","wang2018","uses-as-evidence","G2 §4 architecture step 7"),
 ("seymour2019","melzackcasey1968","builds-on","G2 §4 historical argument table"),
 ("seymour2019","melzackwall1965","builds-on","G2 §4 historical argument table"),
 ("seymour2019","craig2003","builds-on","G2 §4 historical argument table"),
 ("seymour2019","fields2006","builds-on","G2 §4 historical argument table"),
 ("seymour2019","vlaeyen2000","builds-on","G2 §4 backbone (chronic pain)"),
 ("seymour2019","eccleston1999","uses-as-evidence","G2 §4 endogenous control table"),
 ("le2024","jepma2022","uses-as-evidence","G2 §7 place in history (MCC only)"),
 ("lee2024","leknestracey2008","builds-on","H §1 field-history record"),
 ("lee2024","corder2019","builds-on","H §1 backbone introduction"),
 ("flury2025","melzackcasey1968","builds-on","H §2 introduction"),
 ("flury2025","auvray2010","uses-as-evidence","H §2 backbone introduction"),
 ("flury2025","vlaeyen2000","builds-on","H §2 field-history record"),
 ("flury2025","crombez2012","builds-on","H §2 inferential step 2"),
 ("flury2025","seymour2019","builds-on","H §2 backbone discussion"),
 ("shackman2011","rainville1997","builds-on","I §1 field-history record"),
 ("perini2013","shackman2011","builds-on","I §2 backbone introduction; I batch note 1"),
 ("misra2014","shackman2011","builds-on","I §3; I batch note 1"),
 ("budell2015","perini2013","uses-as-evidence","I §4 key result"),
 ("budell2015","shackman2011","builds-on","I batch note 1"),
 ("budell2015","budell2010","builds-on","I §4 place in history"),
 ("procyk2014","misra2014","uses-as-evidence","I §5 key result"),
 ("procyk2014","shackman2011","builds-on","I batch note 1"),
 ("tolomeo2016","shackman2011","builds-on","I §6 manipulation (masks)"),
 ("han2017","perini2013","builds-on","I §7 place in history"),
 ("han2017","rainville1997","builds-on","I §7 place in history"),
 ("perini2020","perini2013","builds-on","I §8 introduction; I batch note 1"),
 ("perini2020","shackman2011","builds-on","I batch note 1"),
 ("koppel2022","perini2013","builds-on","I §9 introduction; I batch note 1"),
 ("koppel2022","perini2020","builds-on","I §9 introduction"),
 ("koppel2022","shackman2011","builds-on","I batch note 1"),
 ("koppel2022","misra2014","builds-on","I batch note 1"),
 ("koppel2022","procyk2014","builds-on","I batch note 1"),
]

NM = "not-measured"
CONTRASTS = {"manipulation", "stimulus-class", "pre-task", "attention-condition", "none-correlational"}
# Rows kept although fewer than two own-pain outcomes are coded (explained in caveats).
DISS_KEEP_BELOW_TWO = {"budell2015"}
DISS = [
 # key, species, n_analysed, n_primary, design, contrast_of, intensity, unpleasantness, avoidance, desire, reflex_or_nocifensive, neural, direction_note, caveats
 ("rainville1997","human","8",8,"Hypnotic suggestion for more vs less unpleasantness of constant hot water","manipulation","unchanged","changed",NM,NM,NM,"H2(15)O PET","Unpleasantness 81 vs 45; ACC activity moved, S1 did not","Selected for the effect; intensity 78 vs 71 n.s., equivalence not tested; fixed state order"),
 ("hofbauer2001","human","10",10,"Hypnotic suggestion for stronger vs weaker pain","manipulation","changed","changed",NM,NM,NM,"H2(15)O PET","Both ratings moved (r=0.81); S1 moved with suggestion, ACC did not","Double dissociation only across two samples; selected sample; fixed state order"),
 ("zubieta2001","human","20",20,"Sustained jaw pain vs placebo; opioid release correlated with scores across people","none-correlational","correlational","correlational",NM,NM,NM,"[11C]carfentanil PET","Different but overlapping regions correlated with sensory vs affective questionnaire scores","Codes are between-person correlations; intensity held at 40-60 VAS; affect is MPQ subscale, not unpleasantness rating"),
 ("kulkarni2005","human","17",17,"Attend to location vs unpleasantness of identical laser pulses","attention-condition","unchanged","correlational",NM,NM,NM,"H2(15)O PET","Location: S1 and parietal; unpleasantness: perigenual ACC, OFC, amygdala, hypothalamus, M1","Intensity = % painful across tasks; unpleasantness rated in one task only, vs rCBF; S1 P=0.05 corrected; men only"),
 ("tiemann2014","human","22",22,"Dopamine-precursor depletion vs balanced amino-acid drink","manipulation","unchanged","changed",NM,NM,NM,"EEG evoked potentials and oscillations","Unpleasantness 5.6 vs 4.7 (p=.048), scaling with tyrosine depletion; EEG unchanged","Intensity null far better powered (75 single-trial ratings) than affect effect (one post-task rating); men only"),
 ("hayen2017","human","19",19,"Remifentanil vs saline during resistive-load breathlessness","manipulation","unchanged","changed",NM,NM,NM,"3T fMRI and arterial spin labelling","Breathlessness unpleasantness 61 to 49 (p=.03); intensity 71 to 68 (p=.21)","Breathlessness, a non-pain analogue; one-tailed; no interaction test; changes correlated r=0.59"),
 ("singh2020","rat","5 rats (units); 6-19 per group (behaviour)","","Optogenetic activation or inhibition of S1->ACC terminals paired with pinprick","manipulation",NM,NM,"changed",NM,NM,"in vivo electrophysiology with optogenetics","Activation increased and inhibition decreased pinprick place aversion","No sensory or reflex test under manipulation; key controls in absent supplement"),
 ("stankewitz2023","human","20",20,"No manipulation; both ratings on every trial of prolonged cold pain","none-correlational","correlational","correlational",NM,NM,NM,"7T fMRI activity and connectivity","Signals tracked unpleasantness slightly more than intensity; ratings r=0.86","Graded difference by authors' account; intensity always rated first; conditions pooled"),
 ("zidda2024","human","19",19,"Negative, neutral or positive picture primes before electric shock","manipulation","unchanged","changed",NM,NM,NM,"64-channel EEG (N2, P2)","Unpleasantness negative > neutral > positive; only P2 change predicted it","Intensity main effect n.s. but quadratic trend p=.04, partial eta2 .12; intensity rated first; picture ERPs overlap"),
 ("claes2015","human","57",57,"Lottery reward added to a painful joystick movement (within-subject)","manipulation","unchanged","unchanged","changed",NM,NM,"none","Choice of the painful movement rose sharply; fear rating also unchanged","Unpleasantness p=.133, no equivalence test; ratings from 50% phases, choices from 100% phase; self-selected groups"),
 ("johansen2001","rat","8 lesion, 10 sham (rostral)","","Rostral vs caudal ACC excitotoxic lesion; formalin place conditioning","manipulation",NM,NM,"changed",NM,"unchanged","excitotoxic lesion","Rostral lesion abolished place avoidance; acute formalin paw behaviour not reduced","Spared measure is nocifensive formalin licking/lifting/flinching, which corder2019 counts as affective; no thresholds; one bin higher"),
 ("johansen2004","rat","7-11 per group","","ACC glutamate blockade during training; agonist without noxious input; post-training lesion","manipulation",NM,NM,"changed",NM,"unchanged","intracerebral microinjection; lesion","Blockade prevented avoidance learning with acute behaviour unchanged; agonist alone produced avoidance","Spared measure is nocifensive formalin behaviour (corder2019 counts it affective); agonist one dose; authors: not conclusive"),
 ("corder2019","mouse","9 imaging; 14 per group silencing","","Chemogenetic silencing of an amygdala nociceptive ensemble","manipulation",NM,NM,"changed",NM,"unchanged","miniscope calcium imaging; activity-tagged chemogenetics","Attending, escape and thermal avoidance reduced; thresholds and withdrawal unchanged","Spared measures are reflexes (von Frey, withdrawal); attending/licking counted affective, unlike johansen2001; supplement absent"),
 ("lee2022","mouse","9-10 per group (avoidance task)","","Optogenetic activation or inhibition of ACC->dl/lPAG terminals","manipulation",NM,NM,"changed",NM,"changed","optogenetics; 15.2T optogenetic fMRI; tracing","Activation increased shock-zone distance and heat sensitivity together","Reflex = heat withdrawal latency; only activation tested in avoidance task (necessity untested); shock-zone entries unchanged"),
 ("gandhi2021","human","32",32,"Reaction-time pain-avoidance task: after failure vs success; migraine vs controls","manipulation",NM,NM,"changed",NM,NM,"3T fMRI","Avoidance vigour dropped after failure, more with helplessness; parietal, not PAG, tracked it","Pain rated only for calibration on one merged scale; helplessness effects n=15; accepted manuscript"),
 ("jepma2022","human","83 (74 fMRI)",83,"Pain-avoidance choice learning under levodopa, naltrexone or placebo","manipulation","unchanged",NM,"changed",NM,NM,"3T fMRI","Both drugs raised learning from avoided pain only; placebo learned more from received pain","Intensity 'unchanged' = no drug effect on pre-task ratings only; no ratings during learning; drug effects in model parameters"),
 ("le2024","human","82",82,"Go/no-go learning to avoid shock or win money","none-correlational",NM,NM,"correlational",NM,NM,"3T fMRI","Individual avoidance learning rate tracked by dorsal and mid cingulate activity","Half of shock feedback without shock; accepted manuscript; asymmetry opposite to jepma2022"),
 ("lee2024","human","58 (+62 test)",58,"Oral capsaicin vs chocolate vs water with continuous pleasant-unpleasant rating","none-correlational",NM,"correlational",NM,NM,NM,"3T fMRI multivariate decoding and connectivity","Signed valence and unsigned affective intensity decoded from largely distinct voxels","'Intensity' in paper is affective, not sensory; small effects; no action or avoidance measure"),
 ("flury2025","human","58",58,"Contingent vs yoked monetary reward for avoiding or discriminating heat","manipulation","unchanged","unchanged","changed",NM,NM,"none","Reward improved avoidance speed and success; ratings unchanged","Contingency main effect on unpleasantness p=.027 across both phases; mild probe stimuli; compliance confound; no differential claim"),
 ("perini2013","human","18 fMRI; 15 ratings","","Button press vs no press crossed with painful and non-painful heat and cold","stimulus-class","changed",NM,NM,"changed",NM,"3T fMRI and ALE meta-analysis","Urge and intensity both steeper for pain (r=0.53-0.83); midcingulate followed pressing","Rating codes compare pain vs non-pain, not press; ratings from separate group; no unpleasantness; press is not escape"),
 ("misra2014","human","15",15,"Grip force, painful heat, and both combined","manipulation","unchanged",NM,NM,NM,NM,"3T fMRI","Adding force did not change pain rating; aMCC overlap of force and pain","One scale mixing sensation and pain; dual-task attention not excluded"),
 ("budell2015","human","23",23,"Observing and reproducing pain faces: express meaning vs imitate movements","manipulation",NM,NM,NM,NM,NM,"3T fMRI with facial action coding","Cingulate pain responses in meaning task, not imitation task","Observer rating of another's pain, coded not-measured; kept for visibility, no own-pain outcome measured"),
 ("han2017","human","30 behaviour; 33 fMRI","","Watching painful vs non-painful clips while pressing a force sensor","stimulus-class",NM,NM,NM,"changed",NM,"3T fMRI","Press force and willingness to help rose for painful clips; pressing reduced responses to observed pain","Observer rating of another's pain (and own unpleasantness at viewing) coded not-measured; desire = willingness to help"),
 ("perini2020","human","12 carriers; 12 controls","","Natural manipulation: reduced C-fibre density (R221W carriers) vs matched controls","manipulation","unchanged",NM,NM,"changed",NM,"3T fMRI with connectivity; resting state","Thresholds normal, urge to withdraw weaker; insula-MCC coupling tracked urge in controls","Fixed-effects group model; urge rated after scan; sensitivity difference only a trend"),
 ("koppel2022","human","30",30,"Cue predicts pain; a timed press could or could not shorten it","manipulation",NM,NM,"changed",NM,NM,"3T fMRI (preregistered and exploratory)","Responses faster when press mattered; cingulate and insula tracked predicted, not current, pain","No pain ratings; press required every trial; preregistered action tests null"),
]

DIM_MODELS = [
 ("melzackwall1965",1965,"Gate control","sensory;affective","Components named (p. 976) without a dimensional model; avoidance sits in the action system (D §1)"),
 ("melzackcasey1968",1968,"Tripartite model","sensory-discriminative;motivational-affective;cognitive-evaluative","Named-only; content as described by D §1, G2 §4 and other citing reviews"),
 ("fernandezturk1992",1992,"Separation and synthesis","sensory;affective","Named-only; talbot2019 adopted its requirements for testing separability (D §4)"),
 ("price2000",2000,"Parallel-serial model","sensation intensity;unpleasantness;secondary affect","Serial chain with parallel arousal inputs; escape desire accompanies, no motivational dimension (D §2)"),
 ("craig2003",2003,"Homeostatic emotion","sensation (insula);motivational drive (ACC)","One homeostatic system with separate cortical substrates for feeling and drive (F §2)"),
 ("klein2007",2007,"Imperative theory of pain","negative imperative (primary affect);secondary affect","Pain's felt character exhausted by a command; fear and worry are secondary reactions (A §1)"),
 ("leknestracey2008",2008,"Common currency with pleasure","hedonic (suffering);motivational (avoidance)","Named separately but hard to disentangle anatomically (D §3)"),
 ("auvray2010",2010,"Two aspects","sensory-discriminative;affective-motivational","Named-only; cited by flury2025 for dissociable components (H §2)"),
 ("martinez2011",2010,"Imperative content model","indicative sensory content;imperative affective content","Sensory side hallucinable and indicative; painfulness imperative (B1 §1)"),
 ("cuttertye2011",2011,"Tracking representationalism","bodily disturbance;badness for subject to a degree","Badness carried by a functional state defined by avoidance role (B1 §2)"),
 ("bain2013",2012,"Composite evaluativism","disturbance representation;evaluative layer","Asymbolia lacks the evaluative layer (B1 §3)"),
 ("perini2013",2013,"Action as constitutive","pain response;action impulse","Action impulses 'partly constitutive' of cortical pain processing (I §2)"),
 ("klein2015",2015,"Pure imperativism","command to protect (pain per se);unpleasantness (separate)","Pain need not hurt; unpleasantness treated separately (B2 §2)"),
 ("carruthers2018",2017,"Evaluativism for all affect","sensory representation;valence (value)","For pain, the sensation is the object represented as bad (A §2)"),
 ("bh2019",2019,"Reflexive imperativism","sensory indicator;reflexive command","Asymbolia = indicator without command; Ploner patient = command without indicator (A §3)"),
 ("seymour2019",2019,"RL control architecture","nociceptive sensing;internal reinforcement signal","Discriminative information preserved while affective components suppressed (G2 §4)"),
 ("talbot2019",2019,"Unitary lean","unitary sensory-unpleasant experience","Tested sensory-discriminative vs affective-motivational; concludes evidence favours unitary (D §4)"),
 ("corder2019",2019,"Reflexive vs affective-motivational behaviour","reflexive;affective-motivational","Operational split in mice; valence and motivation language mixed (G1 §3)"),
 ("raja2020",2020,"Revised IASP definition","sensory;emotional (definition wording)","Named-only; zidda2024 reads it as implying separable dimensions (E2 §4)"),
 ("kauppinen2021",2021,"Relational imperativism","indicative content;background concern;imperative","Valence needs all three ingredients (B3 §1)"),
 ("stankewitz2023",2023,"Graded dimensions","intensity;unpleasantness","Highly correlated ratings; authors do not assume distinct processes (E2 §3)"),
 ("lee2024",2024,"Valence and affective intensity","signed valence;unsigned affective intensity","Shared by pain and pleasure; 'intensity' is not sensory intensity (H §1)"),
 ("flury2025",2025,"Two of Melzack & Casey's three, as behavioural surrogates","sensory-discriminative;emotional-motivational","Discrimination and avoidance tasks stand in for the components; authors decline a differential conclusion (H §2)"),
]

# label, year, community, why_relevant, cited_by (manifest keys; empty if no reviewed paper cites it)
NOT_HELD = [
 ("Cutter & Tye 2014, Pains and reasons: why it is rational to kill the messenger", 2014, "philosophy", "Evaluativist reply to jacobson2013 on relief-seeking (anti-unpleasantness desires)", "bain2017;bain2019;kauppinen2021"),
 ("Bain 2014, Pains that don't hurt", 2014, "philosophy", "Evaluativist account of asymbolia (lost care removes the evaluative layer); answers an early klein2015asym draft", "bain2017;klein2015asym;griffithkind2023;duvalklein2025;kauppinen2021"),
 ("Jacobson 2019, Not only a messenger", 2019, "philosophy", "Further argument against evaluativism after jacobson2013", "barlassina2020;kauppinen2021"),
 ("Martínez 2022, Imperative transparency", 2022, "philosophy", "Later statement of first-order imperativism", "mb2026"),
 ("Cochrane 2019", 2019, "philosophy", "Evaluativist ally cited on attention and on the Ploner case", "carruthers2023"),
 ("Grahek 2007, Feeling Pain and Being in Pain", 2007, "philosophy", "Source of the standard 'pain without painfulness' reading of asymbolia", "bain2013;klein2015asym;griffithkind2023;duvalklein2025;corder2019"),
 ("Hardcastle 1997, 1999", 1997, "philosophy", "Explicit double-dissociation reading of asymbolia and pain affect", "klein2015asym;duvalklein2025"),
 ("Klein & Duval 2023", 2023, "philosophy", "History of German vs French clinical traditions behind the asymbolia taxonomy dispute", "duvalklein2025"),
 ("Aydede 2006; Aydede & Fulkerson", 2006, "philosophy", "Critics of evaluativism: badness not trackable; the normative (messenger) objection", "cuttertye2011;bain2017;bain2019"),
 ("Pautz 2010", 2010, "philosophy", "'Mild and Severe' intensity challenge to tracking representationalism", "cuttertye2011;km2018;kauppinen2021"),
 ("Schilder & Stengel 1928, 1931", 1928, "neurology-neurosurgery", "First clinical descriptions of pain asymbolia; pre-1962 origin", "klein2015asym;griffithkind2023;duvalklein2025"),
 ("Sherrington, 'imperative protective reflex'", "", "unknown", "Pre-1962 command vocabulary for pain, quoted and rejected by melzackwall1965; year not given in reviews", "melzackwall1965"),
 ("Beecher 1956/1959 (wounded soldiers)", 1959, "unknown", "Pre-1962 origin: pain shaped by meaning; reaction component as precursor of the affective dimension", "melzackwall1965;bain2013;bain2017;vlaeyen2000"),
 ("Rainville et al. 1999", 1999, "human-neuroscience", "Hypnosis direction-of-causation experiments behind Price's serial model", "price2000;martinez2011;talbot2019;flury2025"),
 ("Price et al. 1985", 1985, "human-neuroscience", "Low-dose opioids act differently on unpleasantness than intensity (pain precedent for hayen2017)", "hayen2017"),
 ("Berridge & Valenstein 1991; Flynn et al. 1991; Galaverna et al. 1993", 1991, "animal-circuits", "Rat liking/wanting dissociations used as evidence by reflexive imperativists", "loopy2019;barlassina_reflection"),
 ("Mower 1976", 1976, "unknown", "Thermal pleasantness depends on body state; key evidence of the metasemantic argument", "mb2026"),
 ("Kragel et al. 2018", 2018, "human-neuroscience", "Pain-specific yet generalizable MCC patterns; counter-evidence to action-dependence", "perini2020;lee2022"),
 ("Seymour et al. 2004, 2005", 2004, "computational", "Early prediction-error studies with pain", "wiech2013;seymour2019;jepma2022"),
 ("Roy et al. 2014", 2014, "human-neuroscience", "Aversive prediction-error work and dataset reanalysed by jepma2022", "jepma2022;lee2022;le2024"),
 ("Fields 2018", 2018, "unknown", "Updated motivation-decision model (fields2006 named-only); ancestor of the RL strand", "seymour2019"),
 ("Lethem et al. 1983", 1983, "clinical-psychology", "Origin of the term fear-avoidance for pain", "vlaeyen2000;flury2025"),
 ("Crombez et al. 1998", 1998, "clinical-psychology", "Fear-side evidence: task performance tracked fear, not pain intensity", "vlaeyen2000"),
 ("de Jong et al. 2005", 2005, "clinical-psychology", "Fear-side evidence: exposure changed measured behaviour where education did not", "leeuw2006"),
 ("Asmundson et al. 2004", 2004, "clinical-psychology", "Fear-anxiety-avoidance model merged into the leeuw2006 diagram", "leeuw2006;crombez2012"),
 ("Strand: placebo, expectation and desire for relief (Price; Vase; Wager; Atlas; Büchel)", "", "human-neuroscience", "Omitted strand that rated desire for relief beside pain; vase2003 and vase2005 are named-only", "seymour2019;zidda2024;koppel2022"),
 ("Strand: IASP definition history (Merskey 1979 to Raja 2020)", "", "unknown", "Omitted strand; source of the pain vs nociception distinction; raja2020 named-only", "talbot2019;becker2018;zidda2024"),
 ("Strand: chronic-pain affective shift (Apkarian/Baliki; Hashmi 2013; Borsook)", "", "human-neuroscience", "Omitted strand present in the corpus only through becker2018 and citations", "corder2019;stankewitz2023;becker2018;flury2025"),
 ("Strand: attention and interruption (Eccleston & Crombez 1999) and motivation-decision (Fields 2006)", "", "unknown", "Ancestors of the RL strand; both only named-only in the manifest", "leeuw2006;crombez2012;seymour2019;leknestracey2008"),
]

SURVEY = [
 ("cuttertye2011","Key evaluativist source: unpleasantness represents bodily damage as bad","Yes, with refinements: badness is subject-relative and graded ('apt to harm'); paper never uses 'evaluativism' (B1 §2)","holds"),
 ("martinez2015","Unpleasantness is a command: 'protect this body part / stop this'","Command targets bodily damage, not the pain; 'protect this body part' is Klein's wording (B2 §1)","partly"),
 ("klein2015","Imperativism explains motivational force and uninformativeness; content action-directed","Matches chapter 1, but the theory concerns pain per se, not unpleasantness; 12 of ~200 pages held (B2 §2)","holds"),
 ("bain2017","Key evaluativist source: unpleasantness as evaluation of damage as bad","Matches; evaluation is experiential and itself motivating; represented condition left open (B2 §4)","holds"),
 ("bainreview2017","Evaluativism predicts a valenced judgement that causes motivation but is not itself motivational","Review never discusses evaluativism; Bain's own 2017 chapter says the experience is itself motivational (B2 §5)","does-not-hold"),
 ("klein2015asym","Klein: the command is issued but no longer binding","Matches p. 510; offered as best candidate, not a full defence (C §1)","holds"),
 ("griffithkind2023","Counter-reading: asymbolia isn't pain at all","Title says so; body argues only that evidence fails to show it is pain, provisionally (C §2)","partly"),
 ("price2000","Affective and motivational used interchangeably; the fusion was inherited","'Motivational' never appears; the explicit fusion is in talbot2019, which misattributes it to Price (D §2, D §4)","partly"),
 ("talbot2019","Components not independently modifiable; ratings covary; dissociations mostly attention effects","Asymmetric verdict (affect might be modifiable); explanations offered are demand, wording, bias, not attention (D §4)","partly"),
 ("rainville1997","Suggestion moves unpleasantness with intensity fixed; ACC not S1 changes","Matches, with 'fixed' meaning not significantly different (E1 §1)","holds"),
 ("hofbauer2001","The reverse suggestion moves S1","S1 moved, but unpleasantness moved too (r=0.81) and authors reject a simple dichotomy (E1 §2)","partly"),
 ("zubieta2001","Mu-opioid signalling regulates the two dimensions in different regions","Between-person correlations with overlapping regions and no direct test (E1 §3)","partly"),
 ("kulkarni2005","Attending to location vs unpleasantness dissociates lateral vs medial systems","Matches; rests on attention manipulation, S1 effect at P=0.05 corrected (E1 §4)","holds"),
 ("tiemann2014","Dopamine-precursor depletion changes affect but not sensation","Matches; affect effect is one post-task rating at p=.048 (E1 §5)","holds"),
 ("hayen2017","Opioids: unpleasantness down, intensity flat (cited as pain evidence)","Direction right but the sensation was experimentally induced breathlessness, not pain (E2 §1)","misattributed"),
 ("singh2020","In mice, S1->ACC projections carry sensory into affective circuitry","Content matches the authors' conclusion; animals were rats (E2 §2)","partly"),
 ("stankewitz2023","Unnamed '7T/EEG' result: cortex relates more to unpleasantness than intensity","Direction matches; 7T fMRI only, no EEG; authors call the difference gradual (E2 §3)","partly"),
 ("zidda2024","Emotional priming moves unpleasantness not intensity, with distinct ERP components","Matches; intensity quadratic trend p=.04; both N2 and P2 changed, only P2 predicted (E2 §4)","holds"),
 ("vlaeyen2000","The fear-avoidance model across four iterations","Paper reviews two earlier models and credits Lethem 1983; counts no iterations (F §1)","partly"),
 ("leeuw2006","The fear-avoidance model across four iterations","Evidence review with a merged diagram; counts no iterations (F §3)","partly"),
 ("crombez2012","The fear-avoidance model across four iterations","Calls for a next generation in words; no new diagram; counts no iterations (F §4)","partly"),
 ("vlaeyen2016","The fear-avoidance model across four iterations","Pictorial restatement anchored to Vlaeyen & Linton 2012; counts no iterations (F §6)","partly"),
 ("craig2003","Recasts pain as a homeostatic emotion","Matches p. 303 (F §2)","holds"),
 ("claes2015","Experimental work measures avoidance as behaviour: pain-avoidance vs reward-seeking","Matches; headline is that behaviour and self-reported fear came apart (F §5)","holds"),
 ("johansen2001","ACC lesions abolish pain place avoidance without changing nociceptive thresholds","Rostral ACC only; no thresholds measured, acute formalin behaviour instead (G1 §1)","partly"),
 ("johansen2004","ACC activation is itself an aversive teaching signal","Matches; authors call evidence not conclusive; one dose, one paradigm (G1 §2)","holds"),
 ("corder2019","BLA ensemble encodes unpleasantness; silencing removes affective behaviour not reflexes","Matches, but acute effect is a reduction, not removal (G1 §3)","holds"),
 ("lee2022","ACC->PAG projections required for pain avoidance: a command line, not evaluative","Necessity never tested; command-vs-evaluative contrast is not the paper's; paper says ACC encodes unpleasantness (G1 §4)","partly"),
 ("wiech2013","Wiech & Tracey's motivational perspective","It is that review (G2 §1)","holds"),
 ("wang2018","Model-based and model-free routes of pain-avoidance learning","Matches; omits that pain-vs-reward difference is provisional and no neural data (G2 §2)","holds"),
 ("becker2018","Review on emotional-motivational processing","It is that review (G2 §3)","holds"),
 ("seymour2019","Core function motivational; pain a precision-weighted RL control signal","First half verbatim; 'precision' means precise and objectifiable, 'precision-weighted' never appears (G2 §4)","partly"),
 ("gandhi2021","Human pain-avoidance behaviour has neural correlates distinct from pain report","Study never compares avoidance with pain report; claim is parietal rather than PAG role (G2 §5)","does-not-hold"),
 ("jepma2022","Pain-avoidance learning has its own neural systems for received vs avoided pain","Matches; authors' wording is 'suggest', drug effects only in model parameters (G2 §6)","holds"),
 ("le2024","Individual differences in avoidance vs reward learning","Models both in one task, not a single avoidance-vs-reward dimension; title truncated (G2 §7)","partly"),
 ("lee2024","Distinct voxel populations and networks for valence and intensity; no action axis","Accurate; populations lie within the same regions and 'intensity' is affective (H §1)","holds"),
 ("flury2025","Cleanest demonstration that avoidance is separate from both ratings (N=62)","58 analysed; authors say the pattern does not allow a differential conclusion; task-compliance confound (H §2)","partly"),
 ("shackman2011","Adaptive control hypothesis: aMCC integrates pain, affect and control","Matches; framed as working hypothesis on indirect inferences (I §1)","holds"),
 ("perini2013","Mid-cingulate region whose pain activity scales with action processing","Shows action dependence, not graded scaling; RT link not pain-specific (I §2)","partly"),
 ("misra2014","Motor control and pain in MCC","Matches p. 1906 (I §3)","holds"),
 ("budell2015","Facial pain expressions drive motor mirroring in MCC","Reverses the conclusion: pain responses appear with attention to meaning; affective-meaning networks favoured (I §4)","does-not-hold"),
 ("procyk2014","The midcingulate motor map","A motor map exists but evidence is juice-reward feedback; pain only a hypothesis (I §5)","partly"),
 ("tolomeo2016","Causal cingulotomy evidence (used for pain and action)","Lesions predicted facial-emotion and Stroop errors in depression; pain never measured (I §6)","misattributed"),
 ("han2017","Empathy for pain motivates action with motor-dynamic signatures","Matches; change is in vigour of an instructed press (I §7)","holds"),
 ("perini2020","Extended in C-afferent mutation carriers","Matches; 12 per group, fixed-effects model (I §8)","holds"),
 ("koppel2022","Prediction and action in cortical pain processing","Matches title; preregistered action tests null, action dependence exploratory (I §9)","holds"),
 ("gordon2023","SCAN named without a source","This is the defining paper; pain link is by citation only (I §10)","n.a."),
]


def main():
    manifest = {r["key"]: r for r in csv.DictReader(open(os.path.join(ROOT, "references_manifest.csv")))}
    errs = []
    if set(manifest) != set(W):
        errs.append(f"key mismatch: manifest-only={set(manifest)-set(W)} works-only={set(W)-set(manifest)}")
    debate_ids = [d[0] for d in DEBATES]

    def era_of(y):
        for eid, _, s, e, _ in ERAS:
            if s <= y <= e:
                return eid
        raise ValueError(y)

    def status(k):
        m = manifest[k]
        if m["status"] == "named-only":
            return "named-only"
        return "reviewed-full" if m["tier"] == "full" else "reviewed-short"

    # positions.csv is authoritative for debate membership; works.debates is derived from it.
    years = {k: W[k][1] for k in W}
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
        for kk in keys.split(";"):
            if kk not in W:
                errs.append(f"position {pid}: unknown key {kk}")
                continue
            deb_keys[d].add(kk)
            if d not in key_debates[kk]:
                key_debates[kk].append(d)
        if len(summ) > 160:
            errs.append(f"position {pid} summary too long {len(summ)}")
        pos_rows.append([d, pid, lab, keys, summ])

    rows = []
    for k in manifest:  # manifest order
        label, y, yp, comm, role, _unused = W[k]
        if comm not in COMMUNITIES:
            errs.append(f"{k}: community {comm}")
        st = status(k)
        if st == "named-only" and not role.startswith("Not reviewed"):
            errs.append(f"{k}: named-only role must say Not reviewed")
        if len(role) > 160:
            errs.append(f"{k}: role too long ({len(role)})")
        ordered = [d for d in debate_ids if d in key_debates[k]]
        rows.append([k, label, y, yp, comm, era_of(y), st, role, ";".join(ordered)])
    write("works.csv", ["key", "short_label", "year", "year_print", "community", "era", "status", "role", "debates"], rows)
    write("eras.csv", ["era_id", "label", "start_year", "end_year", "summary"], [list(e) for e in ERAS])
    write("positions.csv", ["debate_id", "position_id", "position_label", "keys", "summary"], pos_rows)

    statuses = {"settled", "leaning", "open", "stalled", "untested"}
    drows = []
    for did, title, q, st, reason, direction, scope in DEBATES:
        ys = [years[k] for k in deb_keys[did]]
        if st not in statuses:
            errs.append(f"debate {did} status {st}")
        if (st == "leaning") != bool(direction):
            errs.append(f"debate {did}: status_direction must be set iff leaning")
        for txt in (q, reason, scope):
            if len(txt) > 160:
                errs.append(f"debate {did} text too long {len(txt)}")
        drows.append([did, title, q, st, reason, direction, scope, min(ys), max(ys)])
    write("debates.csv", ["debate_id", "title", "question", "status", "status_reason", "status_direction", "status_scope", "first_year", "latest_year"], drows)

    rel_ok = {"builds-on", "critiques", "replies-to", "reinterprets", "uses-as-evidence"}
    seen = set()
    erows = []
    for f, t, r, ev in EDGES:
        if f not in W or t not in W:
            errs.append(f"edge unknown key {f}->{t}")
            continue
        if manifest[f]["status"] != "pdf":
            errs.append(f"edge from non-reviewed {f}")
        if r not in rel_ok:
            errs.append(f"edge relation {r}")
        if (f, t, r) in seen:
            errs.append(f"dup edge {f}->{t} {r}")
        seen.add((f, t, r))
        erows.append([f, t, r, ev])
    write("edges.csv", ["from_key", "to_key", "relation", "evidence"], erows)

    vals = {"changed", "unchanged", "not-measured", "correlational"}
    drows2 = []
    for row in DISS:
        k, n_primary, contrast = row[0], row[3], row[5]
        if manifest[k]["status"] != "pdf":
            errs.append(f"diss {k} not reviewed")
        if contrast not in CONTRASTS:
            errs.append(f"diss {k} contrast {contrast}")
        if n_primary != "" and not isinstance(n_primary, int):
            errs.append(f"diss {k} n_primary not int")
        outcomes = row[6:11]
        for v in outcomes:
            if v not in vals:
                errs.append(f"diss {k} bad value {v}")
        coded = [v for v in outcomes if v != NM]
        if contrast == "none-correlational" and any(v in ("changed", "unchanged") for v in coded):
            errs.append(f"diss {k}: none-correlational row has changed/unchanged codes")
        measured = len(coded) + (row[11] != "none")
        if measured < 2 and k not in DISS_KEEP_BELOW_TWO:
            errs.append(f"diss {k} measures <2")
        for c in row[12:]:
            if len(c) > 160:
                errs.append(f"diss {k} cell too long {len(c)}")
        drows2.append(list(row))
    write("dissociation_evidence.csv", ["key", "species", "n_analysed", "n_primary", "manipulation_or_design", "contrast_of", "intensity", "unpleasantness", "avoidance_behaviour", "desire_or_urge", "reflex_or_nocifensive", "neural", "direction_note", "caveats"], drows2)

    mrows = []
    for k, y, lab, comps, note in DIM_MODELS:
        if k not in W:
            errs.append(f"dim model unknown {k}")
        elif y != W[k][1]:
            errs.append(f"dim model year {k} {y} vs {W[k][1]}")
        mrows.append([k, y, lab, comps, note])
    write("dimension_models.csv", ["key", "year", "model_label", "components", "note"], mrows)

    nrows = []
    for lab, y, comm, why, cited in NOT_HELD:
        if comm not in COMMUNITIES:
            errs.append(f"not_held {lab}: community {comm}")
        for kk in [c for c in cited.split(";") if c]:
            if kk not in W or manifest[kk]["status"] != "pdf":
                errs.append(f"not_held {lab}: cited_by {kk} not a reviewed key")
        if len(why) > 160:
            errs.append(f"not_held {lab}: why too long {len(why)}")
        nrows.append([lab, y, comm, why, cited])
    write("not_held.csv", ["label", "year", "community", "why_relevant", "cited_by"], nrows)

    srows = []
    sv = {"holds", "partly", "does-not-hold", "misattributed", "n.a."}
    for k, c, f, v in SURVEY:
        if k not in W or manifest[k]["status"] != "pdf":
            errs.append(f"survey {k}")
        if v not in sv:
            errs.append(f"survey verdict {v}")
        for x in (c, f):
            if len(x) > 160:
                errs.append(f"survey {k} cell too long {len(x)}")
        srows.append([k, c, f, v])
    write("survey_corrections.csv", ["key", "survey_claim", "finding", "verdict"], srows)

    if errs:
        print("ERRORS:")
        print("\n".join(errs))
        sys.exit(1)
    print("rows: works", len(rows), "eras", len(ERAS), "debates", len(drows), "positions", len(pos_rows),
          "edges", len(erows), "dissociation", len(drows2), "dim_models", len(mrows), "not_held", len(nrows),
          "survey", len(srows))


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    main()
