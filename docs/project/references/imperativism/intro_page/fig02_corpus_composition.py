#!/usr/bin/env python3
"""FIGURE 12 - what the page rests on: the corpus by era and by how deeply each work was read.

QUESTION IT ANSWERS. How much of each era was actually read, so a reader can weigh era-level statements?

WHAT IS IN IT. One stacked bar per era (eras.csv): works reviewed in full (darkest), reviewed as a short
summary (mid grey), and named only (light grey), counted from works.csv. Counts are printed inside segments.
"""
import collections
import matplotlib.pyplot as plt
import _impfig as _imp
from _impfig import house

STEM = "fig02_corpus_composition"
LEVELS = [("reviewed-full", "reviewed in full", house.INK), ("reviewed-short", "short summary", house.TEXT_LIGHT),
          ("named-only", "named only (not read)", "#cfd3cf")]


def main():
    house.apply()
    works = list(_imp.works().values())
    eras = _imp.read("eras.csv")
    cnt = collections.Counter((w["era"], w["status"]) for w in works)
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ys = list(range(len(eras)))[::-1]
    labelled = set()   # label each level once, on the first bar that has it (a level can be absent in an era)
    for y, er in zip(ys, eras):
        left = 0
        for k, lab, col in LEVELS:
            v = cnt[(er["era_id"], k)]
            if v:
                ax.barh(y, v, left=left, height=0.62, color=col, label=None if k in labelled else lab)
                labelled.add(k)
                ax.text(left + v / 2, y, str(v), ha="center", va="center", fontsize=house.FS_LABEL,
                        color=house.PAPER if col != "#cfd3cf" else house.INK)
            left += v
    ax.set_yticks(ys)
    ax.set_yticklabels([f"Era {i + 1}: {er['start_year']}–{er['end_year']}" for i, er in enumerate(eras)])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("number of works in the corpus")
    handles, labels = ax.get_legend_handles_labels()
    order = [lab for _, lab, _ in LEVELS]
    pairs = sorted(zip(handles, labels), key=lambda p: order.index(p[1]))
    if len(pairs) != len(LEVELS):
        raise SystemExit("legend is missing a level")
    ax.legend([h for h, _ in pairs], [l for _, l in pairs], loc="upper center", bbox_to_anchor=(0.5, -0.2),
              ncol=3, frameon=False)
    fig.subplots_adjust(left=0.2, right=0.98, top=0.97, bottom=0.3)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    total = len(works)
    counted = sum(cnt.values())
    _imp.data_statement(STEM, (
        f"All {counted} of {total} works are counted (100%): "
        + ", ".join(f"{lab} {sum(1 for w in works if w['status'] == k)}" for k, lab, _ in LEVELS) + "."))


if __name__ == "__main__":
    main()
