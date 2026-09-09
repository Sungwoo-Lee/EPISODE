#!/usr/bin/env python
"""Figure 1 — which conditioning mechanism the field published, by year.

Question: has FiLM been displaced? The corpus's own prose says the affine operator got
renamed rather than retired (it reappears folded into a normalisation layer as adaLN), while
hypernetworks grew a separate RL literature. A stacked count by year is the cheapest way to
see whether that story is visible in the papers themselves.

Known weakness, stated on the page: this counts the papers THIS LIBRARY holds, not the
field. The library was assembled around a FiLM-centred research question, so FiLM is
over-represented relative to a neutral sample, and the 2026 column is a partial year.
"""
from collections import Counter

import _style as S

S.apply_style()
import matplotlib.pyplot as plt  # noqa: E402

rows = S.load_corpus()
dated = [r for r in rows if r["year"].isdigit() and 2015 <= int(r["year"]) <= 2026]
years = list(range(min(int(r["year"]) for r in dated), max(int(r["year"]) for r in dated) + 1))

counts = {m: [0] * len(years) for m in S.MECHANISM_ORDER}
for r in dated:
    m = r["mechanism"] if r["mechanism"] in counts else "other"
    counts[m][years.index(int(r["year"]))] += 1

fig, ax = plt.subplots(figsize=(9.2, 4.4))
bottom = [0] * len(years)
for m in S.MECHANISM_ORDER:
    vals = counts[m]
    if not any(vals):
        continue
    ax.bar(years, vals, bottom=bottom, label=m, color=S.MECHANISM_COLORS[m],
           edgecolor="white", linewidth=0.6)
    bottom = [b + v for b, v in zip(bottom, vals)]

ax.set_xlabel("Year of publication (year printed on the paper)")
ax.set_ylabel("Papers held in this library (count)")
ax.set_title("Conditioning mechanism by publication year", loc="left")
ax.set_xticks(years)
ax.set_xticklabels([str(y) for y in years], rotation=0)
ax.yaxis.grid(True, color=S.GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, 1.0))
# The caveat goes in EMPTY MARGIN, not over the plot. Placing it above the final column
# still printed it across the 2025 bar's segments, because "above the last bar" is inside
# the data area whenever a neighbouring bar is taller (format defect F33).
ax.set_xlim(years[0] - 0.8, years[-1] + 1.9)
ax.set_ylim(0, max(bottom) * 1.12)
ax.annotate("2026 is a\npartial year", xy=(years[-1] + 1.0, max(bottom) * 0.52),
            ha="center", va="center", fontsize=8, color=S.MUTED, linespacing=1.4)

# The reason string is DERIVED, not typed. It drifted once already: it claimed the
# excluded rows were undated survey entries, when in fact every row carries a year and the
# only exclusion is a single pre-window paper. A reason written beside a filter goes stale
# the moment the filter moves, so compute it from the same data the filter used.
_excluded = [r for r in rows if r not in dated]
_years_out = sorted({r["year"] for r in _excluded if r["year"].isdigit()})
_note = (f"the window starts at {years[0]}; "
         f"{len(_excluded)} paper(s) fall outside it"
         + (f", dated {', '.join(_years_out)}" if _years_out else "")
         + ". The corpus itself reaches further back than this axis does.")
S.record_samples("fig01_mechanism_over_time", [
    {"what": f"papers dated within the plotted window, {years[0]}\u2013{years[-1]}",
     "used": len(dated), "total": len(rows), "note": _note},
])
import json as _json
(S.FIGDIR / "_fig01_meta.json").write_text(_json.dumps(
    {"year_min": years[0], "year_max": years[-1]}))
S.finish(fig, "fig01_mechanism_over_time")
