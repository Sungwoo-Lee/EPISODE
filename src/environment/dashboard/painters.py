"""One painter per visual KIND -- never one per modality.

PLAIN-LANGUAGE SUMMARY. A "painter" here draws one kind of picture: a labelled
bar, a row of action chips, a diamond of temperature readings, the arena. Adding
a new sense to the environment is a new row in the registry
(:mod:`.panels`) and nothing else, as long as it is drawn as a kind that already
exists; only a genuinely new *picture* adds a painter. Neither touches layout.

HOW A PAINTER IS SHAPED. Every ``build_*`` takes the card's Axes and its size in
pixels, draws every artist it will ever need **once**, and returns an ``update``
callable that only changes values -- a bar's width, a label's string, a token's
colour. That is the whole architecture: the figure is built once per episode and
the per-step cost is setting attributes on existing artists, not constructing a
new figure per frame the way the production renderer does.

COORDINATES. Each card's Axes is in pixels with y growing **downward**
(``xlim 0..w``, ``ylim h..0``), matching the packer's boxes and the approved
sketch.

WHAT IS DELIBERATELY NOT HERE. Square composition -- who stands where inside one
arena square -- lives in :mod:`.cells`, because it is the part with its own
arithmetic and its own tests. The arena painter is a caller.
"""

from __future__ import annotations

import numpy as np
from matplotlib.collections import PatchCollection

from . import cells as C
from . import palette as P
from .labels import display_channel as channel_display
from .layout import LayoutOverflowError
from .style import PT, TITLE_BASE, rrect, signed, text
from .text_fit import CAPTION_FLOOR_PX, PLAYBACK_FLOOR_PX, fit_text

PAD = 16
GAP = 16

#: The action pill's mark for an action with no direction (Rest, Eat). Named
#: rather than inlined because a backslash escape may not appear inside an
#: f-string expression before Python 3.12.
_DOT = "•"

#: Baseline-to-baseline distance for a run of caption lines.
CAPTION_LINE = 17


# --------------------------------------------------------------------------
# small shared helpers
# --------------------------------------------------------------------------
class Fit:
    """A text measured into its slot: it raises rather than overlapping."""

    def __init__(self, dash, ax, x, y, role, max_w, numeric=True, **kw):
        self.dash, self.max_w, self.numeric = dash, max_w, numeric
        self.role = role
        self.t = text(ax, x, y, "", role, **kw)
        self.floor = CAPTION_FLOOR_PX if role.startswith("caption") else PLAYBACK_FLOOR_PX

    def set(self, s) -> float:
        r = fit_text(self.t, str(s), self.max_w, self.dash.renderer,
                     numeric=self.numeric, floor_px=min(self.floor, self._size()),
                     where=f"{self.role}")
        return r.width_px

    def _size(self):
        return float(self.t.get_fontsize()) * self.t.figure.dpi / 72.0


def card_frame(ax, box):
    """A card's own surface and outline.

    Drawn as a SEPARATE unfilled outline rather than as one filled-and-stroked
    rectangle, because the pixel audit forbids text lying across a card's edge
    and can only say that if the edge is its own element (plan section D5.2).
    """
    from .style import CARD_RADIUS
    rrect(ax, 0.5, 0.5, box.w - 1, box.h - 1, CARD_RADIUS, P.CARD, z=0)
    rrect(ax, 0.5, 0.5, box.w - 1, box.h - 1, CARD_RADIUS, "none", P.LINE, 1, z=0.1)


def card_title(dash, ax, w, title, sub=None, reserve=0):
    used = 0
    if sub is not None:
        used = dash.fit(ax, w - PAD, TITLE_BASE, "card_sub", w / 2, ha="right").set(sub) + 12
    dash.fit(ax, PAD, TITLE_BASE, "card_title", w - 2 * PAD - used - reserve).set(title)


def bar(ax, x, y, w, h, colour, z=2):
    """A rounded track with a fill; returns a setter taking a 0..1 value."""
    rrect(ax, x, y, w, h, h / 2, P.TRACK, z=z)
    fill = rrect(ax, x, y, h, h, h / 2, colour, z=z + 1)

    def set_v(v):
        v = min(1.0, max(0.0, float(v)))
        fill.set_visible(v > 0.003)
        fill.set_width(max(h, w * v))
    return set_v


def tick(ax, x, y, h, colour=P.INK, z=4):
    """The mark that shows the noise-free value on a bar."""
    ln, = ax.plot([x, x], [y - 2, y + h + 2], color=colour, lw=1.4 * PT, zorder=z)

    def set_x(px):
        ln.set_xdata([px, px])
    return set_x


def gradient(ax, x, y, w, h, colours, z=2):
    im = ax.imshow(np.asarray(colours)[None, :, :3], extent=(x, x + w, y + h, y),
                   aspect="auto", interpolation="bilinear", zorder=z)
    ax.set_xlim(0, ax._px_w)
    ax.set_ylim(ax._px_h, 0)
    return im


