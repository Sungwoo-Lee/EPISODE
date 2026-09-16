#!/usr/bin/env python3
"""f03 - how much injury the OPEN can clear inside one rest budget, over the (base, accel) plane.

QUESTION IT ANSWERS. The study's condition A is a statement about one number: the injury a
continuously-resting agent can clear outside cover before it starves. This figure computes that
number everywhere in the (recovery_base_rate, recovery_accel_rate) plane that any shipped config
occupies, and draws the contour where it equals theta. Inside that contour, resting in the open is
already not meaningfully recoverable; outside it, the open heals the agent whatever the bush does.

WHY TWO PANELS. Almost the whole plane saturates: at the shipped default the open clears the full
100-point injury scale in 16 rest steps, so a single panel over the shipped accel range is one flat
colour with the answer squeezed into a sliver along the bottom. Panel (b) is that sliver, enlarged.
Both panels share ONE colour scale, so a colour means the same number in each.

HOW IT IS COMPUTED. `recovery_math.open_healable`, which is the geometric sum of the per-step heal
`base * (1 + accel)**(n-1)` over n = 1..budget, clipped at `max_injury` because injury is clipped
to [0, max_injury] every step. Nothing is measured; f06 is the figure that touches the environment.

KNOWN LIMITATION. The budget is an UPPER bound and a fatal one - an agent that really spends its
whole nutrition resting starves at the end of it. So the map OVERSTATES what the open can heal, and
a setting that fails here fails conservatively.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as K            # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import house                   # noqa: E402
import recovery_math as R      # noqa: E402

STEM = "f03_open_ceiling"
BASE_LO, BASE_HI, NB = 0.01, 5.0, 241
ACCEL_HI_A, ACCEL_HI_B, NA = 0.5, 0.06, 241


def _panel(ax, accel_hi, cmap, vmax, marks, title, clabel_at):
    base_e = np.logspace(np.log10(BASE_LO), np.log10(BASE_HI), NB + 1)
    accel_e = np.linspace(0.0, accel_hi, NA + 1)
    base_c = np.sqrt(base_e[:-1] * base_e[1:])
    accel_c = 0.5 * (accel_e[:-1] + accel_e[1:])
    B, A = np.meshgrid(base_c, accel_c)
    Z = R.open_healable(B, A)

    mesh = ax.pcolormesh(base_e, accel_e, Z, cmap=cmap, vmin=0.0, vmax=vmax,
                         shading="flat", rasterized=True)
    cs = ax.contour(B, A, Z, levels=[R.THETA], colors=[house.INK], linewidths=1.6)
    cs.set_path_effects(house.halo(width=3.0))
    # Manual label placement: the automatic one lands the label wherever the contour happens to be
    # densest, which here is on top of a marker in one panel and on an annotation in the other.
    for t in ax.clabel(cs, fmt=lambda v: f"{v:g} points", fontsize=house.FS_LABEL, inline=True,
                       manual=[clabel_at]):
        t.set_path_effects(house.halo())

    for x, y, colour, label, dx, dy, ha in marks:
        if y > accel_hi:
            continue
        ax.plot([x], [y], marker="o", markersize=8, markerfacecolor=colour,
                markeredgecolor=house.PAPER, markeredgewidth=1.8, linestyle="none",
                clip_on=False, zorder=5)
        # A halo, not a colour choice. `--ink-2` is 8:1 on paper and about 1.5:1 on the dark end
        # of a colour ramp, and these three labels sit wherever their setting happens to land, so
        # no single ink is right everywhere. Outline them in the page ground instead (F52).
        ax.annotate(label, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=house.FS_LABEL, color=house.INK, zorder=6,
                    path_effects=house.halo(width=3.0))

    ax.set_xscale("log")
    ax.set_xlim(BASE_LO, BASE_HI)
    ax.set_ylim(-accel_hi * 0.035, accel_hi)
    ax.set_title(title, fontsize=house.FS_BODY)
    ax.grid(False)
    ax.set_xlabel("recovery_base_rate\n(injury points per rest step)")
    return mesh


def main():
    house.apply()
    rec = R.recommend()
    # NOT the shared house ramp. That one runs to --series-1 (blue), which on this page MEANS
    # "the shipped default" - so the blue marker sat on blue ground and survived only on its white
    # edge (register F11, second amendment). Fixed here rather than in `house.py`: the shared ramp
    # is blue by design and other pages depend on it.
    cmap = house.sequential(stops=[house.PAPER, "#dcdedb", "#a8adaa", "#6e747e", "#2b2f33"],
                            name="recovery_grey")
    vmax = R.MAX_INJURY

    marks_a = [(R.SHIPPED["base"], R.SHIPPED["accel"], K.C_SHIPPED, "shipped default", 12, -6, "left"),
               (R.A01["base"], R.A01["accel"], K.C_A01, "a01", -12, 14, "right"),
               (rec["base"], rec["accel"], K.C_REC, "recommended", -12, 16, "right")]
    marks_b = [(R.A01["base"], R.A01["accel"], K.C_A01, "a01", -12, 16, "right"),
               (rec["base"], rec["accel"], K.C_REC, "recommended", -12, 16, "right")]

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.8))
    _panel(axes[0], ACCEL_HI_A, cmap, vmax, marks_a,
           "(a) the whole shipped accel range", clabel_at=(0.30, 0.036))
    mesh = _panel(axes[1], ACCEL_HI_B, cmap, vmax, marks_b,
                  f"(b) the sliver, accel 0 to {ACCEL_HI_B:g}\n"
                  f"the shipped default's {R.SHIPPED['accel']:g} is "
                  f"{R.SHIPPED['accel'] / ACCEL_HI_B:.0f}x above this panel",
                  clabel_at=(0.185, 0.045))
    axes[0].set_ylabel("recovery_accel_rate\n(per-step compounding)")
    axes[1].set_ylabel("recovery_accel_rate")

    house.assert_text_inside_axes(axes)
    cb = fig.colorbar(mesh, ax=axes, fraction=0.035, pad=0.03)
    cb.set_label("injury healed in the open\nwithin the rest budget (points)",
                 fontsize=house.FS_BODY, color=house.INK)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=house.FS_LABEL, colors=house.TEXT_LIGHT)
    cb.set_ticks([0, 25, 50, 75, 100])
    house.save(fig, f"{K.OUT}/{STEM}")

    K.data_statement(STEM, (
        f"Analytic, not measured: a {NB} &times; {NA} grid of "
        f"(<code>recovery_base_rate</code>, <code>recovery_accel_rate</code>) per panel &mdash; "
        f"{NB * NA:,} cells drawn of {NB * NA:,} evaluated (100%) in each. Base rate spans "
        f"{BASE_LO:g}&ndash;{BASE_HI:g} on a log scale, which contains both shipped values "
        f"({R.SHIPPED['base']:g} and {R.A01['base']:g}); accel spans 0&ndash;{ACCEL_HI_A:g} in "
        f"panel (a), which contains both shipped values ({R.SHIPPED['accel']:g} and "
        f"{R.A01['accel']:g}), and 0&ndash;{ACCEL_HI_B:g} in panel (b). Rest budget "
        f"{R.BUDGET:g} steps. No run, episode or seed is summarised."))


if __name__ == "__main__":
    main()
