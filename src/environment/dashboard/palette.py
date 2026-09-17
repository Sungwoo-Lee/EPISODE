"""Named colour tokens, and one machine-readable colour -> meaning map.

PLAIN-LANGUAGE SUMMARY. Every colour the episode dashboard paints is named here
once, and every name says what that colour is allowed to mean. A reader of a
frame should be able to say "orange means nociception" and be right *everywhere*
in the frame -- so the rule is not a convention in somebody's head, it is the
table :data:`MEANING` below, which checkpoint CP-C reads and enforces against a
pixel census of a rendered frame.

WHERE THE VALUES COME FROM. The adopted design spec
(``docs/reviews/design_episode_dashboard.md``), as already encoded in the
approved layout sketch
``docs/develop/active/refactors/renderer_layout_redesign/dashboard_style.py``.
They are copied, not re-chosen: the sketch is the canonical visual reference
(plan "Decided questions", Figure 3), and a second set of hexes that drifted from
it would make the sketch and the renderer two different designs.

ONE RULE WORTH STATING. ``CANVAS`` is the page colour and it is painted as a
**rectangle**, never as the figure's own facecolor. That is Figure 3's own
arrangement and the plan requires it to stay that way (Revision 20 section
R20.6): the audit calls a pixel "ink" when it differs from the figure facecolor
by more than 8/255, and ``TRACK`` -- the neutral square fill in the arena -- is
only 5-6/255 away from ``CANVAS``. Set the figure facecolor to ``CANVAS`` and the
arena's ground squares become **invisible to the instrument**, which would make
"the ground was painted over the animals" undetectable. :data:`FIGURE_FACECOLOR`
is therefore white, and a test pins the distance.
"""

from __future__ import annotations

# -- surfaces ---------------------------------------------------------------
CANVAS = "#F2F3F0"          # the page, drawn as a rectangle (never fig.set_facecolor)
CARD = "#FFFFFF"
LINE = "#E2E4DF"
TRACK = "#ECEEEA"           # an empty bar track, and the arena's neutral ground
CANVAS_TRACK = "#D9DCD5"    # a track drawn ON the canvas, where TRACK would vanish
OUTLINE = "#CDD1CB"         # an outlined empty track: "no signal", not "zero"
WHITE = "#FFFFFF"

#: The figure's own background: a colour NOTHING in this frame ever paints.
#:
#: Deliberately not ``CANVAS`` (see the module docstring) and, since 2026-09-17,
#: deliberately not ``WHITE`` either. The reasoning is the same one applied
#: twice, and the second application is the one that was missed.
#:
#: THE INSTRUMENT MEASURES INK BY ISOLATION: a pixel counts as ink when drawing
#: one element alone moves it more than 8/255 away from the figure with
#: everything hidden -- i.e. away from THIS colour. So an element painted in this
#: colour lays down no measurable ink and is invisible to every rule. That is
#: why it was moved off ``CANVAS``; but it was moved ONTO white, and white is not
#: an unused colour in this frame. It is the movers' token disc, the keyline, the
#: active chip's label, the World map's ring.
#:
#: WHAT IT COST, MEASURED. With the movers drawn as the user's artwork -- a
#: coloured glyph on a white token disc -- the disc was invisible to the probe,
#: so each token's measurable ink was its glyph PLUS its drop shadow with the
#: disc between them missing: two disconnected components for one animal. The
#: co-occupancy rule compares a square's component count with the number of kinds
#: standing there, so it reported 16 findings on a correct campfire frame and 18
#: on a correct M5 frame, every one of them with a survival ratio of **1.000** --
#: the picture was right and the instrument could not see it.
#:
#: THE FIX IS A GAIN IN SENSITIVITY, NOT A RELAXATION. On a colour no element
#: paints, every element's ink is measurable, including white ink that was
#: previously unmeasurable anywhere in the frame. Measured on the campfire frame:
#: `cell_overdraw` 16 -> **0**, squares whose component count disagrees with their
#: kind count 8 -> **0**, and one MORE `text_over_fill` is now reported (14 -> 15)
#: because white label ink became visible. No threshold moved.
#:
#: IT CHANGES NO RENDERED PIXEL, and that is checked rather than assumed: the page
#: colour is painted as a rectangle covering the whole figure, so the facecolor is
#: never on screen. The campfire frame rendered on white and on this colour is
#: byte-identical (max per-channel difference 0).
FIGURE_FACECOLOR = "#FF00FF"

