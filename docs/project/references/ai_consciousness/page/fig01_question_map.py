#!/usr/bin/env python3
"""FIGURE 1 - the seven questions of the field, and how an answer to one feeds the next.

The boxes are the seven questions in field_data/questions.csv, with their status in this collection.
They are grouped into three kinds: questions about what is possible in principle, questions about how
to tell in practice, and the question of what to do. The arrows are a READING AID written for this page
- they show which question a reader usually needs to settle before the next one makes sense. They are
not a claim made by any author.
"""
import textwrap
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import _aifig as _ai
from _aifig import house

STEM = "fig01_question_map"
# question id -> (column, row) in a 3-column grid; columns are the three kinds of question
LAYOUT = {"q7_fact": (0, 0), "q1_possible": (0, 1), "q2_what_copied": (0, 2), "q6_body": (0, 3),
          "q3_how_tell": (1, 1), "q4_llms": (1, 2), "q5_ethics": (2, 2)}
COLUMNS = ["In principle", "In practice", "What to do"]
EDGES = [  # from, to, label - the reading order, not an author's claim
    ("q7_fact", "q1_possible", "is the question well posed?"),
    ("q1_possible", "q2_what_copied", "if yes, what must be copied?"),
    ("q2_what_copied", "q6_body", "is the living body part of it?"),
    ("q1_possible", "q3_how_tell", "how could we tell?"),
    ("q3_how_tell", "q4_llms", "apply it to today's systems"),
    ("q4_llms", "q5_ethics", "what should we do?"),
]


def main():
    house.apply()
    Q = {r["question_id"]: r for r in _ai.read("questions.csv")}
    if set(Q) != set(LAYOUT):
        raise SystemExit(f"{STEM}: questions.csv ids {sorted(Q)} do not match the layout {sorted(LAYOUT)}")
    fig, ax = plt.subplots(figsize=(11.6, 6.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_position([0.01, 0.01, 0.98, 0.98])
    colx = [1, 38.5, 76]
    w, h = 23, 14.5
    for i, name in enumerate(COLUMNS):
        ax.text(colx[i] + w / 2, 97, name, ha="center", va="top", fontsize=house.FS_BODY,
                fontweight="semibold", color=house.INK_2)
    centre = {}
    for qid, (c, r) in LAYOUT.items():
        x0, y0 = colx[c], 88 - r * 22 - h
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                                    linewidth=1.1, edgecolor=house.RULE, facecolor=house.BG_SOFT, zorder=2))
        q = Q[qid]
        ax.text(x0 + 1.4, y0 + h - 1.6, "\n".join(textwrap.wrap(q["title"], 26)), ha="left", va="top",
                fontsize=house.FS_LABEL + 0.5, fontweight="semibold", color=house.INK, zorder=3, linespacing=1.15)
        ax.text(x0 + 1.4, y0 + 1.4, f"status in this collection: {q['status']}", ha="left", va="bottom",
                fontsize=house.FS_LABEL, color=house.TEXT_LIGHT, zorder=3)
        centre[qid] = (x0, y0, w, h)
    for a, b, lab in EDGES:
        xa, ya, wa, ha = centre[a]
        xb, yb, wb, hb = centre[b]
        if abs(xa - xb) < 1:          # same column: straight down
            p0, p1 = (xa + wa / 2, ya), (xb + wb / 2, yb + hb)
            tx, ty, al = xa + wa / 2 + 1.2, (ya + yb + hb) / 2, "left"
        else:                          # next column: from the right edge to the left edge
            p0, p1 = (xa + wa, ya + ha / 2), (xb, yb + hb / 2)
            tx, ty, al = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 5.0, "center"
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12, color=house.INK_2,
                                     lw=1.2, shrinkA=2, shrinkB=2, zorder=1))
        wrapw = 18 if al == "left" else 12
        ax.text(tx, ty, "\n".join(textwrap.wrap(lab, wrapw)), ha=al, va="center", fontsize=house.FS_LABEL,
                color=house.INK_2, style="italic", linespacing=1.1,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=house.PAPER, edgecolor="none"), zorder=4)
    house.save(fig, f"{_ai.FIGS}/{STEM}")
    _ai.note(STEM, (f"The {len(Q)} questions and their status come from field_data/questions.csv. The arrows "
                    "are a reading order written for this page, not a claim made by any author in the collection."))


if __name__ == "__main__":
    main()
