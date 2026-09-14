"""FIGURES 5, 6 and 7 -- three ways to draw an extended-range sense, on one real world state.

QUESTION IT ANSWERS. Olfaction and vision can now read a diamond of cells around the agent at any
range. The dashboard's per-cell bars stop being legible at range 2. Which drawing should the new
renderer use instead? The user chooses after seeing each option on the same data.

WHAT IT IS NOT. Not the renderer. It draws only the two senses, not a full dashboard frame, and it
imports nothing from src/.

HOW IT IS COMPUTED. Reads data/extended.json (export_extended.py): one real state of the
sensory-ladder world with vision range 2 and blur on, read through the production observation code at
the configured ranges and at two in-memory stress ranges (3 and 4). Each reading is a table of diamond
cells x channels in get_visual_offsets order.
    Figure 5, option A: one small diamond per channel, colour = reading, styled per the dashboard design
               spec (docs/reviews/design_episode_dashboard.md) via dashboard_style.py.
    Figure 6, option B: one diamond per sense, colour = strongest channel, strength = its reading.
    Figure 7, option C: per-cell bars while the range is 0-1, a cells x channels table beyond.
All three are styled per the same spec (canvas and cards, Dashboard Sans Tab, full channel names, agent
cell outlined in iris); Figure 6's channel hues avoid every data colour that means something else.
Colour scales run from 0 to the largest reading of that sense in that row, because summed readings can
exceed 1.

OUTPUT (figures/): fig05_option_a_channel_maps, fig06_option_b_dominant_channel,
fig07_option_c_bars_or_table -- each as .svg/.pdf/.png plus a .data.txt used/available statement.

Run (from the repo root)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/fig05_extended_encodings.py
"""
import json
import os
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
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import house  # noqa: E402
import dashboard_style as ds  # noqa: E402

FIGS = os.path.join(HERE, "figures")
OLF_LABELS = ["FOOD", "AN-A", "AN-B", "BUSH", "TREE"]
VIS_LABELS = ["GRS", "SND", "PLN", "FOD", "HPR", "PRD", "RCK", "NEU"]   # HPR = hiding_predator (plan Q11)
# Figure 5 (option A, dashboard spec): full sentence-case names; channel 6 is every obstacle, not only rock
# AN-A / AN-B: shared animal-odour components, named by their leaning (never "Predator" / "Neutral")
OLF_FULL = ["Food", ("Odour A", "predator-leaning"), ("Odour B", "neutral-leaning"), "Bush", "Tree"]
VIS_FULL = ["Food", "Hiding predator", "Predator", "Obstacle", "Neutral"]
VIS_TABLE = ["Grass", "Sand", "Plain"] + VIS_FULL
# Figure 6 channel hues. None reuses a data colour with another meaning in these pages: no orange
# (nociception), no blue or red (temperature), no iris (agent), no teal (smell ramp). Object icon colours
# where free; the two odour components get plum and brown so they differ from each other and from teal.
# odour B: dark gold, a hue no icon, minimap marker or temperature stop uses (was the tree-trunk brown; F11)
OLF_HUE = ["#1E9E5A", "#A23B72", "#B8860B", "#8FA832", "#2F7A45"]   # food, odour A, odour B, bush, tree
VIS_HUE = ["#1E9E5A", "#33503A", "#1F2733", "#6B7380", "#0E7490"]   # food, hiding predator, predator, obstacle, neutral
FW, OUT, PADX, DIV = 1440, 24, 16, 48


def table(sense):
    n = sense["num_features"]
    return np.asarray(sense["vector"], float).reshape(-1, n)


class Probe:
    """Measures rendered text widths before a figure's height is known."""

    def __init__(self):
        self.fig = plt.figure(figsize=(FW / ds.DPI, 1), dpi=ds.DPI)
        self.r = self.fig.canvas.get_renderer()

    def w(self, s, role):
        t = ds.text(self.fig, 0, 0, s, role)
        v = t.get_window_extent(self.r).width
        t.remove()
        return v

    def close(self):
        plt.close(self.fig)


