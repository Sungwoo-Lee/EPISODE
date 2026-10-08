#!/usr/bin/env python3
"""FIGURE 10 - claims commonly made about these works, checked against the works.

QUESTION IT ANSWERS. When a claim routinely attributed to one of these papers is checked against
what the paper actually says, how often does it survive - and which papers are most often
mis-stated?

WHAT IS IN IT. Two panels from corrections.csv. LEFT: one bar per verdict, counting checked claims.
RIGHT: the works with two or more corrections against them, longest first, with each bar split by
verdict in the same greys. No hue ranks a verdict.

WHAT IT IS NOT. A count of errors in the literature. Each row is a claim the reviewers had seen
made or could see being made; the file records what the reviewed text says, and adjudicates nothing.
"""
import collections
import re
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig10_corrections"
ORDER = [("does-not-hold", "does not hold", house.INK),
         ("partly", "partly holds", house.INK_2),
         ("misattributed", "misattributed", house.TEXT_LIGHT),
         ("disputed", "disputed inside the corpus", "#cfd3cf")]
MIN_ROWS = 2


def main():
    house.apply()
    W = _cf.works()
    rows = _cf.read("corrections.csv")
    cnt = collections.Counter(r["verdict"] for r in rows)
    bad = set(cnt) - {k for k, _, _ in ORDER}
    if bad:
        raise SystemExit(f"unexpected verdicts {bad}")
    per = collections.Counter(r["key"] for r in rows)
    split = collections.Counter((r["key"], r["verdict"]) for r in rows)
    shown = [k for k, v in per.items() if v >= MIN_ROWS]
    shown.sort(key=lambda k: (-per[k], int(W[k]["year"])))

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.4), gridspec_kw={"width_ratios": [1, 1.25]})
    ax = axes[0]
    ys = list(range(len(ORDER)))[::-1]
    for y, (k, lab, col) in zip(ys, ORDER):
        ax.barh(y, cnt[k], height=0.6, color=col)
        ax.text(cnt[k] + 0.4, y, str(cnt[k]), va="center", ha="left", fontsize=house.FS_BODY, color=house.INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([lab for _, lab, _ in ORDER])
    ax.set_xlim(0, max(cnt.values()) + 4)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("claims checked against the work")
    ax.set_title("every checked claim, by verdict", loc="left", fontsize=house.FS_BODY,
                 fontweight="semibold", color=house.INK, pad=8)

    ax = axes[1]
    ys = list(range(len(shown)))[::-1]
    labelled = set()
    for y, k in zip(ys, shown):
        left = 0
        for kind, lab, col in ORDER:
            v = split[(k, kind)]
            if v:
                ax.barh(y, v, left=left, height=0.6, color=col, label=None if kind in labelled else lab)
                labelled.add(kind)
            left += v
        ax.text(left + 0.2, y, str(per[k]), va="center", ha="left", fontsize=house.FS_LABEL, color=house.INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([re.sub(r"\s*\(.*?\)", "", W[k]["short_label"]) for k in shown], fontsize=house.FS_LABEL)
    ax.set_xlim(0, max(per[k] for k in shown) + 1.4)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("claims checked against that work")
    ax.set_title(f"works with {MIN_ROWS} or more", loc="left", fontsize=house.FS_BODY,
                 fontweight="semibold", color=house.INK, pad=8)
    handles, labels = ax.get_legend_handles_labels()
    order = [lab for _, lab, _ in ORDER]
    pairs = sorted(zip(handles, labels), key=lambda p: order.index(p[1]))
    fig.legend([h for h, _ in pairs], [l for _, l in pairs], loc="lower center", bbox_to_anchor=(0.5, 0.0),
               ncol=4, frameon=False, fontsize=house.FS_LABEL)
    fig.subplots_adjust(left=0.19, right=0.98, top=0.92, bottom=0.27, wspace=0.65)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    drawn = sum(per[k] for k in shown)
    _cf.data_statement(STEM, (
        f"Left: all {len(rows)} of {len(rows)} rows in corrections.csv are counted (100%). Right: {drawn} of "
        f"{len(rows)} rows ({100 * drawn / len(rows):.0f}%), the ones against the {len(shown)} works carrying "
        f"{MIN_ROWS} or more; rows against a work with a single correction are omitted from the right panel only. "
        "Every row names a reviewed work - a claim about a named-only work could not be checked and is not in the "
        "file, so the absence of a work here is not a clean bill of health."))


if __name__ == "__main__":
    main()
