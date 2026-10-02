"""The episode-dashboard design spec, as code.

WHAT THIS IS. The tokens, type roles, temperature scale and flat glyphs specified in
docs/reviews/design_episode_dashboard.md, in one importable module, so the sketch figures
(fig05_extended_encodings.py) and the asset exporter
(make_dashboard_assets.py) cannot drift apart. It is a sketch-side module: nothing under src/ imports
it, and it imports nothing from src/.

COORDINATES. Every drawing helper assumes an axes in PIXEL units with y growing DOWNWARD
(xlim 0..w, ylim h..0), which is how every card in the sketch is set up.
"""
import glob
import os

import numpy as np
import matplotlib.font_manager as fm
from matplotlib.colors import FuncNorm, LinearSegmentedColormap, to_rgb
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path
from matplotlib.transforms import Affine2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
FONT_DIR = os.path.join(ROOT, "assets", "fonts", "dashboard_sans_tab")
FONT = "Dashboard Sans Tab"

DPI = 100
PT = 72 / DPI            # px -> pt at dpi 100

# ------------------------------------------------------------------ palette (spec "Palette")
CANVAS, CARD, LINE, TRACK = "#F2F3F0", "#FFFFFF", "#E2E4DF", "#ECEEEA"
CANVAS_TRACK = "#D9DCD5"   # a track drawn on the canvas (header progress), where TRACK is invisible
OUTLINE = "#CDD1CB"      # outlined empty track: "no signal", not "zero"
INK, INK2, INK3 = "#15171C", "#4A515C", "#6F7682"
IRIS, IRIS_SOFT = "#5B4BDB", "#ECE9FB"     # agent only
STATE = "#2F3744"
NOCI = "#E8590C"                           # nociception only
# Food is rose, not green: green belongs to the bush and the tree, and a green apple collided with both.
# The leaf stays green because it is the one mark no temperature cell and no nociception bar can carry.
FOOD, PRED, NEUT = "#E03151", "#1F2733", "#A8A29A"
FOOD_LEAF, FOOD_STEM = "#1E9E5A", "#6B4A2B"
# The rabbit is grey with a pink inner ear: teal is the olfaction ramp's. Its grey is warm (R > G > B)
# where the rock's is cool (B > R), and the pink ear is the mark the rock can never have.
NEUT_INNER, EYE_DARK = "#F0A9B4", "#2A241F"
# The hiding predator is a STATIC contact hazard -- it never moves and has no odour -- so it is drawn as a
# thorn cluster, not a lurking animal. Threat charcoal one step lighter than the predator's, amber tips.
HIDE_BODY, HIDE_EYE = "#2B3442", "#F59E0B"
ROCK, ROCK_HI = "#6B7380", "#A1A8B1"
BUSH, BUSH_HI = "#4F8A34", "#65A044"
TREE, TREE_HI, TRUNK = "#2F7A45", "#3E9357", "#7A5634"
FIRE_OUT, FIRE_MID, FIRE_CORE = "#F97316", "#FB9A3C", "#FDE68A"
LOG_BACK, LOG_FRONT, GLOW = "#7C4A2D", "#935C38", "#FDBA74"
# minimap marks: one colour per entity name, taken from its glyph. The campfire mark is log brown with a
# FIRE_CORE dot: orange means nociception in the frame, and flame colours live only inside the glyph
MINIMAP_COLOUR = {"rock": ROCK, "bush": BUSH, "tree": TREE, "campfire": LOG_BACK,
                  "food": FOOD, "hiding_predator": HIDE_BODY, "predator": PRED, "neutral": NEUT}

# sequential ramps, per sense (zero is TRACK, never the ramp's first stop)
OLF_CMAP = LinearSegmentedColormap.from_list("olfaction", ["#EDF7F5", "#7CCBBD", "#14907F", "#0B4F47"])
VIS_CMAP = LinearSegmentedColormap.from_list("vision", ["#EFF1F4", "#A3ACBA", "#556072", "#1C2330"])
TERRAIN = ["#DCEBD2", "#EFE4C9", "#E6E4DD"]     # vision channels 0..2: grass, sand, plain
OFF_WORLD = "#FFFFFF"