def lines_of(label):
    return list(zip(label, ["map_label", "caption"])) if isinstance(label, tuple) else [(label, "map_label")]


def canvas(FH):
    fig = plt.figure(figsize=(FW / ds.DPI, FH / ds.DPI), dpi=ds.DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    ax.set_autoscale_on(False)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), FW, FH, fc=ds.CANVAS, lw=0, zorder=0))
    return fig, ax


def put(fig, ax, x, y, s, role, **kw):
    """Draw a text and return its rendered width."""
    t = ds.text(ax, x, y, s, role, **kw)
    fig.canvas.draw()
    return t.get_window_extent().width


def row_card(fig, ax, y0, h, var):
    ds.rrect(ax, OUT + 0.5, y0 + 0.5, FW - 2 * OUT - 1, h - 1, ds.CARD_RADIUS, ds.CARD, ds.LINE, 1, z=0.5)
    tw = put(fig, ax, OUT + PADX, y0 + 30, var["label"], "card_title")
    put(fig, ax, OUT + PADX + tw + 12, y0 + 30, f"observation width {var['obs_dim']}", "card_sub")


def group_head(fig, ax, x, hy, title, R, note, cmap=None, vmax=None):
    tw = put(fig, ax, x, hy, title, "card_title")
    rw = put(fig, ax, x + tw + 8, hy, f"range {R}", "card_sub")
    if cmap is not None:
        zx = x + tw + 8 + rw + 16
        sx = zx + put(fig, ax, zx, hy, "0", "caption") + 6
        im = ax.imshow(cmap(np.linspace(0, 1, 128))[None, :, :3], extent=(sx, sx + 96, hy, hy - 8),
                       aspect="auto", interpolation="bilinear", zorder=2)
        im.set_clip_path(ds.rrect(ax, sx, hy - 8, 96, 8, 4, "none", z=2))
        put(fig, ax, sx + 102, hy, f"{vmax:.2f}", "caption")
        ax.set_xlim(0, FW)
        ax.set_ylim(ax.get_ylim()[0], 0)
    put(fig, ax, x, hy + 20, note, "caption")