class _Form:
    """The artists one drawn form owns: a patch collection and an image.

    A form is EITHER vector or raster -- a terrain bed is patches, a mover is its
    artwork -- so exactly one of the two is ever visible at a time. Both are
    created up front because this renderer builds every artist once per episode
    and only updates them afterwards, and a square cannot know in advance which
    kind of thing will stand on it.

    ONE artist per form is a requirement, not a tidiness choice: the pixel audit
    separates a square's floor from its occupants by measuring ink AREA, so a bed
    split across six artists would have its small parts counted as an occupant
    (plan section R20.8) -- and two artists for one occupant would be read as two
    occupants sharing pixels, which is the very defect the rule hunts for.
    """

    __slots__ = ("coll", "im")

    def __init__(self, ax, z):
        self.coll = PatchCollection([], match_original=False, zorder=z)
        ax.add_collection(self.coll)
        self.coll.set_transform(ax.transData)
        self.coll.set_visible(False)
        self.im = ax.imshow(np.zeros((1, 1, 4)), extent=(0, 1, 1, 0), zorder=z,
                            interpolation="none", aspect="auto")
        self.im.set_visible(False)


def _collection(ax, z):
    """An empty form artist. Named for the vector case it started as."""
    return _Form(ax, z)


def _fill(form, shapes):
    """Put a compound form into its artists, or hide it when there is none."""
    coll, im = form.coll, form.im
    patches = [s for s in shapes if isinstance(s, C.Shape)]
    rasters = [s for s in shapes if isinstance(s, C.Raster)]
    if len(rasters) > 1:
        raise ValueError(
            f"a form may carry at most one image; got {len(rasters)} "
            f"({[r.name for r in rasters]})"
        )
    if patches:
        coll.set_paths([s.patch for s in patches])
        coll.set_facecolor([s.fc for s in patches])
        coll.set_edgecolor([s.ec for s in patches])
        coll.set_linewidth([s.lw * PT for s in patches])
    coll.set_visible(bool(patches))
    if rasters:
        r = rasters[0]
        im.set_data(C.icon_array(r.name, r.px, r.action))
        im.set_extent(r.extent)
    im.set_visible(bool(rasters))


# --------------------------------------------------------------------------
# header
# --------------------------------------------------------------------------
def build_header(dash, ax, w, h):
    m = dash.meta
    tw = dash.fit(ax, 24, 38, "frame_title", 360).set(m["title"])
    n = dash.n_steps - 1
    of_w = dash.fit(ax, w - 24, 36, "step_aux", 80, ha="right").set(f"/ {n}")
    digits = dash.width("0" * len(str(max(n, 1))), "step")
    num_x = w - 24 - of_w - 8
    num = dash.fit(ax, num_x, 36, "step", digits, ha="right")
    lab_x = num_x - digits - 10
    lab_w = dash.fit(ax, lab_x, 36, "meta", 60, ha="right", color=P.INK3).set("Step")
    bar_w = 132
    rrect(ax, w - 24 - bar_w, 48, bar_w, 4, 2, P.CANVAS_TRACK, z=2)
    prog = rrect(ax, w - 24 - bar_w, 48, 4, 4, 2, P.IRIS, z=3)
    meta_x = 24 + tw + 20
    dash.fit(ax, meta_x, 38, "meta", min(lab_x - lab_w, w - 24 - bar_w) - 32 - meta_x,
             numeric=False).set(m["meta"])

    def upd(v):
        num.set(str(v.step))
        prog.set_width(max(4, bar_w * v.step / max(1, n)))
    dash.updates.append(upd)


# --------------------------------------------------------------------------
# vitals -- the merged card, one row per body state
# --------------------------------------------------------------------------
def build_vitals(dash, ax, w, h, rows):
    """Rows of body states, each with an observed column and a noise-free column.

    THE RULE THIS CARD EXISTS TO ENFORCE (plan section D1.1, decided question
    Q10 = show). A body state the agent cannot sense is still drawn -- the state
    is real -- but its observed column reads **not observed** and it never prints
    a number there. The live renderer prints the true value under an ``OBS``
    caption, which tells a viewer the agent senses something it cannot; that is
    defect D10, and this is where it stops.
    """
    card_title(dash, ax, w, "Interoception")
    cw = (w - 2 * PAD - GAP) / 2
    xs = (PAD, PAD + cw + GAP)
    # "Sensed", not "Observed". The audit rules that any rendered text beginning
    # "OBS" must belong to a panel whose modality is actually in the observation
    # -- a rule that exists to catch a VALUE captioned as observed when it is
    # not (the live defect D10). A column head spanning five rows belongs to no
    # single modality, so it can never satisfy that rule, and the word is not
    # load-bearing here: what carries the meaning is the per-row "not observed"
    # text, which is unchanged.
    dash.fit(ax, xs[0], 66, "col_head", cw).set("Sensed")
    dash.fit(ax, xs[1], 66, "col_head", cw).set(rows[0].get("true_head", "Noise-free"))
    ax.plot([PAD, w - PAD], [76, 76], color=P.LINE, lw=1 * PT)

    # Each row is drawn at the y the PACKER carved for it, not at a stride this
    # painter picks: the packer owns geometry, and a painter that re-derived row
    # positions could drift out of its own card without the layout knowing.
    for row in rows:
        y = row["y"] + 12
        reserve = 0
        if row["kind"] == "temp" and dash.scale is not None:
            reserve = dash.fit(ax, w - PAD, y, "caption", cw, ha="right").set(
                f"limits {signed(dash.scale.low)} / {signed(dash.scale.high)}") + 12
        dash.fit(ax, xs[0], y, "row_label", w - 2 * PAD - reserve).set(row["label"])

        for col, x in zip(("obs", "true"), xs):
            key = row[col]
            if key is None:
                dash.fit(ax, x, y + 30, "not_observed", cw).set(
                    "not observed" if col == "obs" else "not recorded")
                rrect(ax, x, y + 40, cw, 6, 3, "none", P.OUTLINE, 1, z=2)
                continue
            val = dash.fit(ax, x, y + 30, "value", cw)
            if row["kind"] == "bar":
                set_v = bar(ax, x, y + 40, cw, 6, row["colour"])

                def upd(v, key=key, val=val, set_v=set_v):
                    q = key(v)
                    val.set(f"{q:.2f}")
                    set_v(q)
            else:
                set_v = temperature_gauge(dash, ax, x, y + 40, cw)

                def upd(v, key=key, val=val, set_v=set_v):
                    q = key(v)
                    val.set(signed(q, 1) + "°")
                    set_v(q)
            dash.updates.append(upd)

    foot = rows[-1]["y"] + 12 + 46 + 10
    ax.plot([PAD, w - PAD], [foot, foot], color=P.LINE, lw=1 * PT)
    dash.fit(ax, PAD, foot + 24, "caption", w - 2 * PAD, numeric=False).set(dash.meta["noise_note"])


