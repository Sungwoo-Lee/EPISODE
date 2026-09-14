#!/usr/bin/env python3
"""FIGURE 7 - six graph-engineering ideas for this project, and which ones need which.

QUESTION IT ANSWERS. If the project adopted any of the ideas in section 6 of the tutorial page,
where would it start? The figure lays the six ideas out from the smallest change to the largest
and draws which idea needs another in place first.

WHAT IS IN IT. Six grey boxes (ideas A-F) in three columns. A solid arrow means "needs this in place
first"; a dashed arrow means "is easier with this, but does not need it". Column placement is the
author's judgement of effort, not an estimate anyone has checked.

HOW IT IS COMPUTED. Nothing is computed. Box positions are hand-placed inches on a 10.5 x 4.6 inch
canvas; the links are the two lists below, and the Data line counts them.
"""
import _diagram as D
import house

W, H = 2.6, 0.9
IDEAS = {
    "A": (1.7, 3.2, "A · Flows as data", "the playbook as one checked file"),
    "B": (1.7, 1.3, "B · Evidence gates", "no hand-off without proof"),
    "C": (5.25, 3.2, "C · Job ledger", "where every job stands"),
    "D": (5.25, 1.3, "D · Resource claims", "GPUs, git, shared files"),
    "E": (8.8, 3.2, "E · Research cycle", "one graph, design to verdict"),
    "F": (8.8, 1.3, "F · Self-revising flows", "past jobs propose edits"),
}
NEEDS = [("A", "B"), ("A", "C"), ("C", "E"), ("B", "E"), ("C", "F")]
HELPS = [("C", "D")]


def link(ax, a, b, ls="-"):
    xa, ya = IDEAS[a][:2]
    xb, yb = IDEAS[b][:2]
    if xa == xb:                                   # same column: bottom of a to top of b
        D.arrow(ax, (xa, ya - H / 2), (xb, yb + H / 2), ls=ls)
    elif ya == yb:                                 # same row: right edge to left edge
        D.arrow(ax, (xa + W / 2, ya), (xb - W / 2, yb), ls=ls)
    else:                                          # diagonal; bend upward, clear of the box between
        D.arrow(ax, (xa + W / 2, ya + (0.15 if yb > ya else -0.15)),
                (xb - W / 2, yb + (-0.2 if yb > ya else 0.2)), rad=-0.12 if yb > ya else 0.0, ls=ls)


def main():
    fig, ax = D.canvas(10.5, 4.6)
    for x, head in [(1.7, "smaller change"), (5.25, "medium"), (8.8, "larger change")]:
        D.label(ax, x, 4.3, head, colour=house.INK, size=house.FS_BODY, weight="semibold")
    for x, y, t, s in IDEAS.values():
        D.box(ax, x, y, W, H, t, s, role="plain")
    for a, b in NEEDS:
        if (a, b) == ("B", "E"):      # routed from B's top-right to E's bottom-left, clear of C and D
            D.arrow(ax, (2.9, 1.75), (7.8, 2.75))
            continue
        link(ax, a, b)
    for a, b in HELPS:
        link(ax, a, b, ls="--")

    D.arrow(ax, (0.3, 0.35), (0.85, 0.35))
    D.label(ax, 0.98, 0.35, "needs this first", ha="left")
    D.arrow(ax, (2.75, 0.35), (3.3, 0.35), ls="--")
    D.label(ax, 3.43, 0.35, "easier with this", ha="left")

    D.save(fig, "lg07_suggestion_map",
           f"Proposal sketch, not a measurement: {len(IDEAS)} of {len(IDEAS)} ideas from section 6 "
           f"drawn (100%), with {len(NEEDS)} 'needs' links and {len(HELPS)} 'easier with' link. "
           f"Column placement is a judgement of effort, not an estimate.")


if __name__ == "__main__":
    main()
