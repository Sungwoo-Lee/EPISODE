#!/usr/bin/env python3
"""SPECIMEN 1 - the house line chart.

QUESTION IT ANSWERS. None: this figure carries no measurement. It exists so the style module can
be seen rather than read, and so the style document embeds a figure that a script produced, like
every other figure in this project.

WHAT IS IN IT. Two series over a layer index, drawn entirely by `style/house.py`. Nothing about
the appearance is set here - no colours, no font sizes, no spine or grid handling. If this file
had to set any of those, the style module would have failed at its one job.

HOW IT IS COMPUTED. The numbers are a smooth analytic curve, stated as illustrative in the
caption. Using real data would make the specimen a result, and then a change to the house style
would look like a change to a finding.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
os.chdir(ROOT)

import matplotlib.pyplot as plt          # noqa: E402
import house                              # noqa: E402

OUT = os.environ.get("HOUSE_FIG_ROOT", "docs/develop/active/meta/figures")


def main():
    house.apply()
    x = np.arange(1, 17)
    # illustrative, not measured - a saturating curve and a shallower one
    a = 40 * (1 - np.exp(-x / 4.2))
    b = 18 * (1 - np.exp(-x / 7.5)) + 0.35 * x

    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    ax.plot(x, a, label="series 1")
    ax.plot(x, b, label="series 2")
    ax.set_xlabel("transformer layer index, counting from the embedding")
    ax.set_ylabel("effect size (arbitrary units)")
    ax.set_xticks([1, 4, 8, 12, 16])
    ax.set_xlim(0.5, 16.5)
    ax.set_ylim(0, 44)
    ax.set_yticks([0, 10, 20, 30, 40])
    house.legend_below(ax, ncol=2)
    fig.subplots_adjust(bottom=0.26, left=0.09, top=0.96)
    house.save(fig, f"{OUT}/spec01_line_chart")
    # the data-used line the page shows under the caption, emitted here rather than typed there
    n = len(x)
    with open(f"{OUT}/spec01_line_chart.data.txt", "w") as fh:
        fh.write(f"Illustrative, not measured: 2 analytic curves &times; {n} layer indices, "
                 f"all {2 * n} of {2 * n} points drawn (100%). No run, episode or seed is summarised.\n")


if __name__ == "__main__":
    main()
