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
from .labels import channel_labels
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


def _collection(ax, z):
    """An empty artist that will carry one compound form (a bed or a token).

    ONE artist per form is a requirement, not a tidiness choice: the pixel audit
    separates the square's floor from its occupants by measuring ink AREA, so a
    bed split across six artists would have its small parts counted as an
    occupant (plan section R20.8).
    """
    coll = PatchCollection([], match_original=False, zorder=z)
    ax.add_collection(coll)
    coll.set_transform(ax.transData)
    coll.set_visible(False)
    return coll


def _fill(coll, shapes):
    """Put a compound form into its artist, or hide it when there is none."""
    if not shapes:
        coll.set_visible(False)
        return
    coll.set_paths([s.patch for s in shapes])
    coll.set_facecolor([s.fc for s in shapes])
    coll.set_edgecolor([s.ec for s in shapes])
    coll.set_linewidth([s.lw * PT for s in shapes])
    coll.set_visible(True)


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
def build_minimap(dash, ax, w, h):
    """The small world map: it answers WHERE, and the grid view answers WHAT.

    At this square size (about 24-29 px) no shape survives, so colour IS a code
    here -- and the card says so in words rather than leaving a viewer to infer
    it (plan section R17.4). Two occupants split one dot into halves; a third
    becomes a pip on the square's rim, kept outside the dot so it can never be
    confused with the amber identity pip that marks a hiding predator.
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

    # A fixed pool per square: two half-discs, one whole dot, one rim pip.
    pool = {}
    for r in range(hh):
        for c in range(ww):
            cx, cy = (c + 0.5) * cell, (r + 0.5) * cell
            wedges = [gax.add_patch(Wedge((cx, cy), cell * 0.30, 90 + i * 180,
                                          90 + (i + 1) * 180, fc=P.TRACK, ec=P.WHITE,
                                          lw=0.8 * PT, zorder=6 + i * 0.1))
                      for i in range(2)]
            dot = gax.add_patch(Circle((cx, cy), cell * 0.30, fc=P.TRACK, ec=P.WHITE,
                                       lw=1.2 * PT, zorder=6))
            pip = gax.add_patch(Circle((cx + 0.26 * cell, cy - 0.26 * cell), cell * 0.12,
                                       fc=P.TRACK, ec=P.WHITE, lw=0.8 * PT, zorder=7))
            ident = gax.add_patch(Circle((cx, cy), cell * 0.30 * 0.34, fc=P.HIDE_EYE,
                                         lw=0, zorder=6.6))
            for a in (*wedges, dot, pip, ident):
                a.set_visible(False)
            pool[(r, c)] = (wedges, dot, pip, ident)

    dash.fit(ax, PAD, oy + cell * hh + CAPTION_LINE, "caption", w - 2 * PAD,
             numeric=False).set("Shared squares: two occupants split the dot, a third")
    dash.fit(ax, PAD, oy + cell * hh + 2 * CAPTION_LINE, "caption", w - 2 * PAD,
             numeric=False).set("is a rim pip. The grid view shows what they are.")

    def upd(v):
        for (r, c), g in grounds.items():
            g.set_facecolor(dash.ground_colour(r, c))
        for key, t in tints.items():
            occ = v.occupancy.get(key, ())
            ter = [n for n in occ if n in C.TERRAIN_NAMES]
            t.set_visible(bool(ter))
            if ter:
                t.set_facecolor(P.MINIMAP_COLOUR[ter[0]])
        for key, (wedges, dot, pip, ident) in pool.items():
            occ = [n for n in v.occupancy.get(key, ()) if n not in C.TERRAIN_NAMES]
            occ = C.by_priority(occ)
            for a in (*wedges, dot, pip, ident):
                a.set_visible(False)
            if not occ:
                continue
            if len(occ) == 1:
                dot.set_visible(True)
                dot.set_facecolor(P.MINIMAP_COLOUR[occ[0]])
            else:
                for wg, nm in zip(wedges, occ[:2]):
                    wg.set_visible(True)
                    wg.set_facecolor(P.MINIMAP_COLOUR[nm])
                if len(occ) > 2:
                    pip.set_visible(True)
                    pip.set_facecolor(P.MINIMAP_COLOUR[occ[2]])
            # The amber identity pip tells a hiding predator from a predator,
            # which share a body colour. It marks the occupant of the DOT, so it
            # is drawn whenever the hiding predator is one of the occupants the
            # dot (or its two wedges) carries -- not only when it is alone, which
            # is how it was first written. That restriction made the two pips
            # mutually exclusive, and the plan (section R17.4) requires exactly
            # the opposite: the occupancy rim pip and the identity pip must be
            # able to appear on ONE square and share no pixel, with a test that
            # says so. They cannot collide by construction -- the identity pip
            # ends 0.102 x cell from the centre and the rim pip begins
            # 0.248 x cell from it -- and CP2.8 measures that on a rendered frame
            # rather than trusting the arithmetic.
            if "hiding_predator" in occ[:2]:
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


def build_spectrum(dash, ax, w, h, sense, names, colour_stops):
    """Smell at range 0: one bar per odour component."""
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("s", list(colour_stops))
    card_title(dash, ax, w, "Olfaction", "range 0")
    n = len(names)
    gap = 10
    cw = (w - 2 * PAD - gap * (n - 1)) / n
    setters = []
    for i, nm in enumerate(names):
        x = PAD + i * (cw + gap)
        dash.fit(ax, x + cw / 2, h - 16, "map_label", cw, ha="center").set(nm)
        track_h = h - 60 - 26
        rrect(ax, x, 60, cw, track_h, 4, P.TRACK, z=2)
        fill = rrect(ax, x, 60 + track_h, cw, 1, 4, cmap(0.75), z=3)
        setters.append((fill, track_h))

    def upd(v):
        vec = np.asarray(v.sense(sense, "vector"), dtype=float)
        vmax = max(float(dash.sense_max.get(sense, 1.0)), 1e-6)
        for (fill, track_h), q in zip(setters, vec):
            frac = min(1.0, max(0.0, float(q) / vmax))
            fill.set_height(max(1.0, track_h * frac))
            fill.set_y(60 + track_h - max(1.0, track_h * frac))
            fill.set_facecolor(P.TRACK if frac <= 1e-6 else cmap(0.25 + 0.75 * frac))
    dash.updates.append(upd)


def build_channel_bars(dash, ax, w, h, sense, title, vector_size, colour_stops):
    """Vision at range 0: one bar per property channel, with its short label."""
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("v", list(colour_stops))
    names = channel_labels("Visual", vector_size)
    card_title(dash, ax, w, title, "range 0")
    n = len(names)
    gap = 8
    cw = (w - 2 * PAD - gap * (n - 1)) / n
    setters = []
    for i, nm in enumerate(names):
        x = PAD + i * (cw + gap)
        dash.fit(ax, x + cw / 2, h - 16, "map_label", cw + gap, ha="center").set(nm)
        track_h = h - 58 - 26
        rrect(ax, x, 58, cw, track_h, 4, P.TRACK, z=2)
        fill = rrect(ax, x, 58 + track_h, cw, 1, 4, cmap(0.75), z=3)
        setters.append((fill, track_h))

    def upd(v):
        vec = np.asarray(v.sense(sense, "vector"), dtype=float)
        vmax = max(float(dash.sense_max.get(sense, 1.0)), 1e-6)
        for (fill, track_h), q in zip(setters, vec):
            frac = min(1.0, max(0.0, float(q) / vmax))
            fill.set_height(max(1.0, track_h * frac))
            fill.set_y(58 + track_h - max(1.0, track_h * frac))
            fill.set_facecolor(P.TRACK if frac <= 1e-6 else cmap(0.25 + 0.75 * frac))
    dash.updates.append(upd)


def build_cross_bars(dash, ax, w, h, sense, title, offsets, letters):
    """Collision at range 1: the five squares the agent can touch."""
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