def temperature_gauge(dash, ax, x, y, w):
    """Body temperature on the shared scale: the track is the survivable band."""
    sc = dash.scale
    lo, hi, sp = sc.low, sc.high, sc.sp
    g = np.linspace(lo, hi, 128)
    im = gradient(ax, x, y, w, 6, [sc.colour(v) for v in g], z=2)
    im.set_alpha(0.9)
    if sc.out_of_range(lo) or sc.out_of_range(hi):
        rrect(ax, x, y, w, 6, 3, "none", P.INK, 2, z=3)
    xs = x + w * (sp - lo) / (hi - lo)
    ax.plot([xs, xs], [y - 3, y + 9], color=P.INK3, lw=1 * PT, zorder=3)
    from matplotlib.patches import Circle
    dot = ax.add_patch(Circle((x, y + 3), 6, fc=P.WHITE, ec=P.INK, lw=2 * PT, zorder=4))

    def set_v(v):
        dot.set_center((x + w * (min(hi, max(lo, v)) - lo) / (hi - lo), y + 3))
    return set_v


# --------------------------------------------------------------------------
# the World map
# --------------------------------------------------------------------------
#: The World card's two caption lines. They are not decoration and they are not
#: free text: plan section R17.4 makes the on-page statement the honesty
#: condition this map's whole coded encoding rests on, so the caption must say
#: IN WORDS that colour is the code here and that the grid view is where the
#: occupants are identified. Two hard conditions on any rewording -- it must
#: still contain the substring the audit keys on (``shared square``,
#: ``SHARED_CAPTION``), and it must describe the encoding the painter ACTUALLY
#: draws. The previous text said "a third is a rim pip" and the rim pip has been
#: retired; a caption naming a mark that no longer exists is the failure mode
#: plan finding #56 logged, where two parts of one system disagree and the
#: reader builds from the stale one.
#:
#: MEASURED, because a caption that does not fit raises rather than shrinking (the caption
#: role is already at its 12 px legibility floor): the card is 320 px wide, the text slot
#: is 288 px, and these two lines measure 264.0 px and 283.6 px in the vendored font.
#: `test_dashboard_cells.py` pins that, so a reworded caption cannot silently overflow.
MINIMAP_CAPTION = (
    "Shared squares: the dot splits between up to four",
    "occupants. Colour is the code; grid view shows what.",
)

#: The identity pip's radius, as a share of the DOT's radius. Not a new mark and
#: not a new size -- it is the factor the painter already drew the pip at
#: (0.30 x cell x 0.34), named here because :func:`_pip_place` now has to check
#: it still fits inside one wedge rather than assume the whole dot.
IDENT_FRAC = 0.34


def _wedge_angles(n, i):
    """Wedge ``i`` of ``n``, in degrees, starting at 12 o'clock.

    ``n = 2`` reproduces the half-discs that shipped (90..270, 270..450) exactly,
    so the two-occupant encoding -- the one the controls already cover -- is
    unchanged by the generalisation to ``n = 1..4``.
    """
    step = 360.0 / n
    return 90.0 + i * step, 90.0 + (i + 1) * step


def _pip_place(n, i, r_dot):
    """Where the amber identity pip goes INSIDE its owner's wedge, and how big.

    At the square's centre the pip straddles every wedge, so on a shared square
    it eats the NEIGHBOUR's colour rather than annotating its own occupant --
    the latent defect plan section R22.1 found and mutation M-F4 reproduces. It
    is therefore placed at the centroid of its own circular sector,
    ``(2/3) R sin(a) / a`` from the centre at the sector's mid-angle, and its
    radius is clipped so it clears both bounding radii and the dot's rim. The
    clip never binds at :data:`IDENT_FRAC` = 0.34 for n = 1..4 (the tightest is
    n = 4, which allows 0.36); it is computed rather than asserted so the pip
    cannot silently become infeasible the way the retired rim pip did.
    """
    if n <= 1:
        return 0.0, 0.0, r_dot * IDENT_FRAC
    half = np.pi / n
    d = (2.0 / 3.0) * r_dot * np.sin(half) / half
    mid = np.radians(sum(_wedge_angles(n, i)) / 2.0)
    r = min(r_dot * IDENT_FRAC, 0.9 * d * np.sin(half), 0.9 * (r_dot - d))
    return d * np.cos(mid), d * np.sin(mid), r