# ------------------------------------------------------------------ type roles (spec "Type")
# role -> (weight, px, colour)
TYPE = {
    "frame_title": ("semibold", 22, INK),
    "step": ("semibold", 26, INK),
    "step_aux": ("regular", 15, INK3),
    "card_title": ("semibold", 15, INK),
    "card_sub": ("regular", 13, INK3),
    "meta": ("regular", 14, INK2),
    "row_label": ("medium", 14, INK),
    "map_label": ("medium", 13, INK2),
    "value": ("semibold", 18, INK),
    "hero": ("semibold", 30, INK),
    "caption": ("regular", 12, INK3),
    "caption_medium": ("medium", 12, INK3),
    "col_head": ("medium", 12, INK3),
    "not_observed": ("regular", 13, INK3),
    "chip": ("medium", 13, INK2),
    "chip_on": ("semibold", 13, "#FFFFFF"),
    "badge": ("semibold", 14, IRIS),
    "cell_num": ("semibold", 14, INK),
    "coll_letter": ("semibold", 12, INK3),
}
FLOOR_PX = 12

# ------------------------------------------------------------------ spacing (spec "Spacing")
OUTER, GAP, PAD, HEAD = 24, 16, 16, 64
TITLE_BASE = 30          # card title baseline from card top
CARD_RADIUS = 12


def register_fonts():
    """Register the frozen-tabular-digit faces with Matplotlib. Raises if they have not been built."""
    paths = sorted(glob.glob(os.path.join(FONT_DIR, "DashboardSansTab-*.otf")))
    if len(paths) != 3:
        raise FileNotFoundError(f"expected 3 Dashboard Sans Tab faces in {FONT_DIR}, found {len(paths)}: "
                                "run make_dashboard_assets.py first")
    for p in paths:
        fm.fontManager.addfont(p)
    names = {f.name for f in fm.fontManager.ttflist}
    if FONT not in names:
        raise RuntimeError(f"font family {FONT!r} did not register")


def text(ax, x, y, s, role, ha="left", va="baseline", color=None, **kw):
    weight, px, colour = TYPE[role]
    return ax.text(x, y, s, fontsize=px * PT, fontfamily=FONT, fontweight=weight, color=color or colour,
                   ha=ha, va=va, **kw)


def rrect(ax, x, y, w, h, r, fc, ec="none", lw_px=0.0, z=1.0, alpha=1.0):
    return ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                       fc=fc, ec=ec, lw=lw_px * PT, zorder=z, alpha=alpha))


def signed(v, d=0):
    s = f"{v:+.{d}f}"
    if float(s) == 0:
        s = f"{0:.{d}f}"
    return s.replace("-", "−")


def luminance(rgb):
    r, g, b = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4) for c in to_rgb(rgb)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ------------------------------------------------------------------ temperature scale
# ONE range per episode: vmin / vmax are the coldest and hottest cell of the episode's recorded thermal field
# (a setup pre-pass), constant for every frame. Near-white at the setpoint, pale inside the survivable body
# band, and colour deepens only beyond the body limits: blue toward the episode minimum, red toward its maximum.
TEMP_COLD, TEMP_COOL, TEMP_NEUTRAL = "#9FBCE6", "#D3E1F2", "#F3F2EE"
TEMP_WARM, TEMP_HOT_MID, TEMP_HOT = "#F7DCCB", "#E6806A", "#B8323A"
BAND_WEIGHT, OUTER_WEIGHT = 1.0, 1.25     # share of the legend strip: each band half vs each outer tail


def _mix(c1, c2, t):
    t = min(1.0, max(0.0, t))
    return tuple(np.array(to_rgb(c1)) * (1 - t) + np.array(to_rgb(c2)) * t)


