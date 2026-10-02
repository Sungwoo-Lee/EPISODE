#!/usr/bin/env python3
"""FIGURE 11 - how the seed survey's claims held up against the papers.

QUESTION IT ANSWERS. The corpus began as one survey's reference list. When each of its claims was checked
against the paper it cites, how often did the claim hold?

WHAT IS IN IT. One horizontal bar per verdict (survey_corrections.csv), length = number of checked claims
with that verdict, count printed at the bar end. Bars are ink grey; no hue ranks the verdicts.
"""
import collections
import matplotlib.pyplot as plt
import _impfig as _imp
from _impfig import house

STEM = "fig12_survey_corrections"
ORDER = [("holds", "holds as stated"), ("partly", "partly holds"), ("does-not-hold", "does not hold"),
         ("misattributed", "misattributed (not about pain)"), ("n.a.", "not checkable")]


def main():
    house.apply()
    rows = _imp.read("survey_corrections.csv")
    cnt = collections.Counter(r["verdict"] for r in rows)
    unknown = set(cnt) - {k for k, _ in ORDER}
    if unknown:
        raise SystemExit(f"unexpected verdicts {unknown}")
    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    ys = list(range(len(ORDER)))[::-1]
    for y, (k, lab) in zip(ys, ORDER):
        ax.barh(y, cnt[k], height=0.62, color=house.INK_2 if k in ("holds", "partly") else house.INK)
        ax.text(cnt[k] + 0.4, y, str(cnt[k]), va="center", ha="left", fontsize=house.FS_BODY, color=house.INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([lab for _, lab in ORDER])
    ax.set_xlim(0, max(cnt.values()) + 4)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("number of survey claims checked against the cited paper")
    fig.subplots_adjust(left=0.3, right=0.98, top=0.97, bottom=0.2)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    _imp.data_statement(STEM, (
        f"All {len(rows)} checked survey claims are counted (100% of survey_corrections.csv); one of them named a "
        "finding without citing any paper and is counted as not checkable. Claims about named-only papers were not "
        "checked and are not in the file."))


if __name__ == "__main__":
    main()