def build_minimap(dash, ax, w, h):
    """The small world map: it answers WHERE, and the grid view answers WHAT.

    At this square size (18.4 px, measured) no shape survives, so colour IS a
    code here -- and the card says so in words rather than leaving a viewer to
    infer it (plan section R17.4). That exemption is earned by measurement
    rather than asserted: a mark big enough to be a SHAPE cannot be fitted
    beside the dot (R22.2's bound r_p <= 0.1016 x cell, whose colour core is
    4-7 px), and the two predator kinds' body colours differ by 15/255, which
    only an added colour accent can carry.

    THE ENCODING, as decided by plan section R22.3. One dot per square, divided
    between its occupants: one whole dot, two half-discs, three wedges at 120
    degrees, four at 90. The retired rim pip is gone -- it was infeasible by
    construction, since a pip outside the 0.30 x cell dot and inside the square
    must have r_p <= 0.1016 x cell while the painter drew 0.12, so it overlapped
    the dot it was specified to clear. Nothing is drawn outside the dot now, and
    the amber identity pip that tells a hiding predator from a predator sits in
    its OWN wedge. The ceiling is four kinds, matching the grid panel's four
    slots; CELL_PRIORITY decides, so the agent is never the one dropped.
    """
    from matplotlib.patches import Circle, Wedge

    m = dash.meta
    hh, ww = m["height"], m["width"]
    card_title(dash, ax, w, "World", f"{ww} × {hh}")
    # The caption is not decoration: this map encodes occupants as colour, and
    # the card has to SAY so (plan section R17.4). Its two lines are therefore
    # reserved out of the map's own size rather than drawn wherever they land --
    # a caption that falls off the bottom edge of its card is a layout defect.
    cap_h = 2 * CAPTION_LINE + PAD
    s = min(w - 2 * PAD, h - 46 - PAD - cap_h)
    cell = s / max(hh, ww)
    ox, oy = (w - cell * ww) / 2, 46

    # The map grid gets an Axes of its OWN, inside the card -- the same split the
    # arena already uses (`arena_card` / `arena`). A composite colour census can
    # only be taken per world square if the axes it is pointed at IS the grid;
    # pointed at the whole card it samples the title strip and the caption, and
    # the audit can then only report that its grid is unaligned. Everything below
    # is drawn in the grid's own coordinates, so square (r, c) is at
    # (c * cell, r * cell) with no offset to keep in step.
    gax = dash.grid_axes(ax, ox, oy, cell * ww, cell * hh, "minimap")

    grounds = {}
    for r in range(hh):
        for c in range(ww):
            grounds[(r, c)] = rrect(gax, c * cell + 1, r * cell + 1,
                                    cell - 2, cell - 2, 3, P.TRACK, z=1)
    tints = {}
    for r in range(hh):
        for c in range(ww):
            t = rrect(gax, c * cell + 1, r * cell + 1, cell - 2, cell - 2, 3,
                      P.TRACK, z=2, alpha=0.75)
            t.set_visible(False)
            tints[(r, c)] = t

    # A fixed pool per square: FOUR wedges (used as 2, 3 or 4), one whole dot and
    # one identity pip. There is no rim pip -- retired by plan section R22.3, and
    # nothing is drawn outside the dot any more.
    pool = {}
    for r in range(hh):
        for c in range(ww):
            cx, cy = (c + 0.5) * cell, (r + 0.5) * cell
            wedges = [gax.add_patch(Wedge((cx, cy), cell * 0.30, *_wedge_angles(2, i),
                                          fc=P.TRACK, ec=P.WHITE, lw=0.8 * PT,
                                          zorder=6 + i * 0.1))
                      for i in range(4)]
            dot = gax.add_patch(Circle((cx, cy), cell * 0.30, fc=P.TRACK, ec=P.WHITE,
                                       lw=1.2 * PT, zorder=6))
            ident = gax.add_patch(Circle((cx, cy), cell * 0.30 * IDENT_FRAC,
                                         fc=P.HIDE_EYE, lw=0, zorder=6.6))
            for a in (*wedges, dot, ident):
                a.set_visible(False)
            pool[(r, c)] = (wedges, dot, ident)

    dash.fit(ax, PAD, oy + cell * hh + CAPTION_LINE, "caption", w - 2 * PAD,
             numeric=False).set(MINIMAP_CAPTION[0])
    dash.fit(ax, PAD, oy + cell * hh + 2 * CAPTION_LINE, "caption", w - 2 * PAD,
             numeric=False).set(MINIMAP_CAPTION[1])

    def upd(v):
        for (r, c), g in grounds.items():
            g.set_facecolor(dash.ground_colour(r, c))
        for key, t in tints.items():
            occ = v.occupancy.get(key, ())
            ter = [n for n in occ if n in C.TERRAIN_NAMES]
            t.set_visible(bool(ter))
            if ter:
                t.set_facecolor(P.MINIMAP_COLOUR[ter[0]])
        for key, (wedges, dot, ident) in pool.items():
            occ = [n for n in v.occupancy.get(key, ()) if n not in C.TERRAIN_NAMES]
            occ = C.by_priority(occ)
            for a in (*wedges, dot, ident):
                a.set_visible(False)
            if not occ:
                continue
            # The ceiling is FOUR kinds, matching the grid panel's four slots
            # (plan section R22.3 item 6). CELL_PRIORITY orders them and the
            # agent is first, so a fifth kind -- which no episode of any matrix
            # cell produces -- drops the last by priority, never the agent.
            shown = occ[:4]
            n = len(shown)
            cy, cx = (key[0] + 0.5) * cell, (key[1] + 0.5) * cell
            if n == 1:
                dot.set_visible(True)
                dot.set_facecolor(P.MINIMAP_COLOUR[shown[0]])
            else:
                for i, (wg, nm) in enumerate(zip(wedges, shown)):
                    t1, t2 = _wedge_angles(n, i)
                    wg.set_theta1(t1)
                    wg.set_theta2(t2)
                    wg.set_facecolor(P.MINIMAP_COLOUR[nm])
                    wg.set_visible(True)
            # The amber identity pip tells a hiding predator from an ordinary
            # predator, whose body colours differ by 15/255 -- a distinction the
            # census can just barely make and a viewer at 18 px cannot make at
            # all. It annotates ONE mark, so it is drawn inside that mark: the
            # whole dot when the hiding predator is alone, its own wedge when the
            # square is shared. At the square's CENTRE, where it was first
            # written, it straddles every wedge and eats the neighbouring kind's
            # colour -- that is mutation M-F4, and it must fail the audit.
            if "hiding_predator" in shown:
                dx, dy, r_p = _pip_place(n, shown.index("hiding_predator"),
                                         cell * 0.30)
                ident.set_center((cx + dx, cy + dy))
                ident.set_radius(r_p)
                ident.set_visible(True)
    dash.updates.append(upd)