class TemperatureScale:
    """Episode-range diverging scale. Anchors: episode min, lower body limit, setpoint, upper body limit,
    episode max -- a limit the episode range does not reach is dropped, so the ramp stays monotonic.
    Values outside the episode range are clamped to the end colour; callers outline them (out_of_range)."""

    def __init__(self, field, low, high, setpoint):
        f = np.asarray(field, float)
        if f.size == 0:
            raise ValueError("TemperatureScale needs the episode's thermal field")
        if not low < setpoint < high:
            raise ValueError(f"body limits must bracket the setpoint: {low} < {setpoint} < {high}")
        vmin, vmax = float(f.min()), float(f.max())
        if vmax <= vmin:
            raise ValueError(f"the episode's thermal field is constant ({vmin}); no colour range")
        self.vmin, self.vmax, self.low, self.high, self.sp = vmin, vmax, float(low), float(high), float(setpoint)
        cand = [("episode min", vmin), ("lower body limit", self.low), ("setpoint", self.sp),
                ("upper body limit", self.high), ("episode max", vmax)]
        anchors = [(n, v) for n, v in cand if n.startswith("episode") or vmin < v < vmax]
        xs = [v for _, v in anchors]
        pos = [0.0]
        for x0, x1 in zip(xs, xs[1:]):
            if x1 <= self.low or x0 >= self.high:
                w = OUTER_WEIGHT                   # a tail beyond a body limit, always episode end to limit
            else:
                half = (self.sp - self.low) if x1 <= self.sp else (self.high - self.sp)
                w = BAND_WEIGHT * (x1 - x0) / half
            pos.append(pos[-1] + w)
        pos = [q / pos[-1] for q in pos]
        stops = [(q, self.ref_colour(v)) for q, v in zip(pos, xs)]
        if vmax > self.high:                      # hue path peach -> salmon -> crimson in the hot tail
            q0 = pos[xs.index(self.high)]
            stops.insert(-1, ((q0 + 1.0) / 2, TEMP_HOT_MID))
        self.X, self.Y = np.array(xs), np.array(pos)
        self.cmap = LinearSegmentedColormap.from_list("temperature", stops)
        self.norm = FuncNorm((lambda v: np.interp(v, self.X, self.Y), lambda y: np.interp(y, self.Y, self.X)),
                             vmin=vmin, vmax=vmax)
        self.b = dict(vmin=vmin, vmax=vmax, low=self.low, high=self.high, setpoint=self.sp, anchors=anchors,
                      n_cells=int(f.size))

    def ref_colour(self, v):
        if v <= self.low:
            return _mix(TEMP_COOL, TEMP_COLD, (self.low - v) / (self.low - self.vmin)) if self.vmin < self.low else TEMP_COOL
        if v <= self.sp:
            return _mix(TEMP_NEUTRAL, TEMP_COOL, (self.sp - v) / (self.sp - self.low))
        if v <= self.high:
            return _mix(TEMP_NEUTRAL, TEMP_WARM, (v - self.sp) / (self.high - self.sp))
        return TEMP_HOT if v >= self.vmax else _mix(TEMP_WARM, TEMP_HOT, (v - self.high) / (self.vmax - self.high))

    def pos(self, v):
        return float(np.interp(v, self.X, self.Y))           # np.interp clamps outside the episode range

    def colour(self, v):
        return self.cmap(self.pos(v))

    def out_of_range(self, v):
        return v < self.vmin - 1e-9 or v > self.vmax + 1e-9


def visual_offsets(sensor_range):
    """Copy of src/environment/sensor.py get_visual_offsets: range 1 uses the C U R D L order."""
    if sensor_range == 1:
        return [(0, 0), (-1, 0), (0, 1), (1, 0), (0, -1)]
    out = [(0, 0)]
    for d in range(1, sensor_range + 1):
        for dr in range(-d, d + 1):
            a = d - abs(dr)
            out += [(dr, 0)] if a == 0 else [(dr, a), (dr, -a)]
    return out


# ------------------------------------------------------------------ flat glyphs
# Each g_<name>(ax, cx, cy, s, z) draws in a cell of size s centred at (cx, cy) and returns its artists.

