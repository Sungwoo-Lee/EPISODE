"""FIGURES 3 and 4 -- a sketch of the proposed episode dashboard, drawn from a real recorded episode.

QUESTION IT ANSWERS. What would the dashboard proposed in
docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md look like on real data, in the visual design
specified in docs/reviews/design_episode_dashboard.md, and does its layout idea -- a registry of panels,
boxes packed once per episode, text measured into its box -- hold when senses are switched off?

WHAT IT IS NOT. Not the planned renderer. Nothing under src/ is imported or edited, and the production
(V1) video path is untouched. It is a design sketch written in the plan's recommended toolkit:
Matplotlib with its layout engine unused, a small packer, the figure built once per episode, and
artists updated per step. Tokens, type, temperature scale and glyphs come from dashboard_style.py.

HOW IT IS COMPUTED. Reads data/episode.json (written by export_episode.py from the real campfire
world). For a given set of senses it
registers the panels that are present (refusing to start if an observed sense has no panel), runs a
setup pre-pass over the episode for the colour scales (ONE temperature range from the episode's
recorded thermal field, shared by every step; per-sense smell and vision maxima), packs the boxes from params and
measured text (raising LayoutOverflowError instead of squeezing), builds every card, bar, label and
glyph once, then for each step updates values and visibility and draws. Every text must fit its slot
at its design size or the script raises; every drawn frame passes a text audit on rendered extents
(no two texts intersect, none leaves its card, no number inside the grid view).

OUTPUT (figures/, next to this file)
    fig03_frames/step_NNN.png                 every step, 1440 x 896 px (the page's step scrubber)
    fig03_proposed_dashboard.{svg,pdf,png}    step 15 (the page's still and full-size view)
    fig04_repacking.{svg,pdf,png}             step 15 under three sense sets
    <stem>.data.txt                           used / available statement per figure (guide 11b)

Run (from the repo root; run make_dashboard_assets.py once first, for the font)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/fig03_proposed_dashboard.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
sys.path.insert(0, HERE)
os.chdir(ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

import dashboard_style as ds  # noqa: E402
import house  # noqa: E402

FIGS = os.path.join(HERE, "figures")
W, H = 1440, 896
REP_STEP = 15
LEFT_W = 320                  # left column width (spec)
GRID_CELL = 96                # grid-view cell size (spec)
MIN_RIGHT_W = 440             # the thermoception card needs this for its diamond + legend
RES_NAMES = ["food", "hiding_predator"]          # res_type index -> name (export_episode.py)
VIZ = {"Satiation": "Satiation", "Interoceptive Nociception": "Intero Nociception",
       "Extero Nociception": "Extero Nociception", "Thermoception": "Thermoception", "Olfaction": "Olfactory",
       "Collision": "Collision", "Proprioception": "Proprioception", "Visual": "Visual",
       "Body Temperature": "Body Temperature", "Nutrition": "Nutrition", "Injury": "Injury"}
# observed sense -> the toggle that switches its panel off on purpose ("" = always on)
TOGGLE_OF = {"Satiation": "", "Nutrition": "", "Injury": "", "Interoceptive Nociception": "intero",
             "Body Temperature": "thermal", "Extero Nociception": "extero", "Thermoception": "thermal",
             "Olfaction": "olf", "Collision": "coll", "Proprioception": "prop", "Visual": "vis"}
ALL = frozenset({"thermal", "intero", "olf", "extero", "coll", "prop", "vis"})
# AN-A / AN-B are two shared animal-odour components (predators load mostly on A, neutral animals on B,
# with heavy overlap), so they are named by their leaning, never "Predator" / "Neutral"
OLF_NAMES = {"FOOD": "Food", "AN-A": ("Odour A", "predator-leaning"), "AN-B": ("Odour B", "neutral-leaning"),
             "BUSH": "Bush", "TREE": "Tree"}
# channel 6 is shared by every obstacle (rock, bush, campfire), so it is "Obstacle", not "Rock"
VIS_NAMES = {"FOD": "Food", "DNG": "Hiding predator", "HPR": "Hiding predator", "PRD": "Predator",
             "RCK": "Obstacle", "NEU": "Neutral"}


class LayoutOverflowError(ValueError):
    pass


def sensor(st, name):
    for s in st["sensors"]:
        if s["name"] == name:
            return s
    raise KeyError(f"step {st['t']}: no sensory entry {name!r}")


def reset_limits(ax):
    ax.set_xlim(0, ax._px_w)
    ax.set_ylim(ax._px_h, 0)


class Fit:
    """A text measured against its slot at its design size: raises rather than overlapping or shrinking."""

    def __init__(self, dash, ax, x, y, role, max_w, **kw):
        self.d, self.max_w = dash, max_w
        self.t = ds.text(ax, x, y, "", role, **kw)

    def set(self, s):
        self.t.set_text(s)
        w = self.t.get_window_extent(self.d.r).width
        if w > self.max_w + 0.5:
            raise LayoutOverflowError(f"text {s!r} is {w:.0f}px wide; its slot is {self.max_w:.0f}px")
        return w


class Dashboard:
    def __init__(self, meta, steps, scale, on=ALL):
        self.m, self.steps, self.scale, self.on = meta, steps, scale, on
        self.n_steps = len(steps)
        bd = meta["breakdown"]
        for name in bd:                      # completeness rule
            if name not in TOGGLE_OF:
                raise ValueError(f"observed sense {name!r} has no panel in the registry")
        self.has = lambda name: name in bd and TOGGLE_OF[name] in (on | {""})
        self.thermal = "thermal" in on and scale is not None
        st0 = steps[0]
        self.olf_range = sensor(st0, "Olfactory")["range"] if self.has("Olfaction") else None
        self.vis_range = sensor(st0, "Visual")["range"] if self.has("Visual") else None
        for nm, r in (("Olfaction", self.olf_range), ("Visual", self.vis_range)):
            if r is not None and r < 1:
                raise LayoutOverflowError(f"{nm} at range {r}: this sketch draws option A maps only (range >= 1)")
        # setup pre-pass: per-sense colour scales fixed for the whole episode
        self.olf_max = max(max(sensor(s, "Olfactory")["vector"]) for s in steps) if self.olf_range else None
        self.vis_max = (max(max(v for i, v in enumerate(sensor(s, "Visual")["vector"]) if i % 8 >= 3) for s in steps)
                        if self.vis_range else None)

        self.fig = plt.figure(figsize=(W / ds.DPI, H / ds.DPI), dpi=ds.DPI)
        self.fig.set_layout_engine("none")
        self.canvas = FigureCanvasAgg(self.fig)
        self.r = self.canvas.get_renderer()
        bg = self.fig.add_axes([0, 0, 1, 1])
        bg.axis("off")
        bg.add_patch(Rectangle((0, 0), 1, 1, transform=bg.transAxes, fc=ds.CANVAS, lw=0))
        self.bg = bg
        self.updates = []
        self.panels = self.registry()
        self.boxes = self.pack(self.panels)
        self.b_header()
        for p in self.panels:
            ax = self.card(self.boxes[p["key"]], fill=p.get("card", True))
            p["build"](ax, *self.boxes[p["key"]][2:])

    # ------------------------------------------------------------------ registry + packer
    def intero_rows(self):
        m, bd = self.m, self.m["breakdown"]
        rows = []
        for label, name, key, mx in (("Satiation", "Satiation", "satiation", "max_satiation"),
                                     ("Nutrition", "Nutrition", "nutrition", "max_nutrition"),
                                     ("Injury", "Injury", "injury", "max_injury")):
            rows.append(dict(label=label, kind="bar", colour=ds.STATE,
                             obs=(lambda st, n=name: sensor(st, VIZ[n])["intensity"]) if name in bd else None,
                             true=lambda st, k=key, mx=mx: st[k] / m[mx], note=None))
        if self.has("Interoceptive Nociception"):
            has_true = "true_intensity" in sensor(self.steps[0], "Intero Nociception")
            rows.append(dict(label="Interoceptive nociception", kind="bar", colour=ds.NOCI,
                             obs=lambda st: sensor(st, "Intero Nociception")["intensity"],
                             true=(lambda st: sensor(st, "Intero Nociception")["true_intensity"]) if has_true else None,
                             note="noise-free" if has_true else None))
        if self.thermal:
            rows.append(dict(label="Body temperature", kind="temp", colour=None,
                             obs=(lambda st: sensor(st, "Body Temperature")["value"]) if self.has("Body Temperature") else None,
                             true=lambda st: st["body_temp"], note=None))
        return rows

    def registry(self):
        self.rows = self.intero_rows()
        band = bool(self.olf_range or self.vis_range)
        reg = [
            dict(key="intero", region="left", h=76 * len(self.rows) + 124, build=self.b_intero),
            # grows only until the map is as wide as the card; beyond that the column stays top-aligned
            dict(key="minimap", region="left", h=220, grow=True, max_h=46 + LEFT_W - 2 * ds.PAD + ds.PAD,
                 build=self.b_minimap),
            dict(key="arena", region="centre", h=48 + self.m["view"] * GRID_CELL + 16, build=self.b_arena),
            dict(key="prop", region="right", h=104, present=self.has("Proprioception"), build=self.b_prop),
            dict(key="extero", region="right", row="ec", h=150, present=self.has("Extero Nociception"), build=self.b_extero),
            dict(key="coll", region="right", row="ec", h=150, present=self.has("Collision"), build=self.b_coll),
            dict(key="thermo", region="right", h=230, grow=True, present=self.thermal, build=self.b_thermo),
            dict(key="band", region="band", h=200, present=band, build=self.b_band),
        ]
        return [p for p in reg if p.get("present", True)]

    def pack(self, panels):
        top = ds.HEAD
        bottom = H - ds.GAP
        lx = ds.OUTER
        cx = lx + LEFT_W + ds.GAP
        cw = self.m["view"] * GRID_CELL + 64
        rx = cx + cw + ds.GAP
        rw = W - ds.OUTER - rx
        if rw < MIN_RIGHT_W:
            raise LayoutOverflowError(f"right column is {rw}px wide; needs {MIN_RIGHT_W}px")
        arena_h = next(p["h"] for p in panels if p["key"] == "arena")
        band = [p for p in panels if p["region"] == "band"]
        col_bottom = top + arena_h if band else bottom
        regions = {"left": (lx, LEFT_W, top, bottom), "right": (rx, rw, top, col_bottom)}
        boxes = {"arena": (cx, top, cw, arena_h)}
        if band:
            by = top + arena_h + ds.GAP
            if bottom - by < band[0]["h"]:
                raise LayoutOverflowError(f"sensor band needs {band[0]['h']}px, has {bottom - by}px")
            boxes["band"] = (cx, by, W - ds.OUTER - cx, bottom - by)
        for region, (x, w, y0, y1) in regions.items():
            rows = []
            for p in (p for p in panels if p["region"] == region):
                if rows and p.get("row") and rows[-1][0].get("row") == p["row"]:
                    rows[-1].append(p)
                else:
                    rows.append([p])
            if not rows:
                continue
            avail = y1 - y0
            need = sum(max(p["h"] for p in r) for r in rows) + ds.GAP * (len(rows) - 1)
            if need > avail:
                raise LayoutOverflowError(f"{region} column needs {need}px, has {avail}px: "
                                          + ", ".join(f"{p['key']}={p['h']}" for r in rows for p in r))
            growers = [r for r in rows if any(p.get("grow") for p in r)]
            spare = avail - need
            y = y0
            for r in rows:
                h = max(p["h"] for p in r) + (spare // len(growers) if r in growers else 0)
                h = min(h, min(p.get("max_h", h) for p in r))
                pw = (w - ds.GAP * (len(r) - 1)) / len(r)
                for i, p in enumerate(r):
                    boxes[p["key"]] = (x + i * (pw + ds.GAP), y, pw, h)
                y += h + ds.GAP                  # no grower: the column stays top-aligned
        keys = list(boxes)
        for i, a in enumerate(keys):             # boxes are disjoint by construction; prove it
            ax_, ay, aw, ah = boxes[a]
            if ax_ < 0 or ay < 0 or ax_ + aw > W or ay + ah > H:
                raise LayoutOverflowError(f"box {a} leaves the frame")
            for b in keys[i + 1:]:
                bx, by_, bw, bh = boxes[b]
                if ax_ < bx + bw and bx < ax_ + aw and ay < by_ + bh and by_ < ay + ah:
                    raise LayoutOverflowError(f"boxes {a} and {b} intersect")
        return boxes

    # ------------------------------------------------------------------ helpers
    def card(self, box, fill=True):
        x, y, w, h = box
        ax = self.fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
        ax._px_w, ax._px_h = w, h
        ax.set_autoscale_on(False)
        reset_limits(ax)
        ax.axis("off")
        if fill:
            ds.rrect(ax, 0.5, 0.5, w - 1, h - 1, ds.CARD_RADIUS, ds.CARD, ds.LINE, 1, z=0)
        return ax

    def fit(self, ax, x, y, role, max_w, **kw):
        return Fit(self, ax, x, y, role, max_w, **kw)

    def width(self, s, role):
        t = ds.text(self.bg, 0, 0, s, role)
        w = t.get_window_extent(self.r).width
        t.remove()
        return w

    def title(self, ax, w, text, sub=None, reserve=0):
        used = 0
        if sub:
            used = self.fit(ax, w - ds.PAD, ds.TITLE_BASE, "card_sub", w / 2, ha="right").set(sub) + 12
        self.fit(ax, ds.PAD, ds.TITLE_BASE, "card_title", w - 2 * ds.PAD - used - reserve).set(text)

    def bar(self, ax, x, y, w, h, colour):
        ds.rrect(ax, x, y, w, h, h / 2, ds.TRACK, z=2)
        fill = ds.rrect(ax, x, y, h, h, h / 2, colour, z=3)

        def set_v(v):
            v = min(1.0, max(0.0, float(v)))
            fill.set_visible(v > 0.003)
            fill.set_width(max(h, w * v))
        return set_v

    def gradient(self, ax, x, y, w, h, colours, clip_r):
        im = ax.imshow(np.asarray(colours)[None, :, :3], extent=(x, x + w, y + h, y), aspect="auto",
                       interpolation="bilinear", zorder=2)
        clip = ds.rrect(ax, x, y, w, h, clip_r, "none", z=2)
        im.set_clip_path(clip)
        reset_limits(ax)
        return im

    # ------------------------------------------------------------------ header
    def b_header(self):
        ax = self.card((0, 0, W, ds.HEAD), fill=False)
        name = os.path.splitext(os.path.basename(self.m["config"]))[0].replace("_", " ").capitalize()
        tw = self.fit(ax, ds.OUTER, 38, "frame_title", 360).set(name)
        n = self.n_steps - 1
        of_w = self.fit(ax, W - ds.OUTER, 36, "step_aux", 80, ha="right").set(f"/ {n}")
        digits_w = self.width("0" * len(str(n)), "step")
        num_x = W - ds.OUTER - of_w - 8
        num = self.fit(ax, num_x, 36, "step", digits_w, ha="right")
        lab_x = num_x - digits_w - 10
        lab_w = self.fit(ax, lab_x, 36, "meta", 60, ha="right", color=ds.INK3).set("Step")
        bar_w = 132
        ds.rrect(ax, W - ds.OUTER - bar_w, 48, bar_w, 4, 2, ds.CANVAS_TRACK, z=2)
        prog = ds.rrect(ax, W - ds.OUTER - bar_w, 48, 4, 4, 2, ds.IRIS, z=3)
        meta_x = ds.OUTER + tw + 20
        meta = f"seed {self.m['seed']}  ·  random policy  ·  {self.m['view']} × {self.m['view']} view of a " \
               f"{self.m['width']} × {self.m['height']} world"
        if self.m.get("synthetic"):
            meta += "  ·  sensor ranges overridden for this sketch"
        self.fit(ax, meta_x, 38, "meta", min(lab_x - lab_w, W - ds.OUTER - bar_w) - 32 - meta_x).set(meta)

        def upd(st):
            num.set(str(st["t"]))
            prog.set_width(max(4, bar_w * st["t"] / max(1, n)))
        self.updates.append(upd)

    # ------------------------------------------------------------------ interoception
    def b_intero(self, ax, w, h):
        self.title(ax, w, "Interoception")
        cw = (w - 2 * ds.PAD - ds.GAP) / 2
        xs = (ds.PAD, ds.PAD + cw + ds.GAP)
        self.fit(ax, xs[0], 66, "col_head", cw).set("Observed")
        self.fit(ax, xs[1], 66, "col_head", cw).set("True")
        ax.plot([ds.PAD, w - ds.PAD], [76, 76], color=ds.LINE, lw=1 * ds.PT)
        y = 104
        for row in self.rows:
            reserve = 0
            if row["kind"] == "temp":
                t_lo, t_hi = self.scale.b["low"], self.scale.b["high"]
                reserve = self.fit(ax, w - ds.PAD, y, "caption", cw, ha="right").set(
                    f"limits {ds.signed(t_lo)} / {ds.signed(t_hi)}") + 12
            self.fit(ax, xs[0], y, "row_label", w - 2 * ds.PAD - reserve).set(row["label"])
            for col, x in zip(("obs", "true"), xs):
                fn = row[col]
                if fn is None:
                    self.fit(ax, x, y + 30, "not_observed", cw).set("not observed" if col == "obs" else "not recorded")
                    ds.rrect(ax, x, y + 40, cw, 6, 3, "none", ds.OUTLINE, 1, z=2)
                    continue
                note_w = 0
                if col == "true" and row["note"]:
                    note_w = self.fit(ax, x + cw, y + 30, "caption", cw / 2, ha="right").set(row["note"]) + 8
                val = self.fit(ax, x, y + 30, "value", cw - note_w)
                if row["kind"] == "bar":
                    set_v = self.bar(ax, x, y + 40, cw, 6, row["colour"])

                    def upd(st, fn=fn, val=val, set_v=set_v):
                        v = fn(st)
                        val.set(f"{v:.2f}")
                        set_v(v)
                else:
                    set_v = self.gauge(ax, x, y + 40, cw)

                    def upd(st, fn=fn, val=val, set_v=set_v):
                        v = fn(st)
                        val.set(ds.signed(v, 1) + "°")
                        set_v(v)
                self.updates.append(upd)
            y += 76
        foot = y - 76 + 46 + 10
        ax.plot([ds.PAD, w - ds.PAD], [foot, foot], color=ds.LINE, lw=1 * ds.PT)
        note = ("Noise off in this episode, so observed = true." if not self.m["noise"]
                else "Noise on: observed and true values differ.")
        self.fit(ax, ds.PAD, foot + 24, "caption", w - 2 * ds.PAD).set(note)

    def gauge(self, ax, x, y, w):
        """Body temperature on the shared scale: track spans the survivable band, marker = value."""
        lo, hi, sp = self.scale.b["low"], self.scale.b["high"], self.scale.b["setpoint"]
        g = np.linspace(lo, hi, 128)
        im = self.gradient(ax, x, y, w, 6, [self.scale.colour(v) for v in g], 3)
        im.set_alpha(0.9)
        if self.scale.out_of_range(lo) or self.scale.out_of_range(hi):    # band reaches past the episode range
            ds.rrect(ax, x, y, w, 6, 3, "none", ds.INK, 2, z=3)
        xs = x + w * (sp - lo) / (hi - lo)
        ax.plot([xs, xs], [y - 3, y + 9], color=ds.INK3, lw=1 * ds.PT, zorder=3)
        dot = ax.add_patch(Circle((x, y + 3), 6, fc="#FFFFFF", ec=ds.INK, lw=2 * ds.PT, zorder=4))

        def set_v(v):
            dot.set_center((x + w * (min(hi, max(lo, v)) - lo) / (hi - lo), y + 3))
        return set_v

    # ------------------------------------------------------------------ minimap
    def view_origin(self, st):
        n, half = self.m["view"], self.m["view"] // 2
        ar, ac = st["agent"]
        return (max(0, min(self.m["height"] - n, ar - half)), max(0, min(self.m["width"] - n, ac - half)))

    def cell_colour(self, r, c):
        return self.scale.colour(self.m["thermal_field"][r][c]) if self.thermal else ds.TRACK

    def b_minimap(self, ax, w, h):
        m = self.m
        self.title(ax, w, "World", f"{m['width']} × {m['height']}")
        hh, ww = m["height"], m["width"]
        s = min(w - 2 * ds.PAD, h - 46 - ds.PAD)
        cell = s / max(hh, ww)
        ox, oy = (w - cell * ww) / 2, 46
        for r in range(hh):
            for c in range(ww):
                ds.rrect(ax, ox + c * cell + 1, oy + r * cell + 1, cell - 2, cell - 2, 3, self.cell_colour(r, c),
                         z=1, alpha=0.75 if self.thermal else 1.0)
        inside = lambda p: 0 <= p[0] < hh and 0 <= p[1] < ww  # noqa: E731  (inactive entities park off-grid)
        centre = lambda p: (ox + (p[1] + 0.5) * cell, oy + (p[0] + 0.5) * cell)  # noqa: E731
        obs = [ds.rrect(ax, 0, 0, cell * 0.56, cell * 0.56, 2, ds.MINIMAP_COLOUR[m["obstacle_names"][t]], z=3)
               for t in m["obs_type"]]
        cores = [ax.add_patch(Circle((0, 0), cell * 0.12, fc=ds.FIRE_CORE, lw=0, zorder=3.5))
                 if m["obstacle_names"][t] == "campfire" else None for t in m["obs_type"]]
        res = [ax.add_patch(Circle((0, 0), cell * 0.24, fc=ds.MINIMAP_COLOUR[RES_NAMES[t]], ec="#FFFFFF",
                                   lw=1.2 * ds.PT, zorder=4)) for t in m["res_type"]]
        ani = [ax.add_patch(Circle((0, 0), cell * 0.26, fc=ds.MINIMAP_COLOUR[k], ec="#FFFFFF", lw=1.2 * ds.PT, zorder=4))
               for k in m["animal_classes"]]
        # hiding predator: an amber pip (34 % of the dot width) echoing the glyph's eyes, so it is not a predator dot
        pips = [ax.add_patch(Circle((0, 0), cell * 0.24 * 0.34, fc=ds.HIDE_EYE, lw=0, zorder=4.5))
                if RES_NAMES[t] == "hiding_predator" else None for t in m["res_type"]]
        agent = ax.add_patch(Circle((0, 0), cell * 0.32, fc=ds.IRIS, ec="#FFFFFF", lw=2 * ds.PT, zorder=6))
        n = m["view"]
        view = ds.rrect(ax, 0, 0, n * cell + 2, n * cell + 2, 6, "none", ds.IRIS, 2.2, z=7)

        def upd(st):
            for p, core, pos in zip(obs, cores, st["obs_pos"]):
                p.set_visible(inside(pos))
                cx, cy = centre(pos)
                if core is not None:
                    core.set_visible(inside(pos))
                    core.set_center((cx, cy))
                p.set_x(cx - cell * 0.28)
                p.set_y(cy - cell * 0.28)
            for p, pip, pos, act in zip(res, pips, st["res_pos"], st["res_active"]):
                for q in (p, pip):
                    if q is not None:
                        q.set_visible(bool(act) and inside(pos))
                        q.set_center(centre(pos))
            for p, pos in zip(ani, st["animal_pos"]):
                p.set_visible(inside(pos))
                p.set_center(centre(pos))
            agent.set_center(centre(st["agent"]))
            r0, c0 = self.view_origin(st)
            view.set_x(ox + c0 * cell - 1)
            view.set_y(oy + r0 * cell - 1)
        self.updates.append(upd)

    # ------------------------------------------------------------------ grid view
    def b_arena(self, ax, w, h):
        m, n = self.m, self.m["view"]
        pill_w, pill_h = 118, 28
        px = w - ds.PAD - pill_w
        ds.rrect(ax, px, 12, pill_w, pill_h, 14, ds.IRIS_SOFT, z=2)
        badge = self.fit(ax, px + pill_w / 2, 31, "badge", pill_w - 16, ha="center")
        act_w = self.fit(ax, px - 10, 30, "card_sub", 80, ha="right").set("Action")
        self.title(ax, w, "Grid view", reserve=pill_w + act_w + 10)
        cell = GRID_CELL
        x0, y0 = (w - n * cell) / 2, 48
        self.grid_extent = (x0, y0, n * cell, n * cell)
        names = sorted(set(m["obstacle_names"]) | {RES_NAMES[t] for t in m["res_type"]} | set(m["animal_classes"]))
        for nm in names:
            if nm not in ds.TERRAIN_GLYPHS and nm not in ds.TOKEN_GLYPHS:
                raise ValueError(f"entity {nm!r} has no glyph in dashboard_style")
        slots = []
        for i in range(n):
            for j in range(n):
                cx, cy = x0 + (j + 0.5) * cell, y0 + (i + 0.5) * cell
                bg = ds.rrect(ax, cx - cell / 2 + 1, cy - cell / 2 + 1, cell - 2, cell - 2, 8, ds.TRACK, z=1)
                groups = {}
                for nm in names:
                    fn = ds.TERRAIN_GLYPHS.get(nm) or ds.TOKEN_GLYPHS[nm]
                    groups[nm] = fn(ax, cx, cy, cell)
                agent = ds.agent_marker(ax, cx, cy, cell)
                for arts in groups.values():
                    for a in arts:
                        a.set_visible(False)
                for k, a in agent.items():
                    for p in (a if k == "base" else [a]):
                        p.set_visible(False)
                slots.append((bg, groups, agent))
        reset_limits(ax)

        def upd(st):
            an = m["action_names"][st["action"]] if st["action"] >= 0 else None
            badge.set(f"{ds.ARROW_TEXT.get(an, '•')}  {an.title()}" if an else "Start")
            r0, c0 = self.view_origin(st)
            where = {}
            for k, p in enumerate(st["obs_pos"]):
                where.setdefault(tuple(p), set()).add(m["obstacle_names"][m["obs_type"][k]])
            for k, p in enumerate(st["res_pos"]):
                if st["res_active"][k]:
                    where.setdefault(tuple(p), set()).add(RES_NAMES[m["res_type"][k]])
            for k, p in enumerate(st["animal_pos"]):
                where.setdefault(tuple(p), set()).add(m["animal_classes"][k])
            for idx, (bg, groups, agent) in enumerate(slots):
                r, c = r0 + idx // n, c0 + idx % n
                bg.set_facecolor(self.cell_colour(r, c))
                here = where.get((r, c), set())
                for nm, arts in groups.items():
                    for a in arts:
                        a.set_visible(nm in here)
                is_agent = [r, c] == list(st["agent"])
                mark = an if an in ds.ARROW_VEC else "dot"
                for k, a in agent.items():
                    for p in (a if k == "base" else [a]):
                        p.set_visible(is_agent and k in ("base", mark))
        self.updates.append(upd)

    # ------------------------------------------------------------------ right column
    def b_prop(self, ax, w, h):
        self.title(ax, w, "Proprioception", "previous action")
        names, gap = self.m["action_names"], 8
        cw = (w - 2 * ds.PAD - gap * (len(names) - 1)) / len(names)
        chips = []
        for k, nm in enumerate(names):
            x = ds.PAD + k * (cw + gap)
            rect = ds.rrect(ax, x, 52, cw, 32, 8, ds.TRACK, z=2)
            t = self.fit(ax, x + cw / 2, 73, "chip_on", cw - 8, ha="center")
            t.set(nm.title())                # measured at the heavier weight, so both states fit
            chips.append((rect, t.t))

        def upd(st):
            vec = sensor(st, "Proprioception")["vector"]
            hot = int(np.argmax(vec)) if max(vec) > 0 else -1
            for k, (rect, t) in enumerate(chips):
                on = k == hot
                rect.set_facecolor(ds.IRIS if on else ds.TRACK)
                weight, _, colour = ds.TYPE["chip_on" if on else "chip"]
                t.set_color(colour)
                t.set_fontweight(weight)
        self.updates.append(upd)

    def b_extero(self, ax, w, h):
        self.title(ax, w, "Extero nociception")
        val = self.fit(ax, ds.PAD, h - 58, "hero", w - 2 * ds.PAD)
        set_v = self.bar(ax, ds.PAD, h - 38, w - 2 * ds.PAD, 8, ds.NOCI)

        def upd(st):
            v = sensor(st, "Extero Nociception")["intensity"]
            val.set(f"{v:.2f}")
            set_v(v)
        self.updates.append(upd)

    def b_coll(self, ax, w, h):
        self.title(ax, w, "Collision")
        c, g = 30, 4
        ccx, ccy = w / 2, h - ds.PAD - 1.5 * c - g
        cells = []
        for (dr, dc), lab in zip(ds.visual_offsets(1), "CURDL"):
            x, y = ccx + dc * (c + g) - c / 2, ccy + dr * (c + g) - c / 2
            rect = ds.rrect(ax, x, y, c, c, 6, ds.TRACK, z=2)
            t = self.fit(ax, x + c / 2, y + c / 2 + 1, "coll_letter", c - 4, ha="center", va="center")
            t.set(lab)
            cells.append((rect, t.t))

        def upd(st):
            for (rect, t), v in zip(cells, sensor(st, "Collision")["vector"]):
                hit = v > 0.5
                rect.set_facecolor(ds.NOCI if hit else ds.TRACK)
                t.set_color("#FFFFFF" if hit else ds.INK3)
        self.updates.append(upd)

    def b_thermo(self, ax, w, h):
        sensed = self.has("Thermoception")
        sc, b = self.scale, self.scale.b
        if sensed:
            self.title(ax, w, "Thermoception", "cell minus body, °")
            rng = sensor(self.steps[0], "Thermoception")["range"]
            if rng != 1:
                raise LayoutOverflowError(f"thermoception range {rng}: this sketch sizes the diamond for range 1")
            tc, g = 46, 4
            tcx, tcy = ds.PAD + 1.5 * tc + g, 56 + 1.5 * tc + g
            cells = []
            for dr, dc in ds.visual_offsets(1):
                x, y = tcx + dc * (tc + g) - tc / 2, tcy + dr * (tc + g) - tc / 2
                rect = ds.rrect(ax, x, y, tc, tc, 8, ds.TRACK, z=2)
                cells.append((rect, self.fit(ax, x + tc / 2, y + tc / 2 + 1, "cell_num", tc - 6, ha="center", va="center")))

            def upd(st):
                for (rect, t), v in zip(cells, sensor(st, "Thermoception")["vector"]):
                    col = sc.colour(v)
                    rect.set_facecolor(col)
                    clipped = sc.out_of_range(v)          # clamp and outline: beyond the episode range
                    rect.set_edgecolor(ds.INK if clipped else "none")
                    rect.set_linewidth(2 * ds.PT if clipped else 0)
                    t.set(ds.signed(v))
                    t.t.set_color("#FFFFFF" if ds.luminance(col) < 0.45 else ds.INK)
            self.updates.append(upd)
            lx0 = tcx + 1.5 * tc + g + 36
        else:
            self.title(ax, w, "Temperature scale")
            lx0 = ds.PAD + 12
        lw = w - lx0 - 22
        ly = 96
        self.fit(ax, lx0, 66, "caption_medium", lw, color=ds.INK2).set("Scale shared by every step of this episode")
        self.gradient(ax, lx0, ly, lw, 12, sc.cmap(np.linspace(0, 1, 512)), 0.01)
        ax.add_patch(Polygon([(lx0, ly), (lx0 - 9, ly + 6), (lx0, ly + 12)], fc=sc.cmap(0.0), lw=0, zorder=2))
        ax.add_patch(Polygon([(lx0 + lw, ly), (lx0 + lw + 9, ly + 6), (lx0 + lw, ly + 12)], fc=sc.cmap(1.0), lw=0, zorder=2))
        xpos = lambda v: lx0 + lw * sc.pos(v)  # noqa: E731
        # ticks at every anchor; labels placed by priority, dropping any whose measured box crowds a neighbour
        placed = []
        anchors = dict(b["anchors"])
        for name, v in b["anchors"]:
            ax.plot([xpos(v)] * 2, [ly + 12, ly + 17], color=ds.INK3, lw=1 * ds.PT, zorder=3)
        for name in ("setpoint", "lower body limit", "upper body limit", "episode min", "episode max"):
            if name not in anchors:
                continue
            v = anchors[name]
            t = ds.text(ax, xpos(v), ly + 32, ds.signed(v, 0 if float(v).is_integer() else 1), "caption", ha="center")
            bb = t.get_window_extent(self.r)
            if any(bb.x0 < o.x1 + 8 and o.x0 < bb.x1 + 8 for o in placed):
                t.remove()
            else:
                placed.append(bb)
        self.temp_labels = len(placed)
        xa, xb = xpos(b["low"]), xpos(b["high"])
        ax.plot([xa, xa, xb, xb], [ly + 40, ly + 45, ly + 45, ly + 40], color=ds.INK2, lw=1.2 * ds.PT, zorder=3)
        self.fit(ax, (xa + xb) / 2, ly + 62, "caption_medium", lw + 40, ha="center", color=ds.INK2).set("survivable body range")
        for i, line in enumerate(("Grid cells and body temperature: absolute.", "Thermoception: cell minus body.",
                                  f"Same colours; {ds.signed(b['setpoint'])} is neutral.")):
            self.fit(ax, lx0, ly + 86 + 16 * i, "caption", w - lx0 - ds.PAD).set(line)
        tri = ax.add_patch(Polygon([(0, 0), (0, 0), (0, 0)], fc=ds.INK, lw=0, zorder=4))
        body = ds.text(ax, 0, ly - 3, "body", "caption_medium", color=ds.INK)

        def upd_body(st):
            x = xpos(st["body_temp"])
            tri.set_xy([(x, ly - 2), (x - 6, ly - 11), (x + 6, ly - 11)])
            right = x < lx0 + 0.75 * lw
            body.set_x(x + 9 if right else x - 9)
            body.set_ha("left" if right else "right")
        self.updates.append(upd_body)

    # ------------------------------------------------------------------ sensor band (option A)
    def b_band(self, ax, w, h):
        st0 = self.steps[0]
        groups = []
        if self.olf_range:
            s = sensor(st0, "Olfactory")
            R = s["range"]
            groups.append(dict(title="Olfaction", R=R, box=(2 * R + 1) * 22, cmap=ds.OLF_CMAP, vmax=self.olf_max,
                               viz="Olfactory", nf=s["num_features"],
                               maps=[(OLF_NAMES[lab], "seq", k) for k, lab in enumerate(s["labels"])]))
        if self.vis_range:
            s = sensor(st0, "Visual")
            R = s["range"]
            box = 88
            if box / (2 * R + 1) < 12:
                raise LayoutOverflowError(f"vision range {R}: map cells would be {box / (2 * R + 1):.1f}px (< 12px)")
            groups.append(dict(title="Vision", R=R, box=box, cmap=ds.VIS_CMAP, vmax=self.vis_max, viz="Visual",
                               nf=s["num_features"],
                               maps=[("Terrain", "terrain", None)]
                               + [(VIS_NAMES[lab], "seq", 3 + k) for k, lab in enumerate(s["labels"][3:])]))
        gap, divider = 6, 32
        for g in groups:                         # measure: slot widths, wrapped labels, header width
            g["slots"] = []
            for label, kind, ch in g["maps"]:
                slot = g["box"] + gap
                if isinstance(label, tuple):
                    lines, roles = list(label), ["map_label", "caption"]
                else:
                    lines = [label]
                    if self.width(label, "map_label") > slot - 4 and " " in label:
                        lines = label.split(" ", 1)
                    roles = ["map_label"] * len(lines)
                slot = max(slot, max(self.width(li, ro) for li, ro in zip(lines, roles)) + (12 if len(lines) > 1 else 4))
                g["slots"].append((slot, list(zip(lines, roles))))
            g["range_txt"] = f"range {g['R']}"
            g["max_txt"] = f"{g['vmax']:.1f}"
            g["head_w"] = (self.width(g["title"], "card_title") + 8 + self.width(g["range_txt"], "card_sub") + 16
                           + self.width("0", "caption") + 6 + 96 + 6 + self.width(g["max_txt"], "caption"))
            g["w"] = max(g["head_w"], sum(sl for sl, _ in g["slots"]))
        need = 2 * ds.PAD + sum(g["w"] for g in groups) + divider * (len(groups) - 1)
        if need > w:
            raise LayoutOverflowError(f"sensor band needs {need:.0f}px, has {w:.0f}px: "
                                      + ", ".join(f"{g['title']}={g['w']:.0f}" for g in groups))
        maxbox = max(g["box"] for g in groups)
        content = maxbox + 22 + 15 + 4
        top = 52 + max(0, (h - ds.PAD - 52 - content) / 2)
        x = ds.PAD
        updates = []
        for gi, g in enumerate(groups):
            if gi:
                ax.plot([x - divider / 2] * 2, [ds.PAD, h - ds.PAD], color=ds.LINE, lw=1 * ds.PT)
            tw = self.fit(ax, x, ds.TITLE_BASE, "card_title", g["w"]).set(g["title"])
            rw = self.fit(ax, x + tw + 8, ds.TITLE_BASE, "card_sub", 80).set(g["range_txt"])
            zx = x + tw + 8 + rw + 16
            zw = self.fit(ax, zx, ds.TITLE_BASE, "caption", 20).set("0")
            sx = zx + zw + 6
            self.gradient(ax, sx, ds.TITLE_BASE - 8, 96, 8, g["cmap"](np.linspace(0, 1, 128)), 4)
            self.fit(ax, sx + 96 + 6, ds.TITLE_BASE, "caption", 40).set(g["max_txt"])
            offs = ds.visual_offsets(g["R"])
            k = 2 * g["R"] + 1
            cs = g["box"] / k
            mx = x
            for (label, kind, ch), (slot, lines) in zip(g["maps"], g["slots"]):
                bx = mx + (slot - g["box"]) / 2
                by = top + (maxbox - g["box"]) / 2
                cells = []
                for dr, dc in offs:
                    cells.append(ds.rrect(ax, bx + (dc + g["R"]) * cs + 1.5, by + (dr + g["R"]) * cs + 1.5,
                                          cs - 3, cs - 3, 3, ds.TRACK, z=2))
                ds.rrect(ax, bx + g["R"] * cs + 0.5, by + g["R"] * cs + 0.5, cs - 1, cs - 1, 3, "none", ds.IRIS, 2, z=3)
                for li, (line, role) in enumerate(lines):
                    self.fit(ax, mx + slot / 2, top + maxbox + 22 + li * 15, role, slot, ha="center").set(line)
                updates.append((g, kind, ch, cells))
                mx += slot
            x += g["w"] + divider

        def upd(st):
            tabs = {}
            for g, kind, ch, cells in updates:
                if g["viz"] not in tabs:
                    tabs[g["viz"]] = np.asarray(sensor(st, g["viz"])["vector"], float).reshape(-1, g["nf"])
                tab = tabs[g["viz"]]
                for p, row in zip(cells, tab):
                    if kind == "terrain":
                        off = row[:3].max() <= 0
                        p.set_facecolor(ds.OFF_WORLD if off else ds.TERRAIN[int(np.argmax(row[:3]))])
                        p.set_edgecolor(ds.OUTLINE if off else "none")
                        p.set_linewidth(1 * ds.PT)
                    else:
                        v = row[ch]
                        if v > g["vmax"] + 1e-9:
                            raise ValueError(f"{g['title']} reading {v} above the episode maximum {g['vmax']}")
                        p.set_facecolor(ds.TRACK if v <= 1e-6 else g["cmap"](min(1.0, v / g["vmax"])))
        self.updates.append(upd)

    # ------------------------------------------------------------------ per step
    def frame(self, st):
        for u in self.updates:
            u(st)
        self.canvas.draw()
        self.audit()
        return np.asarray(self.canvas.buffer_rgba())[..., :3].copy()

    def audit(self):
        """Text audit on RENDERED extents: none leaves its card, no two intersect, no number in the grid view."""
        items = []
        for ax in self.fig.axes:
            if ax is self.bg:
                continue
            box = ax.bbox
            for t in ax.texts:
                if not t.get_visible() or not t.get_text():
                    continue
                bb = t.get_window_extent(self.r)
                if bb.x0 < box.x0 - 0.5 or bb.x1 > box.x1 + 0.5 or bb.y0 < box.y0 - 0.5 or bb.y1 > box.y1 + 0.5:
                    raise LayoutOverflowError(f"text {t.get_text()!r} leaves its card")
                items.append((t.get_text(), bb))
        for i, (sa, a) in enumerate(items):
            for sb, b in items[i + 1:]:
                if a.x0 < b.x1 - 1 and b.x0 < a.x1 - 1 and a.y0 < b.y1 - 1 and b.y0 < a.y1 - 1:
                    raise LayoutOverflowError(f"text collision: {sa!r} / {sb!r}")
        ax_x, ax_y, _, _ = self.boxes["arena"]
        gx, gy, gw, gh = self.grid_extent
        x0, x1 = ax_x + gx, ax_x + gx + gw
        y0, y1 = H - (ax_y + gy + gh), H - (ax_y + gy)            # display coords, y up
        for s, bb in items:
            if re.search(r"[-+−]?\d", s) and bb.x0 < x1 and x0 < bb.x1 and bb.y0 < y1 and y0 < bb.y1:
                raise LayoutOverflowError(f"numeric text {s!r} inside the grid view")
        self.n_texts = len(items)


def write_data(stem, rows):
    with open(os.path.join(FIGS, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            fh.write("\t".join(str(r[k]) for k in ("what", "used", "total", "note")) + "\n")


def main():
    with open(os.path.join(HERE, "data", "episode.json")) as fh:
        ep = json.load(fh)
    meta, steps = ep["meta"], ep["steps"]
    house.apply()
    ds.register_fonts()
    scale = ds.TemperatureScale(meta["thermal_field"], meta["min_temperature"], meta["max_temperature"],
                                meta["temperature_setpoint"])
    b = scale.b
    print("temperature anchors (episode range): " + ", ".join(f"{n} {v:+.2f} @ {q:.3f}" for (n, v), q in
                                                             zip(b["anchors"], scale.Y)))
    out_dir = os.path.join(FIGS, "fig03_frames")
    os.makedirs(out_dir, exist_ok=True)

    d = Dashboard(meta, steps, scale, ALL)
    audited, max_diff, changed_px = 0, 0, 0
    frames = []
    for st in steps:
        arr = d.frame(st)
        assert arr.shape == (H, W, 3), arr.shape
        frames.append(arr)
        audited += 1
    # 256-colour PNG only if it is visually identical: measure the worst per-pixel change
    quant = []
    for arr in frames:
        q = np.asarray(Image.fromarray(arr).quantize(256, method=Image.Quantize.MEDIANCUT,
                                                     dither=Image.Dither.NONE).convert("RGB"))
        diff = np.abs(q.astype(int) - arr.astype(int)).max(2)
        max_diff = max(max_diff, int(diff.max()))
        changed_px = max(changed_px, int((diff > 6).sum()))
        quant.append(q)
    use_quant = max_diff <= 6
    for st, arr in zip(steps, frames):
        im = Image.fromarray(arr)
        if use_quant:
            im = im.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(os.path.join(out_dir, f"step_{st['t']:03d}.png"), optimize=True)
    size = sum(os.path.getsize(os.path.join(out_dir, f)) for f in os.listdir(out_dir))
    print(f"frames: {audited}, {'256-colour' if use_quant else 'RGB'} PNG (quantised worst channel change {max_diff}, "
          f"{changed_px} px changed by > 6 in the worst frame), folder {size / 1e6:.2f} MB")
    d.frame(steps[REP_STEP])
    n_panels = len(d.boxes)
    print(f"step {REP_STEP}: {d.n_texts} texts audited, {d.temp_labels} temperature-scale labels placed")
    house.save(d.fig, os.path.join(FIGS, "fig03_proposed_dashboard"), column_px=1084)
    field = np.asarray(meta["thermal_field"])
    write_data("fig03_proposed_dashboard", [
        dict(what="recorded steps drawn (step scrubber)", used=audited, total=len(steps),
             note="every step of the exported episode; each frame passed the text audit"),
        dict(what="observed senses given a panel", used=sum(1 for k in meta["breakdown"] if k in TOGGLE_OF),
             total=len(meta["breakdown"]), note="the completeness rule refuses to draw if an observed sense has no panel"),
        dict(what="thermal field cells setting the temperature colour range", used=b["n_cells"], total=field.size,
             note=f"episode min {b['vmin']:+.1f} to max {b['vmax']:+.1f} over the one field recorded for the episode; "
                  "every step uses this range, and readings beyond it are clamped and outlined"),
    ])

    # Figure 4: the same step under three sense sets, to show re-packing
    variants = [
        ("All senses", ALL),
        ("Temperature system and proprioception switched off", ALL - {"thermal", "prop"}),
        ("Only satiation, extero nociception, collision and vision", frozenset({"extero", "coll", "vis"})),
    ]
    imgs, titles = [], []
    for label, on in variants:
        dv = Dashboard(meta, steps, scale, on)
        imgs.append(dv.frame(steps[REP_STEP]))
        titles.append((label, f"{len(dv.boxes)} panels · text audit passed"))
        plt.close(dv.fig)
    head, gap, pad = 48, 24, 24
    FW, FH = W + 2 * pad, pad + len(imgs) * (head + H) + (len(imgs) - 1) * gap + pad
    fig = plt.figure(figsize=(FW / ds.DPI, FH / ds.DPI), dpi=ds.DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), FW, FH, fc=ds.CANVAS, lw=0, zorder=0))
    y = pad
    for img, (label, sub) in zip(imgs, titles):
        t = ds.text(ax, pad, y + 30, label, "frame_title")
        fig.canvas.draw()
        ds.text(ax, pad + t.get_window_extent().width + 16, y + 30, sub, "card_sub")
        ax.imshow(img, extent=(pad, pad + W, y + head + H, y + head), interpolation="none", zorder=1)
        ds.rrect(ax, pad - 0.5, y + head - 0.5, W + 1, H + 1, 2, "none", ds.LINE, 1, z=2)
        ax.set_xlim(0, FW)
        ax.set_ylim(FH, 0)
        y += head + H + gap
    with matplotlib.rc_context({"savefig.dpi": ds.DPI}):
        house.save(fig, os.path.join(FIGS, "fig04_repacking"), column_px=1084)
    write_data("fig04_repacking", [
        dict(what="recorded steps drawn", used=1, total=len(steps), note=f"step {REP_STEP}, mid-episode, drawn under each sense set"),
        dict(what="sense sets drawn", used=len(variants), total=len(variants),
             note="the full campfire observation and two reduced sets; the recorded numbers are identical, only the panels change"),
    ])
    print(f"figure 3: {audited} frames, {n_panels} panels; figure 4: {len(variants)} sense sets")


if __name__ == "__main__":
    main()
