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
        im.set_data(C.icon_array(r.name, r.px_w, r.px_h, r.action))
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
    # "Observed" -- the approved design's own word, restored 2026-09-17.
    #
    # It had been changed to "Sensed" to get around an audit rule: any rendered
    # text beginning "OBS" must belong to a panel whose modality is in the
    # observation breakdown, and a column head spanning five rows belongs to no
    # single modality, so it could never satisfy that rule. The word was the
    # wrong thing to move. The rule exists to catch a VALUE captioned as observed
    # when it is not (the live defect D10), and a column head captions no value,
    # so the rule is what was over-scoped -- it now requires the caption to carry
    # a number (see `render_layout_audit.audit_frame`). D10 still fires, because
    # the caption it fires on reads "OBS:  0.65".
    dash.fit(ax, xs[0], 66, "col_head", cw).set("Observed")
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
#: Which entity a resource slot's type index names. The environment's own order,
#: and the same one `episode.occupancy_of` reads.
RES_NAMES = ("food", "hiding_predator")


def build_minimap(dash, ax, w, h):
    """The whole world, and the box showing where the grid view is looking.

    WHAT THIS PANEL IS FOR, AND WHY IT EARNS ITS PLACE. The grid view beside it
    draws a WINDOW -- `visualization.local_view_size` squares centred on the
    agent -- so on any world bigger than that window the grid alone cannot tell a
    viewer where the agent is in the world, nor what is off screen. This map
    answers exactly that: it draws every square of the world, every entity in it,
    and an outlined box around the part the grid view is showing. It is the
    approved design's own answer (`fig03_proposed_dashboard.py::b_minimap`) and
    it is restored here together with the window.

    WHAT IT REPLACES (2026-09-17). Between Revisions 22 and 23 this panel encoded
    a shared square as a DOT SPLIT INTO WEDGES -- halves, thirds, quarters -- with
    an amber pip to tell a hiding predator from a predator. That encoding was
    built for a whole-world grid view that no longer exists: it was the map's
    attempt to answer "what is in this square?", which was needed when the grid
    beside it was drawing 100 squares at 50 px and the map was the only place a
    reader could see the whole world at once. With the window restored, the grid
    view answers "what" at 96 px a square and this map answers "where". One mark
    per entity, at its own square, is what the approved design draws, and the
    wedges, the split dot and the caption explaining them are withdrawn with it.
    """
    from matplotlib.patches import Circle

    from ..state import select_by_class

    m = dash.meta
    hh, ww = m["height"], m["width"]
    params = dash.params
    card_title(dash, ax, w, "World", f"{ww} × {hh}")
    s = min(w - 2 * PAD, h - 46 - PAD)
    cell = s / max(hh, ww)
    ox, oy = (w - cell * ww) / 2, 46

    # The map grid gets an Axes of its OWN, inside the card -- the same split the
    # arena uses. Everything below is drawn in the grid's own coordinates, so
    # square (r, c) is at (c * cell, r * cell) with no offset to keep in step.
    gax = dash.grid_axes(ax, ox, oy, cell * ww, cell * hh, "minimap")

    grounds = {}
    for r in range(hh):
        for c in range(ww):
            grounds[(r, c)] = rrect(gax, c * cell + 1, r * cell + 1,
                                    cell - 2, cell - 2, 3, P.TRACK, z=1,
                                    alpha=0.75 if dash.scale is not None else None)

    obs_names = list(params.obstacle_names)
    obs_type = [int(t) for t in np.asarray(params.obs_type)]
    obs = [rrect(gax, 0, 0, cell * 0.56, cell * 0.56, 2,
                 P.MINIMAP_COLOUR[obs_names[t]], z=3) for t in obs_type]
    cores = [gax.add_patch(Circle((0, 0), cell * 0.12, fc=P.FIRE_CORE, lw=0,
                                  zorder=3.5))
             if obs_names[t] == "campfire" else None for t in obs_type]
    res_type = [int(t) for t in np.asarray(params.res_type)]
    res = [gax.add_patch(Circle((0, 0), cell * 0.24, fc=P.MINIMAP_COLOUR[RES_NAMES[t]],
                                ec=P.WHITE, lw=1.2 * PT, zorder=4))
           for t in res_type]
    # the hiding predator's amber pip, echoing its glyph's spike tips, so it is
    # not read as an ordinary predator's dot
    pips = [gax.add_patch(Circle((0, 0), cell * 0.24 * 0.34, fc=P.HIDE_EYE, lw=0,
                                 zorder=4.5))
            if RES_NAMES[t] == "hiding_predator" else None for t in res_type]
    is_pred = [bool(x) for x in np.asarray(select_by_class(params, "predator"))]
    ani = [gax.add_patch(Circle((0, 0), cell * 0.26,
                                fc=P.MINIMAP_COLOUR["predator" if p else "neutral"],
                                ec=P.WHITE, lw=1.2 * PT, zorder=4))
           for p in is_pred]
    agent = gax.add_patch(Circle((0, 0), cell * 0.32, fc=P.IRIS, ec=P.WHITE,
                                 lw=2 * PT, zorder=6))
    n_view = int(dash.layout.view_cells)
    view = rrect(gax, 0, 0, n_view * cell + 2, n_view * cell + 2, 6, "none",
                 P.IRIS, 2.2, z=7)

    def inside(p):
        return 0 <= int(p[0]) < hh and 0 <= int(p[1]) < ww

    def centre(p):
        return (int(p[1]) + 0.5) * cell, (int(p[0]) + 0.5) * cell

    def upd(v):
        st = v.state
        for (r, c), g in grounds.items():
            g.set_facecolor(dash.ground_colour(r, c))
        for p, core, pos in zip(obs, cores, np.asarray(st.obs_pos)):
            p.set_visible(inside(pos))
            cx, cy = centre(pos)
            p.set_x(cx - cell * 0.28)
            p.set_y(cy - cell * 0.28)
            if core is not None:
                core.set_visible(inside(pos))
                core.set_center((cx, cy))
        active = np.asarray(st.res_active)
        for i, (p, pip, pos) in enumerate(zip(res, pips, np.asarray(st.res_pos))):
            on = bool(active[i]) and inside(pos)
            for q in (p, pip):
                if q is not None:
                    q.set_visible(on)
                    q.set_center(centre(pos))
        for p, pos in zip(ani, np.asarray(st.animal_pos)):
            p.set_visible(inside(pos))
            p.set_center(centre(pos))
        agent.set_center(centre(np.asarray(st.agent_pos)))
        r0, c0 = dash.view_origin(v)
        view.set_x(c0 * cell - 1)
        view.set_y(r0 * cell - 1)
    dash.updates.append(upd)


