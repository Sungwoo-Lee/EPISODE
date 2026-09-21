"""Shared helpers for the imperativism field-review figures.

ONE COLOUR, ONE MEANING, PER PAGE (register F11 amendment). On this page:
  * blue / orange  -> imperative vs evaluative CONTENT (Figure "three contents" only);
  * the six COMMUNITY hues below -> which research community a work belongs to, on every figure
    that shows communities. None of them is blue or orange, so the two encodings never collide;
  * everything else (debate status, measured/not measured, eras) is drawn in ink greys, glyphs and
    line styles, never in a hue.
Each community also gets its own marker shape, so the figures do not rely on hue alone.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
DATA = os.path.join(HERE, "..", "field_history_data")
FIGS = os.path.join(HERE, "figures")
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
import house  # noqa: E402

COMMUNITIES = [   # (id, label, colour, marker) - order = swimlane order, top to bottom
    ("philosophy",             "Philosophy",               "#6d4fb3", "D"),
    ("clinical-psychology",    "Clinical psychology",      house.GREEN, "s"),
    ("neurology-neurosurgery", "Neurology & neurosurgery", "#8a5a2b", "v"),
    ("human-neuroscience",     "Human neuroscience",       "#1f7f8c", "o"),
    ("animal-circuits",        "Animal circuits",          house.RED, "^"),
    ("computational",          "Computational",            "#a8318f", "P"),
    ("unknown",                "Community not recorded",   "#9aa0a8", "X"),
]
COLOUR = {c[0]: c[2] for c in COMMUNITIES}
MARKER = {c[0]: c[3] for c in COMMUNITIES}
LABEL = {c[0]: c[1] for c in COMMUNITIES}


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        raise SystemExit(f"missing data file {path} - the synthesis writes it")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def data_statement(stem, text):
    """The used/available line the page prints under a figure (guide 11b) - emitted, never typed."""
    os.makedirs(FIGS, exist_ok=True)
    with open(os.path.join(FIGS, f"{stem}.data.txt"), "w") as fh:
        fh.write(text.strip() + "\n")


def works():
    return {r["key"]: r for r in read("works.csv")}


def label_positions(ax, fig, items, fontsize, pad_px=2.0, tries=None, halo=False):
    """Greedy, collision-free label placement for point labels.

    `items` is a list of (x, y, text, colour). Each label tries a sequence of pixel offsets around its
    point and takes the first whose rendered box overlaps no placed label, no other point and no
    already-drawn leader line, whose own leader crosses no placed label, and which stays inside the
    axes. A label that fits nowhere is dropped and reported, never overprinted.

    With `halo=True` the label also gets an opaque page-coloured box behind it, so an arrow drawn
    afterwards by the caller is interrupted by the text rather than running through its glyphs
    (format register F33). A halo of stroked outlines does not do this - the arrow still crosses the
    counters of the letters.
    """
    from matplotlib.transforms import Bbox
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    axbox = ax.get_window_extent(renderer=r)
    pts = [tuple(float(v) for v in ax.transData.transform((x, y))) for x, y, _, _ in items]
    # every marker is an obstacle, padded by about a marker radius at the figure's dpi (register F57)
    mpad = 9.0 * fig.dpi / 150.0
    point_boxes = [Bbox.from_extents(px - mpad, py - mpad, px + mpad, py + mpad) for px, py in pts]

    def seg_hits_box(seg, box):
        """Liang-Barsky: does the pixel segment cross the axis-aligned box at all?"""
        (x0, y0), (x1, y1) = seg
        dx, dy = x1 - x0, y1 - y0
        t0, t1 = 0.0, 1.0
        for pp, qq in ((-dx, x0 - box.x0), (dx, box.x1 - x0), (-dy, y0 - box.y0), (dy, box.y1 - y0)):
            if pp == 0:
                if qq < 0:
                    return False
                continue
            r = qq / pp
            if pp < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
        return True

    def dist(box, p):
        dx = max(box.x0 - p[0], 0, p[0] - box.x1)
        dy = max(box.y0 - p[1], 0, p[1] - box.y1)
        return (dx * dx + dy * dy) ** 0.5
    tries = tries or [(0, 9), (0, -9), (8, 9), (-8, 9), (8, -9), (-8, -9), (0, 19), (0, -19),
                      (14, 0), (-14, 0), (0, 29), (0, -29)]
    placed, dropped, leaders = [], [], []
    # second tier: farther positions joined to the mark by a thin leader line, which makes the pairing
    # explicit, so the "nearer to its own mark" rule is relaxed for them
    leader_tries = [(0, 26), (0, -26), (26, 18), (-26, 18), (26, -18), (-26, -18), (34, 0), (-34, 0),
                    (0, 38), (0, -38), (40, 26), (-40, 26), (40, -26), (-40, -26)]
    for (x, y, text, colour), (px, py) in zip(items, pts):
        ok = False
        for dx, dy, leader in [(a, b_, False) for a, b_ in tries] + [(a, b_, True) for a, b_ in leader_tries]:
            ha = "left" if dx > 0 else "right" if dx < 0 else "center"
            va = "bottom" if dy > 0 else "top" if dy < 0 else "center"
            props = dict(arrowstyle="-", color=house.TEXT_LIGHT, lw=0.7, shrinkA=1, shrinkB=5) if leader else None
            t = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                            fontsize=fontsize, color=colour, zorder=6, arrowprops=props)
            if halo:
                # an opaque box, not a stroked halo: the caller draws arrows after this routine runs
                t.set_bbox(dict(boxstyle="round,pad=0.16", facecolor=house.PAPER, edgecolor="none", alpha=0.92))
            from matplotlib.text import Text as _Text
            t.update_positions(r)                      # apply the offset before measuring
            b = _Text.get_window_extent(t, renderer=r)   # the text alone: an Annotation box includes its leader
            b = Bbox.from_extents(b.x0 - pad_px, b.y0 - pad_px, b.x1 + pad_px, b.y1 + pad_px)
            inside = (b.x0 >= axbox.x0 and b.x1 <= axbox.x1 and b.y0 >= axbox.y0 and b.y1 <= axbox.y1)
            own = (px, py)
            foreign = [p for p in pts if abs(p[0] - px) > 0.5 or abs(p[1] - py) > 0.5]
            seg = ((px, py), (px + dx, py + dy)) if leader else None
            clash = (any(b.overlaps(o) for o in placed)
                     or any(b.overlaps(pb) for pb, p in zip(point_boxes, pts) if p in foreign)
                     # a leader is ink: it must not be drawn through a label, in either order
                     or any(seg_hits_box(s_, b) for s_ in leaders)
                     or (seg is not None and any(seg_hits_box(seg, o) for o in placed))
                     # a label must read as belonging to its own mark: nearer to it than to any other mark
                     or (not leader and any(dist(b, p) <= dist(b, own) + 2.0 for p in foreign)))
            if inside and not clash:
                placed.append(b)
                if seg is not None:
                    leaders.append(seg)
                ok = True
                break
            t.remove()
        if not ok:
            dropped.append(text)
    return dropped