def option_a(ext):
    """Option A in the dashboard design spec (docs/reviews/design_episode_dashboard.md): one diamond map per
    channel, teal olfaction / slate vision ramps, zero = track, agent cell outlined in iris, a compact
    "0 ... max" legend strip per sense, full sentence-case channel names. Laid out in pixels: one white card
    per range row; within a row every cell is the same size, shrunk only until the row fits (raises below 10px)."""
    ds.register_fonts()
    V = ext["variants"]
    FW, OUT, PADX, GAPM, DIV = 1440, 24, 16, 10, 32
    probe = plt.figure(figsize=(FW / ds.DPI, 1), dpi=ds.DPI)
    r = probe.canvas.get_renderer()

    def width(t, role):
        a = ds.text(probe, 0, 0, t, role)
        w = a.get_window_extent(r).width
        a.remove()
        return w

    MIN_CELL = 12        # the renderer's floor on map cell pitch (spec); below it a row wraps to two lines

    def measure(g, cs):
        box = (2 * g["R"] + 1) * cs
        g["slots"] = []
        for label, _, _ in g["maps"]:
            slot = box + GAPM
            if isinstance(label, tuple):
                lines, roles = list(label), ["map_label", "caption"]
            else:
                lines = [label]
                if width(label, "map_label") > slot - 4 and " " in label:
                    lines = label.split(" ", 1)
                roles = ["map_label"] * len(lines)
            g["slots"].append((max(slot, max(width(li, ro) for li, ro in zip(lines, roles)) + (12 if len(lines) > 1 else 4)),
                               list(zip(lines, roles))))
        g["max_txt"] = f"{g['vmax']:.2f}"
        head = (width(g["title"], "card_title") + 8 + width(f"range {g['R']}", "card_sub") + 16
                + width("0", "caption") + 6 + 96 + 6 + width(g["max_txt"], "caption"))
        g["w"] = max(head, sum(sl for sl, _ in g["slots"]))
        return g["w"]

    def fit_line(gs, avail):
        """Largest cell pitch (18 down to the floor) at which these groups fit one line, else None."""
        cs = 18.0
        while cs >= MIN_CELL:
            if sum(measure(g, cs) for g in gs) + DIV * (len(gs) - 1) <= avail:
                return cs
            cs -= 0.5
        return None

    rows = []
    avail = FW - 2 * OUT - 2 * PADX
    for var in V:
        olf, vis = table(var["olf"]), table(var["vis"])
        groups = [dict(title="Olfaction", R=var["olf_range"], offs=var["offsets_olf"], cmap=ds.OLF_CMAP,
                       vmax=max(olf.max(), 1e-9),
                       maps=[(OLF_FULL[k], "seq", olf[:, k]) for k in range(olf.shape[1])]),
                  dict(title="Vision", R=var["vis_range"], offs=var["offsets_vis"], cmap=ds.VIS_CMAP,
                       vmax=max(vis[:, 3:].max(), 1e-9),
                       maps=[("Terrain", "terrain", vis[:, :3])]
                       + [(VIS_FULL[k], "seq", vis[:, 3 + k]) for k in range(vis.shape[1] - 3)])]
        # one line if every map keeps a >= 12 px cell; otherwise one line per sense, at one shared pitch
        cs = fit_line(groups, avail)
        if cs is not None:
            line_groups = [groups]
        else:
            per = [fit_line([g], avail) for g in groups]
            if None in per:
                raise ValueError(f"{var['label']}: a sense does not fit {avail}px even on its own line at a "
                                 f"{MIN_CELL}px cell")
            cs = min(per)
            line_groups = [[g] for g in groups]
        lines = []
        for gs in line_groups:
            for g in gs:
                measure(g, cs)
            maxbox = max((2 * g["R"] + 1) * cs for g in gs)
            nlines = max(len(ln) for g in gs for _, ln in g["slots"])
            lines.append((gs, maxbox, 36 + maxbox + 22 + 15 * (nlines - 1) + 12))
        h = 48 + sum(lh for _, _, lh in lines) + 8
        rows.append((var, lines, cs, h))
    plt.close(probe)
    FH = OUT + sum(rw[3] for rw in rows) + ds.GAP * (len(rows) - 1) + OUT
    fig = plt.figure(figsize=(FW / ds.DPI, FH / ds.DPI), dpi=ds.DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    ax.set_autoscale_on(False)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), FW, FH, fc=ds.CANVAS, lw=0, zorder=0))
    y0 = OUT
    for var, lines, cs, h in rows:
        ds.rrect(ax, OUT + 0.5, y0 + 0.5, FW - 2 * OUT - 1, h - 1, ds.CARD_RADIUS, ds.CARD, ds.LINE, 1, z=0.5)
        t = ds.text(ax, OUT + PADX, y0 + 30, var["label"], "card_title")
        fig.canvas.draw()
        sub = f"observation width {var['obs_dim']}"
        if len(lines) > 1:
            sub += f"  ·  two lines, so every map cell stays at least {MIN_CELL} px"
        ds.text(ax, OUT + PADX + t.get_window_extent().width + 12, y0 + 30, sub, "card_sub")
        ly = y0 + 48
        for li_, (gs, maxbox, lh) in enumerate(lines):
            if li_:
                ax.plot([OUT + PADX, FW - OUT - PADX], [ly - 6, ly - 6], color=ds.LINE, lw=1 * ds.PT, zorder=1)
            x = OUT + PADX
            for gi, g in enumerate(gs):
                if gi:
                    ax.plot([x - DIV / 2] * 2, [ly + 4, ly + lh - 8], color=ds.LINE, lw=1 * ds.PT, zorder=1)
                hy = ly + 16
                tw = ds.text(ax, x, hy, g["title"], "card_title")
                fig.canvas.draw()
                cx = x + tw.get_window_extent().width + 8
                rt = ds.text(ax, cx, hy, f"range {g['R']}", "card_sub")
                fig.canvas.draw()
                zx = cx + rt.get_window_extent().width + 16
                zt = ds.text(ax, zx, hy, "0", "caption")
                fig.canvas.draw()
                sx = zx + zt.get_window_extent().width + 6
                im = ax.imshow(g["cmap"](np.linspace(0, 1, 128))[None, :, :3], extent=(sx, sx + 96, hy, hy - 8),
                               aspect="auto", interpolation="bilinear", zorder=2)
                im.set_clip_path(ds.rrect(ax, sx, hy - 8, 96, 8, 4, "none", z=2))
                ds.text(ax, sx + 102, hy, g["max_txt"], "caption")
                R = g["R"]
                box = (2 * R + 1) * cs
                top = ly + 36 + (maxbox - box) / 2
                mx = x
                for (label, kind, vals), (slot, lab_lines) in zip(g["maps"], g["slots"]):
                    bx = mx + (slot - box) / 2
                    for (dr, dc), v in zip(g["offs"], vals):
                        if kind == "terrain":
                            off = v.max() <= 0
                            fc, ec = (ds.OFF_WORLD, ds.OUTLINE) if off else (ds.TERRAIN[int(np.argmax(v))], "none")
                        else:
                            fc, ec = (ds.TRACK if v <= 1e-6 else g["cmap"](min(1.0, v / g["vmax"]))), "none"
                        ds.rrect(ax, bx + (dc + R) * cs + 1.5, top + (dr + R) * cs + 1.5, cs - 3, cs - 3,
                                 min(3, cs / 5), fc, ec, 1, z=2)
                    ds.rrect(ax, bx + R * cs + 0.5, top + R * cs + 0.5, cs - 1, cs - 1, min(3, cs / 5), "none",
                             ds.IRIS, 2, z=3)
                    for k, (line, role) in enumerate(lab_lines):
                        ds.text(ax, mx + slot / 2, ly + 36 + maxbox + 22 + 15 * k, line, role, ha="center")
                    mx += slot
                x += g["w"] + DIV
            ly += lh
        y0 += h + ds.GAP
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    return fig


