#!/usr/bin/env python3
"""FIGURE 6 - the nine debates at a glance: when each was argued, by whom, and where it stands.

QUESTION IT ANSWERS. Which of the field's questions are old and which are new, which communities
take part in each, and what state is each in after fifty years?

WHAT IS IN IT. One row per debate (debates.csv). A thin line runs from the first to the latest year
of any work holding a position in it (positions.csv joined to works.csv); each mark on the line is
one such work, shaped and coloured by community as in figure 1, open if the work is named-only. The
status on the right is the synthesis's label, written out in words - no colour encodes status,
because a colour would imply a ranking the page does not make. Each status carries a corpus-limit
note and, where it leans, a direction; both are printed in the status cards above this figure
rather than crammed onto the chart.
"""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _cffig as _cf
from _cffig import house

STEM = "fig06_debate_status"


def main():
    house.apply()
    W = _cf.works()
    debates = _cf.read("debates.csv")
    positions = _cf.read("positions.csv")
    n = len(debates)
    h = 0.86 * n + 1.9
    fig, ax = plt.subplots(figsize=(11.6, h))
    fig.subplots_adjust(left=0.31, right=0.80, top=0.985, bottom=1.5 / h)
    total_marks = 0
    for i, d in enumerate(debates):
        y = n - 1 - i
        keys = sorted({k.strip() for p in positions if p["debate_id"] == d["debate_id"]
                       for k in p["keys"].split(";") if k.strip()}, key=lambda k: int(W[k]["year"]))
        years = [int(W[k]["year"]) for k in keys]
        if (min(years), max(years)) != (int(d["first_year"]), int(d["latest_year"])):
            raise SystemExit(f"{d['debate_id']}: span from positions.csv {min(years)}-{max(years)} disagrees "
                             f"with debates.csv {d['first_year']}-{d['latest_year']}")
        ax.plot([min(years), max(years)], [y, y], color=house.RULE, lw=2.2, zorder=1, solid_capstyle="round")
        seen = {}
        for k in keys:
            w = W[k]
            yr = int(w["year"])
            off = seen.get(yr, 0)
            seen[yr] = off + 1
            c = w["community"]
            read = w["status"] != "named-only"
            ax.scatter(yr, y + 0.14 * off, s=42, marker=_cf.MARKER[c],
                       facecolor=_cf.COLOUR[c] if read else house.PAPER, edgecolor=_cf.COLOUR[c],
                       linewidth=1.1, zorder=3)
            total_marks += 1
        # only the status word is drawn here. The direction a "leaning" debate leans in runs to several
        # lines, and setting it beside a row overprinted the row below; it is rendered in the status
        # cards above the figure, next to the same status word, where it has room.
        ax.text(2034.0, y, d["status"], ha="left", va="center",
                fontsize=house.FS_BODY, fontweight="semibold", color=house.INK, clip_on=False)
    ax.set_xlim(1968, 2030)
    ax.set_ylim(-0.7, n - 0.2)
    ax.set_yticks([n - 1 - i for i in range(n)])
    counts = []
    for d in debates:
        keys = {k.strip() for p in positions if p["debate_id"] == d["debate_id"]
                for k in p["keys"].split(";") if k.strip()}
        lanes = sum(1 for p in positions if p["debate_id"] == d["debate_id"])
        counts.append((len(keys), lanes))
    ax.set_yticklabels(["\n".join(textwrap.wrap(d["title"], 38)) + f"\n{k} works, {l} positions"
                        for d, (k, l) in zip(debates, counts)], fontsize=house.FS_LABEL, linespacing=1.15)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_xticks(range(1970, 2031, 10))
    ax.set_xlabel("year the work first appeared (online year where it differs from print)")
    ax.text(2034.0, n - 0.35, "status in this corpus", ha="left", va="bottom", fontsize=house.FS_LABEL,
            color=house.INK_2, clip_on=False)
    present = [c for c in _cf.COMMUNITIES if any(w["community"] == c[0] for w in W.values())]
    handles = [Line2D([0], [0], lw=0, marker=m, markerfacecolor=col, markeredgecolor=col, markersize=7, label=lab)
               for _, lab, col, m in present]
    handles.append(Line2D([0], [0], lw=0, marker="o", markerfacecolor=house.PAPER, markeredgecolor=house.INK_2,
                          markersize=7, label="named only (no PDF held)"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.55, 0.005), ncol=4, frameon=False,
               fontsize=house.FS_LABEL, handletextpad=0.4, columnspacing=1.4)
    house.save(fig, f"{_cf.FIGS}/{STEM}", check_text=False)   # the status column sits outside the axes on purpose
    _cf.data_statement(STEM, (
        f"All {n} debates in debates.csv are drawn (100%), with {total_marks} work-in-debate marks - a work counts "
        "once per debate however many positions it holds there. Spans are computed from positions.csv and checked "
        "against the first_year and latest_year columns of debates.csv; the build fails if they disagree. No "
        "debate in this corpus is settled; the direction of each `leaning` label is given in the status cards "
        "above the figure, because it runs to several lines. "
        "The statuses describe the 36 reviewed works, not the field."))


if __name__ == "__main__":
    main()