# --------------------------------------------------------------------------
# the arena -- the whole world, at 50 px a square
# --------------------------------------------------------------------------
def build_arena_chrome(dash, ax, w, h):
    """The arena card's title strip: the panel's name and the action pill."""
    m = dash.meta
    pill_w, pill_h = 118, 28
    px = w - PAD - pill_w
    rrect(ax, px, 12, pill_w, pill_h, 14, P.IRIS_SOFT, z=2)
    badge = dash.fit(ax, px + pill_w / 2, 31, "badge", pill_w - 16, ha="center")
    act_w = dash.fit(ax, px - 10, 30, "card_sub", 80, ha="right").set("Action")
    # The world's size goes in the TITLE, not in a right-aligned subtitle: the
    # right edge of this card's title strip already belongs to the action pill,
    # and a subtitle anchored there prints straight through it.
    card_title(dash, ax, w,
               f"Grid view · whole {m['width']} × {m['height']} world",
               reserve=pill_w + act_w + 10)

    def upd(v):
        if not v.action_name:
            badge.set("Start")
            return
        mark = C.ARROW_TEXT.get(v.action_name, _DOT)
        badge.set(f"{mark}  {v.action_name.title()}")
    dash.updates.append(upd)


def build_arena(dash, ax, w, h):
    """The whole world, one square per world square, at 50 px (decided Q20).

    There is no window and no panning: the world's origin is the panel's corner
    and the agent moves inside a fixed frame. Each square gets a fixed pool of
    artists -- a ground, a bed, four token slots and the agent's square outline --
    built once here and only ever updated.
    """
    m = dash.meta
    cell = dash.cell_px
    hh, ww = m["height"], m["width"]
    squares = {}
    for r in range(hh):
        for c in range(ww):
            cx, cy = (c + 0.5) * cell, (r + 0.5) * cell
            ground = rrect(ax, cx - cell / 2 + 1, cy - cell / 2 + 1, cell - 2, cell - 2,
                           8, P.TRACK, z=C.GROUND_Z)
            bed = _collection(ax, C.BED_Z)
            outline = rrect(ax, cx - cell / 2 + 2, cy - cell / 2 + 2, cell - 4, cell - 4,
                            7, "none", P.IRIS, 2, z=C.OUTLINE_Z)
            outline.set_visible(False)
            toks = [_collection(ax, C.TOKEN_Z + i * 0.01) for i in range(4)]
            squares[(r, c)] = (ground, bed, outline, toks)

    ax.set_xlim(0, ww * cell)
    ax.set_ylim(hh * cell, 0)

    def upd(v):
        for (r, c), (ground, bed, outline, toks) in squares.items():
            ground.set_facecolor(dash.ground_colour(r, c))
            occ = v.occupancy.get((r, c), ())
            bed_name, drawn = C.compose(occ, (c + 0.5) * cell, (r + 0.5) * cell,
                                        cell, action=v.action_name)
            _fill(bed, C.bed(bed_name, (c + 0.5) * cell, (r + 0.5) * cell, cell)
                  if bed_name else [])
            for i, coll in enumerate(toks):
                _fill(coll, drawn[i][1] if i < len(drawn) else [])
            outline.set_visible("agent" in occ)
    dash.updates.append(upd)