def option_b(ext):
    """Option B restyled to the dashboard spec: one diamond per sense, hue = strongest channel, paler = weaker,
    outlined blank = nothing read, agent cell outlined in iris."""
    ds.register_fonts()
    V = ext["variants"]
    cs = 26
    pr = Probe()
    rows = []
    for var in V:
        R = max(var["olf_range"], var["vis_range"])
        legend_h = max(sum(14 + 20 * len(lines_of(l)) for l in labels) + 34 for labels in (OLF_FULL, VIS_FULL))
        rows.append((var, R, 104 + max((2 * R + 1) * cs, legend_h) + 20))
    legend_w = max(pr.w(li, ro) for l in OLF_FULL + VIS_FULL for li, ro in lines_of(l)) + 24
    pr.close()
    FH = OUT + sum(h for _, _, h in rows) + ds.GAP * (len(rows) - 1) + OUT
    fig, ax = canvas(FH)
    y0 = OUT
    for var, R, h in rows:
        row_card(fig, ax, y0, h, var)
        box = (2 * R + 1) * cs
        x = OUT + PADX
        for gi, (title, tab, hues, labels, offs, r, note) in enumerate((
                ("Olfaction", table(var["olf"]), OLF_HUE, OLF_FULL, var["offsets_olf"], var["olf_range"],
                 "hue = strongest channel; paler = weaker"),
                ("Vision", table(var["vis"])[:, 3:], VIS_HUE, VIS_FULL, var["offsets_vis"], var["vis_range"],
                 "hue = strongest object channel; paler = weaker"))):
            if gi:
                ax.plot([x - DIV / 2] * 2, [y0 + 48, y0 + h - 16], color=ds.LINE, lw=1 * ds.PT, zorder=1)
            group_head(fig, ax, x, y0 + 64, title, r, note)
            top = y0 + 104
            vmax = max(tab.max(), 1e-9)
            for (dr, dc), row in zip(offs, tab):
                k = int(np.argmax(row))
                st = row[k] / vmax
                cx, cy = x + (dc + R) * cs, top + (dr + R) * cs
                if st < 0.02:
                    ds.rrect(ax, cx + 2, cy + 2, cs - 4, cs - 4, 4, ds.OFF_WORLD, ds.OUTLINE, 1, z=2)
                else:
                    a_ = 0.25 + 0.75 * st
                    fc = tuple(np.array(to_rgb(hues[k])) * a_ + (1 - a_))
                    ds.rrect(ax, cx + 1.5, cy + 1.5, cs - 3, cs - 3, 4, fc, z=2)
            ds.rrect(ax, x + R * cs + 0.5, top + R * cs + 0.5, cs - 1, cs - 1, 4, "none", ds.IRIS, 2, z=3)
            lx, ly = x + box + 24, top
            for hue, label in list(zip(hues, labels)) + [(None, "none")]:
                if hue is None:
                    ds.rrect(ax, lx, ly, 14, 14, 3, ds.OFF_WORLD, ds.OUTLINE, 1, z=2)
                else:
                    ds.rrect(ax, lx, ly, 14, 14, 3, hue, z=2)
                for i, (li, ro) in enumerate(lines_of(label)):
                    ds.text(ax, lx + 22, ly + 12 + 16 * i, li, ro)
                ly += 14 + 20 * len(lines_of(label))
            x += box + 24 + legend_w + DIV
        y0 += h + ds.GAP
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    return fig


