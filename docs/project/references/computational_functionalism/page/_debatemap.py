"""Draw one debate as a small map: positions as lanes, works as marks by year, engagements as arrows.

Used by the three debate-group figures so that every debate on the page is drawn the same way.
"""
import re
import textwrap
from matplotlib.patches import FancyArrowPatch
import _cffig as _cf
from _cffig import house

# Only disagreement is drawn: a debate map shows who argues with whom. Agreement and support
# ("builds on", "uses as evidence") is already shown by two works sharing a position lane, and drawing
# it too turned the busiest panel into a hairball (checked 2026-09-17).
REL_STYLE = {   # relation -> (linestyle, legend label) ; ink grey, never a hue
    "critiques": ("-", "critiques"),
    "replies-to": ((0, (5, 3)), "replies to"),
}
LEGEND = [("-", "critiques"), ((0, (5, 3)), "replies to")]


def draw(ax, debate, positions, W, edges, x_min=1994, x_max=2030):
    lanes = [p for p in positions if p["debate_id"] == debate["debate_id"]]
    n = len(lanes)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.9, n - 0.1)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels(["\n".join(textwrap.wrap(p["position_label"], 34)) for p in reversed(lanes)],
                       fontsize=house.FS_LABEL, linespacing=1.1)
    where = {}        # one anchor per work, for the arrows
    placements = []   # every drawn mark, so a work holding two positions is labelled twice
    drawn, skipped, empty = 0, 0, 0
    for i, p in enumerate(lanes):
        y = n - 1 - i
        keys = [k.strip() for k in p["keys"].split(";") if k.strip()]
        if not keys:
            # a position nobody in the corpus holds is still a position: say so on the lane rather
            # than leaving a blank row that reads as a drawing error
            empty += 1
            ax.plot([x_min + 1, x_max - 1], [y, y], color=house.TICK_LINE, lw=1.0, ls=(0, (2, 3)), zorder=1)
            ax.text((x_min + x_max) / 2, y + 0.12, "no work held in this corpus takes this position",
                    ha="center", va="bottom", fontsize=house.FS_LABEL, color=house.TEXT_LIGHT, style="italic")
        placed_years = []
        for k in sorted(keys, key=lambda k: int(W[k]["year"])):
            w = W[k]
            yr = int(w["year"])
            if yr < x_min:
                skipped += 1
                continue
            # works within 2 years of each other in one lane are fanned out vertically, alternating
            near = sum(1 for py in placed_years if abs(py - yr) <= 2)
            placed_years.append(yr)
            yy = y + (0.3 * ((near + 1) // 2) * (1 if near % 2 else -1) if near else 0.0)
            c = w["community"]
            read = w["status"] != "named-only"
            ax.scatter(yr, yy, s=42, marker=_cf.MARKER[c], facecolor=_cf.COLOUR[c] if read else house.PAPER,
                       edgecolor=_cf.COLOUR[c], linewidth=1.2, zorder=4)
            drawn += 1
            placements.append((k, yr, yy))
            where.setdefault(k, (yr, yy))
    # a mark label has to be short: drop "et al." and any parenthetical version note
    items = [(x, y, re.sub(r"\s*\(.*?\)", "", W[k]["short_label"]).replace(" et al.", ""), house.INK_2)
             for k, x, y in placements]
    dropped = _cf.label_positions(ax, ax.get_figure(), items, fontsize=house.FS_LABEL,
                                   tries=[(0, 7), (0, -7), (7, 0), (-7, 0), (6, 7), (-6, 7), (6, -7), (-6, -7),
                                          (0, 15), (0, -15), (10, 12), (-10, 12), (10, -12), (-10, -12),
                                          (16, 0), (-16, 0), (24, 6), (-24, 6), (24, -6), (-24, -6)],
                                   pad_px=8.0, halo=True)
    arrows = 0
    for e in edges:
        a, b = e["from_key"], e["to_key"]
        if a in where and b in where and a != b and e["relation"] in REL_STYLE:
            ls, _ = REL_STYLE[e["relation"]]
            (x1, y1), (x2, y2) = where[a], where[b]
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
                                         color=house.INK_2, lw=1.0, ls=ls, shrinkA=6, shrinkB=6,
                                         connectionstyle="arc3,rad=0.12", zorder=2, alpha=0.75))
            arrows += 1
    ax.set_title(f"{debate['title']}  —  status: {debate['status']}", loc="left",
                 fontsize=house.FS_BODY, fontweight="semibold", color=house.INK, pad=8)
    return {"dropped": dropped, "lanes": n, "marks": drawn, "arrows": arrows,
            "skipped_pre_axis": skipped, "empty_lanes": empty}