# --------------------------------------------------------------------------
# the arena -- a window of the world, in a fixed box
# --------------------------------------------------------------------------
def build_arena_chrome(dash, ax, w, h):
    """The arena card's title strip: the panel's name and the action pill.

    The title is the approved design's: "Grid view", and nothing else. How much
    of the world is on screen is said once, in the header's own meta line
    ("5 × 5 view of a 10 × 10 world"), rather than twice.
    """
    pill_w, pill_h = 118, 28
    px = w - PAD - pill_w
    rrect(ax, px, 12, pill_w, pill_h, 14, P.IRIS_SOFT, z=2)
    badge = dash.fit(ax, px + pill_w / 2, 31, "badge", pill_w - 16, ha="center")
    act_w = dash.fit(ax, px - 10, 30, "card_sub", 80, ha="right").set("Action")
    card_title(dash, ax, w, "Grid view", reserve=pill_w + act_w + 10)

    def upd(v):
        if not v.action_name:
            badge.set("Start")
            return
        mark = C.ARROW_TEXT.get(v.action_name, _DOT)
        badge.set(f"{mark}  {v.action_name.title()}")
    dash.updates.append(upd)


def build_arena(dash, ax, w, h):
    """A window of the world, centred on the agent, in a fixed-size box.

    THE CONFIG DECIDES WHAT IS DRAWN. `visualization.local_view_size` squares are
    drawn across (at least `2 * max_sense_range + 1`, so the view always covers
    what the agent can sense), the window is centred on the agent and clamped to
    the world's edges, and the square size follows from the arena's fixed 480 px
    box: 96 px at a 5-wide window, 48 px at a 10-wide one. A world no larger than
    the window is drawn whole, which is the special case rather than the rule.

    Each screen slot owns a fixed pool of artists -- a ground and four token
    slots -- built once here and only ever updated. The slot at screen position
    (i, j) shows a DIFFERENT world square as the agent moves, which is what
    panning is; nothing is created or destroyed per frame.
    """
    n = int(dash.layout.view_cells)
    cell = float(dash.cell_px)
    hh, ww = dash.meta["height"], dash.meta["width"]
    squares = []
    for i in range(n):
        for j in range(n):
            cx, cy = (j + 0.5) * cell, (i + 0.5) * cell
            ground = rrect(ax, cx - cell / 2 + 1, cy - cell / 2 + 1,
                           cell - 2, cell - 2, 8, P.TRACK, z=C.GROUND_Z)
            toks = [_collection(ax, C.TOKEN_Z + k * 0.01) for k in range(C.MAX_SLOTS)]
            squares.append((i, j, ground, toks))

    ax.set_xlim(0, n * cell)
    ax.set_ylim(n * cell, 0)

    def upd(v):
        r0, c0 = dash.view_origin(v)
        # What the grid view is SHOWING, declared on the axes so the pixel audit
        # can divide this panel into the right world squares instead of assuming
        # it holds the whole world. Read by `render_layout_audit.arena_view`.
        ax._world_view = (int(r0), int(c0), n, n)
        for (i, j, ground, toks) in squares:
            r, c = r0 + i, c0 + j
            off = not (0 <= r < hh and 0 <= c < ww)
            ground.set_facecolor(P.OFF_WORLD if off else dash.ground_colour(r, c))
            occ = () if off else v.occupancy.get((r, c), ())
            drawn = C.compose(occ, (j + 0.5) * cell, (i + 0.5) * cell, cell,
                              action=v.action_name)
            for k, coll in enumerate(toks):
                _fill(coll, drawn[k][1] if k < len(drawn) else [])
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

