#!/usr/bin/env python3
"""f01 - the primitive question: how many rest steps does recovery take?

QUESTION IT ANSWERS. Before any talk of food, thresholds or allowances, recovery has one plain
property: given the healing settings, how long does undoing a wound actually take? That is a
property of the recovery parameters alone. It needs no budget, no threshold and no reward - it is
just the healing arithmetic read in the direction a reader thinks in, which is TIME.

WHY THIS IS FIRST. An earlier draft of this page led with "how much injury can be cleared inside a
budget", which forced a threshold (theta) and a food limit into the first paragraph and invited two
misreadings: theta read as an injury LEVEL, and the budget read as how long healing takes. Steps
have no such ambiguity. f02 then adds food; nothing before it needs to.

WHAT THE FIGURE SHOWS. Rest steps to undo one wound, against the size of that wound, for the two
settings that ship and the recommendation in and out of cover. Three readings fall out of it:
compounding nearly erases wound size (the shipped default takes 11 steps for a scratch and 16 for a
near-fatal wound); flat healing scales in proportion; and the in-bush multiplier is visible as the
gap between the recommendation's two curves, which is exactly the multiplier.

KNOWN LIMITATION. Consecutive rest is assumed - any other action resets the streak, which only
matters for the compounding curve. The wound axis stops at max_injury because a larger wound is not
something to recover from; it is death.
"""
import os
import sys

import math

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

STEM = "f01_recovery_time"
WMIN = 15.0                    # the lightest hit the jump-attack world deals
NW = 400


def series():
    rec = R.recommend()
    return [
        (R.SHIPPED["base"], R.SHIPPED["accel"], 1.0, K.C_SHIPPED, K.OPEN_STYLE,
         f"shipped default, in the open  (base {R.SHIPPED['base']:g}, "
         f"compounding {R.SHIPPED['accel']:g})"),
        (R.A01["base"], R.A01["accel"], 1.0, K.C_A01, K.OPEN_STYLE,
         f"a01 comparison setting, in the open  (base {R.A01['base']:g}, no compounding)"),
        (rec["base"], rec["accel"], 1.0, K.C_REC, K.OPEN_STYLE,
         f"recommended, in the open  (base {rec['base']:g}, no compounding)"),
        (rec["base"], rec["accel"], rec["mult"], K.C_REC, K.BUSH_STYLE,
         f"recommended, on a bush  (the same base, {rec['mult']:g}x in cover)"),
    ]


def draw(ax, wounds):
    for i, (base, accel, mult, colour, style, label) in enumerate(series()):
        y = np.array([float(R.steps_to_heal(w, base, accel, mult)) for w in wounds])
        # index 1 is a01 and index 3 is the recommendation in cover: the SAME rate, by clause 2 of
        # the selection rule. Draw a01 thick and the other thin on top, so the overlap reads as
        # deliberate rather than as one badly drawn line.
        ax.plot(wounds, y, color=colour, linestyle=style,
                linewidth=3.8 if i == 1 else 2.2, label=label)
    ax.set_yscale("log")
    ax.set_xlim(WMIN, R.MAX_INJURY)
    ax.set_xlabel("size of the wound to undo (injury points)")
    ax.set_ylabel("rest steps needed\n(log scale)")


def main():
    house.apply()
    rec = R.recommend()
    wounds = np.linspace(WMIN, R.MAX_INJURY, NW)

    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    draw(ax, wounds)
    ax.set_ylim(2, 900)

        # the readings, put on the figure rather than left to the caption. Whole steps: the
    # simulation has no fractional step, so a wound cleared partway through step 11 takes 11.
    _ceil = lambda x: math.ceil(float(x) - 1e-9)
    s_lo = _ceil(R.steps_to_heal(WMIN, R.SHIPPED["base"], R.SHIPPED["accel"]))
    s_hi = _ceil(R.steps_to_heal(R.MAX_INJURY, R.SHIPPED["base"], R.SHIPPED["accel"]))
    ax.text(58, 6.4,
            f"compounding almost erases wound size:\n{s_lo:g} steps for the lightest hit, "
            f"{s_hi:g} for a fatal one",
            ha="left", va="top", fontsize=house.FS_LABEL, color=K.C_SHIPPED)

    # the multiplier, drawn as the vertical distance it actually is
    w_mid = 70.0
    open_n = _ceil(R.steps_to_heal(w_mid, rec["base"], rec["accel"]))
    cov_n = _ceil(R.steps_to_heal(w_mid, rec["base"], rec["accel"], rec["mult"]))
    ax.annotate("", xy=(w_mid, open_n), xytext=(w_mid, cov_n),
                arrowprops=dict(arrowstyle="<->", color=K.C_REC, linewidth=1.3))
    ax.text(w_mid - 2.5, 62,
            f"{rec['mult']:g}x, read as time:\n{open_n:g} rest steps out here,\n{cov_n:g} on a bush",
            ha="right", va="center", fontsize=house.FS_LABEL, color=K.C_REC)
    # kept clear of the block above: same x-band would have the two notes touching
    # y sits between the 30 and 100 gridlines: a rule running through the text reads as a
    # strike-through, and the halo cannot fix occlusion (register F33 amendment).
    ax.text(16.5, 52, "a01 and recommended-in-cover\ncoincide: the same rate",
            ha="left", va="center", fontsize=house.FS_LABEL, color=K.C_FAINT_INK)

    ax.set_xticks([20, 40, 60, 80, 100])   # uniform: 70 is marked by the arrow, not a tick
    ax.set_yticks([3, 10, 30, 100, 300])
    ax.set_yticklabels(["3", "10", "30", "100", "300"])
    for _t in ax.texts:
        _t.set_path_effects(house.halo())
    house.assert_text_inside_axes(ax)
    house.legend_below(ax, ncol=1)
    fig.subplots_adjust(bottom=0.36, left=0.11, top=0.97, right=0.98)
    house.save(fig, f"{K.OUT}/{STEM}")

    K.data_statement(STEM, (
        f"Analytic, not measured: 4 settings &times; {NW} wound sizes spanning the whole range the "
        f"world can deal and an animal can survive &mdash; {WMIN:g} injury points (the lightest "
        f"hit the jump-attack world draws) to {R.MAX_INJURY:g} (the scale itself) &mdash; all "
        f"{4 * NW} of {4 * NW} points drawn (100%), none omitted. The two shipped settings are "
        f"read from their YAML files at run time rather than transcribed. No run, episode or seed "
        f"is summarised; f06 is the one figure on this page that touches the environment."))


if __name__ == "__main__":
    main()