# -- ink --------------------------------------------------------------------
INK, INK2, INK3 = "#15171C", "#4A515C", "#6F7682"

# -- reserved hues ----------------------------------------------------------
IRIS, IRIS_SOFT = "#5B4BDB", "#ECE9FB"     # the agent, and nothing else
STATE = "#2F3744"                          # body-state bars
NOCI = "#E8590C"                           # nociception, and nothing else

# -- entities ---------------------------------------------------------------
FOOD = "#E03151"
FOOD_LEAF, FOOD_STEM = "#1E9E5A", "#6B4A2B"
PRED = "#1F2733"
NEUT, NEUT_INNER, EYE_DARK = "#A8A29A", "#F0A9B4", "#2A241F"
HIDE_BODY, HIDE_EYE = "#2B3442", "#F59E0B"
ROCK, ROCK_HI = "#6B7380", "#A1A8B1"
BUSH, BUSH_HI = "#4F8A34", "#65A044"
TREE, TREE_HI, TRUNK = "#2F7A45", "#3E9357", "#7A5634"
FIRE_OUT, FIRE_MID, FIRE_CORE = "#F97316", "#FB9A3C", "#FDE68A"
LOG_BACK, LOG_FRONT, GLOW = "#7C4A2D", "#935C38", "#FDBA74"

#: One colour per entity NAME for the World map, taken from that entity's own
#: form. The campfire's mark is log brown with a flame-core dot: orange means
#: nociception in this frame, so flame colours live only inside the arena form.
MINIMAP_COLOUR: dict[str, str] = {
    "rock": ROCK, "bush": BUSH, "tree": TREE, "campfire": LOG_BACK,
    "food": FOOD, "hiding_predator": HIDE_BODY, "predator": PRED,
    "neutral": NEUT, "agent": IRIS,
}

#: Every palette colour a kind's OWN map mark is drawn in -- the table above's
#: body colour, plus any accent that belongs to the same mark.
#:
#: WHY A SECOND TABLE EXISTS. The pixel audit measures a map mark by counting the
#: pixels that still carry its colour in the finished image, against the pixels
#: it carries when drawn alone. With one colour per kind, a mark drawn in TWO
#: paints reads as partly missing: the hiding predator's amber identity pip --
#: the thing that tells it from an ordinary predator, whose body colour is only
#: 15/255 away -- covered about 21 % of its own body colour, and a correct frame
#: was reported as an occlusion. This is the union-of-a-token's-own-parts rule
#: the grid panel already had (plan section R19.1 step 5) arriving on the panel
#: that never inherited it (section R22.1).
#:
#: THE GUARD THAT KEEPS IT HONEST. Letting amber count towards `hiding_predator`
#: would be an amnesty if anything else on the map were amber. Nothing is --
#: `MINIMAP_COLOUR` contains no amber and `HIDE_EYE` is drawn only for a hiding
#: predator's identity pip -- and because that is a fact about today's painter
#: rather than a law, mutation M-F5 asserts it in the failing direction.
MINIMAP_MARK_COLOURS: dict[str, frozenset[str]] = {
    name: frozenset({colour} | ({HIDE_EYE} if name == "hiding_predator" else set()))
    for name, colour in MINIMAP_COLOUR.items()
}

# -- sense ramps ------------------------------------------------------------
OLF_STOPS = ("#EDF7F5", "#7CCBBD", "#14907F", "#0B4F47")     # teal: smell only
VIS_STOPS = ("#EFF1F4", "#A3ACBA", "#556072", "#1C2330")     # slate: vision only
TERRAIN_FILL = ("#DCEBD2", "#EFE4C9", "#E6E4DD")             # grass / sand / plain
OFF_WORLD = "#FFFFFF"

# -- temperature ------------------------------------------------------------
TEMP_COLD, TEMP_COOL, TEMP_NEUTRAL = "#9FBCE6", "#D3E1F2", "#F3F2EE"
TEMP_WARM, TEMP_HOT_MID, TEMP_HOT = "#F7DCCB", "#E6806A", "#B8323A"


