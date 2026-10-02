#!/usr/bin/env python3
"""FIGURE 5 - the dial nobody sets: how finely a system must be copied before the copy counts.

QUESTION IT ANSWERS. Every argument on this page needs an answer to "copied at what level of
detail?" - the computations a brain performs, single neurons, synapses, sub-neuronal receptors.
Who sets that dial, where, and how many works say the dial is the wrong picture?

WHAT IS IN IT. Two panels, both drawn from grain.csv (31 rows: every reviewed work that commits to
or comments on a level), with the community colours of figure 1.
  * TOP - the 10 works whose setting sits on an ordered scale, split by the file's own definition:
    `coarse` is above the neural level, `fine` is at or finer than it.
  * BOTTOM - the 21 works that are NOT points on that scale, in the file's four other codes: the
    level is derived from a theory's own postulate, the work denies there is a bottom level at all,
    the level is assumed without argument, the work commits to a level it never locates on this
    scale, or - the largest group - the work's claim is ABOUT the parameter rather than a setting
    of it. Those nine are the field's unresolved axis.
"""
import collections
import re
import textwrap
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import _cffig as _cf
from _cffig import house

STEM = "fig05_grain_ladder"
ON = [("coarse", "coarse — above the neural level"),
      ("fine", "fine — at or finer than the neural level")]
OFF = [("meta", "the claim is ABOUT the dial,\nnot a setting of it"),
       ("unspecified", "commits to a level,\nnever locates it on this scale"),
       ("derived", "the level falls out of the\ntheory's own postulate"),
       ("no-bottom", "denies there is a\nbottom level at all"),
       ("assumed", "commits without argument")]
X0, X1 = 1966, 2040


def short(label):
    """First-author-and-year, with any parenthetical version note dropped, and wrapped if it is long.

    A one-line label of a three-author paper is wide enough that, near the right edge of a crowded
    lane, no offset fits inside the axes and the label is dropped. Two lines are narrower and place.
    """
    lab = re.sub(r"\s*\(.*?\)", "", label).replace(" et al.", "")
    return "\n".join(textwrap.wrap(lab, 20)) if len(lab) > 22 else lab


def lane(ax, rows, lanes, W, title):
    ypos = {k: len(lanes) - 1 - i for i, (k, _) in enumerate(lanes)}
    seen = collections.Counter()
    items = []
    for r in sorted(rows, key=lambda r: (int(r["year"]), r["key"])):
        d = r["direction"]
        if d not in ypos:
            continue
        yr = int(r["year"])
        off = seen[(d, yr // 4)]
        seen[(d, yr // 4)] += 1
        y = ypos[d] + (0.30 * ((off + 1) // 2) * (1 if off % 2 else -1) if off else 0.0)
        c = W[r["key"]]["community"]
        ax.scatter(yr, y, s=48, marker=_cf.MARKER[c], facecolor=_cf.COLOUR[c],
                   edgecolor=_cf.COLOUR[c], linewidth=1.2, zorder=4)
        items.append((yr, y, short(W[r["key"]]["short_label"]), house.INK_2))
    ax.set_xlim(X0, X1)
    ax.set_ylim(-0.75, len(lanes) - 0.25)
    ax.set_yticks(range(len(lanes)))
    n = collections.Counter(r["direction"] for r in rows)
    ax.set_yticklabels([f"{lab}  ({n[k]})" for k, lab in reversed(lanes)], fontsize=house.FS_LABEL,
                       linespacing=1.15)
    ax.set_xticks(range(1970, 2041, 10))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True, color=house.TICK_LINE, lw=0.8)
    ax.set_title(title, loc="left", fontsize=house.FS_BODY, fontweight="semibold", color=house.INK, pad=8)
    return items


def main():
    house.apply()
    W = _cf.works()
    rows = _cf.read("grain.csv")
    known = {k for k, _ in ON} | {k for k, _ in OFF}
    bad = {r["direction"] for r in rows} - known
    if bad:
        raise SystemExit(f"unexpected grain direction {bad}")
    on = [r for r in rows if r["direction"] in {k for k, _ in ON}]
    off = [r for r in rows if r["direction"] not in {k for k, _ in ON}]

    fig, axes = plt.subplots(2, 1, figsize=(11.6, 12.4), gridspec_kw={"height_ratios": [2, 5]})
    fig.subplots_adjust(left=0.29, right=0.99, top=0.945, bottom=0.135, hspace=0.30)
    items_a = lane(axes[0], on, ON, W, f"On the scale — {len(on)} of {len(rows)} works set the dial")
    items_b = lane(axes[1], off, OFF, W, f"Off the scale — {len(off)} of {len(rows)} works do not")
    axes[1].set_xlabel("year the work first appeared (online year where it differs from print)")
    # place the most hemmed-in labels first: a greedy placer that starts with the roomy ones spends
    # the free space on labels that had alternatives and then has none left for the crowded cluster
    def crowding(it, items):
        return -sum(1 for o in items if abs(o[0] - it[0]) <= 3 and abs(o[1] - it[1]) <= 1.2)
    items_a = sorted(items_a, key=lambda it: crowding(it, items_a))
    items_b = sorted(items_b, key=lambda it: crowding(it, items_b))
    tries = [(0, 8), (0, -8), (9, 0), (-9, 0), (8, 8), (-8, 8), (8, -8), (-8, -8),
             (0, 16), (0, -16), (16, 8), (-16, 8), (16, -8), (-16, -8), (20, 0), (-20, 0),
             (0, 24), (0, -24), (24, 16), (-24, 16), (24, -16), (-24, -16), (28, 0), (-28, 0)]
    dropped = []
    for ax, items in ((axes[0], items_a), (axes[1], items_b)):
        dropped += _cf.label_positions(ax, fig, items, fontsize=house.FS_LABEL, tries=tries,
                                       pad_px=6.0, halo=True)
    if dropped:
        raise SystemExit(f"{STEM}: labels could not be placed without overlap: {dropped}")
    present = [c for c in _cf.COMMUNITIES if any(W[r["key"]]["community"] == c[0] for r in rows)]
    handles = [Line2D([0], [0], lw=0, marker=m, markerfacecolor=col, markeredgecolor=col, markersize=7, label=lab)
               for _, lab, col, m in present]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.55, -0.004), ncol=3, frameon=False,
               fontsize=house.FS_LABEL, handletextpad=0.4, columnspacing=1.6)
    house.save(fig, f"{_cf.FIGS}/{STEM}")
    n = collections.Counter(r["direction"] for r in rows)
    _cf.data_statement(STEM, (
        f"All {len(rows)} of {len(rows)} rows in grain.csv are drawn (100%), one mark per reviewed work: "
        f"{len(on)} on the ordered scale (fine {n['fine']}, coarse {n['coarse']}) and {len(off)} off it "
        f"(about the parameter {n['meta']}, unspecified {n['unspecified']}, derived {n['derived']}, no bottom "
        f"{n['no-bottom']}, assumed {n['assumed']}). The nodes are grain.csv - every reviewed work that commits "
        "to or comments on a level, 31 keys from 1972 - and NOT the grain debate's position list in "
        "positions.csv, which is a different and smaller set (17 keys, from 1980). The two rungs are the file's "
        "own definition of `fine` and `coarse`; the works inside a rung are not ranked against each other, "
        "because no reviewed work argues that another's setting is wrong."))


if __name__ == "__main__":
    main()