def token(ax, cx, cy, r, z):
    return [ax.add_patch(Circle((cx, cy + r * 0.07), r * 1.02, fc="#000000", alpha=0.10, lw=0, zorder=z)),
            ax.add_patch(Circle((cx, cy), r, fc="#FFFFFF", lw=0, zorder=z + 0.05))]


def _teardrop(ax, cx, cy, w, h, fc, z):
    verts = [(cx, cy - h), (cx + w * 0.15, cy - h * 0.55), (cx + w, cy - h * 0.25), (cx + w, cy),
             (cx + w, cy + h * 0.30), (cx + w * 0.55, cy + h * 0.42), (cx, cy + h * 0.42),
             (cx - w * 0.55, cy + h * 0.42), (cx - w, cy + h * 0.30), (cx - w, cy),
             (cx - w, cy - h * 0.25), (cx - w * 0.15, cy - h * 0.55), (cx, cy - h)]
    return ax.add_patch(PathPatch(Path(verts, [Path.MOVETO] + [Path.CURVE4] * 12), fc=fc, lw=0, zorder=z))


def g_food(ax, cx, cy, s, z=7):
    """Two-lobed apple in rose, with a green leaf and a brown stem. The leaf is load-bearing and is kept at
    every size: it is the one mark a temperature cell or a nociception bar can never have, so it is what
    separates the food token from every other red in the frame."""
    out = token(ax, cx, cy, s * 0.34, z - 1)
    r = s * 0.15
    out += [ax.add_patch(Circle((cx - r * 0.45, cy + r * 0.15), r, fc=FOOD, lw=0, zorder=z)),
            ax.add_patch(Circle((cx + r * 0.45, cy + r * 0.15), r, fc=FOOD, lw=0, zorder=z)),
            ax.add_patch(Rectangle((cx - s * 0.008, cy - r * 1.35), s * 0.016, r * 0.6, fc=FOOD_STEM, lw=0, zorder=z)),
            ax.add_patch(Ellipse((cx + r * 0.45, cy - r * 1.15), r * 0.9, r * 0.42, angle=-30, fc=FOOD_LEAF, lw=0, zorder=z))]
    return out


def g_predator(ax, cx, cy, s, z=7):
    out = token(ax, cx, cy, s * 0.34, z - 1)
    k = s * 0.19
    pts = [(-0.95, -0.95), (-0.45, -0.35), (0.45, -0.35), (0.95, -0.95), (0.9, 0.05), (0.35, 0.95), (-0.35, 0.95), (-0.9, 0.05)]
    out.append(ax.add_patch(Polygon([(cx + a * k, cy + b * k) for a, b in pts], closed=True, fc=PRED, lw=0, zorder=z)))
    for sx in (-1, 1):
        out.append(ax.add_patch(Polygon([(cx + sx * 0.52 * k, cy + 0.02 * k), (cx + sx * 0.18 * k, cy + 0.12 * k),
                                         (cx + sx * 0.44 * k, cy + 0.26 * k)], fc=HIDE_EYE, lw=0, zorder=z + 0.1)))
    return out


def g_neutral(ax, cx, cy, s, z=7):
    """Rabbit head: two long ears with a pink lining, a round head, two dark eyes. The pink lining is what
    keeps it apart from the rock at small sizes -- the rock is a cool grey mound with no warm mark anywhere
    -- so the ears are drawn tall and kept separated, and the lining runs most of the ear's length."""
    out = token(ax, cx, cy, s * 0.34, z - 1)
    k = s * 0.19
    for sx in (-1, 1):
        out.append(ax.add_patch(Ellipse((cx + sx * 0.34 * k, cy - 0.58 * k), 0.38 * k, 1.12 * k, angle=sx * 10,
                                        fc=NEUT, lw=0, zorder=z)))
        out.append(ax.add_patch(Ellipse((cx + sx * 0.34 * k, cy - 0.58 * k), 0.21 * k, 0.78 * k, angle=sx * 10,
                                        fc=NEUT_INNER, lw=0, zorder=z + 0.05)))
    out.append(ax.add_patch(Circle((cx, cy + 0.32 * k), 0.62 * k, fc=NEUT, lw=0, zorder=z)))
    for sx in (-1, 1):
        out.append(ax.add_patch(Circle((cx + sx * 0.24 * k, cy + 0.22 * k), 0.10 * k, fc=EYE_DARK, lw=0, zorder=z + 0.1)))
    return out