#: The sensor band's own spacing, from the approved sketch's `b_band`: the gap
#: between two maps, the gap between the two senses, and the width of the ramp
#: drawn beside a sense's title.
MAP_GAP = 6
BAND_DIVIDER = 32
RAMP_W = 96


def _ramp(stops, label="ramp"):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(label, list(stops))


def band_head(dash, ax, x0, w, sense, title, cmap, vmax):
    """A sense's line in the band: its name, how far it reaches, and its ramp.

    The approved design puts the colour key IN the band's header rather than in a
    caption under it -- "Olfaction  range 1   0 [ramp] 2.4" -- so a reader can
    read a map's colour without leaving the panel. Returns the width used.
    """
    tw = dash.fit(ax, x0, TITLE_BASE, "card_title", w / 2).set(title)
    # The reach gets a real slot rather than a round number: at range 0 it is a
    # phrase ("the agent's own square", 135 px measured) because "range 0" is an
    # index a viewer cannot interpret, and at range >= 1 it is the sketch's own
    # "range N", because the diamond maps underneath already show the shape.
    rng = dash.fit(ax, x0 + tw + 8, TITLE_BASE, "card_sub", w * 0.45).set(sense["reach"])
    zx = x0 + tw + 8 + rng + 16
    zw = dash.fit(ax, zx, TITLE_BASE, "caption", 24).set("0")
    sx = zx + zw + 6
    gradient(ax, sx, TITLE_BASE - 8, RAMP_W, 8, cmap(np.linspace(0, 1, 128)), z=2)
    mw = dash.fit(ax, sx + RAMP_W + 6, TITLE_BASE, "caption", 48).set(f"{vmax:.1f}")
    return sx + RAMP_W + 6 + mw - x0


