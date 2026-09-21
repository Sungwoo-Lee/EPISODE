#!/usr/bin/env python3
"""FIGURE 4 - what the field runs on: the kind of evidence each work brings.

QUESTION IT ANSWERS. Is this a debate settled by measurement, by proof, or by argument?

WHAT IS IN IT. One bar per value of works.csv `evidence_type`, counting works. The field-history
record for each work names the kind of thing it puts on the table: a conceptual analysis, a thought
experiment, a formal proof, a survey or review, a position piece - or `unknown`, which is every
named-only work. Bars are ink grey; no hue ranks the kinds.

WHAT IT IS NOT. A judgement of quality. A thought experiment is not a weaker thing than a proof here;
the figure only records which kind of move a work makes.
"""
import collections
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig04_evidence_base"


def main():
    house.apply()
    works = list(_cf.works().values())
    cnt = collections.Counter(w["evidence_type"] for w in works)
    order = sorted(cnt, key=lambda k: (k == "unknown", -cnt[k], k))
    fig, ax = plt.subplots(figsize=(9.4, 3.6))
    ys = list(range(len(order)))[::-1]
    for y, k in zip(ys, order):
        ax.barh(y, cnt[k], height=0.6, color="#cfd3cf" if k == "unknown" else house.INK_2)
        ax.text(cnt[k] + 0.25, y, str(cnt[k]), va="center", ha="left", fontsize=house.FS_BODY, color=house.INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([("named only — no evidence recorded" if k == "unknown" else k) for k in order])
    ax.set_xlim(0, max(cnt.values()) + 2)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("number of works in the corpus")
    fig.subplots_adjust(left=0.33, right=0.98, top=0.97, bottom=0.2)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    emp = [w["short_label"] for w in works if w["key"] == "piccinini2013"]
    _cf.data_statement(STEM, (
        f"All {len(works)} of {len(works)} works are counted (100%), one bar per value of the works.csv "
        f"`evidence_type` field. No category is 'measurement': exactly one reviewed work, {emp[0]}, reaches its "
        "verdict from published neurophysiology, and that verdict is about what kind of computation the brain "
        "performs, not about whether computation suffices for a mind. Several works cite experiments in support of "
        "a premise; none tests the thesis."))


if __name__ == "__main__":
    main()
