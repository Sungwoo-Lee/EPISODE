"""FIGURES 3 and 4 -- a sketch of the proposed episode dashboard, drawn from a real recorded episode.

QUESTION IT ANSWERS. What would the dashboard proposed in
docs/develop/active/refactors/RENDERER_LAYOUT_REDESIGN.md look like on real data, and does its layout
idea -- a registry of panels, boxes packed once per episode, text measured into its box -- hold when
senses are switched off?

WHAT IT IS NOT. Not the planned renderer. Nothing under src/ is imported or edited, the production
(V1) video path is untouched, and exact sizes, fonts and colours are the implementer's to settle. It
is a design sketch written in the plan's recommended toolkit: Matplotlib with its layout engine
unused, a small column packer, the figure built once per episode, and artists updated per step.

HOW IT IS COMPUTED. Reads data/episode.json (written by export_episode.py from the real campfire
world). For a given set of senses it registers the panels that are present, refuses to start if an
observed sense has no panel, packs three columns of boxes (raising LayoutOverflowError instead of
squeezing), builds every card, bar, label and icon slot once, then for each step updates their
values and draws. Every text is measured and shrunk into its box, down to an 11 pt floor, and every
drawn frame passes a text audit on the rendered extents: no two texts intersect and none leaves its
card.

OUTPUT (figures/, next to this file)
    fig03_frames/step_NNN.png                 every step, 1440 x 896 px (the page's step scrubber)
    fig03_proposed_dashboard.{svg,pdf,png}    step 15 (the page's still and full-size view)
    fig04_repacking.{svg,pdf,png}             step 15 under three sense sets
    <stem>.data.txt                           used / available statement per figure (guide 11b)

Run (from the repo root)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/fig03_proposed_dashboard.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
os.chdir(ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

import house  # noqa: E402

FIGS = os.path.join(HERE, "figures")
W, H, DPI = 1440, 896, 100
GUT, GAP, HEAD, PAD = 16, 12, 48, 12
COL_L, COL_R = 300, 330
MIN_PT = 11                      # text floor; numbers and labels raise rather than ellipsise
REP_STEP = 15
TRACK = "#e2e4e0"
GRASS = np.array(to_rgb("#ECFDF5"))
CMAP = matplotlib.colormaps["RdBu_r"]      # the production thermal colormap (renderer.py THERMAL_CMAP)
MONO = house.FONT_MONO
# colour -> meaning, fixed once for this sketch (register F11)
C_SAT, C_INOC, C_HARM, C_SMELL, C_VIS, C_AGENT = house.GREEN, house.ORANGE, house.RED, house.BLUE, house.INK_2, house.BLUE
ARROW = {"UP": "↑", "RIGHT": "→", "DOWN": "↓", "LEFT": "←", "REST": "○", "EAT": "+"}
DIAMOND = [(0, 0), (-1, 0), (0, 1), (1, 0), (0, -1)]     # get_visual_offsets(1): C U R D L
VIS_LABELS = ["GRS", "SND", "PLN", "FOD", "HPR", "PRD", "RCK", "NEU"]   # HPR = hiding_predator (plan Q11)
OWNER = {"Satiation": "vitals", "Interoceptive Nociception": "vitals", "Extero Nociception": "extero",
         "Thermoception": "thermo", "Olfaction": "olf", "Collision": "coll", "Proprioception": "prop",
         "Visual": "vis"}
TOGGLE_OF = {"Interoceptive Nociception": "intero", "Extero Nociception": "extero", "Thermoception": "thermal",
             "Olfaction": "olf", "Collision": "coll", "Proprioception": "prop", "Visual": "vis"}
ALL = frozenset({"thermal", "intero", "olf", "extero", "coll", "prop", "vis"})


class LayoutOverflowError(ValueError):
    pass


def load_icons():
    out = {}
    for name in ["agent", "agent_food", "agent_predator", "agent_hiding_predator", "bush_agent", "bush", "food",
                 "hiding_predator", "neutral", "predator", "rock", "tree"]:
        im = Image.open(os.path.join(ROOT, "assets", f"{name}.png")).convert("RGBA")
        im.thumbnail((96, 96), Image.LANCZOS)
        sq = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        sq.paste(im, ((96 - im.width) // 2, (96 - im.height) // 2))
        out[name] = np.asarray(sq).astype(float) / 255.0
    return out


class Fit:
    """A text that is measured into a width: shrinks toward MIN_PT, and raises below it."""

    def __init__(self, ax, x, y, size, max_w, **kw):
        self.t = ax.text(x, y, "", fontsize=size, clip_on=True, **kw)
        self.size, self.max_w = size, max_w

    def set(self, s, renderer):
        size = self.size
        self.t.set_text(s)
        self.t.set_fontsize(size)
        while self.t.get_window_extent(renderer).width > self.max_w:
            if size - 0.5 < MIN_PT:
                raise LayoutOverflowError(f"text {s!r} does not fit {self.max_w:.0f}px at the {MIN_PT} pt floor")
            size -= 0.5
            self.t.set_fontsize(size)


def sensor(st, name):
    for s in st["sensors"]:
        if s["name"] == name:
            return s
    return None


def signed(v, d=0):
    return f"{v:+.{d}f}".replace("-", "−")


class Dashboard:
    def __init__(self, meta, n_steps, icons, on=ALL):
        self.m, self.n_steps, self.icons, self.on = meta, n_steps, icons, on
        self.fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
        self.fig.set_layout_engine("none")
        self.canvas = FigureCanvasAgg(self.fig)
        self.r = self.canvas.get_renderer()
        self.updates = []
        bd = meta["breakdown"]
        self.thermal = "thermal" in on and len(meta["thermal_field"]) > 0
        # completeness rule: every observed sense has a present panel, or was switched off on purpose
        for name in bd:
            if name not in OWNER:
                raise ValueError(f"observed sense {name!r} has no panel in the registry")
        self.has = lambda name: name in bd and TOGGLE_OF.get(name, "") in on | {""}
        panels = self.registry()
        self.boxes = self.pack(panels)
        self.header()
        for p in panels:
            ax = self.card(self.boxes[p["key"]])
            p["build"](ax, *self.boxes[p["key"]][2:])

    # ------------------------------------------------------------------ registry + packer
    def registry(self):
        rows = int("Satiation" in self.m["breakdown"]) + int(self.has("Interoceptive Nociception"))
        reg = [
            dict(key="vitals", col="left", min_h=44 + 48 * rows + (68 if self.thermal else 0), build=self.b_vitals),
            dict(key="minimap", col="left", min_h=220, grow=True, build=self.b_minimap),
            dict(key="arena", col="centre", min_h=420, grow=True, build=self.b_arena),
            dict(key="olf", col="right", min_h=132, present=self.has("Olfaction"), build=self.b_olf),
            dict(key="extero", col="right", min_h=96, present=self.has("Extero Nociception"), build=self.b_extero),
            dict(key="thermo", col="right", min_h=140, present=self.has("Thermoception") and self.thermal, build=self.b_thermo),
            dict(key="coll", col="right", min_h=100, present=self.has("Collision"), build=self.b_coll),
            dict(key="prop", col="right", min_h=112, present=self.has("Proprioception"), build=self.b_prop),
            dict(key="vis", col="right", min_h=132, present=self.has("Visual"), build=self.b_vis),
        ]
        return [p for p in reg if p.get("present", True)]

    @staticmethod
    def pack(panels):
        cols = {"left": (GUT, COL_L), "centre": (2 * GUT + COL_L, W - 4 * GUT - COL_L - COL_R),
                "right": (W - GUT - COL_R, COL_R)}
        top, avail = HEAD + GUT, H - HEAD - 2 * GUT
        boxes = {}
        for col, (x, w) in cols.items():
            ps = [p for p in panels if p["col"] == col]
            if not ps:
                continue
            need = sum(p["min_h"] for p in ps) + GAP * (len(ps) - 1)
            if need > avail:
                raise LayoutOverflowError(f"{col} column needs {need}px, has {avail}px: "
                                          + ", ".join(f"{p['key']}={p['min_h']}" for p in ps))
            growers = [p for p in ps if p.get("grow")] or ps
            spare, total = avail - need, sum(p["min_h"] for p in growers)
            y = top
            for i, p in enumerate(ps):
                h = p["min_h"] + (int(spare * p["min_h"] / total) if p in growers else 0)
                if i == len(ps) - 1:
                    h = top + avail - y
                boxes[p["key"]] = (x, y, w, h)
                y += h + GAP
        keys = list(boxes)
        for i, a in enumerate(keys):              # boxes are disjoint by construction; prove it
            for b in keys[i + 1:]:
                ax_, ay, aw, ah = boxes[a]
                bx, by, bw, bh = boxes[b]
                if ax_ < bx + bw and bx < ax_ + aw and ay < by + bh and by < ay + ah:
                    raise LayoutOverflowError(f"boxes {a} and {b} intersect")
        return boxes

    # ------------------------------------------------------------------ drawing helpers
    def card(self, box, fill=True):
        x, y, w, h = box
        ax = self.fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
        ax.set_autoscale_on(False)
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        ax.axis("off")
        if fill:
            ax.add_patch(FancyBboxPatch((0.5, 0.5), w - 1, h - 1, boxstyle="round,pad=0,rounding_size=4",
                                        facecolor=house.BG_SOFT, edgecolor=house.TICK_LINE, linewidth=1, zorder=0))
        return ax

    def title(self, ax, w, text, sub=None, reserve=0):
        used = 0
        if sub:
            s = ax.text(w - PAD, 12, sub, fontsize=MIN_PT, fontfamily=MONO, color=house.TEXT_LIGHT,
                        ha="right", va="top", clip_on=True)
            used = s.get_window_extent(self.r).width + 10
        Fit(ax, PAD, 11, 13, w - 2 * PAD - used - reserve, fontweight="semibold", color=house.INK_2,
            va="top").set(text.upper(), self.r)

    def obs_note(self):
        return None if self.m["noise"] else "obs only"

    def bar(self, ax, x, y, w, h, color):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=TRACK, edgecolor="none", zorder=1))
        return ax.add_patch(Rectangle((x, y), 0, h, facecolor=color, edgecolor="none", zorder=2))

    # ------------------------------------------------------------------ panels
    def header(self):
        ax = self.card((0, 0, W, HEAD), fill=False)
        ax.plot([0, W], [HEAD - 0.5, HEAD - 0.5], color=house.TICK_LINE, linewidth=1)
        Fit(ax, 20, HEAD / 2, 17, 900, fontweight="semibold", color=house.INK, va="center").set(
            f"GridWorld · campfire world · seed {self.m['seed']} · random policy", self.r)
        right = Fit(ax, W - 20, HEAD / 2, 15, 300, fontfamily=MONO, color=house.INK_2, ha="right", va="center")
        self.updates.append(lambda st: right.set(f"step {st['t']} / {self.n_steps - 1}", self.r))

    def b_vitals(self, ax, w, h):
        self.title(ax, w, "Vitals", self.obs_note())
        y, rows = 44, []
        if "Satiation" in self.m["breakdown"]:
            rows.append(("Satiation", "Satiation", C_SAT))
        if self.has("Interoceptive Nociception"):
            rows.append(("Interoceptive nociception", "Intero Nociception", C_INOC))
        for label, name, color in rows:
            # label takes the full card width; the value sits at the right end of the bar line, so a
            # long sense name never competes with its number for the same line
            Fit(ax, PAD, y, 12, w - 2 * PAD, fontweight="semibold", color=house.INK_2, va="top").set(label.upper(), self.r)
            val = Fit(ax, w - PAD, y + 27, 14, 60, fontfamily=MONO, color=house.INK, ha="right", va="center")
            bw = w - 2 * PAD - 70
            fill = self.bar(ax, PAD, y + 22, bw, 10, color)

            def upd(st, name=name, val=val, fill=fill, bw=bw):
                v = sensor(st, name)["intensity"]
                val.set(f"{v:.2f}", self.r)
                fill.set_width(bw * min(1.0, max(0.0, v)))
            self.updates.append(upd)
            y += 48
        if self.thermal:
            lo, hi, sp = self.m["min_temperature"], self.m["max_temperature"], self.m["temperature_setpoint"]
            gw = w - 2 * PAD
            Fit(ax, PAD, y, 12, gw - 70, fontweight="semibold", color=house.INK_2, va="top").set("BODY TEMPERATURE", self.r)
            val = Fit(ax, w - PAD, y - 1, 14, 70, fontfamily=MONO, color=house.INK, ha="right", va="top")
            ax.add_patch(Rectangle((PAD, y + 24), gw, 14, facecolor=TRACK, edgecolor="none", zorder=1))
            fill = ax.add_patch(Rectangle((PAD, y + 24), 0, 14, facecolor="none", edgecolor="none", zorder=2))
            xs = PAD + gw * (sp - lo) / (hi - lo)
            ax.plot([xs, xs], [y + 22, y + 40], color=house.INK, linewidth=1, zorder=3)
            for xd in (PAD + 1.5, PAD + gw - 1.5):
                ax.plot([xd, xd], [y + 24, y + 38], color=house.RED, linewidth=3, zorder=3)
            third = gw / 3 - 4
            Fit(ax, PAD, y + 44, MIN_PT, third, fontfamily=MONO, color=house.TEXT_LIGHT, va="top").set(f"{signed(lo)} limit", self.r)
            Fit(ax, w / 2, y + 44, MIN_PT, third, fontfamily=MONO, color=house.TEXT_LIGHT, ha="center", va="top").set("setpoint", self.r)
            Fit(ax, w - PAD, y + 44, MIN_PT, third, fontfamily=MONO, color=house.TEXT_LIGHT, ha="right", va="top").set(f"limit {signed(hi)}", self.r)

            def upd(st):
                bt = st["body_temp"]
                val.set(signed(bt, 2), self.r)
                xv = PAD + gw * (min(hi, max(lo, bt)) - lo) / (hi - lo)
                fill.set_x(min(xv, xs))
                fill.set_width(abs(xv - xs))
                fill.set_facecolor(CMAP((min(hi, max(lo, bt)) - lo) / (hi - lo)))
            self.updates.append(upd)

    def cell_rgb(self, r, c, alpha):
        if not self.thermal:
            return GRASS
        lo, hi = self.m["clim"]
        rgb = np.array(CMAP((self.m["thermal_field"][r][c] - lo) / (hi - lo))[:3])
        return rgb * alpha + GRASS * (1 - alpha)

    def view_origin(self, st):
        n, half = self.m["view"], self.m["view"] // 2
        ar, ac = st["agent"]
        return (max(0, min(self.m["height"] - n, ar - half)), max(0, min(self.m["width"] - n, ac - half)))

    def b_minimap(self, ax, w, h):
        self.title(ax, w, "Minimap", f"{self.m['width']} × {self.m['height']} world")
        hh, ww = self.m["height"], self.m["width"]
        s = min(w - 2 * PAD, h - 52)
        ox, oy, cell = (w - s) / 2, 40 + (h - 52 - s) / 2, s / max(hh, ww)
        img = np.array([[self.cell_rgb(r, c, 0.55) for c in range(ww)] for r in range(hh)])
        ax.imshow(img, extent=(ox, ox + cell * ww, oy + cell * hh, oy), interpolation="nearest", zorder=1)
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        pos = lambda p: (ox + (p[1] + 0.5) * cell, oy + (p[0] + 0.5) * cell)  # noqa: E731
        inside = lambda p: 0 <= p[0] < hh and 0 <= p[1] < ww  # noqa: E731  (inactive entities are parked off-grid)
        obs_col = {"rock": "#4B5563", "bush": "#4d7c0f", "campfire": "#ea580c"}
        obs = ax.scatter([], [], s=(cell * 0.45) ** 2, marker="s", zorder=3, linewidths=0)
        res = ax.scatter([], [], s=(cell * 0.4) ** 2, zorder=4, linewidths=0)
        ani = ax.scatter([], [], s=(cell * 0.5) ** 2, zorder=5, linewidths=0)
        agent = ax.scatter([], [], s=(cell * 0.6) ** 2, zorder=7, color=C_AGENT, edgecolors="white", linewidths=1.2)
        n = self.m["view"]
        view = ax.add_patch(Rectangle((0, 0), n * cell, n * cell, fill=False, edgecolor=C_AGENT, linewidth=1.6, zorder=6))
        m = self.m

        def upd(st):
            ok = [i for i, p in enumerate(st["obs_pos"]) if inside(p)]
            obs.set_offsets([pos(st["obs_pos"][i]) for i in ok] or np.empty((0, 2)))
            obs.set_facecolors([obs_col.get(m["obstacle_names"][m["obs_type"][i]], "#6b7280") for i in ok])
            act = [i for i, a in enumerate(st["res_active"]) if a and inside(st["res_pos"][i])]
            res.set_offsets([pos(st["res_pos"][i]) for i in act] or np.empty((0, 2)))
            res.set_facecolors([house.GREEN if m["res_type"][i] == 0 else house.RED for i in act])
            ok = [i for i, p in enumerate(st["animal_pos"]) if inside(p)]
            ani.set_offsets([pos(st["animal_pos"][i]) for i in ok] or np.empty((0, 2)))
            ani.set_facecolors(["#111827" if m["animal_classes"][i] == "predator" else "#0891B2" for i in ok])
            agent.set_offsets([pos(st["agent"])])
            r0, c0 = self.view_origin(st)
            view.set_xy((ox + c0 * cell, oy + r0 * cell))
        self.updates.append(upd)

    def b_arena(self, ax, w, h):
        n = self.m["view"]
        badge = ax.text(w - PAD, 10, "", fontsize=13, fontfamily=MONO, color=C_AGENT, ha="right", va="top",
                        clip_on=True, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=house.TICK_LINE))
        self.title(ax, w, f"Grid view · {n} × {n} around the agent", reserve=130)
        strip = 64 if self.thermal else 0
        side = min(w - 2 * PAD, h - 48 - PAD - strip)
        x0, y0, cell = (w - side) / 2, 46, side / n
        slots = []
        for i in range(n):
            for j in range(n):
                cx, cy = x0 + j * cell, y0 + i * cell
                bg = ax.add_patch(Rectangle((cx + 0.5, cy + 0.5), cell - 1, cell - 1, edgecolor="none", zorder=1))
                ins = cell * 0.13
                ext = (cx + ins, cx + cell - ins, cy + cell - ins, cy + ins)
                base = ax.imshow(np.zeros((96, 96, 4)), extent=ext, zorder=3, interpolation="bilinear")
                top = ax.imshow(np.zeros((96, 96, 4)), extent=ext, zorder=4, interpolation="bilinear")
                fire = ax.add_patch(Circle((cx + cell / 2, cy + cell / 2), cell * 0.2, facecolor="#f97316",
                                           edgecolor="#b91c1c", linewidth=2, zorder=3))
                tag = ax.text(cx + 6, cy + cell - 6, "", fontsize=MIN_PT, fontfamily=MONO, color=house.INK,
                              va="bottom", clip_on=True, zorder=6,
                              bbox=dict(boxstyle="square,pad=0.15", facecolor="white", alpha=0.8, edgecolor="none"))
                slots.append((bg, base, top, fire, tag))
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        if self.thermal:
            lo, hi = self.m["clim"]
            ys = y0 + side + 14
            ax.imshow(CMAP(np.linspace(0, 1, 256))[None, :, :3], extent=(x0 + 90, x0 + side - 90, ys + 10, ys),
                      aspect="auto", zorder=2)
            ax.set_xlim(0, w)
            ax.set_ylim(h, 0)
            Fit(ax, x0 + 82, ys + 5, 12, 80, fontfamily=MONO, color=house.INK_2, ha="right", va="center").set(f"cold {signed(lo)}", self.r)
            Fit(ax, x0 + side - 82, ys + 5, 12, 80, fontfamily=MONO, color=house.INK_2, va="center").set(f"{signed(hi)} hot", self.r)
            Fit(ax, w / 2, ys + 20, MIN_PT, side, color=house.TEXT_LIGHT, ha="center", va="top").set(
                "cell temperature, scale fixed for the whole episode", self.r)
        m, icons, blank = self.m, self.icons, np.zeros((96, 96, 4))

        def upd(st):
            an = m["action_names"][st["action"]] if st["action"] >= 0 else None
            badge.set_text(f"{ARROW[an]} {an}" if an else "start")
            r0, c0 = self.view_origin(st)
            where = {}
            for k, p in enumerate(st["obs_pos"]):
                where.setdefault(tuple(p), []).append(m["obstacle_names"][m["obs_type"][k]])
            for k, p in enumerate(st["res_pos"]):
                if st["res_active"][k]:
                    where.setdefault(tuple(p), []).append("food" if m["res_type"][k] == 0 else "hiding_predator")
            for k, p in enumerate(st["animal_pos"]):
                where.setdefault(tuple(p), []).append(m["animal_classes"][k])
            for idx, (bg, base, top, fire, tag) in enumerate(slots):
                r, c = r0 + idx // n, c0 + idx % n
                bg.set_facecolor(self.cell_rgb(r, c, 0.85))
                names = where.get((r, c), [])
                b_img = t_img = None
                fire.set_visible(False)
                if [r, c] == list(st["agent"]):
                    t_img = ("agent_predator" if "predator" in names else "agent_hiding_predator" if "hiding_predator" in names
                             else "bush_agent" if "bush" in names else "agent_food" if "food" in names else "agent")
                else:
                    for nm in names:
                        if nm == "campfire":
                            fire.set_visible(True)
                        elif nm in ("predator", "neutral"):
                            t_img = nm
                        elif nm in icons:
                            b_img = nm
                base.set_data(icons[b_img] if b_img else blank)
                top.set_data(icons[t_img] if t_img else blank)
                tag.set_text(signed(m["thermal_field"][r][c]) if self.thermal else "")
                tag.set_visible(self.thermal)
        self.updates.append(upd)

    def b_extero(self, ax, w, h):
        self.title(ax, w, "Extero nociception", self.obs_note())
        Fit(ax, PAD, 44, 12, 120, color=house.INK_2, va="top").set("observed", self.r)
        val = Fit(ax, w - PAD, 43, 14, 64, fontfamily=MONO, color=house.INK, ha="right", va="top")
        fill, bw = self.bar(ax, PAD, 68, w - 2 * PAD, 10, C_HARM), w - 2 * PAD

        def upd(st):
            v = sensor(st, "Extero Nociception")["intensity"]
            val.set(f"{v:.2f}", self.r)
            fill.set_width(bw * min(1.0, max(0.0, v)))
        self.updates.append(upd)

    def legend_and_bars(self, ax, w, h, labels, color):
        n, gap = len(labels), 6
        cw = (w - 2 * PAD - gap * (n - 1)) / n
        for k, lab in enumerate(labels):
            Fit(ax, PAD + k * (cw + gap) + cw / 2, 40, MIN_PT, cw, fontfamily=MONO, color=house.INK_2,
                ha="center", va="top").set(lab, self.r)
        top, bottom = 62, h - PAD
        fills = []
        for k in range(n):
            x = PAD + k * (cw + gap)
            ax.add_patch(Rectangle((x, top), cw, bottom - top, facecolor=TRACK, edgecolor="none", zorder=1))
            fills.append(ax.add_patch(Rectangle((x, bottom), cw, 0, facecolor=color, edgecolor="none", zorder=2)))
        return fills, bottom - top, bottom

    def b_olf(self, ax, w, h):
        self.title(ax, w, "Olfaction", self.obs_note())
        fills, span, bottom = self.legend_and_bars(ax, w, h, ["FOOD", "AN-A", "AN-B", "BUSH", "TREE"], C_SMELL)
        vmax = self.olf_max

        def upd(st):
            for f, v in zip(fills, sensor(st, "Olfactory")["vector"]):
                f.set_y(bottom - span * v / vmax)
                f.set_height(span * v / vmax)
        self.updates.append(upd)

    def b_vis(self, ax, w, h):
        self.title(ax, w, "Visual", "agent cell" + (" · obs only" if not self.m["noise"] else ""))
        fills, span, bottom = self.legend_and_bars(ax, w, h, VIS_LABELS, C_VIS)

        def upd(st):
            for f, v in zip(fills, sensor(st, "Visual")["vector"][:8]):
                v = min(1.0, max(0.0, v))
                f.set_y(bottom - span * v)
                f.set_height(span * v)
        self.updates.append(upd)

    def b_thermo(self, ax, w, h):
        self.title(ax, w, "Thermoception", "cell minus body")
        cw, ch, g = 70, 28, 4
        x0, y0 = (w - 3 * cw - 2 * g) / 2, 44
        span = max(abs(v) for v in self.m["clim"])
        cells = []
        for dr, dc in DIAMOND:
            x, y = x0 + (dc + 1) * (cw + g), y0 + (dr + 1) * (ch + g)
            rect = ax.add_patch(Rectangle((x, y), cw, ch, edgecolor="none", zorder=1))
            txt = Fit(ax, x + cw / 2, y + ch / 2, 13, cw - 6, fontfamily=MONO, ha="center", va="center")
            cells.append((rect, txt))

        def upd(st):
            for (rect, txt), v in zip(cells, sensor(st, "Thermoception")["vector"]):
                rect.set_facecolor(CMAP((v + span) / (2 * span)))
                txt.set(signed(v), self.r)
                txt.t.set_color("white" if abs(v) / span > 0.45 else house.INK)
        self.updates.append(upd)

    def b_coll(self, ax, w, h):
        self.title(ax, w, "Collision", self.obs_note())
        n, gap = 5, 6
        cw = (w - 2 * PAD - gap * (n - 1)) / n
        cells = []
        for k, lab in enumerate("CURDL"):
            x = PAD + k * (cw + gap)
            Fit(ax, x + cw / 2, 40, MIN_PT, cw, fontfamily=MONO, color=house.INK_2, ha="center", va="top").set(lab, self.r)
            cells.append(ax.add_patch(Rectangle((x, 62), cw, 24, facecolor=TRACK, edgecolor="none", zorder=1)))

        def upd(st):
            for rect, v in zip(cells, sensor(st, "Collision")["vector"]):
                rect.set_facecolor(C_HARM if v > 0.5 else TRACK)
        self.updates.append(upd)

    def b_prop(self, ax, w, h):
        self.title(ax, w, "Proprioception", "previous action")
        names, gap = self.m["action_names"], 6
        per_row = 3
        cw = (w - 2 * PAD - gap * (per_row - 1)) / per_row
        chips = []
        for k, nm in enumerate(names):
            x, y = PAD + (k % per_row) * (cw + gap), 42 + (k // per_row) * 30
            rect = ax.add_patch(Rectangle((x, y), cw, 24, facecolor=TRACK, edgecolor="none", zorder=1))
            txt = Fit(ax, x + cw / 2, y + 12, MIN_PT, cw - 6, fontfamily=MONO, ha="center", va="center")
            txt.set(nm, self.r)
            chips.append((rect, txt))

        def upd(st):
            vec = sensor(st, "Proprioception")["vector"]
            hot = int(np.argmax(vec)) if max(vec) > 0 else -1
            for k, (rect, txt) in enumerate(chips):
                rect.set_facecolor(C_AGENT if k == hot else TRACK)
                txt.t.set_color("white" if k == hot else house.TEXT_LIGHT)
        self.updates.append(upd)

    # ------------------------------------------------------------------ per step
    olf_max = 1.0

    def frame(self, st):
        for u in self.updates:
            u(st)
        self.canvas.draw()
        self.audit()
        return np.asarray(self.canvas.buffer_rgba())[..., :3].copy()

    def audit(self):
        """Text audit on RENDERED extents: no text leaves its card, no two texts intersect."""
        items = []
        for ax in self.fig.axes:
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
        self.n_texts = len(items)


def write_data(stem, rows):
    with open(os.path.join(FIGS, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            fh.write("\t".join(str(r[k]) for k in ("what", "used", "total", "note")) + "\n")


def main():
    with open(os.path.join(HERE, "data", "episode.json")) as fh:
        ep = json.load(fh)
    meta, steps = ep["meta"], ep["steps"]
    Dashboard.olf_max = max(max(sensor(st, "Olfactory")["vector"]) for st in steps) or 1.0
    house.apply()
    icons = load_icons()
    os.makedirs(os.path.join(FIGS, "fig03_frames"), exist_ok=True)

    # Figure 3: every step, then the representative still through house.save
    d = Dashboard(meta, len(steps), icons, ALL)
    audited = 0
    for st in steps:
        arr = d.frame(st)
        assert arr.shape == (H, W, 3), arr.shape
        # 256-colour PNG, no dithering: a flat dashboard loses nothing visible and the page embeds 35 of these
        Image.fromarray(arr).quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(
            os.path.join(FIGS, "fig03_frames", f"step_{st['t']:03d}.png"), optimize=True)
        audited += 1
    d.frame(steps[REP_STEP])
    n_panels = len(d.boxes)
    house.save(d.fig, os.path.join(FIGS, "fig03_proposed_dashboard"), column_px=1084)
    write_data("fig03_proposed_dashboard", [
        dict(what="recorded steps drawn (step scrubber)", used=audited, total=len(steps),
             note="every step of the exported episode; each frame passed the text audit"),
        dict(what="observed senses given a panel", used=sum(1 for k in meta["breakdown"] if k in OWNER), total=len(meta["breakdown"]),
             note="the completeness rule refuses to draw if an observed sense has no panel"),
    ])

    # Figure 4: the same step under three sense sets, to show re-packing
    variants = [
        ("All eight observed senses", ALL),
        ("Temperature system and proprioception switched off", ALL - {"thermal", "prop"}),
        ("Only satiation, extero nociception, collision and visual", frozenset({"extero", "coll", "vis"})),
    ]
    frames, titles = [], []
    for label, on in variants:
        dv = Dashboard(meta, len(steps), icons, on)
        frames.append(dv.frame(steps[REP_STEP]))
        titles.append(f"{label} · {len(dv.boxes)} panels, no text collisions")
        plt.close(dv.fig)
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 12.6))
    for ax, img, ttl in zip(axes, frames, titles):
        ax.imshow(img)
        ax.set_title(ttl, fontsize=house.FS_LABEL)
        ax.axis("off")
    fig.subplots_adjust(hspace=0.16, left=0.01, right=0.99, top=0.97, bottom=0.01)
    house.save(fig, os.path.join(FIGS, "fig04_repacking"))
    write_data("fig04_repacking", [
        dict(what="recorded steps drawn", used=1, total=len(steps), note=f"step {REP_STEP}, mid-episode, drawn under each sense set"),
        dict(what="sense sets drawn", used=len(variants), total=len(variants),
             note="the full campfire observation and two reduced sets; the recorded numbers are identical, only the panels change"),
    ])
    print(f"figure 3: {audited} frames, {n_panels} panels; figure 4: {len(variants)} sense sets")


if __name__ == "__main__":
    main()
