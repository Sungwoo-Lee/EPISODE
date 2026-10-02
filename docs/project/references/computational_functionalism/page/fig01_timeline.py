#!/usr/bin/env python3
"""FIGURE 1 - the whole corpus on one timeline, by research community and era.

QUESTION IT ANSWERS. When did each community start arguing about whether a computation could be a
mind, how dense was each era, and how much of the corpus was actually read?

WHAT IS IN IT. One horizontal lane per community (works.csv `community`), years on the x-axis
(works.csv `year`, the first public year). Filled marks were reviewed from the PDF; open marks are
named-only, which the page never attributes a position to. Grey bands are the five eras (eras.csv).
No work is labelled here - a label drifting off its mark would read as belonging to the wrong lane;
figure 6 and the debate maps name the works.
"""
import collections
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig01_timeline"


def main():
    house.apply()
    works = list(_cf.works().values())
    eras = _cf.read("eras.csv")
    lanes = [c[0] for c in _cf.COMMUNITIES if any(w["community"] == c[0] for w in works)]
    ypos = {c: len(lanes) - 1 - i for i, c in enumerate(lanes)}

    fig, ax = plt.subplots(figsize=(11.6, 5.2))
    shade = ["#eef0ed", "#f7f8f6"]
    for i, er in enumerate(eras):
        x0, x1 = int(er["start_year"]) - 0.5, int(er["end_year"]) + 0.5
        ax.axvspan(x0, x1, color=shade[i % 2], zorder=0, lw=0)
        ax.text((x0 + x1) / 2, len(lanes) - 0.3, f"Era {i + 1}\n{er['start_year']}–{er['end_year']}",
                ha="center", va="bottom", fontsize=house.FS_LABEL, color=house.INK_2, linespacing=1.2)
    slot = collections.Counter()
    for w in sorted(works, key=lambda r: (int(r["year"]), r["key"])):
        c = w["community"]
        k = (c, int(w["year"]))
        off = slot[k]
        slot[k] += 1
        y = ypos[c] + off * 0.17 - 0.25
        read = w["status"] != "named-only"
        ax.scatter(int(w["year"]), y, s=48 if w["status"] == "reviewed-full" else 36,
                   marker=_cf.MARKER[c], facecolor=_cf.COLOUR[c] if read else house.PAPER,
                   edgecolor=_cf.COLOUR[c], linewidth=1.3, zorder=3)
    ax.set_xlim(1964, 2029)
    ax.set_ylim(-0.75, len(lanes) + 0.6)
    ax.set_yticks([ypos[c] for c in lanes])
    per = collections.Counter(w["community"] for w in works)
    ax.set_yticklabels([f"{_cf.LABEL[c]} ({per[c]})" for c in lanes])
    ax.set_xticks(range(1970, 2030, 10))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_xlabel("year the work first appeared (online year where it differs from print)")
    fig.subplots_adjust(left=0.185, right=0.99, top=0.97, bottom=0.13)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    n = len(works)
    read = sum(w["status"] != "named-only" for w in works)
    biggest = max(per.items(), key=lambda kv: kv[1])
    _cf.data_statement(STEM, (
        f"All {n} of {n} works in the corpus are drawn (100%): {read} reviewed from the PDF (filled marks) and "
        f"{n - read} named-only (open marks). The number after each community is its count of works, from "
        f"{biggest[1]} for {_cf.LABEL[biggest[0]]} down to one for biology and neuroscience. The corpus was "
        "assembled to trace one thesis, so a lane's size is a fact about this collection and not about the size "
        "of that community's literature."))


if __name__ == "__main__":
    main()