# --------------------------------------------------------------------------
# the right-hand pods
# --------------------------------------------------------------------------
def build_proprioception(dash, ax, w, h, action_names):
    card_title(dash, ax, w, "Proprioception", "previous action")
    gap = 8
    cw = (w - 2 * PAD - gap * (len(action_names) - 1)) / len(action_names)
    chips = []
    for k, nm in enumerate(action_names):
        x = PAD + k * (cw + gap)
        rect = rrect(ax, x, 52, cw, 32, 8, P.TRACK, z=2)
        t = dash.fit(ax, x + cw / 2, 73, "chip_on", cw - 8, ha="center")
        t.set(nm.title())
        chips.append((rect, t.t))

    def upd(v):
        vec = v.sense("Proprioception", "vector")
        hot = int(np.argmax(vec)) if vec is not None and float(np.max(vec)) > 0 else -1
        for k, (rect, t) in enumerate(chips):
            on = k == hot
            rect.set_facecolor(P.IRIS if on else P.TRACK)
            weight, _px, colour = dash.type_of("chip_on" if on else "chip")
            t.set_color(colour)
            t.set_fontweight(weight)
    dash.updates.append(upd)


def build_intensity(dash, ax, w, h, title, sense, colour, real):
    card_title(dash, ax, w, title)
    val = dash.fit(ax, PAD, h - 58, "hero", (w - 2 * PAD) * 0.6)
    set_v = bar(ax, PAD, h - 38, w - 2 * PAD, 8, colour)
    set_t = None
    if real:
        dash.fit(ax, w - PAD, h - 62, "caption", (w - 2 * PAD) * 0.4, ha="right").set(
            "noise-free")
        real_val = dash.fit(ax, w - PAD, h - 44, "value", (w - 2 * PAD) * 0.4, ha="right")
        set_t = tick(ax, PAD, h - 38, 8)

    def upd(v):
        q = float(v.sense(sense, "intensity"))
        val.set(f"{q:.2f}")
        set_v(q)
        if set_t is not None:
            t = float(v.sense(sense, "true_intensity"))
            real_val.set(f"{t:.2f}")
            set_t(PAD + (w - 2 * PAD) * min(1.0, max(0.0, t)))
    dash.updates.append(upd)


#: Baseline-to-baseline pitch of a named channel row, per sense. Olfaction has
#: five channels and vision eight, so vision's rows are a little tighter; both
#: are two columns.
CHANNEL_ROW_PITCH = {"Olfaction": 40, "Visual": 38}
CHANNEL_BAR_H = 6


def _ramp(stops, label="ramp"):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(label, list(stops))


def build_channel_rows(dash, ax, w, h, sense, title, codes, colour_stops):
    """A sense read at range 0: one NAMED row per channel, with its number.

    WHAT THIS REPLACES, AND WHY IT IS NOT A RESTYLE. The shipped panel drew one
    coloured swatch per channel under a four-letter code -- ``FOOD AN-A AN-B BUSH
    TREE`` -- so the reader was given a shade, a code and no value: three of the
    five channels were indistinguishable pale blocks, and no number appeared
    anywhere. A row carries the channel's real name, the qualifier that makes the
    two shared animal odours mean anything, and the reading itself. The bar
    stays, because a column of numbers alone is hard to compare at video speed.

    Range 0 means the sense reads exactly one square -- the one the agent is
    standing in -- so the card says that in words instead of printing
    ``range 0``, which is an index a viewer has no way to interpret.
    """
    cmap = _ramp(colour_stops, sense)
    card_title(dash, ax, w, title, "the agent's own square")
    names = [channel_display(sense, c) for c in codes]

    n = len(names)
    cols = 2
    per_col = (n + cols - 1) // cols
    pitch = CHANNEL_ROW_PITCH[sense]
    gap = 24
    cw = (w - 2 * PAD - gap * (cols - 1)) / cols
    top = 64

    setters = []
    for i, (name, qualifier) in enumerate(names):
        col, row = divmod(i, per_col)
        x = PAD + col * (cw + gap)
        y = top + row * pitch
        # The value is measured first and its width reserved, so a long channel
        # name is shrunk into what is left rather than colliding with its number.
        val = dash.fit(ax, x + cw, y, "value", cw * 0.32, ha="right")
        used = dash.width("0.00", "value") + 10
        name_w = dash.fit(ax, x, y, "row_label", cw - used).set(name)
        if qualifier:
            dash.fit(ax, x + name_w + 8, y, "caption",
                     max(8.0, cw - used - name_w - 8)).set(qualifier)
        rrect(ax, x, y + 8, cw, CHANNEL_BAR_H, CHANNEL_BAR_H / 2, P.TRACK, z=2)
        fill = rrect(ax, x, y + 8, CHANNEL_BAR_H, CHANNEL_BAR_H,
                     CHANNEL_BAR_H / 2, cmap(0.75), z=3)
        setters.append((val, fill, cw))

    foot = top + per_col * pitch + 4
    if foot + 14 <= h - 8:
        dash.fit(ax, PAD, foot + 12, "caption", w - 2 * PAD, numeric=False).set(
            "Scale 0 … episode maximum, shared by every step of this episode")

    def upd(v):
        vec = np.asarray(v.sense(sense, "vector"), dtype=float)
        vmax = max(float(dash.sense_max.get(dash.viz_name(sense), 1.0)), 1e-6)
        for (val, fill, bar_w), q in zip(setters, vec):
            q = float(q)
            val.set(f"{q:.2f}")
            frac = min(1.0, max(0.0, q / vmax))
            # A non-zero reading is never thinner than the bar is tall, so a
            # small value stays visible as a dot instead of vanishing.
            fill.set_visible(frac > 1e-6)
            fill.set_width(max(CHANNEL_BAR_H, bar_w * frac))
            fill.set_facecolor(cmap(0.25 + 0.75 * frac))
    dash.updates.append(upd)


