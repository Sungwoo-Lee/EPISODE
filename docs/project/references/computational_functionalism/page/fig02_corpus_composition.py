#!/usr/bin/env python3
"""FIGURE 2 - what the page rests on: the corpus by era and by how deeply each work was read.

QUESTION IT ANSWERS. How much of each era was actually read, so a reader can weigh any era-level
statement on this page?

WHAT IS IN IT. One stacked bar per era (eras.csv): works reviewed in full (darkest), works reviewed
as a short structured summary from the PDF (mid grey), and works named only, with no PDF held
(lightest). Counts are printed inside the segments. Counted from works.csv `status`.
"""
import collections
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig02_corpus_composition"
LEVELS = [("reviewed-full", "reviewed in full", house.INK),
          ("reviewed-short", "short summary from the PDF", house.TEXT_LIGHT),
          ("named-only", "named only (no PDF held)", "#cfd3cf")]


def main():
    house.apply()
    works = list(_cf.works().values())
    eras = _cf.read("eras.csv")
    cnt = collections.Counter((w["era"], w["status"]) for w in works)
    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    ys = list(range(len(eras)))[::-1]
    labelled = set()
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
    fig.subplots_adjust(left=0.22, right=0.98, top=0.97, bottom=0.3)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    counted = sum(cnt.values())
    _cf.data_statement(STEM, (
        f"All {counted} of {len(works)} works are counted (100%): "
        + ", ".join(f"{lab} {sum(1 for w in works if w['status'] == k)}" for k, lab, _ in LEVELS)
        + ". Era membership follows works.csv `year` (the first public year), so five works sit one era away "
          "from where their print year would put them."))


if __name__ == "__main__":
    main()
