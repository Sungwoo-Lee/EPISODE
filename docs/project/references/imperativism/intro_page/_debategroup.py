"""Build one multi-panel debate-group figure (used by fig06, fig08, fig09)."""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _impfig as _imp
from _impfig import house
import _debatemap


def build(stem, debate_ids, x_min=1994):
    house.apply()
    W = _imp.works()
    debates = {d["debate_id"]: d for d in _imp.read("debates.csv")}
    positions = _imp.read("positions.csv")
    edges = _imp.read("edges.csv")
    heights = [max(3, sum(p["debate_id"] == d for p in positions)) for d in debate_ids]
    fig, axes = plt.subplots(len(debate_ids), 1, figsize=(11.6, 1.00 * sum(heights) + 0.9 * len(debate_ids) + 0.9),
                             gridspec_kw={"height_ratios": heights})
    axes = [axes] if len(debate_ids) == 1 else list(axes)
    # fix the layout BEFORE placing labels: label placement measures pixels, and a later
    # subplots_adjust would move every axis under labels that were already placed
    h_in = fig.get_size_inches()[1]
    fig.subplots_adjust(left=0.27, right=0.99, top=1 - 0.45 / h_in, bottom=1.05 / h_in, hspace=0.9 / (h_in / len(debate_ids)))
    stats = {}
    for ax, d in zip(axes, debate_ids):
        stats[d] = _debatemap.draw(ax, debates[d], positions, W, edges, x_min=x_min)
        if stats[d]["dropped"]:
            raise SystemExit(f"{stem}/{d}: labels could not be placed without overlap: {stats[d]['dropped']}")
    axes[-1].set_xlabel("year the work first appeared (online year where it differs from print)")
    handles = [Line2D([0], [0], color=house.INK_2, ls=ls, lw=1.2, label=lab) for ls, lab in _debatemap.LEGEND]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.6, 0.0), ncol=2, frameon=False,
               fontsize=house.FS_LABEL, handlelength=2.8)
    house.save(fig, f"{_imp.FIGS}/{stem}")
    marks = sum(s["marks"] for s in stats.values())
    arrows = sum(s["arrows"] for s in stats.values())
    pre = sum(s["skipped_pre_axis"] for s in stats.values())
    per = "; ".join(f"{debates[d]['title'].split('?')[0].split(':')[0]}: {stats[d]['lanes']} positions, "
                    f"{stats[d]['marks']} placements, {stats[d]['arrows']} arrows" for d in debate_ids)
    _imp.data_statement(stem, (
        f"All positions recorded for these {len(debate_ids)} debates in positions.csv are drawn ({marks} "
        f"work placements; a work holding two positions appears twice). Arrows: {arrows} of the "
        f"{len(edges)} recorded engagements - only critiques and replies whose both ends sit in the same panel. "
        f"Supportive links (builds on, uses as evidence) and links to works outside the panel are not drawn. {pre} placements before {x_min} fall off the axis and are omitted. "
        + per + "."))
