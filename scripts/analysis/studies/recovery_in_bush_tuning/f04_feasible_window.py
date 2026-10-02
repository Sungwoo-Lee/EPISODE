#!/usr/bin/env python3
"""f04 - the answer figure: which (base rate, in-bush multiplier) pairs satisfy BOTH conditions.

QUESTION IT ANSWERS. The study asks for settings that make resting outside cover not meaningfully
recoverable WITHOUT making the world one where nobody can heal. Those are two conditions pulling in
opposite directions, and this is the plane where they are both visible: the base rate sets how fast
the open heals, and the multiplier sets how much better cover is. The shaded region is where both
hold; the marked point is the recommendation.

WHY accel = 0 HERE. f03 and f05 are the evidence: with any appreciable `recovery_accel_rate` the
open's healing compounds past theta inside the budget, so the accel = 0 plane is the one that has a
feasible region worth drawing. The rest-premium arm a01 is a real shipped config on this plane; the
shipped default is NOT (its accel is 0.5) and is deliberately not plotted.

TWO ALGEBRAIC FACTS THE FIGURE IS BUILT ON, both from `recovery_math` and neither typed:
  * at accel = 0, condition A is exactly `base <= theta / budget` - a VERTICAL line, and it depends
    on theta and the budget only through their RATIO, so halving theta and doubling the budget are
    the same move. That is why one set of vertical lines carries both sensitivities.
  * at accel = 0, condition B is exactly `base * multiplier >= wound / cover_steps` - a hyperbola
    in these coordinates, again depending only on the ratio.

KNOWN LIMITATION. The feasible region is unbounded upward: nothing in the stated definition stops a
multiplier so large that a bush erases a wound in one step. The dashed advisory line marks where a
70-point wound would close in under five rest steps, at which point cover has stopped being a place
to convalesce and become a heal button. That line is an opinion, not part of the definition.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

STEM = "f04_feasible_window"
BASE_LO, BASE_HI, NB = 0.02, 6.0, 321
MULT_LO, MULT_HI, NM = 0.8, 60.0, 321

FILL_FAIL_A = house.BG_SOFT       # the open already heals too well
FILL_FAIL_B = house.TICK_LINE     # cover cannot close a wound in time
FILL_OK = "#d8ebe2"               # both hold - the green of the recommendation, tinted


def main():
    house.apply()
    rec = R.recommend()

    base_e = np.logspace(np.log10(BASE_LO), np.log10(BASE_HI), NB + 1)
    mult_e = np.logspace(np.log10(MULT_LO), np.log10(MULT_HI), NM + 1)
    base_c = np.sqrt(base_e[:-1] * base_e[1:])
    mult_c = np.sqrt(mult_e[:-1] * mult_e[1:])
    B, M = np.meshgrid(base_c, mult_c)

    a_ok = R.open_is_unrecoverable(B, np.zeros_like(B))
    b_ok = R.cover_is_usable(B, np.zeros_like(B), M)
    cat = np.where(~a_ok, 0, np.where(~b_ok, 1, 2))

    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    ax.pcolormesh(base_e, mult_e, cat, cmap=house.categorical([FILL_FAIL_A, FILL_FAIL_B, FILL_OK]),
                  vmin=-0.5, vmax=2.5, shading="flat", rasterized=True)

    # condition A boundaries: base = theta / budget. One ratio, both sensitivities.
    for theta, budget, style, note in (
            (R.THETA, R.BUDGET, "-", "primary"),
            (R.THETA / 2.0, R.BUDGET, "--", "stricter"),
            (R.THETA * 2.0, R.BUDGET, ":", "looser")):
        x = theta / budget
        ax.axvline(x, color=house.INK, linestyle=style, linewidth=1.5 if note == "primary" else 1.1)
    ax.annotate(f"the open clears exactly {R.THETA:g} points in {R.BUDGET:g} rest steps",
                xy=(R.THETA / R.BUDGET, 6.4), xytext=(-8, 0), textcoords="offset points",
                ha="right", va="center", rotation=90,
                fontsize=house.FS_LABEL, color=house.INK)
    # Anchored at the SAME height as the solid line's label, not near the floor. With rotation=90
    # and ha="right" the text runs DOWNWARD from its anchor, so an anchor low on a log axis sends
    # it out through the bottom of the panel and over the x-axis title (register F18 amendment).
    ax.annotate("half the threshold", xy=(R.THETA / 2 / R.BUDGET, 6.4),
                xytext=(-8, 0), textcoords="offset points", ha="right", va="center", rotation=90,
                fontsize=house.FS_LABEL, color=house.INK_2)
    ax.annotate("twice the threshold", xy=(R.THETA * 2 / R.BUDGET, 2.1), xytext=(8, 0),
                textcoords="offset points", ha="left", va="center", rotation=90,
                fontsize=house.FS_LABEL, color=house.INK_2)

    # condition B boundaries: base * multiplier = wound / cover_steps.
    xs = np.logspace(np.log10(BASE_LO), np.log10(BASE_HI), 400)
    ax.plot(xs, (R.WOUND / R.COVER_STEPS) / xs, color=house.INK, linestyle="-", linewidth=1.5)
    ax.annotate(f"cover closes a {R.WOUND:g}-point wound\nin exactly {R.COVER_STEPS:g} rest steps",
                xy=(0.050, (R.WOUND / R.COVER_STEPS) / 0.050), xytext=(12, -4),
                textcoords="offset points", ha="left", va="top",
                fontsize=house.FS_LABEL, color=house.INK)

    # advisory ceiling, NOT part of the definition
    # NOT red: red is this page's fourth data category (f05's base 0.05 curve), and an advisory
    # annotation is chrome, not a category (register F11). Neutral ink, dashed.
    ax.plot(xs, (R.WOUND / R.COVER_STEPS_FLOOR) / xs, color=K.C_FAINT_INK, linestyle=(0, (5, 3)),
            linewidth=1.4)
    for x, y, colour, label, dx, dy, ha in (
            (R.A01["base"], R.A01["mult"], K.C_A01,
             f"a01 shipped\n(base {R.A01['base']:g}, no premium)", -8, 30, "right"),
            (rec["base"], rec["mult"], K.C_REC,
             f"RECOMMENDED\nbase {rec['base']:g}, x{rec['mult']:g}", 0, -28, "center")):
        ax.plot([x], [y], marker="o", markersize=9, markerfacecolor=colour,
                markeredgecolor=house.PAPER, markeredgewidth=2.0, linestyle="none", zorder=6)
        ax.annotate(label, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=house.FS_LABEL, color=house.INK, zorder=7)

    # Every hand-placed label is outlined in the page ground: several of them sit on top of the
    # condition boundaries, and a 1.5px black line through a word is enough to lose it (F33, F52).
    for t in ax.texts:
        t.set_path_effects(house.halo())

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(BASE_LO, BASE_HI)
    ax.set_ylim(MULT_LO, MULT_HI)
    ax.set_yticks([1, 2, 5, 10, 20, 50])
    ax.set_yticklabels(["1x", "2x", "5x", "10x", "20x", "50x"])
    ax.minorticks_off()
    ax.set_xlabel("recovery_base_rate (injury points healed per rest step, in the open)")
    ax.set_ylabel("recovery_in_bush_multiplier\n(healing in cover, as a multiple)")
    ax.grid(False)

    handles = [Line2D([], [], color=K.C_FAINT_INK, linestyle=(0, (5, 3)), linewidth=1.4,
                      label=f"advisory ceiling \u2014 above it a {R.WOUND:g}-point wound closes in "
                            f"under {R.COVER_STEPS_FLOOR:g} rest steps (not part of the definition)"),
               Patch(facecolor=FILL_OK, edgecolor=house.RULE,
                     label="both conditions hold"),
               Patch(facecolor=FILL_FAIL_A, edgecolor=house.RULE,
                     label="the open heals too well (condition A fails)"),
               Patch(facecolor=FILL_FAIL_B, edgecolor=house.RULE,
                     label="condition A holds, but cover heals too slowly (B fails)")]
    leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.155), ncol=1,
                    frameon=False)
    for t in leg.get_texts():
        t.set_color(house.INK)
        t.set_fontsize(house.FS_LABEL)
    fig.subplots_adjust(bottom=0.33, left=0.12, top=0.97, right=0.98)
    house.assert_text_inside_axes(ax)
    house.save(fig, f"{K.OUT}/{STEM}")

    K.data_statement(STEM, (
        f"Analytic, not measured: a {NB} &times; {NM} grid of (<code>recovery_base_rate</code>, "
        f"<code>recovery_in_bush_multiplier</code>) at <code>recovery_accel_rate</code> = 0 "
        f"&mdash; {NB * NM:,} cells classified of {NB * NM:,} evaluated (100%). Base rate spans "
        f"{BASE_LO:g}&ndash;{BASE_HI:g} and the multiplier {MULT_LO:g}&ndash;{MULT_HI:g}, both on "
        f"log scales. One of the two shipped settings is on this plane and is marked "
        f"(<code>04-restprem_a01</code>, accel 0); the other is NOT and is deliberately absent "
        f"(<code>default.yaml</code> has accel {R.SHIPPED['accel']:g}). No run, episode or seed "
        f"is summarised."))


if __name__ == "__main__":
    main()
