"""FIGURE 8 -- the forms the renderer draws inside a world square.

QUESTION IT ANSWERS. What does each thing in the world look like, and what happens
when two or three of them stand in the same square?

WHAT CHANGED ON 2026-09-17, AND WHY IT MATTERS. This sheet used to draw the
*sketch's* glyphs (``dashboard_style.GLYPHS``), which were a mock's imitation of a
design. The renderer now exists, so the sheet draws the renderer's OWN forms by
calling ``src/environment/dashboard/cells.py`` directly -- the same
``compose()`` the arena calls for every square of every frame. A sheet drawn from
a second copy of the forms could drift from the shipped ones, which is plan
finding #56's failure mode.

WHAT IS ON IT, and why the third row is the point. Terrain is no longer a picture
in the middle of a square: it is the **floor** the square wears (decided question
Q18, variant H), inset so a ring of the square's own temperature colour always
shows. Because the floor costs the occupants no room, a square holding an agent
AND a bush draws both -- which is the defect this redesign exists to remove,
where whichever name sorted later in the alphabet was painted last and won.

SCALE, STATED BECAUSE IT IS EASY TO MISREAD. Every square here is drawn at the
renderer's real square size -- ``cell = 50`` px, the size decided in Revision 18
-- and the whole sheet is then magnified, uniformly, so the marks are visible on
a page. Nothing is redrawn at a larger size: magnifying the sheet is not the same
as drawing bigger squares, and the arithmetic that decides whether a mark
survives (``MIN_MARK x h`` against a 3 px floor) is the arithmetic of the 50 px
square.

OUTPUT: figures/fig08_icon_set.{svg,pdf,png} and figures/fig08_icon_set.data.txt

Run (from anywhere)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/fig08_icon_set.py
"""
import os
import sys

