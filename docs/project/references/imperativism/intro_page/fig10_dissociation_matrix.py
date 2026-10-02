#!/usr/bin/env python3
"""FIGURE 10 - what each experiment measured and what moved.

QUESTION IT ANSWERS. When a study claims that pain's parts come apart, which parts did it actually
measure, and which changed?

WHAT IS IN IT. One row per empirical study that measured two or more outcomes
(dissociation_evidence.csv), grouped by community and ordered by year. Columns are the five outcomes.
Glyphs, in ink only: a filled circle = changed (a significant change reported under the named manipulation);
an open circle = no significant change reported (NOT shown to be zero: no study ran an equivalence test);
a half-filled circle = a correlational relation, no manipulation; a small dash = not measured. Species and
number analysed are printed at the right, then what the coded cells compare (contrast_of): the named
manipulation, a painful-vs-non-painful stimulus contrast, attention conditions, a pre-task check, or no
manipulation at all (correlational). Rows whose sensation is not the participant's own pain carry a note.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
import _impfig as _imp
from _impfig import house

STEM = "fig10_dissociation_matrix"
CONTRAST = {"manipulation": "named manipulation", "stimulus-class": "painful vs non-painful",
            "attention-condition": "attention conditions", "pre-task": "pre-task check",
            "none-correlational": "correlational only"}
# Not the participant's own pain (synthesis section 5.2); the note keeps such rows from reading as pain evidence.
NOTE = {"hayen2017": " (breathlessness)", "budell2015": " (observed pain)", "han2017": " (observed pain)"}
COLS = [("intensity", "Intensity"), ("unpleasantness", "Unpleasant\nness"),
        ("avoidance_behaviour", "Avoidance\nor escape"), ("desire_or_urge", "Desire\nor urge"),
        ("reflex_or_nocifensive", "Reflex or\nnocifensive")]
DX = 2.7          # horizontal spacing between outcome columns, in data units (one row = 1 unit)
X_LABEL = -10.4   # study name column
X_SPECIES = (len(COLS) - 1) * DX + 1.9
X_CONTRAST = X_SPECIES + 5.1


def glyph(ax, x, y, code, r=0.26):
    if code == "changed":
        ax.add_patch(Circle((x, y), r, fc=house.INK, ec=house.INK, lw=1.2))
    elif code == "unchanged":
        ax.add_patch(Circle((x, y), r, fc=house.PAPER, ec=house.INK, lw=1.4))
    elif code == "correlational":
        ax.add_patch(Circle((x, y), r, fc=house.PAPER, ec=house.INK, lw=1.4))
        ax.add_patch(Wedge((x, y), r, 90, 270, fc=house.INK, ec=house.INK, lw=0))
    elif code == "not-measured":
        ax.plot([x - 0.12, x + 0.12], [y, y], color=house.TEXT_LIGHT, lw=1.4)
    else:
        raise SystemExit(f"unknown outcome code {code!r}")


def main():
    house.apply()
    W = _imp.works()
    order = {c[0]: i for i, c in enumerate(_imp.COMMUNITIES)}
    rows = sorted(_imp.read("dissociation_evidence.csv"),
                  key=lambda r: (order[W[r["key"]]["community"]], int(W[r["key"]]["year"])))
    n = len(rows)
    fig, ax = plt.subplots(figsize=(11.4, 0.4 * n + 2.2))
    ax.set_xlim(X_LABEL - 0.4, X_CONTRAST + 5.4)
    ax.set_ylim(-2.1, n + 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    for j, (_, lab) in enumerate(COLS):
        ax.text(j * DX, n + 0.1, lab, ha="center", va="bottom", fontsize=house.FS_LABEL, color=house.INK, linespacing=1.1)
    ax.text(X_SPECIES, n + 0.1, "species ·\nN analysed", ha="left", va="bottom", fontsize=house.FS_LABEL,
            color=house.INK_2, linespacing=1.1)
    ax.text(X_CONTRAST, n + 0.1, "what the codes\ncompare", ha="left", va="bottom", fontsize=house.FS_LABEL,
            color=house.INK_2, linespacing=1.1)
    prev = None
    for i, r in enumerate(rows):
        y = n - 1 - i
        w = W[r["key"]]
        c = w["community"]
        if prev is not None and c != prev:
            ax.plot([X_LABEL - 0.3, X_CONTRAST + 5.3], [y + 0.5, y + 0.5], color=house.RULE, lw=0.9)
        prev = c
        ax.scatter(X_LABEL, y, s=36, marker=_imp.MARKER[c], color=_imp.COLOUR[c], zorder=3)
        ax.text(X_LABEL + 0.4, y, w["short_label"] + NOTE.get(r["key"], ""), ha="left", va="center",
                fontsize=house.FS_LABEL, color=house.INK)
        for j, (col, _) in enumerate(COLS):
            glyph(ax, j * DX, y, r[col])
        n_txt = r["n_primary"] or "multi-group"
        ax.text(X_SPECIES, y, f"{r['species']} · {n_txt}", ha="left", va="center",
                fontsize=house.FS_LABEL, color=house.INK_2)
        ax.text(X_CONTRAST, y, CONTRAST[r["contrast_of"]], ha="left", va="center",
                fontsize=house.FS_LABEL, color=house.INK_2)
    legend = [("changed", "changed"), ("unchanged", "no significant change (not shown to be zero)"),
              ("correlational", "correlational only"), ("not-measured", "not measured")]
    for i, (code, lab) in enumerate(legend):
        lx, ly = X_LABEL + (0 if i % 2 == 0 else 9.0), -1.0 - 0.6 * (i // 2)
        glyph(ax, lx, ly, code, r=0.18)
        ax.text(lx + 0.35, ly, lab, ha="left", va="center", fontsize=house.FS_LABEL, color=house.INK)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    house.save(fig, f"{_imp.FIGS}/{STEM}")
    reviewed_emp = sum(1 for k, w in W.items() if w["status"] != "named-only")
    _imp.data_statement(STEM, (
        f"{n} studies are drawn: every reviewed empirical study that measured at least two of the five outcomes "
        f"(dissociation_evidence.csv); Budell 2015 stays as an empty row because its ratings were recoded as another "
        f"person's pain. The other reviewed works ({reviewed_emp - n} of {reviewed_emp}) are "
        "theory, reviews, philosophy, or measured fewer than two outcomes; named-only works are excluded because "
        "their measures were never read. Codes refer to the manipulation the row names."))


if __name__ == "__main__":
    main()
