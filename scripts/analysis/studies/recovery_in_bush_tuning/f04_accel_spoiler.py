#!/usr/bin/env python3
"""f04 - does any non-zero recovery_accel_rate survive the design?

QUESTION IT ANSWERS. f03 draws its feasible region at `recovery_accel_rate = 0`, which is a choice
that has to be defended rather than assumed. The worry is concrete: the shipped default sets accel
to 0.5, and compounding is exactly the thing that lets a small base rate clear a large wound if the
agent simply keeps resting. So the question is whether the design survives ANY positive accel, and
if so how much.

WHAT IS PLOTTED. For four base rates, the number of consecutive rest steps an agent needs IN THE
OPEN before it has cleared theta. The two horizontal rules are the rest budgets: where a curve
drops below a rule, the open can clear theta inside that budget and condition A has failed. The
marked point on each curve is that crossing, i.e. the largest accel that base rate can tolerate.

HOW IT IS COMPUTED. `recovery_math.steps_to_heal`, the closed-form inverse of the geometric sum:
at accel = 0 it is `theta / base`, and otherwise `log(1 + theta*accel/base) / log(1 + accel)`. The
value is a fractional step count; the environment takes whole steps, so the honest reading of a
curve at 47.3 is "48 rest steps". No environment is run.

KNOWN LIMITATION. The x-axis stops well short of the shipped 0.5 on purpose - by 0.12 every curve
has already collapsed, and drawing out to 0.5 would compress the only region where the answer
lives into the leftmost few pixels. The caption states where the shipped value is.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

STEM = "f04_accel_spoiler"
ACCEL_HI = 0.12


def _max_accel(base, budget):
    """Largest accel at which the open still needs MORE than `budget` rest steps to clear theta.

    Solved by bisection on the monotone `steps_to_heal`; returns None where even accel = 0 already
    fails, so the curve never crosses and there is nothing to mark.
    """
    if R.steps_to_heal(R.THETA, base, 0.0) <= budget:
        return None
    lo, hi = 0.0, 5.0
    if R.steps_to_heal(R.THETA, base, hi) > budget:
        return None
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if R.steps_to_heal(R.THETA, base, mid) > budget:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    house.apply()
    rec = R.recommend()
    a = np.linspace(0.0, ACCEL_HI, 601)

    series = [
        (0.05, K.C_OTHER, "base 0.05"),
        (R.SHIPPED["base"], K.C_SHIPPED, f"base {R.SHIPPED['base']:g}  (the shipped default's base)"),
        (rec["base"], K.C_REC, f"base {rec['base']:g}  (recommended)"),
        (R.A01["base"], K.C_A01, f"base {R.A01['base']:g}  (the a01 arm's base)"),
    ]

    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    for base, colour, label in series:
        y = R.steps_to_heal(R.THETA, base, a)
        ax.plot(a, y, color=colour, linestyle=K.OPEN_STYLE, label=label)
        cross = _max_accel(base, R.BUDGET)
        if cross is not None:
            ax.plot([cross], [R.BUDGET], marker="o", markersize=8, markerfacecolor=colour,
                    markeredgecolor=house.PAPER, markeredgewidth=1.8, linestyle="none", zorder=6)
            ax.annotate(f"{cross:.3f}", xy=(cross, R.BUDGET), xytext=(0, 13),
                        textcoords="offset points", ha="center", va="bottom",
                        fontsize=house.FS_LABEL, color=colour, zorder=7)

    for budget, style, name in ((R.BUDGET, "-", f"{R.BUDGET:g}-step rest budget (median start)"),
                                (R.BUDGET_FIXED_START, "--",
                                 f"{R.BUDGET_FIXED_START:g}-step budget (full start nutrition)")):
        ax.axhline(budget, color=K.C_RULE, linewidth=1.2, linestyle=style)
        ax.annotate(name, xy=(ACCEL_HI, budget), xytext=(-6, 5), textcoords="offset points",
                    ha="right", va="bottom", fontsize=house.FS_LABEL, color=K.C_RULE)

    ax.annotate("below a rule: the open clears the\nthreshold inside that budget,\n"
                "and the design has failed",
                xy=(0.062, 13), fontsize=house.FS_LABEL, color=house.INK_2,
                ha="left", va="center")

    ax.set_yscale("log")
    ax.set_xlim(0, ACCEL_HI)
    ax.set_ylim(3, 1200)
    ax.set_yticks([5, 10, 50, 100, 500, 1000])
    ax.set_yticklabels(["5", "10", "50", "100", "500", "1000"])
    ax.minorticks_off()
    ax.set_xlabel("recovery_accel_rate (extra healing per consecutive rest step, as a fraction)")
    ax.set_ylabel("consecutive rest steps in the open\n"
                  f"to clear {R.THETA:g} injury points")
    # Every hand-placed label is outlined in the page ground, so a data line crossing it cannot
    # eat a word (register F33, F52).
    for _t in ax.texts:
        _t.set_path_effects(house.halo())
    house.assert_text_inside_axes(ax)
    house.legend_below(ax, ncol=2)
    fig.subplots_adjust(bottom=0.32, left=0.12, top=0.97, right=0.98)
    house.save(fig, f"{K.OUT}/{STEM}")

    crossings = {b: _max_accel(b, R.BUDGET) for b, _, _ in series}
    named = ", ".join(f"base {b:g} tolerates up to accel {v:.3f}"
                      for b, v in crossings.items() if v is not None)
    K.data_statement(STEM, (
        f"Analytic, not measured: 4 base rates &times; 601 values of "
        f"<code>recovery_accel_rate</code> on 0&ndash;{ACCEL_HI:g}, all {4 * 601:,} of "
        f"{4 * 601:,} points drawn (100%). Two of the four base rates are shipped values "
        f"({R.SHIPPED['base']:g} from <code>default.yaml</code> and {R.A01['base']:g} from "
        f"<code>04-restprem_a01</code>); the other two are the recommendation and one lower "
        f"comparison. Crossings of the {R.BUDGET:g}-step budget, solved by bisection: {named}. "
        f"No run, episode or seed is summarised."))


if __name__ == "__main__":
    main()
