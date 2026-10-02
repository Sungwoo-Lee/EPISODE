#!/usr/bin/env python3
"""FIGURE 3 - where the corpus stands on the thesis, era by era. NOT A VOTE.

QUESTION IT ANSWERS. As the decades pass, does the balance of positions on "the right computation
would suffice for a mind" change - and does anyone flatly reject it?

WHAT IS IN IT. One stacked bar per era (eras.csv), split by works.csv `stance`: supports (blue),
restricts (dark grey), rejects (orange), declines to take a side (light grey), and unknown, which is
every named-only work. Blue and orange are spent on stance here and on nothing else on this page.

WHAT IT IS NOT. A vote, a poll, or a measure of what the field believes. The corpus was assembled to
trace this one thesis, so works that engage it are over-represented by construction. `restricts` is
not `rejects`: it marks a work that narrows the thesis or declines its stronger form in its own words.
"""
import collections
import matplotlib.pyplot as plt
import _cffig as _cf
from _cffig import house

STEM = "fig03_stance"
STANCES = [("supports", "supports the thesis", house.BLUE),
           ("restricts", "restricts or narrows it", house.INK_2),
           ("rejects", "rejects it", house.ORANGE),
           ("neutral", "declines to take a side", "#a8aeaa"),
           ("unknown", "no stance recorded (named-only)", "#d8dbd7")]


def main():
    house.apply()
    works = list(_cf.works().values())
    eras = _cf.read("eras.csv")
    known = {s for s, _, _ in STANCES}
    bad = {w["stance"] for w in works} - known
    if bad:
        raise SystemExit(f"unexpected stance values {bad}")
    cnt = collections.Counter((w["era"], w["stance"]) for w in works)
    fig, ax = plt.subplots(figsize=(9.8, 4.4))
    ys = list(range(len(eras)))[::-1]
    labelled = set()
    for y, er in zip(ys, eras):
        left = 0
        for k, lab, col in STANCES:
            v = cnt[(er["era_id"], k)]
            if v:
                ax.barh(y, v, left=left, height=0.62, color=col, label=None if k in labelled else lab)
                labelled.add(k)
                ax.text(left + v / 2, y, str(v), ha="center", va="center", fontsize=house.FS_LABEL,
                        color=house.PAPER if col in (house.BLUE, house.INK_2, house.ORANGE) else house.INK)
            left += v
    ax.set_yticks(ys)
    ax.set_yticklabels([f"Era {i + 1}: {er['start_year']}–{er['end_year']}" for i, er in enumerate(eras)])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("number of works in the corpus")
    handles, labels = ax.get_legend_handles_labels()
    order = [lab for _, lab, _ in STANCES]
    pairs = sorted(zip(handles, labels), key=lambda p: order.index(p[1]))
    ax.legend([h for h, _ in pairs], [l for _, l in pairs], loc="upper center", bbox_to_anchor=(0.5, -0.19),
              ncol=3, frameon=False)
    fig.subplots_adjust(left=0.22, right=0.98, top=0.97, bottom=0.33)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    tot = collections.Counter(w["stance"] for w in works)
    _cf.data_statement(STEM, (
        f"All {len(works)} of {len(works)} works are counted (100%), by the corpus-wide stance field in works.csv: "
        + ", ".join(f"{lab} {tot[k]}" for k, lab, _ in STANCES) + ". This is the corpus-wide tally over "
        f"{sum(tot[k] for k in ('supports', 'restricts', 'rejects', 'neutral'))} reviewed works and is not the tally "
        "for any single debate - the sufficiency debate positions 29 works (11 support, 9 restrict, 5 reject, 4 "
        "abstain) and is drawn from positions.csv, not from this field. Two of the supports are narrow: Fodor 1974 "
        "supports only indirectly and Dennett 1988 only defensively."))


if __name__ == "__main__":
    main()