def build_channel_rows(dash, ax, x0, w, h, sense, title, codes, colour_stops):
    """A sense read at range 0: one NAMED row per channel, with its number.

    THE ONE PANEL THE APPROVED MOCK DOES NOT SHOW, and it is drawn this way for a
    reason the mock could not answer: the sketch overrode its sensor ranges so
    that both senses reach past the agent's own square, and it raises outright on
    a sense at range 0. Every maintained world but one reads both senses at range
    ZERO, i.e. one square, so a diamond map would be a single tile per channel --
    a map of one place. A labelled row carries the channel's real name and its
    reading instead.
    """
    cmap = _ramp(colour_stops, sense)
    vmax = max(float(dash.sense_max.get(dash.viz_name(sense), 1.0)), 1e-6)
    band_head(dash, ax, x0, w, {"reach": "the agent's own square"}, title, cmap, vmax)
    names = [channel_display(sense, c) for c in codes]

    n = len(names)
    cols = 2
    per_col = (n + cols - 1) // cols
    pitch = CHANNEL_ROW_PITCH[sense]
    gap = 24
    cw = (w - gap * (cols - 1)) / cols
    top = 64

    setters = []
    for i, (name, qualifier) in enumerate(names):
        col, row = divmod(i, per_col)
        x = x0 + col * (cw + gap)
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

    def upd(v):
        vec = np.asarray(v.sense(sense, "vector"), dtype=float)
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


#: The three visual channels that are one thing seen three ways. A square is
#: grass OR sand OR plain, never two, so the approved design draws them as a
#: single "Terrain" map in three flat colours instead of three maps that are
#: empty wherever the other two are not.
TERRAIN_CHANNELS = ("GRS", "SND", "PLN")


def _map_plan(sense, codes):
    """Which maps a sense draws: ``[(name, qualifier, kind, channel), ...]``.

    One map per channel, except that vision's three terrain channels become a
    single categorical map (the sketch's own arrangement). The composite applies
    only when the vector really is the standard 8 channels in the standard order;
    any other width gets one map per channel, because a composite keyed by index
    is a lie as soon as the layout changes -- the same scope rule
    ``labels.visual_labels`` already follows.
    """
    out = []
    composite = sense == "Visual" and tuple(codes[:3]) == TERRAIN_CHANNELS
    if composite:
        out.append(("Terrain", "", "terrain", None))
    for i, code in enumerate(codes):
        if composite and i < 3:
            continue
        name, qualifier = channel_display(sense, code)
        out.append((name, qualifier, "seq", i))
    return out