def g_hiding_predator(ax, cx, cy, s, z=7):
    """Thorn / spine cluster: three spikes of unequal height on a low mound, each tipped amber.

    The entity is a stationary trap tile -- it never moves, carries no odour, and damages on contact -- so the
    glyph must read as a static hazard, not as a creature that could emerge. It keeps the predator's threat
    pair (charcoal body, amber accent) so the two read as siblings, but shares no shape with it, and shares
    neither shape nor green with the bush, which is the agent's refuge. The amber tip is the top 44 % of each
    spike, which is what survives a 28 px grid cell."""
    out = token(ax, cx, cy, s * 0.34, z - 1)
    k = s * 0.19
    out.append(ax.add_patch(Ellipse((cx, cy + 0.62 * k), 1.85 * k, 0.48 * k, fc=HIDE_BODY, lw=0, zorder=z)))
    for xo, h, w in ((-0.56, 0.52, 0.26), (0.0, 0.98, 0.30), (0.56, 0.60, 0.26)):
        ytip, ybase = cy - h * k, cy + 0.62 * k
        out.append(ax.add_patch(Polygon([(cx + xo * k, ytip), (cx + (xo - w) * k, ybase), (cx + (xo + w) * k, ybase)],
                                        closed=True, fc=HIDE_BODY, lw=0, zorder=z + 0.1)))
        t = 0.44                                   # amber tip = top 44 % of the spike (survives 28 px)
        ycut, wcut = ytip + t * (ybase - ytip), w * t
        out.append(ax.add_patch(Polygon([(cx + xo * k, ytip), (cx + (xo - wcut) * k, ycut), (cx + (xo + wcut) * k, ycut)],
                                        closed=True, fc=HIDE_EYE, lw=0, zorder=z + 0.2)))
    return out


def g_rock(ax, cx, cy, s, z=5):
    k = s * 0.30
    pts = [(-0.85, 0.55), (-0.7, -0.1), (-0.3, -0.55), (0.25, -0.6), (0.75, -0.2), (0.9, 0.55)]
    pts2 = [(-0.3, -0.55), (0.25, -0.6), (0.75, -0.2), (0.1, 0.05)]
    return [ax.add_patch(Polygon([(cx + a * k, cy + b * k) for a, b in pts], fc=ROCK, lw=0, zorder=z)),
            ax.add_patch(Polygon([(cx + a * k, cy + b * k) for a, b in pts2], fc=ROCK_HI, lw=0, zorder=z + 0.1))]


def g_bush(ax, cx, cy, s, z=5):
    k = s * 0.30
    return [ax.add_patch(Circle((cx + dx * k, cy + dy * k), r * k, fc=c, lw=0, zorder=z))
            for dx, dy, r, c in ((-0.45, 0.2, 0.42, BUSH), (0.45, 0.2, 0.42, BUSH), (0, -0.15, 0.5, BUSH_HI), (0, 0.3, 0.42, BUSH))]


def g_tree(ax, cx, cy, s, z=5):
    k = s * 0.30
    return [ax.add_patch(Rectangle((cx - 0.13 * k, cy + 0.1 * k), 0.26 * k, 0.75 * k, fc=TRUNK, lw=0, zorder=z)),
            ax.add_patch(Circle((cx, cy - 0.25 * k), 0.62 * k, fc=TREE, lw=0, zorder=z + 0.1)),
            ax.add_patch(Circle((cx - 0.18 * k, cy - 0.42 * k), 0.28 * k, fc=TREE_HI, lw=0, zorder=z + 0.2))]


