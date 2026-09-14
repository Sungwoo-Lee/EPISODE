"""The episode-dashboard design spec, as code.

WHAT THIS IS. The tokens, type roles, temperature scale and flat glyphs specified in
docs/reviews/design_episode_dashboard.md, in one importable module, so the sketch figures
(fig03_proposed_dashboard.py, fig05_extended_encodings.py) and the asset exporter
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
FOOD, PRED, NEUT = "#1E9E5A", "#1F2733", "#0E7490"
HIDE_BODY, HIDE_EYE = "#33503A", "#F59E0B"
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
TEMP_STOPS = ["#9FBCE6", "#D3E1F2", "#F3F2EE", "#F7DCCB", "#E6806A", "#B8323A", "#5E1320"]
TEMP_POS = [0.00, 0.25, 0.50, 0.58, 0.75, 0.88, 1.00]
TEMP_CMAP = LinearSegmentedColormap.from_list("temperature", list(zip(TEMP_POS, TEMP_STOPS)))
WARM_MULT, FIRE_MULT = 4.0, 10.0      # design rules: warm = setpoint + 4 x band half-width, fire = 10 x


def _mandatory(d, key, where):
    if key not in d:
        raise ValueError(f"{where}: missing mandatory key {key!r}")
    return d[key]


def temperature_bounds(cfg):
    """Params-only colour bounds for the thermal field (plan RENDERER_LAYOUT_REDESIGN §D4.3, Revision 7).

    The field is  default_temp  + random spots  + scatter-ADDED entity heat  (abs + ratio * |default_temp|),
    then a weight-normalised blur that cannot leave the raw range. Refinement of the plan's formula: the
    fire term is evaluated PER default-temperature corner d (and at 0 if the range crosses 0), because the
    ratio multiplies |d| of the same draw. That is still an upper bound, and it is attained in the
    separated case (a lone fire on the coldest ground), so it is the supremum:
        vmax = max_d [ d + spots + fire(d) ],   fire(d) = max_i c_i(d)   if min_fire_separation > 0
                                                          sum_i count_high_i * c_i(d)   otherwise
        c_i(d) = absolute_i + max(ratio_low_i, ratio_high_i) * |d|,  positive c_i only
        vmin = min_d [ d - spots + negative stamps ],  then both widened to include the body limits.
    Returns a dict with the bounds, the anchors and the plan's un-refined vmax for the record.
    """
    th = _mandatory(cfg, "thermal", "config")
    if not _mandatory(th, "enabled", "thermal"):
        raise ValueError("temperature_bounds called on a config with thermal.enabled false")
    lo_d, hi_d = [float(x) for x in _mandatory(th, "default_temp", "thermal")]
    corners = sorted({lo_d, hi_d} | ({0.0} if lo_d < 0 < hi_d else set()))
    D = max(abs(lo_d), abs(hi_d))
    spot = 0.0
    if _mandatory(th, "use_random_spots", "thermal"):
        rs = _mandatory(th, "random_spots", "thermal")
        spot = float(_mandatory(rs, "temp", "random_spots")) * int(_mandatory(rs, "count", "random_spots"))
    sep = int(_mandatory(th, "min_fire_separation", "thermal"))
    sources = []
    if _mandatory(th, "use_object_sources", "thermal"):
        env = _mandatory(cfg, "environment", "config")
        for sec in ("obstacles", "resources"):
            for e in env.get(sec, []) or []:
                a = float(e.get("temperature", 0.0) or 0.0)
                r = e.get("temperature_ratio")
                rmax = max(float(r[0]), float(r[1])) if r is not None else 0.0
                if a != 0.0 or rmax != 0.0:
                    sources.append((e["name"], a, rmax, int(_mandatory(e, "count_high", e["name"]))))

    def stamps(d, sign):
        cs = [(a + rmax * abs(d), n) for _, a, rmax, n in sources]
        cs = [(c, n) for c, n in cs if sign * c > 0]
        if not cs:
            return 0.0
        return max(cs, key=lambda t: sign * t[0])[0] if sep > 0 else sum(c * n for c, n in cs)

    vmax = max(d + spot + stamps(d, +1) for d in corners)
    vmin = min(d - spot + stamps(d, -1) for d in corners)
    plan_vmax = max(lo_d, hi_d) + spot + stamps(D if D else 0.0, +1) if sources else vmax
    t_lo, t_hi = float(_mandatory(th, "min_temperature", "thermal")), float(_mandatory(th, "max_temperature", "thermal"))
    sp = float(_mandatory(th, "temperature_setpoint", "thermal"))
    vmin, vmax = min(vmin, t_lo), max(vmax, t_hi)
    half = t_hi - sp
    anchors = [("vmin", vmin), ("lower body limit", t_lo), ("setpoint", sp), ("upper body limit", t_hi),
               ("warm", sp + WARM_MULT * half), ("fire", sp + FIRE_MULT * half), ("vmax", vmax)]
    xs = [v for _, v in anchors]
    if any(b <= a for a, b in zip(xs, xs[1:])):
        raise ValueError("temperature anchors are not strictly increasing for this config: "
                         + ", ".join(f"{n}={v:g}" for n, v in anchors))
    return dict(vmin=vmin, vmax=vmax, setpoint=sp, low=t_lo, high=t_hi, anchors=anchors,
                plan_vmax=plan_vmax, sources=sources, separation=sep, corners=corners)


class TemperatureScale:
    """Piecewise-linear FuncNorm through the named anchors, colour stops sitting exactly on them."""

    def __init__(self, bounds):
        self.b = bounds
        self.X = np.array([v for _, v in bounds["anchors"]], float)
        self.Y = np.array(TEMP_POS, float)
        self.norm = FuncNorm((lambda v: np.interp(v, self.X, self.Y), lambda y: np.interp(y, self.Y, self.X)),
                             vmin=self.X[0], vmax=self.X[-1])
        self.cmap = TEMP_CMAP

    def pos(self, v):
        return float(np.interp(v, self.X, self.Y))

    def colour(self, v):
        return self.cmap(self.pos(v))

    def check_field_in_bounds(self, field, config_name=""):
        """Raise (never clip) when a cell lies outside the params-only bounds: the bounds are wrong."""
        f = np.asarray(field, float)
        for bound, bad in (("vmin", f < self.X[0]), ("vmax", f > self.X[-1])):
            if bad.any():
                r, c = map(int, np.argwhere(bad)[0])
                lim = self.X[0] if bound == "vmin" else self.X[-1]
                raise ValueError(f"{config_name}: thermal_field cell (row {r}, col {c}) = {f[r, c]:.2f} lies outside "
                                 f"{bound} = {lim:.2f}; the params-only temperature bounds do not cover this config")
        return f.size


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
    out = token(ax, cx, cy, s * 0.34, z - 1)
    r = s * 0.15
    out += [ax.add_patch(Circle((cx - r * 0.45, cy + r * 0.15), r, fc=FOOD, lw=0, zorder=z)),
            ax.add_patch(Circle((cx + r * 0.45, cy + r * 0.15), r, fc=FOOD, lw=0, zorder=z)),
            ax.add_patch(Rectangle((cx - s * 0.008, cy - r * 1.35), s * 0.016, r * 0.6, fc="#6B4A2B", lw=0, zorder=z)),
            ax.add_patch(Ellipse((cx + r * 0.45, cy - r * 1.15), r * 0.9, r * 0.42, angle=-30, fc="#14683D", lw=0, zorder=z))]
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
    out = token(ax, cx, cy, s * 0.34, z - 1)
    k = s * 0.19
    for sx in (-1, 1):
        out.append(ax.add_patch(Ellipse((cx + sx * 0.32 * k, cy - 0.55 * k), 0.36 * k, 1.05 * k, angle=sx * 10,
                                        fc=NEUT, lw=0, zorder=z)))
    out.append(ax.add_patch(Circle((cx, cy + 0.32 * k), 0.62 * k, fc=NEUT, lw=0, zorder=z)))
    for sx in (-1, 1):
        out.append(ax.add_patch(Circle((cx + sx * 0.24 * k, cy + 0.22 * k), 0.09 * k, fc="#FFFFFF", lw=0, zorder=z + 0.1)))
    return out


def g_hiding_predator(ax, cx, cy, s, z=7):
    out = token(ax, cx, cy, s * 0.34, z - 1)
    k = s * 0.19
    for dx, dy, r in ((-0.5, 0.25, 0.5), (0.5, 0.25, 0.5), (0, -0.2, 0.6), (-0.15, 0.45, 0.5), (0.3, 0.5, 0.45)):
        out.append(ax.add_patch(Circle((cx + dx * k, cy + dy * k), r * k, fc=HIDE_BODY, lw=0, zorder=z)))
    for sx in (-1, 1):
        out.append(ax.add_patch(Circle((cx + sx * 0.25 * k, cy + 0.05 * k), 0.12 * k, fc=HIDE_EYE, lw=0, zorder=z + 0.1)))
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
