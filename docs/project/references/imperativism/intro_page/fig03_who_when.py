#!/usr/bin/env python3
"""FIGURE 2 - who wrote what, when: every work in the corpus, named, one row each.

QUESTION IT ANSWERS. The same timeline as Figure 1, but readable at the level of individual works:
which paper sits where, in which community, and whether it was read.

WHAT IS IN IT. Works grouped by community (works.csv `community`), sorted by year inside each group,
one row per work so no label can collide with another. The mark sits at the work's year; the name is
printed beside it (to the right for works before 2000, to the left from 2000 on, so no name runs off
the edge). Filled marks were reviewed from the PDF, open marks are named-only.
"""
import collections
import matplotlib.pyplot as plt
import _impfig as _imp
from _impfig import house

STEM = "fig03_who_when"


def main():
    house.apply()
    works = list(_imp.works().values())
    eras = _imp.read("eras.csv")
    lanes = [c[0] for c in _imp.COMMUNITIES]
    rows = []
    for c in lanes:
        group = sorted([w for w in works if w["community"] == c], key=lambda r: (int(r["year"]), r["short_label"]))
        if group:
            rows.append(("header", c))
            rows += [("work", w) for w in group]
    n = len(rows)
    fig, ax = plt.subplots(figsize=(11.0, 0.205 * n + 0.9))
    shade = ["#eef0ed", "#f7f8f6"]
    for i, er in enumerate(eras):
        ax.axvspan(int(er["start_year"]) - 0.5, int(er["end_year"]) + 0.5, color=shade[i % 2], zorder=0, lw=0)
        ax.text((int(er["start_year"]) + int(er["end_year"])) / 2, n + 0.35, f"Era {i + 1}",
                ha="center", va="bottom", fontsize=house.FS_LABEL, color=house.INK_2)
    for i, (kind, v) in enumerate(rows):
        y = n - 1 - i
        if kind == "header":
            ax.text(1960.5, y, _imp.LABEL[v], ha="left", va="center", fontsize=house.FS_BODY,
                    fontweight="semibold", color=_imp.COLOUR[v] if v != "unknown" else house.INK_2)
            continue
        c, yr = v["community"], int(v["year"])
        read = v["status"] != "named-only"
        ax.scatter(yr, y, s=34, marker=_imp.MARKER[c], facecolor=_imp.COLOUR[c] if read else house.PAPER,
                   edgecolor=_imp.COLOUR[c], linewidth=1.2, zorder=3)
        tag = "" if read else "  (named only)"
        right = yr < 2000
        ax.text(yr + (0.9 if right else -0.9), y, v["short_label"] + tag, ha="left" if right else "right",
                va="center", fontsize=house.FS_LABEL, color=house.INK if read else house.INK_2)
    ax.set_xlim(1959, 2028)
    ax.set_ylim(-0.8, n + 1.4)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_xticks(range(1960, 2030, 10))
    ax.set_xlabel("year the work first appeared (online year where it differs from print)")
    fig.subplots_adjust(left=0.02, right=0.99, top=0.985, bottom=0.03)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    read = sum(w["status"] != "named-only" for w in works)
    _imp.data_statement(STEM, (
        f"All {len(works)} of {len(works)} works are drawn and named (100%): {read} reviewed from the PDF, "
        f"{len(works) - read} named-only. Years are plotting years from works.csv; where a work appeared "
        "online before print, its label keeps the familiar citation year, so a few labels differ from the "
        "position of their mark by a year or two (Procyk 2016 appeared online in 2014)."))


if __name__ == "__main__":
    main()
