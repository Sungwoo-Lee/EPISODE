#!/usr/bin/env python3
"""f01 - what theta is, drawn: the height of a box whose diagonal is the healing-rate ceiling.

QUESTION IT ANSWERS. Theta is the one number on this page that nobody measured - it is the line
the study CHOOSES between "the open cannot really heal you" and "it can". Every later figure is
read against it, so a reader who does not have a picture of what theta does cannot read the theta
contour in f03 or the vertical lines in f04. This figure gives theta a shape.

THE IDEA, in one sentence. Condition A says a continuously-resting agent must not clear more than
theta injury points before its nutrition runs out, so draw theta as the HEIGHT of a box and the
rest budget as its WIDTH: a healing line passes condition A exactly when it is still inside the
box at the right-hand edge, and fails exactly when it leaves through the top.

WHY THE DIAGONAL MATTERS. At `recovery_accel_rate` = 0 the healing line is straight through the
origin, so "inside the box at the right-hand edge" is the same statement as "no steeper than the
box's diagonal". The diagonal's slope IS theta / budget - a rate, in injury points per rest step -
which is why condition A rearranges to `base <= theta / budget` and why theta and the budget never
have to be argued about separately: panel (b) shows a halved theta and a doubled budget producing
two differently-shaped boxes with the same diagonal.

HOW IT IS COMPUTED. Straight lines and rectangles from `recovery_math.THETA`, `.BUDGET` and
`.recommend()`; the two plotted settings are the same ones f02 draws. Nothing is typed.

KNOWN LIMITATION. The box picture is exact only at accel = 0. With a positive accel the healing
curve bends upward and can leave through the top after passing under the diagonal early - which is
the whole subject of f05, and is why this figure states its accel = 0 assumption on its face.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

STEM = "f01_theta_geometry"

XMAX_A = 62.0           # a little past the budget, so the right-hand edge is a line and not a wall
CEILING = R.THETA / R.BUDGET


def _box(ax, w, h, colour, lw=1.4, ls="-", fill=None):
    """The condition-A box: width = a rest budget, height = a threshold."""
    if fill is not None:
        ax.fill([0, w, w, 0], [0, 0, h, h], color=fill, zorder=0, linewidth=0)
    ax.plot([0, w, w], [h, h, 0], color=colour, linewidth=lw, linestyle=ls, zorder=3)


def panel_a(ax):
    """The box picture: theta is the height, the rest budget the width, the diagonal the ceiling."""
    rec = R.recommend()
    n = np.linspace(0, XMAX_A, 400)

    # The two reference rules ARE the box: everything below theta and left of the budget is the
    # region condition A allows a healing line to stay inside.
    ax.fill([0, R.BUDGET, R.BUDGET, 0], [0, 0, R.THETA, R.THETA],
            color=K.C_FAINT, zorder=0, linewidth=0)
    ax.axhline(R.THETA, color=K.C_RULE, linewidth=1.1, linestyle=":", zorder=3)
    ax.axvline(R.BUDGET, color=K.C_RULE, linewidth=1.1, linestyle=":", zorder=3)
    ax.plot([0, R.BUDGET], [0, R.THETA], color=K.C_RULE, linewidth=2.6, linestyle="--", zorder=4)

    # The two real settings this page argues about, in the hues the page already gives them.
    ax.plot(n, rec["base"] * n, color=K.C_REC, linewidth=2.2, zorder=5,
            label=f"recommended, in the open  (base {rec['base']:g} per rest step)")
    ax.plot(n, R.A01["base"] * n, color=K.C_A01, linewidth=2.2, zorder=5,
            label=f"a01 comparison setting, in the open  (base {R.A01['base']:g} per rest step)")

    ax.text(10.0, R.THETA + 1.2, f"θ = {R.THETA:g} points", ha="left", va="bottom",
            fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.text(R.BUDGET - 1.6, 98, f"{R.BUDGET:g}-step rest budget", ha="right", va="top",
            rotation=90, fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.text(19.5, 36.0, f"the diagonal is the CEILING:\nθ / budget = {CEILING:g} points per step",
            ha="left", va="bottom", fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.plot([R.BUDGET], [rec["base"] * R.BUDGET], "o", color=K.C_REC, markersize=7, zorder=6)
    ax.text(R.BUDGET + 1.6, rec["base"] * R.BUDGET + 4.0, "passes A", ha="left", va="bottom",
            fontsize=house.FS_LABEL, color=K.C_REC)
    ax.plot([R.THETA / R.A01["base"]], [R.THETA], "o", color=K.C_A01, markersize=7, zorder=6)
    ax.annotate(f"fails A — leaves through\nthe TOP after {R.THETA / R.A01['base']:g} rest steps",
                xy=(R.THETA / R.A01["base"], R.THETA), xytext=(13.0, 62.0),
                ha="left", va="top", fontsize=house.FS_LABEL, color=K.C_A01,
                arrowprops=dict(arrowstyle="-", color=K.C_A01, linewidth=0.9))

    ax.set_xlim(0, XMAX_A)
    ax.set_ylim(0, 100)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xlabel("consecutive rest steps in the open")
    ax.set_ylabel("cumulative injury healed\n(points of the 0-100 scale)")
    ax.set_title("(a) θ is the height of the box", fontsize=house.FS_BODY)


def panel_b(ax):
    """Same ceiling, two different boxes: halving theta and doubling the budget coincide."""
    half, dbl = R.THETA / 2.0, R.BUDGET * 2.0
    moved = half / R.BUDGET                                # == R.THETA / dbl, by construction
    assert abs(moved - R.THETA / dbl) < 1e-12
    xmax, ymax = dbl * 1.14, R.THETA * 1.90

    # the reference: drawn as its diagonal and its corner only, because its box would share a top
    # edge with the doubled-budget box and the two outlines would read as one
    ax.plot([0, R.BUDGET], [0, R.THETA], color=K.C_FAINT_INK, linewidth=1.4, linestyle=":")
    ax.plot([R.BUDGET], [R.THETA], "o", color=K.C_FAINT_INK, markersize=6, zorder=6)

    # the two MOVES - different boxes, one shared diagonal
    _box(ax, R.BUDGET, half, K.C_RULE, lw=1.5)
    _box(ax, dbl, R.THETA, K.C_RULE, lw=1.5)
    ax.plot([0, xmax], [0, moved * xmax], color=K.C_RULE, linewidth=2.8, linestyle="--", zorder=4)
    for x, y in ((R.BUDGET, half), (dbl, R.THETA)):
        ax.plot([x], [y], "o", color=K.C_RULE, markersize=7, zorder=6)

    ax.text(1.5, ymax - 0.8,
            f"two different boxes, ONE diagonal —\n"
            f"both moves give {moved:g} points per rest step",
            ha="left", va="top", fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.annotate(f"(a)'s ceiling: {CEILING:g}/step",
                xy=(R.BUDGET, R.THETA), xytext=(R.BUDGET - 4.0, R.THETA + 1.4),
                ha="right", va="bottom", fontsize=house.FS_LABEL, color=K.C_FAINT_INK,
                arrowprops=dict(arrowstyle="-", color=K.C_FAINT_INK, linewidth=0.9))
    ax.annotate(f"halve θ → {half:g}", xy=(R.BUDGET, half), xytext=(R.BUDGET + 6.0, half - 1.6),
                ha="left", va="top", fontsize=house.FS_LABEL, color=K.C_RULE,
                arrowprops=dict(arrowstyle="-", color=K.C_RULE, linewidth=0.9))
    ax.annotate(f"double the budget → {dbl:g}", xy=(dbl, R.THETA), xytext=(dbl + 3.0, R.THETA + 5.0),
                ha="right", va="bottom", fontsize=house.FS_LABEL, color=K.C_RULE,
                arrowprops=dict(arrowstyle="-", color=K.C_RULE, linewidth=0.9))

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, half, R.THETA, R.THETA * 1.5])
    ax.set_yticklabels([f"{v:g}" for v in (0, half, R.THETA, R.THETA * 1.5)])
    ax.set_xlabel("consecutive rest steps in the open")
    ax.set_ylabel("cumulative injury healed\n(points of the 0-100 scale)")
    ax.set_title("(b) only θ / budget is ever used", fontsize=house.FS_BODY)


def main():
    house.apply()
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(10.6, 5.0))
    panel_a(axa)
    panel_b(axb)

    handles = [
        Line2D([], [], color=K.C_RULE, linestyle="--", linewidth=2.4,
               label="the ceiling — a line of slope θ / budget"),
        Line2D([], [], color=K.C_RULE, linewidth=1.6,
               label="the box — θ tall, one rest budget wide"),
    ]
    axa.legend_ = None
    for ax in (axa, axb):
        for _t in ax.texts:
            _t.set_path_effects(house.halo())
        house.assert_text_inside_axes(ax)
    house.legend_below(axa, ncol=1)
    axb.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.20),
               ncol=1, frameon=False, fontsize=house.FS_LABEL)
    fig.subplots_adjust(bottom=0.33, left=0.085, top=0.91, right=0.975, wspace=0.28)
    house.save(fig, f"{K.OUT}/{STEM}")

    K.data_statement(STEM, (
        f"Analytic, not measured: 2 straight lines over 400 step counts in panel (a) and 2 boxes, "
        f"2 diagonals and 1 marked corner in panel (b) &mdash; every point drawn (100%), nothing "
        f"sampled or omitted. &theta; = {R.THETA:g} points and the {R.BUDGET:g}-step budget come from "
        f"<code>recovery_math</code>, which derives the budget from "
        f"<code>configs/environment/default.yaml</code>; the two plotted base rates are the "
        f"recommendation and the a01 comparison setting, the same two f02 draws. "
        f"No run, episode or seed is summarised; f06 is the one figure here that touches the "
        f"environment."))


if __name__ == "__main__":
    main()