# This draws pictures; it must never take a training GPU. Set before any import of src/.
os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
os.chdir(ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import house  # noqa: E402
from src.environment.dashboard import cells as C  # noqa: E402
from src.environment.dashboard import painters as PN  # noqa: E402
from src.environment.dashboard import palette as P  # noqa: E402
from src.environment.dashboard import style as S  # noqa: E402

FIGS = os.path.join(HERE, "figures")

CELL = 50.0            # the renderer's real square, in its own pixels
PITCH = CELL + 34
PAD = 22
HEAD = 24              # a row's heading, above its tiles
LABEL = 34             # room under a tile for a two-line name
ROW_GAP = 26
NCOL = 5
SCALE = 2.8            # the whole sheet is magnified by this, uniformly

#: Each row: a heading, then (occupants, label template). ``occupants`` is handed
#: to the renderer's own ``compose()`` exactly as the arena hands it a square's
#: census. The template's ``{0}``, ``{1}`` ... are filled with the READER'S names
#: for those occupants, taken from ``cells.DISPLAY_NAME`` rather than typed here:
#: the code's token for the rabbit is ``neutral``, and a label that restated the
#: reader's name by hand is free to disagree with every other surface that prints
#: it (register F57). A template with no placeholder is a count, not a name.
ROWS = [
    ("One occupant, alone in a square", [
        (("agent",), "{0}"),
        (("food",), "{0}"),
        (("predator",), "{0}"),
        (("hiding_predator",), "{0}"),
        (("neutral",), "{0}"),
    ]),
    ("Terrain is the floor, not a picture in the middle", [
        (("bush",), "{0}"),
        (("rock",), "{0}"),
        (("tree",), "{0}"),
        (("campfire",), "{0}"),
    ]),
    ("A shared square keeps every occupant", [
        (("agent", "bush"), "{0}\non {1}"),
        (("agent", "food"), "{0}\n+ {1}"),
        (("neutral", "rock"), "{0}\non {1}"),
        (("agent", "hiding_predator", "predator"), "Three\noccupants"),
        (("agent", "predator", "food", "neutral"), "Four\n(synthetic)"),
    ]),
]


def tile_label(occupants, template):
    """One tile's caption, built from the renderer's own reader-facing names.

    The leading name opens the label, so it is capitalised and, if it is two
    words, broken over the tile's two lines; the rest read as ordinary prose
    inside the template ("Agent / on bush").
    """
    lead = C.display(occupants[0]).capitalize().replace(" ", "\n")
    return template.format(lead, *[C.display(n) for n in occupants[1:]])

ACTION = "RIGHT"       # so the agent's chevron shows which way it last moved


def draw_square(ax, occupants, cx, cy):
    """One world square, drawn by the renderer's own composition function."""
    S.rrect(ax, cx - CELL / 2 + 1, cy - CELL / 2 + 1, CELL - 2, CELL - 2, 8,
            P.TRACK, z=C.GROUND_Z)
    bed_name, drawn = C.compose(occupants, cx, cy, CELL, action=ACTION)
    PN._fill(PN._collection(ax, C.BED_Z),
             C.bed(bed_name, cx, cy, CELL) if bed_name else [])
    if "agent" in occupants:
        S.rrect(ax, cx - CELL / 2 + 2, cy - CELL / 2 + 2, CELL - 4, CELL - 4, 7,
                "none", P.IRIS, 2, z=C.OUTLINE_Z)
    for i, (_name, shapes) in enumerate(drawn):
        PN._fill(PN._collection(ax, C.TOKEN_Z + i * 0.01), shapes)


def text(ax, x, y, s, px, weight, colour, ha="left"):
    ax.text(x, y, s, fontsize=px * S.PT, fontfamily=S.FONT, fontweight=weight,
            color=colour, ha=ha, va="top", linespacing=1.25)


def main():
    house.apply()
    S.register_fonts()

    # The sheet must show every form the renderer can draw. Asserted, not trusted:
    # a form added to the package and forgotten here is exactly the drift this
    # figure was rewritten to stop.
    shown = {n for _, tiles in ROWS for occ, _ in tiles for n in occ}
    known = set(C.COMPANION) | set(C.BED)
    if shown != known:
        raise SystemExit(
            f"the sheet draws {sorted(shown)} but the renderer can draw {sorted(known)}; "
            f"missing {sorted(known - shown)}, unknown {sorted(shown - known)}"
        )

    w = 2 * PAD + NCOL * CELL + (NCOL - 1) * (PITCH - CELL)
    row_h = HEAD + CELL + LABEL
    h = 2 * PAD + len(ROWS) * row_h + (len(ROWS) - 1) * ROW_GAP + 24

    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100 * SCALE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_autoscale_on(False)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)          # y downward, the package's own convention
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), w, h, fc=P.CANVAS, lw=0, zorder=0))

    y = PAD
    for heading, tiles in ROWS:
        text(ax, PAD, y, heading, 12, "semibold", P.INK2)
        for i, (occ, template) in enumerate(tiles):
            cx = PAD + i * PITCH + CELL / 2
            draw_square(ax, occ, cx, y + HEAD + CELL / 2)
            text(ax, cx, y + HEAD + CELL + 8, tile_label(occ, template), 10, "medium",
                 P.INK, ha="center")
        y += row_h + ROW_GAP

    text(ax, PAD, h - PAD - 22,
         f"Every square is the renderer's real {CELL:.0f} px square, magnified {SCALE:g}x.\n"
         f"The floor is inset, so the square's own colour still shows around it.",
         9, "regular", P.INK3)

    house.save(fig, os.path.join(FIGS, "fig08_icon_set"), column_px=1084)
    with open(os.path.join(FIGS, "fig08_icon_set.data.txt"), "w") as fh:
        fh.write(f"entity forms drawn\t{len(known)}\t{len(known)}\tevery form "
                 f"src/environment/dashboard/cells.py can draw - {len(C.COMPANION)} occupant "
                 f"tokens and {len(C.BED)} terrain floors; the script stops if the two lists "
                 f"disagree\n")
        fh.write("occupant counts shown\t4\t4\tone, two, three and four occupants in a square - "
                 "four is the ceiling the draw-order table enforces. The four-way occurs in no "
                 "recorded episode and is built here on purpose, so it is evidence about the "
                 "painter and none about the worlds\n")


if __name__ == "__main__":
    main()