#: colour token -> (plain-English meaning, the panel keys it may appear in).
#: ``None`` for the panel list means "anywhere" (neutral chrome). CP-C reads this
#: table, classifies every foreground pixel of a frame to its nearest token, and
#: fails if a token is found outside its allowed panels.
#:
#: WHAT THE TABLE OMITTED, AND WHY THAT MATTERED (2026-09-17). It listed the
#: campfire's LOG colour but none of its three FLAME colours, and neither sense
#: ramp. Those are the two places in the frame where the one-meaning-per-colour
#: rule is under actual pressure -- the flames are the frame's only other orange
#: beside the nociception bars, which is a collision this plan recorded in prose
#: and then could not see, because the instrument was not given the colours to
#: look for. A census that cannot name a colour cannot report it in the wrong
#: panel, so the omission made the rule quietly weaker than it reads. Both are
#: added here WITH panel scopes, which is what keeps the flame orange legal in
#: the arena and illegal everywhere a nociception bar lives.
MEANING: dict[str, tuple[str, tuple[str, ...] | None]] = {
    IRIS: ("the agent", ("arena", "minimap", "proprioception", "header", "action_badge")),
    IRIS_SOFT: ("the agent, softened", ("arena", "action_badge")),
    NOCI: ("nociception", ("intero_nociception", "extero_nociception", "collision")),
    STATE: ("a body state", ("satiation", "nutrition", "injury",
                             "satiation_hidden", "nutrition_hidden", "injury_hidden")),
    FOOD: ("food", ("arena", "minimap")),
    PRED: ("a predator", ("arena", "minimap")),
    NEUT: ("a neutral animal", ("arena", "minimap")),
    HIDE_BODY: ("a hiding predator (a static contact hazard)", ("arena", "minimap")),
    HIDE_EYE: ("the threat accent shared by predator and hiding predator",
               ("arena", "minimap")),
    ROCK: ("rock", ("arena", "minimap")),
    BUSH: ("bush", ("arena", "minimap")),
    TREE: ("tree", ("arena", "minimap")),
    LOG_BACK: ("campfire", ("arena", "minimap")),
    # The flame, scoped to the one panel that draws a campfire. This is the
    # frame's only orange besides NOCI, and the two are 21/255 apart at their
    # closest (FIRE_OUT vs NOCI), so the scope is what carries the distinction:
    # orange inside the arena is fire, orange anywhere a bar lives is pain.
    FIRE_OUT: ("a campfire's flame", ("arena",)),
    FIRE_MID: ("a campfire's flame, mid", ("arena",)),
    FIRE_CORE: ("a campfire's flame core", ("arena",)),
    GLOW: ("a campfire's heat glow", ("arena",)),
    LOG_FRONT: ("campfire, front log", ("arena",)),
    TEMP_COLD: ("temperature, cold end", ("arena", "thermoception", "body_temp")),
    TEMP_HOT: ("temperature, hot end", ("arena", "thermoception", "body_temp")),
    # The two sense ramps. Each is listed by its THREE SATURATED stops only; the
    # palest stop of each is deliberately absent, and the reason is arithmetic
    # rather than taste. OLF_STOPS[0] `#EDF7F5` is 11/255 from TRACK `#ECEEEA`,
    # inside the census's own 12/255 tolerance, so registering it would make
    # every empty track in the frame classify as a smell reading -- the census
    # would report the panel's background as signal. The painter draws a zero
    # reading as TRACK for exactly the same reason, so the palest ramp stop is
    # very nearly unreachable ink in the first place.
    OLF_STOPS[1]: ("a smell reading", ("olfactory",)),
    OLF_STOPS[2]: ("a smell reading", ("olfactory",)),
    OLF_STOPS[3]: ("a smell reading", ("olfactory",)),
    VIS_STOPS[1]: ("a vision reading", ("visual",)),
    VIS_STOPS[2]: ("a vision reading", ("visual",)),
    VIS_STOPS[3]: ("a vision reading", ("visual",)),
    TRACK: ("an empty track, or bare ground", None),
    CARD: ("a card", None),
    CANVAS: ("the page", None),
}
