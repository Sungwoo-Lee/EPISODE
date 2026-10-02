#!/usr/bin/env python3
"""f02 - the same recovery times, now against what hunger can pay for.

QUESTION IT ANSWERS. f01 asked how long recovery TAKES. It said nothing about whether the animal
has that long. This figure answers the second half by laying one horizontal line across f01's
curves: the number of consecutive rest steps the animal can afford before it starves. Above the
line, recovery is not slow - it is impossible, because the animal dies first.

WHY HUNGER AND NOTHING ELSE, YET. Hunger is the only competing demand on the same currency (steps)
that this page has measured. Body temperature is a second one and is being tuned elsewhere; when
that lands, it adds another line to this figure and changes nothing above it. That is the reason
the page is built in this order: f01 is a fact about recovery alone and does not move when a new
demand arrives.

HOW HUNGER ENTERS, AND ONLY HERE. A resting animal eats nothing while nutrition falls by
`metabolic_cost` every step, so it can rest `nutrition / metabolic_cost` times and no more. The
healing arithmetic itself has no hunger term at all - `recovery_math.cumulative` takes no nutrition
argument. Hunger sets how LONG; the recovery parameters set how MUCH. They meet only here.

KNOWN LIMITATION. Both lines are upper bounds in the strongest sense: an animal that really spends
its whole nutrition resting starves on the last step. So a curve sitting just under a line is not
actually survivable, and the figure is generous to the open by construction.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402
import f01_recovery_time as F1  # noqa: E402  - one definition of the curves, not two

STEM = "f02_against_hunger"


def main():
    house.apply()
    rec = R.recommend()
    wounds = np.linspace(F1.WMIN, R.MAX_INJURY, F1.NW)

    fig, ax = plt.subplots(figsize=(8.2, 5.6))

    # everything above the tighter of the two budgets is unaffordable: shade it once, faintly
    ax.axhspan(R.BUDGET, 900, color=K.C_FAINT, zorder=0, linewidth=0)
    F1.draw(ax, wounds)
    ax.set_ylim(2, 900)

    for budget, label in ((R.BUDGET, f"{R.BUDGET:g} steps &mdash; half a stomach"),
                          (R.BUDGET_FIXED_START, f"{R.BUDGET_FIXED_START:g} steps &mdash; full")):
        ax.axhline(budget, color=K.C_RULE, linewidth=1.4, linestyle=":")
    # budget labels on the RIGHT: the open-ground curve crosses both lines on the left
    ax.text(R.MAX_INJURY - 1.0, R.BUDGET_FIXED_START * 1.12,
            f"{R.BUDGET_FIXED_START:g} steps — a full stomach",
            ha="right", va="bottom", fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.text(R.MAX_INJURY - 1.0, R.BUDGET * 0.89,
            f"{R.BUDGET:g} steps — all half a stomach pays for",
            ha="right", va="top", fontsize=house.FS_LABEL, color=K.C_RULE)
    # the finding, not a generic statement about the shaded band
    ax.text(16.5, 780,
            "the recommendation in the open never dips\nbelow either line, at any wound size:\n"
            "recovery out there is unaffordable, full stop",
            ha="left", va="top", fontsize=house.FS_LABEL, color=K.C_REC)
    ax.text(R.MAX_INJURY - 1.0, 4.6,
            "below here recovery fits inside one\nstretch of resting, whatever the wound",
            ha="right", va="bottom", fontsize=house.FS_LABEL, color=K.C_FAINT_INK)
    ax.set_xticks([20, 40, 60, 80, 100])
    ax.set_yticks([3, 10, 30, 50, 100, 300])
    ax.set_yticklabels(["3", "10", "30", "50", "100", "300"])
    for _t in ax.texts:
        _t.set_path_effects(house.halo())
    house.assert_text_inside_axes(ax)
    house.legend_below(ax, ncol=1)
    fig.subplots_adjust(bottom=0.36, left=0.11, top=0.97, right=0.98)
    house.save(fig, f"{K.OUT}/{STEM}")

    w = R.WOUND
    _c = lambda x: int(np.ceil(float(x) - 1e-9))
    K.data_statement(STEM, (
        f"Analytic, not measured: the same 4 settings &times; {F1.NW} wound sizes as f01, all "
        f"{4 * F1.NW} of {4 * F1.NW} points drawn (100%), plus 2 horizontal rules at the two rest "
        f"budgets. Both budgets are derived, not chosen: {R.BUDGET:g} steps from the median of a "
        f"start nutrition drawn uniformly over 0&ndash;{R.MAX_NUTRITION:g}, and "
        f"{R.BUDGET_FIXED_START:g} from the full-nutrition start the shipped base world uses, both "
        f"at a metabolic cost of {R.METABOLIC_COST:g} per step read from "
        f"<code>configs/environment/default.yaml</code>. At the typical {w:g}-point wound the "
        f"recommendation needs {_c(R.steps_to_heal(w, rec['base'], rec['accel']))} steps in the "
        f"open against {_c(R.steps_to_heal(w, rec['base'], rec['accel'], rec['mult']))} on a bush. "
        f"No run, episode or seed is summarised."))


if __name__ == "__main__":
    main()
