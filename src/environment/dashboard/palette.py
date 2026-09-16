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

#: The figure's own background. Deliberately NOT ``CANVAS`` -- see the module
#: docstring; this is what keeps the arena's ground visible to the pixel audit.
FIGURE_FACECOLOR = "#FFFFFF"

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
    TEMP_COLD: ("temperature, cold end", ("arena", "thermoception", "body_temp")),
    TEMP_HOT: ("temperature, hot end", ("arena", "thermoception", "body_temp")),
    TRACK: ("an empty track, or bare ground", None),
    CARD: ("a card", None),
    CANVAS: ("the page", None),
}
