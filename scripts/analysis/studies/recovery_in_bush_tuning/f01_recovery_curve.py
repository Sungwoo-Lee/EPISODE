#!/usr/bin/env python3
"""f01 - cumulative injury healed against consecutive rest steps, for four settings.

QUESTION IT ANSWERS. Two settings ship in this repository and they are not variations of one
another - they are qualitatively different problems. `recovery_accel_rate: 0.5` (the default)
compounds: each consecutive rest step heals 1.5x what the last one did, so the total explodes and
the whole injury scale is gone in a dozen steps. `recovery_accel_rate: 0.0` (the rest-premium arm
a01) is flat: the total is a straight line and the agent heals at a rate it can be reasoned about.
This figure puts the two on one pair of axes, with the recommended setting drawn in the open and
in cover, so the reader can see the gap the multiplier opens.

HOW IT IS COMPUTED. Closed form only - `recovery_math.cumulative`, evaluated at whole step counts
0..55, then clipped at `max_injury` because injury is clipped to [0, max_injury] every step and an
agent cannot heal more than the scale it is measured on. No environment is run here; f05 does that.

KNOWN LIMITATION. The curves describe an agent that rests on every step and takes no damage. A hit
suspends recovery for the `injury_smoothing_duration` steps over which it lands, while the rest
streak keeps climbing - so after a hit the accel = 0.5 curve is even steeper than drawn.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

STEM = "f01_recovery_curve"
NMAX = 55


def main():
    house.apply()
    rec = R.recommend()
    n = np.arange(0, NMAX + 1)

    series = [
        (R.SHIPPED["base"], R.SHIPPED["accel"], 1.0, K.C_SHIPPED, K.OPEN_STYLE,
         f"shipped default, in the open  (base {R.SHIPPED['base']:g}, accel {R.SHIPPED['accel']:g})"),
        (R.A01["base"], R.A01["accel"], 1.0, K.C_A01, K.OPEN_STYLE,
         f"rest-premium arm a01, in the open  (base {R.A01['base']:g}, accel {R.A01['accel']:g})"),
        (rec["base"], rec["accel"], 1.0, K.C_REC, K.OPEN_STYLE,
         f"recommended, in the open  (base {rec['base']:g}, accel {rec['accel']:g})"),
        (rec["base"], rec["accel"], rec["mult"], K.C_REC, K.BUSH_STYLE,
         f"recommended, on a bush  (x{rec['mult']:g} premium)"),
    ]

    fig, ax = plt.subplots(figsize=(7.8, 5.6))
    for i, (base, accel, mult, colour, style, label) in enumerate(series):
        y = R.healable(n, base, accel, mult)
        # The a01 line is drawn thick and the recommended-in-cover line thin on top of it, because
        # the two are the SAME rate: the recommendation anchors its in-cover healing to a01's flat
        # 5.0 per step. Without the width difference the overlap reads as a drawing fault.
        lw = 3.8 if i == 1 else 2.0
        ax.plot(n, y, color=colour, linestyle=style, linewidth=lw, label=label)

    ax.axhline(R.THETA, color=K.C_RULE, linewidth=1.1, linestyle=":")
    ax.axvline(R.BUDGET, color=K.C_RULE, linewidth=1.1, linestyle=":")
    ax.text(46.5, R.THETA + 2.2,
            f"the {R.THETA:g}-point threshold", ha="right", va="bottom",
            fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.text(R.BUDGET - 1.4, 97,
            f"{R.BUDGET:g}-step rest budget", ha="right", va="top", rotation=90,
            fontsize=house.FS_LABEL, color=K.C_RULE)
    ax.annotate("these two coincide by design:\nthe recommendation's in-cover rate\n"
                "IS a01's flat 5.0 per rest step",
                xy=(17.5, 87.5), xytext=(24.5, 60), fontsize=house.FS_LABEL, color=K.C_RULE,
                ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=K.C_RULE, linewidth=0.9))

    ax.set_xlabel("consecutive rest steps (whole environment steps)")
    # Two short lines, not one long one: a rotated label is measured against the AXES HEIGHT, and
    # this one at full length is taller than the plot it labels (guide 2.4).
    ax.set_ylabel("cumulative injury healed\n(points of the 0-100 scale)")
    ax.set_xlim(0, NMAX)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_ylim(0, 104)
    ax.set_yticks([0, 25, 50, 70, 100])
    # Every hand-placed label is outlined in the page ground, so a data line crossing it cannot
    # eat a word (register F33, F52).
    for _t in ax.texts:
        _t.set_path_effects(house.halo())
    house.assert_text_inside_axes(ax)
    house.legend_below(ax, ncol=1)
    fig.subplots_adjust(bottom=0.34, left=0.10, top=0.96, right=0.99)
    house.save(fig, f"{K.OUT}/{STEM}")

    K.data_statement(STEM, (
        f"Analytic, not measured: 4 settings &times; {len(n)} whole step counts (0&ndash;{NMAX}), "
        f"all {4 * len(n)} of {4 * len(n)} points drawn (100%). The two shipped settings are read "
        f"from <code>configs/environment/default.yaml</code> and "
        f"<code>configs/environment/experiment/archive/basic_bushrefuge_restpremium/"
        f"04-restprem_a01.yaml</code> rather than typed. No run, episode or seed is summarised; "
        f"the one figure on this page that touches the environment is f05."))


if __name__ == "__main__":
    main()
