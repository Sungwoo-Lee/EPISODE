"""TABLE — how much the scripted agent's own timing moves the headline numbers (plan-reviewer finding 1).

The agent goes to a need when that need's spare time (steps until it kills, minus the walk) falls below
`margin` steps. The page's figures use 25. This emits an HTML fragment of the share of episodes lasting
500 steps at margins 25, 50 and 100, for grid 10, 14 and 20, knows the pond / must find it, list
placement, planned drain and gain. The template embeds it via __TABLE:t1_margin__.
"""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C
from _sw import SW

rows = []
for g in (10, 14, 20):
    for sr, lab in ((False, "knows the pond"), (True, "must find it")):
        v = [100 * SW["margin"][f"{mg}|{g}|{sr}"]["survive"] for mg in (25, 50, 100)]
        rows.append(f'<tr><td>{g} × {g}</td><td>{lab}</td>' + "".join(f'<td class="n">{x:.0f} %</td>' for x in v)
                    + f'<td class="n">{100 * SW["no_water"][str(g)]["survive"]:.0f} %</td></tr>')
html = ('<p class="cue" hidden>Wider than the screen — scroll sideways.</p><div class="scroll">'
        '<table class="datatable wide"><thead><tr><th>grid</th><th>agent</th><th class="n">margin 25 (figures)</th>'
        '<th class="n">margin 50</th><th class="n">margin 100</th><th class="n">no water</th></tr></thead><tbody>'
        + "".join(rows) + '</tbody></table></div>'
        '<p class="prov">Emitted by <code>scripts/<wbr>analysis/<wbr>studies/<wbr>thirst_water/<wbr>t1_margin.py</code>'
        f' from <code>sweep.json</code>; {SW["_meta"]["E"]:,} episodes per cell.</p>')
os.makedirs(C.FIG, exist_ok=True)
open(os.path.join(C.FIG, "t1_margin.html"), "w").write(html)
print("wrote t1_margin.html")