def g_campfire(ax, cx, cy, s, z=5):
    """Campfire spec: k = 0.30 s; glow 0.95k @28 %; two logs 1.6k x 0.22k crossed at +-18 deg about a point
    0.55k below centre; three nested teardrops (0.48k x 0.95k, 0.30k x 0.62k down 0.10k, 0.15k x 0.34k down 0.18k)."""
    k = s * 0.30
    out = [ax.add_patch(Circle((cx, cy), 0.95 * k, fc=GLOW, alpha=0.28, lw=0, zorder=z))]
    for ang, col in ((18, LOG_BACK), (-18, LOG_FRONT)):
        p = FancyBboxPatch((cx - 0.8 * k, cy + 0.44 * k), 1.6 * k, 0.22 * k,
                           boxstyle=f"round,pad=0,rounding_size={0.11 * k}", fc=col, lw=0, zorder=z + 0.1)
        p.set_transform(Affine2D().rotate_deg_around(cx, cy + 0.55 * k, ang) + ax.transData)
        out.append(ax.add_patch(p))
    base = cy + 0.12 * k
    out += [_teardrop(ax, cx, base, 0.48 * k, 0.95 * k, FIRE_OUT, z + 0.2),
            _teardrop(ax, cx, base + 0.10 * k, 0.30 * k, 0.62 * k, FIRE_MID, z + 0.3),
            _teardrop(ax, cx, base + 0.18 * k, 0.15 * k, 0.34 * k, FIRE_CORE, z + 0.4)]
    return out


ARROW_VEC = {"UP": (0, -1), "RIGHT": (1, 0), "DOWN": (0, 1), "LEFT": (-1, 0)}
ARROW_TEXT = {"UP": "↑", "RIGHT": "→", "DOWN": "↓", "LEFT": "←"}


def agent_marker(ax, cx, cy, s, z=8):
    """Composable agent: iris disc + white ring + halo, plus one mark per last action.
    Returns {'base': [...], 'UP'|'RIGHT'|'DOWN'|'LEFT': chevron, 'dot': dot} so a caller toggles one mark."""
    r = s * 0.30
    parts = {"base": [ax.add_patch(Circle((cx, cy), r * 1.32, fc=IRIS, alpha=0.16, lw=0, zorder=z)),
                      ax.add_patch(Circle((cx, cy + r * 0.07), r * 1.04, fc="#000000", alpha=0.12, lw=0, zorder=z + 0.02)),
                      ax.add_patch(Circle((cx, cy), r, fc=IRIS, ec="#FFFFFF", lw=max(1.0, s / 32) * PT, zorder=z + 0.1))]}
    a = r * 0.55
    for name, (dx, dy) in ARROW_VEC.items():
        nx, ny = -dy, dx
        tip = (cx + dx * a, cy + dy * a)
        b1 = (cx - dx * a * 0.3 + nx * a * 0.6, cy - dy * a * 0.3 + ny * a * 0.6)
        b2 = (cx - dx * a * 0.3 - nx * a * 0.6, cy - dy * a * 0.3 - ny * a * 0.6)
        parts[name] = ax.add_patch(Polygon([tip, b1, (cx, cy), b2], fc="#FFFFFF", lw=0, zorder=z + 0.2))
    parts["dot"] = ax.add_patch(Circle((cx, cy), r * 0.28, fc="#FFFFFF", lw=0, zorder=z + 0.2))
    return parts


def g_agent(ax, cx, cy, s, z=8, action=None):
    parts = agent_marker(ax, cx, cy, s, z)
    keep = action if action in ARROW_VEC else "dot"
    out = list(parts["base"])
    for k, p in parts.items():
        if k == "base":
            continue
        if k == keep:
            out.append(p)
        else:
            p.remove()
    return out


TERRAIN_GLYPHS = {"rock": g_rock, "bush": g_bush, "tree": g_tree, "campfire": g_campfire}
TOKEN_GLYPHS = {"food": g_food, "hiding_predator": g_hiding_predator, "predator": g_predator, "neutral": g_neutral}
GLYPHS = {"agent": g_agent, **TOKEN_GLYPHS, **TERRAIN_GLYPHS}
