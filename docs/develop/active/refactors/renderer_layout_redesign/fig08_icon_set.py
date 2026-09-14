"""FIGURE 8 -- the flat icon set of the episode-dashboard sketch.

QUESTION IT ANSWERS. What do the redrawn icons look like, including the new campfire, which never enters
the grid view in the Figure 3 episode?

HOW IT IS COMPUTED. Draws each glyph with the same functions the dashboard sketch uses
(dashboard_style.GLYPHS), one tile per glyph, on the frame's canvas colour. Creatures and food carry
their white token; terrain is drawn flat on a setpoint-neutral cell. The agent is shown with the chevron
for its last action (Left).

OUTPUT: figures/fig08_icon_set.{svg,pdf,png} and figures/fig08_icon_set.data.txt

Run (from the repo root; run make_dashboard_assets.py once first, for the font)
    /home/vncuser/miniconda3/envs/grid_world_pain/bin/python \
        docs/develop/active/refactors/renderer_layout_redesign/fig08_icon_set.py
"""
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
from matplotlib.patches import Rectangle  # noqa: E402

import dashboard_style as ds  # noqa: E402
import house  # noqa: E402

FIGS = os.path.join(HERE, "figures")
ITEMS = [("Agent", "agent"), ("Food", "food"), ("Predator", "predator"), ("Hiding predator", "hiding_predator"),
         ("Neutral", "neutral"), ("Rock", "rock"), ("Bush", "bush"), ("Tree", "tree"), ("Campfire", "campfire")]
NEUTRAL_CELL = ds.TEMP_STOPS[2]        # the temperature ramp's setpoint colour


def main():
    house.apply()
    ds.register_fonts()
    if sorted(n for _, n in ITEMS) != sorted(ds.GLYPHS):
        raise ValueError(f"icon sheet {[n for _, n in ITEMS]} does not match dashboard_style.GLYPHS {list(ds.GLYPHS)}")
    tile, gap, pad = 128, 24, 28
    FW = 2 * pad + len(ITEMS) * tile + (len(ITEMS) - 1) * gap
    FH = 250
    fig = plt.figure(figsize=(FW / ds.DPI, FH / ds.DPI), dpi=ds.DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    ax.set_autoscale_on(False)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), FW, FH, fc=ds.CANVAS, lw=0, zorder=0))
    ty = 28
    for i, (label, name) in enumerate(ITEMS):
        x = pad + i * (tile + gap)
        ds.rrect(ax, x, ty, tile, tile, 12, NEUTRAL_CELL, ds.LINE, 1, z=1)
        cx, cy = x + tile / 2, ty + tile / 2
        if name == "agent":
            ds.g_agent(ax, cx, cy, tile, action="LEFT")
        else:
            ds.GLYPHS[name](ax, cx, cy, tile)
        ax.text(cx, ty + tile + 30, label, fontsize=16 * ds.PT, fontfamily=ds.FONT, fontweight="medium",
                color=ds.INK, ha="center")
    ax.text(pad, FH - 26, "Creatures and food sit on a white token; terrain is drawn flat on the cell. "
            "The agent's chevron shows its last action.", fontsize=15 * ds.PT, fontfamily=ds.FONT,
            fontweight="regular", color=ds.INK3)
    ax.set_xlim(0, FW)
    ax.set_ylim(FH, 0)
    house.save(fig, os.path.join(FIGS, "fig08_icon_set"), column_px=1084)
    with open(os.path.join(FIGS, "fig08_icon_set.data.txt"), "w") as fh:
        fh.write(f"icons drawn\t{len(ITEMS)}\t{len(ds.GLYPHS)}\tevery glyph the dashboard sketch uses, "
                 "including the new campfire\n")


if __name__ == "__main__":
    main()
