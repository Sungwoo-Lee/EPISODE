#!/usr/bin/env python3
"""FIGURE 15 - the works the corpus argues with, and whether the argument cites the document held.

QUESTION IT ANSWERS. Which works does the rest of the corpus engage most - and when a reviewer
recorded an engagement, did the engaging work actually cite the document in this collection?

WHAT IS IN IT. One bar per work with three or more incoming engagements (edges.csv `to_key`),
longest first. Each bar is split by edges.csv `cites_held_document`: dark = the engaging work cites
this very document; mid grey = it cites a sibling statement of the same theory or author; light =
it cites a different document entirely. Counts are printed at the bar end.

WHY THE SPLIT MATTERS. A node is not a citation count. The integrated-information node is the clear
case: most of what engages it cites a different paper of that programme, so the node stands for the
programme rather than for the 2015 paper held here.
"""
import collections
import matplotlib.pyplot as plt
import re
import _cffig as _cf
from _cffig import house

STEM = "fig15_most_engaged"
KINDS = [("yes", "cites this document", house.INK),
         ("sibling", "cites a sibling paper of the same theory or author", house.TEXT_LIGHT),
         ("other", "cites a different document", "#cfd3cf")]
MIN_EDGES = 3


def main():
    house.apply()
    W = _cf.works()
    edges = _cf.read("edges.csv")
    bad = {e["cites_held_document"] for e in edges} - {k for k, _, _ in KINDS}
    if bad:
        raise SystemExit(f"unexpected cites_held_document value {bad}")
    incoming = collections.Counter(e["to_key"] for e in edges)
    split = collections.Counter((e["to_key"], e["cites_held_document"]) for e in edges)
    shown = [k for k, v in incoming.items() if v >= MIN_EDGES]
    shown.sort(key=lambda k: (-incoming[k], int(W[k]["year"])))
    fig, ax = plt.subplots(figsize=(10.4, 0.46 * len(shown) + 1.9))
    ys = list(range(len(shown)))[::-1]
    labelled = set()
    for y, k in zip(ys, shown):
        left = 0
        for kind, lab, col in KINDS:
            v = split[(k, kind)]
            if v:
                ax.barh(y, v, left=left, height=0.62, color=col, label=None if kind in labelled else lab)
                labelled.add(kind)
            left += v
        ax.text(left + 0.2, y, str(incoming[k]), va="center", ha="left", fontsize=house.FS_LABEL, color=house.INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([re.sub(r"\s*\(.*?\)", "", W[k]["short_label"]) for k in shown], fontsize=house.FS_LABEL)
    ax.set_xlim(0, max(incoming[k] for k in shown) + 1.6)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("number of documented engagements recorded into this work")
    h = 0.46 * len(shown) + 1.9
    handles, labels = ax.get_legend_handles_labels()
    order = [lab for _, lab, _ in KINDS]
    pairs = sorted(zip(handles, labels), key=lambda p: order.index(p[1]))
    ax.legend([hh for hh, _ in pairs], [l for _, l in pairs], loc="lower center", bbox_to_anchor=(0.42, -1.5 / h),
              ncol=1, frameon=False, fontsize=house.FS_LABEL)
    fig.subplots_adjust(left=0.28, right=0.98, top=0.98, bottom=1.35 / h)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    tot = collections.Counter(e["cites_held_document"] for e in edges)
    drawn = sum(incoming[k] for k in shown)
    top = shown[0]
    _cf.data_statement(STEM, (
        f"{drawn} of the {len(edges)} documented engagements in edges.csv are drawn ({100 * drawn / len(edges):.0f}%): "
        f"every engagement into one of the {len(shown)} works that receive at least {MIN_EDGES}. The "
        f"{len(edges) - drawn} engagements into less-engaged works are omitted, and no engagement is counted twice. "
        f"Across the whole file, {tot['yes']} engagements cite the document held here, {tot['sibling']} cite a "
        f"sibling paper and {tot['other']} cite a different document. The most-engaged work is "
        f"{re.sub(r'  *', ' ', W[top]['short_label'])} with {incoming[top]}."))


if __name__ == "__main__":
    main()
