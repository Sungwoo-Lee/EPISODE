"""FIGURES 5, 6 and 7 -- three ways to draw an extended-range sense, on one real world state.

QUESTION IT ANSWERS. Olfaction and vision can now read a diamond of cells around the agent at any
range. The dashboard's per-cell bars stop being legible at range 2. Which drawing should the new
renderer use instead? The user chooses after seeing each option on the same data.

WHAT IT IS NOT. Not the renderer. It draws only the two senses, not a full dashboard frame, and it
imports nothing from src/. Sizes and colours are illustrative.

HOW IT IS COMPUTED. Reads data/extended.json (export_extended.py): one real state of the
sensory-ladder world with vision range 2 and blur on, read through the production observation code at
the configured ranges and at two in-memory stress ranges (3 and 4). Each reading is a table of diamond
cells x channels in get_visual_offsets order.
    Figure 5, option A: one small diamond per channel, colour = reading, styled per the dashboard design
               spec (docs/reviews/design_episode_dashboard.md) via dashboard_style.py.
    Figure 6, option B: one diamond per sense, colour = strongest channel, strength = its reading.
    Figure 7, option C: per-cell bars while the range is 0-1, a cells x channels table beyond.
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
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize, to_rgb  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import house  # noqa: E402
import dashboard_style as ds  # noqa: E402

FIGS = os.path.join(HERE, "figures")
OLF_LABELS = ["FOOD", "AN-A", "AN-B", "BUSH", "TREE"]
VIS_LABELS = ["GRS", "SND", "PLN", "FOD", "HPR", "PRD", "RCK", "NEU"]   # HPR = hiding_predator (plan Q11)
# Figure 5 (option A, dashboard spec): full sentence-case names; channel 6 is every obstacle, not only rock
# AN-A / AN-B: shared animal-odour components, named by their leaning (never "Predator" / "Neutral")
OLF_FULL = ["Food", ("Odour A", "predator-leaning"), ("Odour B", "neutral-leaning"), "Bush", "Tree"]
VIS_FULL = ["Food", "Hiding predator", "Predator", "Obstacle", "Neutral"]
SEQ = matplotlib.colormaps["magma_r"]
GREYS = matplotlib.colormaps["Greys"]
PAPER = np.array(to_rgb(house.PAPER))
# colour -> meaning for option B, fixed once for these three figures
# No grey among the channel colours: an empty cell is an outlined blank, and a grey channel read as "empty".
# No hue inside the magma ramp either (yellow-orange-red-pink-violet-black): in Figures 5 and 7 those
# hues mean "reading strength", so here they would read as strength rather than identity (register F11).
FOOD_C, TEAL, CYAN, OCHRE, SLATE = "#65a30d", "#0d9488", "#0891b2", "#a16207", "#475569"
OLF_COL = [FOOD_C, TEAL, CYAN, OCHRE, SLATE]          # FOOD AN-A AN-B BUSH TREE
ENT_COL = [FOOD_C, OCHRE, TEAL, SLATE, CYAN]          # FOD HPR PRD RCK NEU


def table(sense):
    n = sense["num_features"]
    return np.asarray(sense["vector"], float).reshape(-1, n)


def frame(ax, R):
    ax.set_xlim(-R - 0.6, R + 0.6)
    ax.set_ylim(R + 0.6, -R - 0.6)
    ax.set_aspect("equal")
    ax.axis("off")


def agent_mark(ax):
    ax.add_patch(Rectangle((-0.5, -0.5), 1, 1, fill=False, edgecolor=house.INK, linewidth=1.4, zorder=5))


def diamond(ax, offsets, colours, R):
    frame(ax, R)
    for (dr, dc), col in zip(offsets, colours):
        if col is None:     # read nothing: outlined blank, so it cannot be mistaken for a colour
            ax.add_patch(Rectangle((dc - 0.43, dr - 0.43), 0.86, 0.86, facecolor=house.PAPER,
                                   edgecolor=house.RULE, linewidth=0.8))
        else:
            ax.add_patch(Rectangle((dc - 0.46, dr - 0.46), 0.92, 0.92, facecolor=col, edgecolor="none"))
    agent_mark(ax)


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
    V = ext["variants"]
    fig = plt.figure(figsize=(11, 4.6 * len(V)), layout="constrained")
    for sf, var in zip(fig.subfigures(len(V), 1), V):
        sf.suptitle(f"{var['label']} · observation width {var['obs_dim']}", fontsize=house.FS_BODY, x=0.01, ha="left")
        R = max(var["olf_range"], var["vis_range"])
        axes = sf.subplots(1, 2)
        for ax, tab, cols, labels, title, offs in (
                (axes[0], table(var["olf"]), OLF_COL, OLF_LABELS, f"smell, range {var['olf_range']}: strongest channel", var["offsets_olf"]),
                (axes[1], table(var["vis"])[:, 3:], ENT_COL, VIS_LABELS[3:], f"vision, range {var['vis_range']}: strongest object channel", var["offsets_vis"])):
            vmax = max(tab.max(), 1e-9)
            colours = []
            for row in tab:
                k = int(np.argmax(row))
                s = row[k] / vmax
                if s < 0.02:
                    colours.append(None)
                else:
                    a = 0.25 + 0.75 * s
                    colours.append(tuple(np.array(to_rgb(cols[k])) * a + PAPER * (1 - a)))
            diamond(ax, offs, colours, R)
            ax.set_title(title, fontsize=house.FS_LABEL)
            ax.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(cols, labels)]
                      + [Patch(facecolor=house.PAPER, edgecolor=house.RULE, label="none")],
                      loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=False, fontsize=house.FS_LABEL)
    return fig


def bars_diamond(ax, offsets, tab, R, vmax, color):
    frame(ax, R)
    n = tab.shape[1]
    for (dr, dc), row in zip(offsets, tab):
        ax.add_patch(Rectangle((dc - 0.46, dr - 0.46), 0.92, 0.92, facecolor=house.BG_SOFT, edgecolor="none"))
        w = 0.8 / n
        for k, x in enumerate(row):
            h = 0.8 * min(1.0, x / vmax)
            ax.add_patch(Rectangle((dc - 0.4 + k * w + w * 0.1, dr + 0.4 - h), w * 0.8, h, facecolor=color, edgecolor="none"))
    agent_mark(ax)


def heat_table(ax, offsets, tab, labels, vmax, terrain_cols=0):
    """Terrain columns (always ~1 inside the world) get a grey scale of their own; letting them set the
    colour scale washed every object channel out to pale."""
    rgb = np.zeros(tab.shape + (3,))
    for j in range(tab.shape[1]):
        if j < terrain_cols:
            rgb[:, j] = [GREYS(0.15 + 0.6 * min(1.0, x))[:3] for x in tab[:, j]]
        else:
            rgb[:, j] = [SEQ(min(1.0, x / vmax))[:3] for x in tab[:, j]]
    ax.imshow(rgb, aspect="auto", interpolation="nearest")
    ax.set_yticks(range(len(offsets)), [f"({dr:+d},{dc:+d})" for dr, dc in offsets], fontsize=house.FS_LABEL)
    ax.set_xticks(range(len(labels)), labels, fontsize=house.FS_LABEL)
    ax.xaxis.tick_top()
    ax.grid(False)


def option_c(ext):
    V = ext["variants"]
    heights = [max(len(v["offsets_vis"]), 8) * 0.24 + 1.4 for v in V]
    fig = plt.figure(figsize=(11, sum(heights)), layout="constrained")
    for sf, var in zip(fig.subfigures(len(V), 1, height_ratios=heights), V):
        sf.suptitle(f"{var['label']} · observation width {var['obs_dim']}", fontsize=house.FS_BODY, x=0.01, ha="left")
        axes = sf.subplots(1, 2, width_ratios=[5, 8])
        for ax, key, labels, rng_key, offs_key, color in ((axes[0], "olf", OLF_LABELS, "olf_range", "offsets_olf", house.INK_2),
                                                          (axes[1], "vis", VIS_LABELS, "vis_range", "offsets_vis", house.INK_2)):
            tab, r = table(var[key]), var[rng_key]
            terrain_cols = 3 if key == "vis" else 0
            vmax = max(tab[:, terrain_cols:].max(), 1e-9)
            name = "smell" if key == "olf" else "vision"
            if r <= 1:
                bars_diamond(ax, var[offs_key], tab, r, vmax, color)
                ax.set_title(f"{name}, range {r}: bars per cell ({' '.join(labels)})", fontsize=house.FS_LABEL)
            else:
                heat_table(ax, var[offs_key], tab, labels, vmax, terrain_cols)
                ax.set_title(f"{name}, range {r}: table, one row per cell", fontsize=house.FS_LABEL)
                ax.set_ylabel("cell offset (rows down, columns right)", fontsize=house.FS_LABEL)
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
