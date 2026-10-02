#!/usr/bin/env python3
"""_common.py - the page-wide colour and line-style map, and the figure output path.

NOT a figure script. It sets no font size, no gridline and no palette of its own: the four hues
below are `house.SERIES` under names that say what they MEAN on this page, which is the thing the
artifact guide asks for once per page (§10b item 39 - fix the colour to meaning map in the shared
module, with a comment saying why).

THE MAP, two dimensions:

    HUE   = WHICH SETTING of (recovery_base_rate, recovery_accel_rate, recovery_in_bush_multiplier)
            blue   the shipped default          base 0.1 / accel 0.5
            orange the rest-premium arm a01     base 5.0 / accel 0.0
            green  the recommendation           base 0.2 / accel 0.0 / multiplier 25
            red    a fourth comparison setting that belongs to no named regime

    STYLE = WHERE THE AGENT IS RESTING
            solid  in the open
            dashed on a concealing bush

Because all four hues are spent on categories here, the PAGE's chrome must not use any of them -
format register F11. The page states that and sets its section numbers, links and box borders in
ink and grey.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "analysis", "style"))
sys.path.insert(0, _HERE)

import house  # noqa: E402

#: Where every figure of this study is written. One place, so the builder and the scripts agree.
OUT = os.environ.get(
    "RECOVERY_FIG_ROOT",
    os.path.join(ROOT, "docs", "experiments", "active", "recovery_in_bush_tuning", "figures"))

C_SHIPPED = house.BLUE
C_A01 = house.ORANGE
C_REC = house.GREEN
C_OTHER = house.RED

OPEN_STYLE = "-"        # resting in the open
BUSH_STYLE = "--"       # resting on a concealing bush

#: Neutral ink for reference rules (θ, the rest budget) - a threshold is not a data series.
C_RULE = house.INK_2
C_FAINT = house.RULE
#: A dashed advisory line inside a figure is CHROME, not a data category, so it must not borrow one
#: of the four hues above (register F11). This is the neutral it uses instead.
C_FAINT_INK = house.TEXT_LIGHT


def data_statement(stem, text):
    """Write the used / available statement the page shows under the caption (guide §11b).

    Emitted by the figure script, never typed into the page. An analytic figure still has to
    declare what it drew and over what grid, because 'analytic' is not the same as 'exhaustive' -
    a sweep's range is a choice exactly like a data subset is.
    """
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{stem}.data.txt"), "w") as fh:
        fh.write(text.strip() + "\n")
    print(f"  wrote {OUT}/{stem}.data.txt")
