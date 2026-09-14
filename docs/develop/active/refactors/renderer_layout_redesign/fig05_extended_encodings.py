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
    Figure 5, option A: one small diamond per channel, colour = reading.
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
os.chdir(ROOT)

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize, to_rgb  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import house  # noqa: E402

FIGS = os.path.join(HERE, "figures")
OLF_LABELS = ["FOOD", "AN-A", "AN-B", "BUSH", "TREE"]
VIS_LABELS = ["GRS", "SND", "PLN", "FOD", "HPR", "PRD", "RCK", "NEU"]   # HPR = hiding_predator (plan Q11)
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
    V = ext["variants"]
    fig = plt.figure(figsize=(14, 3.3 * len(V)), layout="constrained")
    for sf, var in zip(fig.subfigures(len(V), 1), V):
        sf.suptitle(f"{var['label']} · observation width {var['obs_dim']}", fontsize=house.FS_BODY, x=0.01, ha="left")
        olf, vis = table(var["olf"]), table(var["vis"])
        R = max(var["olf_range"], var["vis_range"])
        # colour bars get their own row, so every map in the row keeps the same box and title height
        mosaic = sf.subplot_mosaic([[f"m{k}" for k in range(11)], ["o"] * 5 + ["."] + ["v"] * 5],
                                   height_ratios=[1, 0.05])
        axes = [mosaic[f"m{k}"] for k in range(11)]
        omax = max(olf.max(), 1e-9)
        for k in range(5):
            diamond(axes[k], var["offsets_olf"], [SEQ(x / omax) for x in olf[:, k]], R)
            axes[k].set_title(f"smell\n{OLF_LABELS[k]}", fontsize=house.FS_LABEL)
        terrain = vis[:, :3].sum(1)
        diamond(axes[5], var["offsets_vis"], [GREYS(0.15 + 0.6 * min(1.0, x)) for x in terrain], R)
        axes[5].set_title("vision\nterrain", fontsize=house.FS_LABEL)
        ent = vis[:, 3:]
        emax = max(ent.max(), 1e-9)
        for k in range(5):
            diamond(axes[6 + k], var["offsets_vis"], [SEQ(x / emax) for x in ent[:, k]], R)
            axes[6 + k].set_title(f"vision\n{VIS_LABELS[3 + k]}", fontsize=house.FS_LABEL)
        sf.colorbar(ScalarMappable(Normalize(0, omax), SEQ), cax=mosaic["o"], orientation="horizontal",
                    label="smell reading, 0 to this row's largest")
        sf.colorbar(ScalarMappable(Normalize(0, emax), SEQ), cax=mosaic["v"], orientation="horizontal",
                    label="vision object reading, 0 to this row's largest")
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