def option_c(ext):
    """Option C restyled to the dashboard spec: at range 0-1 a diamond of cells with one state-ink bar per
    channel; beyond, a table with one row per cell (teal smell / slate vision ramps, terrain columns in the
    light terrain tints, zero = track), the agent's cell outlined in iris."""
    ds.register_fonts()
    V = ext["variants"]
    pr = Probe()
    PITCH, ROW_H, LABEL_W, HEAD_H = 64, 16, 72, 36

    def plan(tab, R, labels):
        if R <= 1:
            box = (2 * R + 1) * PITCH
            return dict(kind="bars", w=max(box, 300), h=box + 44)
        cols = [max(44, max(pr.w(li, ro) for li, ro in lines_of(l)) + 12) for l in labels]
        return dict(kind="table", cols=cols, w=LABEL_W + sum(cols), h=HEAD_H + len(tab) * ROW_H)

    rows = []
    for var in V:
        olf, vis = table(var["olf"]), table(var["vis"])
        gs = [dict(title="Olfaction", tab=olf, R=var["olf_range"], offs=var["offsets_olf"], labels=OLF_FULL,
                   cmap=ds.OLF_CMAP, vmax=max(olf.max(), 1e-9), terrain=0),
              dict(title="Vision", tab=vis, R=var["vis_range"], offs=var["offsets_vis"], labels=VIS_TABLE,
                   cmap=ds.VIS_CMAP, vmax=max(vis[:, 3:].max(), 1e-9), terrain=3)]
        for g in gs:
            g.update(plan(g["tab"], g["R"], g["labels"]))
            g["w"] = max(g["w"], 380)
        rows.append((var, gs, 104 + max(g["h"] for g in gs) + 20))
    pr.close()
    FH = OUT + sum(h for _, _, h in rows) + ds.GAP * (len(rows) - 1) + OUT
    fig, ax = canvas(FH)
    y0 = OUT
    for var, gs, h in rows:
        row_card(fig, ax, y0, h, var)
        x = OUT + PADX
        for gi, g in enumerate(gs):
            if gi:
                ax.plot([x - DIV / 2] * 2, [y0 + 48, y0 + h - 16], color=ds.LINE, lw=1 * ds.PT, zorder=1)
            top = y0 + 104
            tab, R, n = g["tab"], g["R"], g["tab"].shape[1]
            if g["kind"] == "bars":
                vmax = max(tab.max(), 1e-9)
                group_head(fig, ax, x, y0 + 64, g["title"], R, "bars per cell, one per channel")
                for (dr, dc), row in zip(g["offs"], tab):
                    cx, cy = x + (dc + R) * PITCH, top + (dr + R) * PITCH
                    ds.rrect(ax, cx + 2, cy + 2, PITCH - 4, PITCH - 4, 6, ds.TRACK, z=2)
                    bw = (PITCH - 16) / n
                    for k, v in enumerate(row):
                        bh = (PITCH - 16) * min(1.0, v / vmax)
                        if bh > 0.5:
                            ax.add_patch(Rectangle((cx + 8 + k * bw + bw * 0.15, cy + PITCH - 8 - bh), bw * 0.7, bh,
                                                   fc=ds.STATE, lw=0, zorder=3))
                ds.rrect(ax, x + R * PITCH + 1, top + R * PITCH + 1, PITCH - 2, PITCH - 2, 6, "none", ds.IRIS, 2, z=4)
                names = ", ".join((l[0] if isinstance(l, tuple) else l) for l in g["labels"])
                ds.text(ax, x, top + (2 * R + 1) * PITCH + 20, f"Bars, left to right: {names}", "caption")
                ds.text(ax, x, top + (2 * R + 1) * PITCH + 36, f"Bar height: 0 to {vmax:.2f}", "caption")
            else:
                group_head(fig, ax, x, y0 + 64, g["title"], R, "table, one row per cell (rows down, columns right)",
                           g["cmap"], g["vmax"])
                cx = x + LABEL_W
                for j, (cw, label) in enumerate(zip(g["cols"], g["labels"])):
                    for i, (li, ro) in enumerate(lines_of(label)):
                        ds.text(ax, cx + cw / 2, top + 13 + 15 * i, li, ro, ha="center")
                    for ri, v in enumerate(tab[:, j]):
                        yy = top + HEAD_H + ri * ROW_H
                        if v <= 1e-6:
                            fc = ds.TRACK
                        elif j < g["terrain"]:
                            a_ = 0.35 + 0.65 * min(1.0, v)
                            fc = tuple(np.array(to_rgb(ds.TERRAIN[j])) * a_ + (1 - a_))
                        else:
                            fc = g["cmap"](min(1.0, v / g["vmax"]))
                        ds.rrect(ax, cx + 1, yy + 1, cw - 2, ROW_H - 2, 2, fc, z=2)
                    cx += cw
                for ri, (dr, dc) in enumerate(g["offs"]):
                    lab = f"({dr:+d}, {dc:+d})".replace("-", "−")
                    ds.text(ax, x + LABEL_W - 8, top + HEAD_H + ri * ROW_H + 12, lab, "caption", ha="right")
                    if (dr, dc) == (0, 0):
                        ds.rrect(ax, x + LABEL_W, top + HEAD_H + ri * ROW_H, cx - x - LABEL_W, ROW_H, 3,
                                 "none", ds.IRIS, 2, z=3)
            x += g["w"] + DIV
        y0 += h + ds.GAP
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    return fig


def write_data(stem, rows):
    with open(os.path.join(FIGS, f"{stem}.data.txt"), "w") as fh:
        for r in rows:
            fh.write("\t".join(str(r[k]) for k in ("what", "used", "total", "note")) + "\n")


def main():
    with open(os.path.join(HERE, "data", "extended.json")) as fh:
        ext = json.load(fh)
    house.apply()
    for stem, build in (("fig05_option_a_channel_maps", option_a), ("fig06_option_b_dominant_channel", option_b),
                        ("fig07_option_c_bars_or_table", option_c)):
        fig = build(ext)
        house.save(fig, os.path.join(FIGS, stem), column_px=1084)
        write_data(stem, ext["meta"]["samples"])


if __name__ == "__main__":
    main()
