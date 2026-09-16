#!/usr/bin/env python3
"""FIGURE 5 - the eight debates at a glance: when each was argued, by which communities, where it stands.

QUESTION IT ANSWERS. Which debates are old and which are new, which communities take part in each, and
what state each is in now?

WHAT IS IN IT. One row per debate (debates.csv). A thin line runs from the first to the latest year of
any work holding a position in it (positions.csv joined to works.csv); each mark on the line is one such
work, shaped and coloured by community. The status on the right is the synthesis's label for the debate,
written out in words - no colour encodes status, because a colour would suggest a ranking the page does
not make.
"""
import textwrap
import matplotlib.pyplot as plt
import _impfig as _imp
from _impfig import house

STEM = "fig06_debate_status"


def main():
    house.apply()
    W = _imp.works()
    debates = _imp.read("debates.csv")
    positions = _imp.read("positions.csv")
    n = len(debates)
    fig, ax = plt.subplots(figsize=(11.6, 0.78 * n + 0.9))
    fig.subplots_adjust(left=0.3, right=0.8, top=0.98, bottom=0.8 / (0.78 * n + 0.9))
    total_marks = 0
    for i, d in enumerate(debates):
        y = n - 1 - i
        keys = sorted({k.strip() for p in positions if p["debate_id"] == d["debate_id"]
                       for k in p["keys"].split(";") if k.strip()}, key=lambda k: int(W[k]["year"]))
        years = [int(W[k]["year"]) for k in keys]
        ax.plot([min(years), max(years)], [y, y], color=house.RULE, lw=2.2, zorder=1, solid_capstyle="round")
        seen = {}
        for k in keys:
            w = W[k]
            yr = int(w["year"])
            off = seen.get(yr, 0)
            seen[yr] = off + 1
            c = w["community"]
            read = w["status"] != "named-only"
            ax.scatter(yr, y + 0.13 * off, s=40, marker=_imp.MARKER[c],
                       facecolor=_imp.COLOUR[c] if read else house.PAPER, edgecolor=_imp.COLOUR[c],
                       linewidth=1.1, zorder=3)
            total_marks += 1
        ax.text(2033.5, y + (0.12 if d["status_direction"] else 0), d["status"], ha="left", va="center",
                fontsize=house.FS_BODY, fontweight="semibold", color=house.INK, clip_on=False)
        if d["status_direction"]:
            ax.text(2033.5, y - 0.2, "\n".join(textwrap.wrap(d["status_direction"], 22)), ha="left", va="top",
                    fontsize=house.FS_LABEL, color=house.INK_2, clip_on=False, linespacing=1.05)
    ax.set_xlim(1994, 2029)
    ax.set_ylim(-0.6, n - 0.2)
    ax.set_yticks([n - 1 - i for i in range(n)])
    ax.set_yticklabels(["\n".join(textwrap.wrap(d["title"], 40)) for d in debates], fontsize=house.FS_LABEL,
                       linespacing=1.1)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_xlabel("year the work first appeared (online year where it differs from print)")
    ax.text(2033.5, n - 0.35, "status", ha="left", va="bottom", fontsize=house.FS_LABEL, color=house.INK_2,
            clip_on=False)
    house.save(fig, f"{_imp.FIGS}/{STEM}", check_text=False)   # status column sits outside the axes on purpose
    _imp.data_statement(STEM, (
        f"All {n} debates in debates.csv are drawn (100%), with {total_marks} work-in-debate marks (a work that "
        "takes part in a debate once, however many positions it holds there). Works before 1994 hold no "
        "position in any debate, so the axis starts there without dropping any mark."))


if __name__ == "__main__":
    main()
