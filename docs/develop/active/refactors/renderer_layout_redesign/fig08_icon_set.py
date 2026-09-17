"""FIGURE 8 -- the forms the renderer draws inside a world square.

QUESTION IT ANSWERS. What does each thing in the world look like, and what happens
when two or three of them stand in the same square?

WHAT CHANGED ON 2026-09-17, AND WHY IT MATTERS. This sheet draws the renderer's
OWN forms by calling ``src/environment/dashboard/cells.py`` directly -- the same
``compose()`` the arena calls for every square of every frame. A sheet drawn from
a second copy of the forms could drift from the shipped ones, which is plan
finding #56's failure mode.

WHAT THIS REPLACES (plan Revision 27). Between 2026-09-16 and the restoration of
the approved design, terrain was drawn as "variant H": a full-bleed FLOOR filling
the square, with the movers standing on top of it. This sheet drew those floors,
through a ``cells.bed()`` that no longer exists. Terrain is an **occupant** now,
drawn as its own centred glyph from the user's chosen artwork, so the middle row
is a row of glyphs rather than a row of carpets. Nothing here re-implements the
artwork: the script asks ``compose()`` what to draw and paints exactly what it
returns, through the arena painter's own ``_fill``.

WHAT IS ON IT, and why the third row is the point. One occupant is a centred
glyph at its own size -- the approved mock's own picture. Two or more are laid
out in disjoint quarter-square slots, so every occupant survives; that is the
defect this redesign exists to remove, where whichever name sorted later in the
alphabet was painted last and won.

SCALE, STATED BECAUSE IT IS EASY TO MISREAD. Every square here is drawn at the
renderer's real square size, and that size is DERIVED from the package rather
than typed: the arena is a fixed :data:`layout.ARENA_PX` box and the window zooms
inside it, so ``arena_cell_px(5)`` is the 96 px square of the approved design's
own 5-wide window. The whole sheet is then magnified, uniformly, so the marks are
visible on a page. Nothing is redrawn at a larger size: magnifying the sheet is
not the same as drawing bigger squares, and the arithmetic that decides whether a
token survives (its diameter against :data:`cells.RASTER_MIN_DIAMETER_PX`, its
body colour against :data:`cells.RASTER_MIN_BODY_AREA_PX2`) is the arithmetic of
the 96 px square.

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
from src.environment.dashboard import layout as LY  # noqa: E402
from src.environment.dashboard import painters as PN  # noqa: E402
from src.environment.dashboard import palette as P  # noqa: E402
from src.environment.dashboard import style as S  # noqa: E402

FIGS = os.path.join(HERE, "figures")

#: The window this sheet draws at. Five is the approved design's own window, and
#: the square size follows from the fixed arena rather than being chosen here.
VIEW_CELLS = 5
CELL = LY.arena_cell_px(VIEW_CELLS)    # 480 / 5 = 96 px, the renderer's real square

PITCH = CELL + 38
PAD = 22
HEAD = 26              # a row's heading, above its tiles
LABEL = 36             # room under a tile for a two-line name
ROW_GAP = 28
NCOL = 5
SCALE = 1.8            # the whole sheet is magnified by this, uniformly

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
    ("Terrain is an occupant too, drawn as its own centred glyph", [
        (("bush",), "{0}"),
        (("rock",), "{0}"),
        (("tree",), "{0}"),
        (("campfire",), "{0}"),
    ]),
    ("A shared square keeps every occupant, in its own slot", [
        (("agent", "bush"), "{0}\n+ {1}"),
        (("agent", "food"), "{0}\n+ {1}"),
        (("neutral", "rock"), "{0}\n+ {1}"),
        (("agent", "hiding_predator", "predator"), "Three\noccupants"),
        (("agent", "predator", "food", "neutral"), "Four\n(synthetic)"),
    ]),
]


def tile_label(occupants, template):
    """One tile's caption, built from the renderer's own reader-facing names.

    The leading name opens the label, so it is capitalised and, if it is two
    words, broken over the tile's two lines; the rest read as ordinary prose
    inside the template ("Agent / + bush").
    """
    lead = C.display(occupants[0]).capitalize().replace(" ", "\n")
    return template.format(lead, *[C.display(n) for n in occupants[1:]])

ACTION = "RIGHT"       # so the agent's chevron shows which way it last moved


def draw_square(ax, occupants, cx, cy):
    """One world square, drawn the way the ARENA PAINTER draws one.

    Deliberately the same three lines as ``painters.build_arena``'s per-square
    body: a ground fill, then ``compose()``, then one ``_fill`` per occupant into
    its own artist. The sheet owns no artwork of its own -- if it did, it could
    show a picture the renderer does not draw, which is the whole failure this
    figure exists to rule out.
    """
    S.rrect(ax, cx - CELL / 2 + 1, cy - CELL / 2 + 1, CELL - 2, CELL - 2, 8,
            P.TRACK, z=C.GROUND_Z)
    for i, (_name, shapes) in enumerate(
            C.compose(occupants, cx, cy, CELL, action=ACTION)):
        PN._fill(PN._collection(ax, C.TOKEN_Z + i * 0.01), shapes)


def text(ax, x, y, s, px, weight, colour, ha="left"):
    ax.text(x, y, s, fontsize=px * S.PT, fontfamily=S.FONT, fontweight=weight,
            color=colour, ha=ha, va="top", linespacing=1.25)


def main():
    house.apply()
    S.register_fonts()

    # The sheet must show every entity the renderer can draw. Asserted, not
    # trusted: an entity added to the package and forgotten here is exactly the
    # drift this figure was rewritten to stop. The table asked is the one the
    # drawing path itself uses -- `SOLO_FRAC` is what `token()` raises on -- and
    # `cells.py` already pins DISPLAY_NAME and CELL_PRIORITY against it at import.
    shown = {n for _, tiles in ROWS for occ, _ in tiles for n in occ}
    known = set(C.SOLO_FRAC)
    if shown != known:
        raise SystemExit(
            f"the sheet draws {sorted(shown)} but the renderer can draw {sorted(known)}; "
            f"missing {sorted(known - shown)}, unknown {sorted(shown - known)}"
        )

    w = 2 * PAD + NCOL * CELL + (NCOL - 1) * (PITCH - CELL)
    row_h = HEAD + CELL + LABEL
    h = 2 * PAD + len(ROWS) * row_h + (len(ROWS) - 1) * ROW_GAP + 26

    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100 * SCALE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_autoscale_on(False)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)          # y downward, the package's own convention
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), w, h, fc=P.CANVAS, lw=0, zorder=0))

    y = PAD
    for heading, tiles in ROWS:
        text(ax, PAD, y, heading, 14, "semibold", P.INK2)
        for i, (occ, template) in enumerate(tiles):
            cx = PAD + i * PITCH + CELL / 2
            draw_square(ax, occ, cx, y + HEAD + CELL / 2)
            text(ax, cx, y + HEAD + CELL + 10, tile_label(occ, template), 12, "medium",
                 P.INK, ha="center")
        y += row_h + ROW_GAP

    text(ax, PAD, h - PAD - 24,
         f"Every square is the renderer's real {CELL:.0f} px square "
         f"({LY.ARENA_PX:.0f} px arena ÷ a {VIEW_CELLS}-wide window), "
         f"magnified {SCALE:g}×.\n"
         f"One occupant is centred at its own size; two or more take "
         f"quarter-square slots, so none is painted over.",
         11, "regular", P.INK3)

    house.save(fig, os.path.join(FIGS, "fig08_icon_set"), column_px=1084)
    with open(os.path.join(FIGS, "fig08_icon_set.data.txt"), "w") as fh:
        fh.write(f"entity forms drawn\t{len(known)}\t{len(known)}\tevery entity "
                 f"src/environment/dashboard/cells.py can draw - five movers and four "
                 f"terrain glyphs, all nine from the chosen artwork; the script stops if "
                 f"the sheet and the renderer's own table disagree\n")
        fh.write("occupant counts shown\t4\t4\tone, two, three and four occupants in a square - "
                 "four is the ceiling the draw-order table enforces. The four-way occurs in no "
                 "recorded episode and is built here on purpose, so it is evidence about the "
                 "painter and none about the worlds\n")


if __name__ == "__main__":
    main()