def build_channel_maps(dash, ax, w, h, sense, title, codes, colour_stops,
                       offsets, sensor_range):
    """A sense read over a diamond of squares: one small map per channel.

    THE PANEL THE SHIPPED RENDERER HAD NO BUILDER FOR AT ALL. A world whose smell
    or sight reaches past its own square declares a ``channel_maps`` panel, the
    registry places a box for it, and nothing drew into it -- which is why the
    one verification world with smell at range 1 reported its Olfaction panel as
    missing. This is that builder.

    Each channel gets the Manhattan diamond the sensor actually reads, in the
    sensor's own offset order, with the agent's own square outlined in the agent
    colour and the channel's reader-facing name under it.
    """
    cmap = _ramp(colour_stops, sense)
    names = [channel_display(sense, c) for c in codes]
    k = 2 * int(sensor_range) + 1

    # Header: the sense, how far it reaches in words, and the ramp it is read on.
    tw = dash.fit(ax, PAD, TITLE_BASE, "card_title", w / 2).set(title)
    reach = ("the agent's own square and its four neighbours" if sensor_range == 1
             else f"{k} × {k} diamond around the agent")
    dash.fit(ax, PAD + tw + 10, TITLE_BASE, "card_sub", w - PAD - tw - 10).set(reach)

    n = len(names)
    gap = 8
    slot = (w - 2 * PAD - gap * (n - 1)) / n
    box = min(slot, h - 58 - 34)
    cs = box / k
    if cs < 10:
        raise LayoutOverflowError(
            f"{title} at range {sensor_range}: its map squares would be {cs:.1f}px "
            f"across (floor 10px). The panel refuses to draw an unreadable map "
            f"rather than shrinking one."
        )
    top = 58
    cells = []
    for i, (name, qualifier) in enumerate(names):
        x0 = PAD + i * (slot + gap) + (slot - box) / 2
        mine = []
        for dr, dc in offsets:
            cx = x0 + (dc + sensor_range) * cs
            cy = top + (dr + sensor_range) * cs
            mine.append(rrect(ax, cx + 1.5, cy + 1.5, cs - 3, cs - 3, 3, P.TRACK, z=2))
        # the agent's own square, outlined in the agent's colour
        rrect(ax, x0 + sensor_range * cs + 0.5, top + sensor_range * cs + 0.5,
              cs - 1, cs - 1, 3, "none", P.IRIS, 2, z=3)
        label_y = top + box + 18
        dash.fit(ax, x0 + box / 2, label_y, "map_label", slot + gap,
                 ha="center").set(name)
        if qualifier:
            dash.fit(ax, x0 + box / 2, label_y + 15, "caption", slot + gap,
                     ha="center").set(qualifier)
        cells.append(mine)

    def upd(v):
        vec = np.asarray(v.sense(sense, "vector"), dtype=float).reshape(-1, n)
        vmax = max(float(dash.sense_max.get(dash.viz_name(sense), 1.0)), 1e-6)
        for i, mine in enumerate(cells):
            for patch, q in zip(mine, vec[:, i]):
                frac = min(1.0, max(0.0, float(q) / vmax))
                patch.set_facecolor(P.TRACK if frac <= 1e-6
                                    else cmap(0.25 + 0.75 * frac))
    dash.updates.append(upd)


def build_cross_bars(dash, ax, w, h, sense, title, offsets, letters):
    """Collision at range 1: the five squares the agent can touch.

    THE ONE PLACE SHORT CODES SURVIVE. C/U/R/D/L name POSITIONS rather than
    entities, they have to fit inside a 30 px square, and the diamond they are
    arranged in already shows what each one means. They are glossed in the card's
    own subtitle so the frame carries its own key -- which is exactly what the
    sense panels' four-letter channel codes did not.
    """
    card_title(dash, ax, w, title)
    # 22 px cells, not the 30 this card used to draw. The gloss below needs a
    # line of its own, and the card is 150 px tall, so the diamond has to give
    # the room up. MEASURED, twice: at 30 px the title strip and the diamond
    # leave 6 px, which is not a caption; at 26 px the caption's cap-height
    # crossed the bottom cell by ~7 px, which the frame shows as a line struck
    # through the word "right" whenever that cell is a hit. At 22 px the diamond
    # is 3 x 22 + 2 x 4 = 74 px, its bottom cell ends at 126, and the caption's
    # tallest glyph starts at 131.
    c, g = 22, 4
    ccx, ccy = w / 2, 52 + 1.5 * c + g
    cellsx = []
    for (dr, dc), lab in zip(offsets, letters):
        x, y = ccx + dc * (c + g) - c / 2, ccy + dr * (c + g) - c / 2
        rect = rrect(ax, x, y, c, c, 6, P.TRACK, z=2)
        t = dash.fit(ax, x + c / 2, y + c / 2 + 1, "coll_letter", c - 4,
                     ha="center", va="center")
        t.set(lab)
        cellsx.append((rect, t.t))
    dash.fit(ax, w / 2, h - 10, "caption", w - 2 * PAD, ha="center",
             numeric=False).set("centre, up, right, down, left")

    def upd(v):
        for (rect, t), q in zip(cellsx, np.asarray(v.sense(sense, "vector"), dtype=float)):
            hit = float(q) > 0.5
            rect.set_facecolor(P.NOCI if hit else P.TRACK)
            t.set_color(P.WHITE if hit else P.INK3)
    dash.updates.append(upd)


