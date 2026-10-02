"""FIGURE pr03 - primer: how one panel of Figure A1 earns its word.

WHAT IS PLOTTED. Three made-up panels in the style of Figure A1, one per word the registered rule
can give a statistic on one layer. Each shows the 3 ordinary-ordinary pairs (blue) with the band
[L, U] they define, the 6 modulated-ordinary pairs at different seeds (orange) and the mean of those
6 with its bootstrap interval (orange bar). "different": all 6 left of L and the whole bar left of L.
"same": at most 2 of 6 left of L and the whole bar at or right of L. "undetermined at 3 seeds":
anything in between. The words come from the rule in the rules file, section 4 (A1
per_statistic_verdict); the positions are invented to show each case.

WHAT IT READS. Nothing: the positions are fixed toy values.

    python scripts/analysis/studies/modulator_clues/pr03_verdict_rule.py [--out <folder>]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np                                                         # noqa: E402
import matplotlib.pyplot as plt                                            # noqa: E402
import _an_common as C                                                     # noqa: E402
from _an_common import house                                               # noqa: E402

STEM = "pr03_verdict_rule"
BAND = (0.80, 0.84)
OO = [0.807, 0.822, 0.834]
SCEN = [("different", [0.742, 0.751, 0.758, 0.763, 0.770, 0.781], (0.752, 0.775)),
        ("same", [0.791, 0.806, 0.812, 0.820, 0.829, 0.837], (0.803, 0.826)),
        ("undetermined at 3 seeds", [0.768, 0.779, 0.788, 0.803, 0.815, 0.826], (0.782, 0.808))]


def word(mo, ci):
    """The registered rule, as the rules file states it (per_statistic_verdict)."""
    L = BAND[0]
    below = sum(v < L for v in mo)
    if below == len(mo) and ci[1] < L:
        return "different"
    if below <= len(mo) // 3 and ci[0] >= L:
        return "same"
    return "undetermined at 3 seeds"


def main():
    ap = argparse.ArgumentParser(description="primer figure pr03")
    ap.add_argument("--out", default=C.FIG_DIR)
    out = ap.parse_args().out
    house.apply()
    fig, axs = plt.subplots(1, 3, figsize=(10.4, 3.9), sharex=True)
    for ax, (name, mo, ci) in zip(axs, SCEN):
        got = word(mo, ci)
        if got != name:
            raise SystemExit(f"{STEM}: scenario '{name}' reads '{got}' under the rule; fix the toy values")
        ax.axvspan(*BAND, color=house.BLUE, alpha=0.15, lw=0)
        ax.axvline(BAND[0], color=house.BLUE, lw=1.2, ls="--")
        ax.text(BAND[0] - 0.003, 3.55, "L", ha="right", va="center", fontsize=house.FS_LABEL,
                color=house.BLUE)
        ax.scatter(OO, [3.0] * 3, color=house.BLUE, s=34, zorder=3)
        ax.scatter(mo, np.linspace(2.35, 1.35, len(mo)), color=house.ORANGE, s=34, zorder=3)
        ax.plot(ci, [0.8, 0.8], color=house.ORANGE, lw=6, solid_capstyle="butt")
        ax.set_ylim(0.4, 3.8)
        ax.set_yticks([3.0, 1.85, 0.8])
        ax.set_yticklabels(["ordinary pairs", "modulated vs\nordinary pairs", "their mean"]
                           if ax is axs[0] else ["", "", ""], fontsize=house.FS_LABEL)
        ax.set_title(name, loc="left", fontsize=house.FS_LABEL, color=house.INK)
        ax.set_xlim(0.72, 0.86)
        ax.set_xticks([0.74, 0.78, 0.82, 0.86])
        ax.grid(axis="y", visible=False)
    axs[1].set_xlabel("similarity score (higher = more alike)")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    C.illustration_footer(fig, y=0.04)
    C.finish(fig, STEM, out)
    C.write_illustration(STEM, out, f"fixed toy values in {STEM}.py; the rule is the one in the rules file", [
        {"what": "ordinary pairs per panel", "used": 3, "total": 3, "note": "as in the study: 3 seeds give 3 pairs"},
        {"what": "modulated-vs-ordinary pairs per panel", "used": 6, "total": 6,
         "note": "as in the study: 3 x 3 seeds minus the 3 same-seed pairs"},
        {"what": "panels", "used": 3, "total": 3, "note": "one per word the rule can give"}])


if __name__ == "__main__":
    main()