def build_channel_maps(dash, ax, x0, w, h, sense, title, codes, colour_stops,
                       offsets, sensor_range):
    """A sense read over a diamond of squares: one small map per channel.

    THE PANEL THE APPROVED DESIGN IS DRAWN AROUND. Each channel gets the
    Manhattan diamond the sensor actually reads, in the sensor's own offset
    order, with the agent's own square outlined in the agent colour and the
    channel's reader-facing name under it.
    """
    cmap = _ramp(colour_stops, sense)
    vmax = max(float(dash.sense_max.get(dash.viz_name(sense), 1.0)), 1e-6)
    band_head(dash, ax, x0, w, {"reach": f"range {sensor_range}"}, title, cmap, vmax)

    n_ch = len(codes)
    maps = _map_plan(sense, codes)
    k = 2 * int(sensor_range) + 1
    n = len(maps)
    slot = (w - MAP_GAP * (n - 1)) / n
    box = min(slot, h - 58 - 40)
    cs = box / k
    if cs < 10:
        raise LayoutOverflowError(
            f"{title} at range {sensor_range}: its map squares would be {cs:.1f}px "
            f"across (floor 10px). The panel refuses to draw an unreadable map "
            f"rather than shrinking one."
        )
    top = 58
    cells = []
    for i, (name, qualifier, kind, ch) in enumerate(maps):
        bx = x0 + i * (slot + MAP_GAP) + (slot - box) / 2
        mine = []
        for dr, dc in offsets:
            cx = bx + (dc + sensor_range) * cs
            cy = top + (dr + sensor_range) * cs
            mine.append(rrect(ax, cx + 1.5, cy + 1.5, cs - 3, cs - 3, 3, P.TRACK, z=2))
        # the agent's own square, outlined in the agent's colour
        rrect(ax, bx + sensor_range * cs + 0.5, top + sensor_range * cs + 0.5,
              cs - 1, cs - 1, 3, "none", P.IRIS, 2, z=3)
        label_y = top + box + 20
        # A label too wide for its own map WRAPS at its first space, exactly as
        # the approved sketch does it ("Hiding predator" over two lines). It is a
        # numeric kind, so the fitter would otherwise raise rather than shrink --
        # correctly: the alternative is a channel name a viewer cannot read.
        lines = [name]
        if dash.width(name, "map_label") > slot - 4 and " " in name:
            lines = list(name.split(" ", 1))
        for li, line in enumerate(lines):
            dash.fit(ax, bx + box / 2, label_y + li * 15, "map_label", slot + MAP_GAP,
                     ha="center").set(line)
        if qualifier:
            dash.fit(ax, bx + box / 2, label_y + len(lines) * 15, "caption",
                     slot + MAP_GAP, ha="center").set(qualifier)
        cells.append((kind, ch, mine))

    def upd(v):
        vec = np.asarray(v.sense(sense, "vector"), dtype=float).reshape(-1, n_ch)
        for kind, ch, mine in cells:
            for patch, row in zip(mine, vec):
                if kind == "terrain":
                    # Grass / sand / plain are mutually exclusive, so the three
                    # channels are ONE map in three flat colours rather than three
                    # near-empty maps. A square reading zero on all three is
                    # outside the world, and is drawn as such rather than as a
                    # terrain the agent cannot see.
                    off = float(np.max(row[:3])) <= 0
                    patch.set_facecolor(P.OFF_WORLD if off
                                        else P.TERRAIN_FILL[int(np.argmax(row[:3]))])
                    patch.set_edgecolor(P.OUTLINE if off else "none")
                    patch.set_linewidth(1 * PT)
                else:
                    frac = min(1.0, max(0.0, float(row[ch]) / vmax))
                    patch.set_facecolor(P.TRACK if frac <= 1e-6
                                        else cmap(0.25 + 0.75 * frac))
    dash.updates.append(upd)


def band_divider(ax, x, h):
    """The hairline between the two senses of the band -- the mock's own rule."""
    ax.plot([x, x], [PAD, h - PAD], color=P.LINE, lw=1 * PT, zorder=2)


def build_cross_bars(dash, ax, w, h, sense, title, offsets, letters):
    """Collision at range 1: the five squares the agent can touch.

    THE MOCK'S OWN GEOMETRY (restored 2026-09-17). 30 px cells, bottom-anchored,
    and no gloss line under them. The gloss this removes ("centre, up, right,
    down, left") was added so the C/U/R/D/L codes would carry their own key, and
    it cost the diamond 8 px a cell to make room; the approved design does not
    have it, and the mock wins where the two disagree. The letters name POSITIONS
    rather than entities and the diamond they sit in already shows what each one
    means, which is why this is the one place short codes survive at all.
    """
    card_title(dash, ax, w, title)
    c, g = 30, 4
    ccx, ccy = w / 2, h - PAD - 1.5 * c - g
    cellsx = []
    for (dr, dc), lab in zip(offsets, letters):
        x, y = ccx + dc * (c + g) - c / 2, ccy + dr * (c + g) - c / 2
        rect = rrect(ax, x, y, c, c, 6, P.TRACK, z=2)
        t = dash.fit(ax, x + c / 2, y + c / 2 + 1, "coll_letter", c - 4,
                     ha="center", va="center")
        t.set(lab)
        cellsx.append((rect, t.t))

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