def build_thermoception(dash, ax, w, h, offsets):
    """The heat sense, plus the temperature scale the whole frame shares.

    The diamond reads **cell minus body**; the arena's squares and the body row
    read absolute temperature. Same colours, one legend, stated on the card --
    there is exactly one temperature legend per frame and CP-C checks it.
    """
    from matplotlib.patches import Polygon

    sc = dash.scale
    sensed = dash.has("Thermoception")
    if sensed:
        card_title(dash, ax, w, "Thermoception", "cell minus body, °")
        tc, g = 46, 4
        tcx, tcy = PAD + 1.5 * tc + g, 56 + 1.5 * tc + g
        cellsx = []
        for dr, dc in offsets:
            x, y = tcx + dc * (tc + g) - tc / 2, tcy + dr * (tc + g) - tc / 2
            rect = rrect(ax, x, y, tc, tc, 8, P.TRACK, z=2)
            cellsx.append((rect, dash.fit(ax, x + tc / 2, y + tc / 2 + 1, "cell_num",
                                          tc - 6, ha="center", va="center")))

        def upd(v):
            for (rect, t), q in zip(cellsx, np.asarray(v.sense("Thermoception", "vector"),
                                                       dtype=float)):
                col = sc.colour(float(q))
                rect.set_facecolor(col)
                clipped = sc.out_of_range(float(q))
                rect.set_edgecolor(P.INK if clipped else "none")
                rect.set_linewidth(2 * PT if clipped else 0)
                t.set(signed(float(q)))
                t.t.set_color(P.WHITE if _luminance(col) < 0.45 else P.INK)
        dash.updates.append(upd)
        lx0 = tcx + 1.5 * tc + g + 36
    else:
        card_title(dash, ax, w, "Temperature scale")
        lx0 = PAD + 12

    lw = w - lx0 - 22
    ly = 96
    dash.fit(ax, lx0, 66, "caption_medium", lw, numeric=False, color=P.INK2).set(
        "Scale shared by every step of this episode")
    gradient(ax, lx0, ly, lw, 12, sc.cmap(np.linspace(0, 1, 512)), z=2)
    ax.add_patch(Polygon([(lx0, ly), (lx0 - 9, ly + 6), (lx0, ly + 12)],
                         fc=sc.cmap(0.0), lw=0, zorder=2))
    ax.add_patch(Polygon([(lx0 + lw, ly), (lx0 + lw + 9, ly + 6), (lx0 + lw, ly + 12)],
                         fc=sc.cmap(1.0), lw=0, zorder=2))

    def xpos(q):
        return lx0 + lw * sc.pos(q)

    placed = []
    anchors = dict(sc.anchors)
    for _name, q in sc.anchors:
        ax.plot([xpos(q)] * 2, [ly + 12, ly + 17], color=P.INK3, lw=1 * PT, zorder=3)
    for name in ("setpoint", "lower body limit", "upper body limit",
                 "episode min", "episode max"):
        if name not in anchors:
            continue
        q = anchors[name]
        t = text(ax, xpos(q), ly + 32,
                 signed(q, 0 if float(q).is_integer() else 1), "caption", ha="center")
        bb = t.get_window_extent(dash.renderer)
        if any(bb.x0 < o.x1 + 8 and o.x0 < bb.x1 + 8 for o in placed):
            t.remove()
        else:
            placed.append(bb)
    xa, xb = xpos(sc.low), xpos(sc.high)
    ax.plot([xa, xa, xb, xb], [ly + 40, ly + 45, ly + 45, ly + 40],
            color=P.INK2, lw=1.2 * PT, zorder=3)
    dash.fit(ax, (xa + xb) / 2, ly + 62, "caption_medium", lw + 40, ha="center",
             numeric=False, color=P.INK2).set("survivable body range")
    for i, line in enumerate((
            "Grid squares and body temperature: absolute.",
            "Thermoception: cell minus body.",
            f"Same colours; {signed(sc.sp)} is neutral.")):
        dash.fit(ax, lx0, ly + 86 + 16 * i, "caption", w - lx0 - PAD,
                 numeric=False).set(line)

    tri = ax.add_patch(Polygon([(0, 0), (0, 0), (0, 0)], fc=P.INK, lw=0, zorder=4))
    # Clear of the strip, not merely on top of it. The live renderer's own D13 is
    # a temperature label the colour strip paints over, so a label that merely
    # wins on draw order against this strip is the same arrangement one z-order
    # change away from the same bug.
    body = text(ax, 0, ly - 14, "body", "caption_medium", color=P.INK)

    def upd_body(v):
        x = xpos(v.body_temp)
        tri.set_xy([(x, ly - 2), (x - 6, ly - 11), (x + 6, ly - 11)])
        right = x < lx0 + 0.75 * lw
        body.set_x(x + 9 if right else x - 9)
        body.set_ha("left" if right else "right")
    dash.updates.append(upd_body)


def build_text_row(dash, ax, w, h, sense, title):
    lab = dash.fit(ax, PAD, h / 2 + 5, "row_label", w - 2 * PAD)

    def upd(v):
        lab.set(f"{title}  {v.sense(sense, 'value_text')}")
    dash.updates.append(upd)


def _luminance(rgb):
    from matplotlib.colors import to_rgb
    r, g, b = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
               for c in to_rgb(rgb[:3] if len(rgb) == 4 else rgb)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
