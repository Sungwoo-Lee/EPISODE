"""TABLE E4 — every measure on the page, as a neuromodulated-minus-ordinary gap, per world and level.

Emitted as an HTML fragment (figures/e4_clue_table.html) that the page builder embeds, so no number in
it is typed by hand. The last column counts how many cells share the sign of the median gap: a gap
that points the same way in most worlds and levels is a better lead than a large one that flips.
Nothing here says how big a gap must be to matter -- with one training run per cell there is no
between-run spread to compare against -- so the table ranks leads, it does not test them.
"""
import sys, os, json, csv, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ladder"))
import numpy as np
import _common as C
from _ladder import proximity_effect

COLS = [c for c in C.COLUMNS if c[0] == "blind" or c[1] >= 4]


def lad(world, lvl, arm, key):
    d = C.ladder(world, lvl, arm)
    if d is None: return np.nan
    if key == "survival": return d["mean_survival"]
    if key == "hiding": return d["bush_dwell_pct"]
    g = d["grids"]; f = lambda k, b: proximity_effect(g[f"{k}_bush"], g[f"{k}_tot"], b)
    pre = f("pd", (3,)) - f("pd", (0,)); rab = f("rd", (3,)) - f("rd", (0,))
    return {"predshift": pre, "criterion": rab - pre}[key]


def drive(world, lvl, arm, i):
    z = C.npz(world, lvl, arm)
    return np.nan if z is None else C.spans(z, world)[i]


def entry_gap(world, lvl):
    g = C.paired_gaps(world, lvl, C.entry_change)
    return np.median(g) if g.size else np.nan


MEAS = [("survival (steps)", lambda w, l, a: lad(w, l, a, "survival"), "A1", "observational"),
        ("overall hiding (% of steps)", lambda w, l, a: lad(w, l, a, "hiding"), "A1", "observational"),
        ("injury span (pp)", lambda w, l, a: drive(w, l, a, 0), "A5", "causal"),
        ("hunger span (pp)", lambda w, l, a: drive(w, l, a, 1), "A5", "causal"),
        ("over-full span (pp)", lambda w, l, a: drive(w, l, a, 2), "A5", "causal"),
        ("bush-entry change (pp)", None, "A2", "causal"),
        ("wound's predator shift (pp)", lambda w, l, a: lad(w, l, a, "predshift"), "A4", "causal"),
        ("criterion shift (pp)", lambda w, l, a: lad(w, l, a, "criterion"), "A4", "causal")]
rows = []
for name, fn, fig, kind in MEAS:
    gaps = ([entry_gap(w, l) for w, l in COLS] if fn is None
            else [fn(w, l, "modulated") - fn(w, l, "control") for w, l in COLS])
    fin = np.array([g for g in gaps if np.isfinite(g) and round(g, 1) != 0.0])
    med = np.median(fin) if fin.size else np.nan
    agree = int((np.sign(fin) == np.sign(med)).sum()) if fin.size and med != 0 else 0
    rows.append((name, fig, kind, gaps, agree, fin.size, med))
groups = [("blind", [c for c in COLS if c[0] == "blind"]), ("Wave 1", [c for c in COLS if c[0] == "w1"]),
          ("Wave 2", [c for c in COLS if c[0] == "w2"])]
top = "".join(f"<th class=\"n\" colspan=\"{len(cs)}\">{g}</th>" if g != "blind" else
              f"<th class=\"n\" rowspan=\"2\">blind</th>" for g, cs in groups)
head2 = "".join(f"<th class=\"n\">{c[1]:02d}</th>" for c in COLS if c[0] != "blind")
body = ""
for name, fig, kind, gaps, agree, n, med in rows:
    cells = "".join(f"<td class=\"n\">{'—' if not np.isfinite(g) else f'{g:+.1f}'}</td>" for g in gaps)
    body += (f"<tr><td>{name} <span class=\"tag\">{fig} · {kind}</span></td>{cells}"
             f"<td class=\"agree\">{agree} of {n} {'below' if med < 0 else 'above'} zero</td></tr>")
html = ('<p class="cue" hidden>Scroll the table sideways to see every column.</p>\n<div class="scroll">'
        f'<table class="cluetable"><thead><tr><th rowspan="2">measure</th>{top}<th rowspan="2">agree</th></tr>'
        f'<tr>{head2}</tr></thead>'
        f'<tbody>{body}</tbody></table></div>')
os.makedirs(C.FIG, exist_ok=True)
open(os.path.join(C.FIG, "e4_clue_table.html"), "w").write(html)
for name, fig, kind, gaps, agree, n, med in rows:
    print(f"  {name:30} " + " ".join('   —  ' if not np.isfinite(g) else f"{g:+6.1f}" for g in gaps) + f"   {agree}/{n}")
