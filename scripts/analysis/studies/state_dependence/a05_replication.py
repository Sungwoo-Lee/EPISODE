"""FIGURE 5 — The one place the modulator looked like it was doing something, and why it isn't.

WHAT IS PLOTTED. A second measure: not how much the agent hides when wounded, but how much a nearby
predator's effect on its hiding GROWS as the wound gets worse. The prediction behind the
neuromodulator is about exactly this — an interaction, the agent's response to the outside world
changing with the state of its body. Each row is the neuromodulated agent's value minus its
ordinary twin's, so zero means the modulator changed nothing.

WHY IT IS THE INTERESTING FIGURE. In the middle block — four levels of one world, the only place
this was ever looked at before — every one of the four comes out negative. Four from four, each
several times the noise floor if you use the narrow estimate. That is the shape of a real effect,
and it is what a one-world analysis would have reported.

It does not survive the other two worlds. In the blind world the same difference is POSITIVE; in the
cover-heals world the largest value is positive and bigger than anything in the middle block. A
mechanism that genuinely made behaviour depend on the body would not reverse when the scenery
changes. What reverses like this is noise that happened to line up.

THE TWO BANDS matter as much as the points. The narrow one is the seed spread of the return
estimator these runs used; the wide one is the spread of its twin. Which band you pick decides
whether nearly every point here is "significant" or nearly none is -- which is itself the argument
for measuring a noise floor rather than accepting the one a tool prints.
"""
import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
ss = C.seed_scale()
BLOCKS = [("no vision", [("GAE returns", f"{C.A}/context_prev", "prev_{arm}"),
                         ("MC returns", f"{C.A}/context_prevmc_mc", "prevmc_{arm}")]),
          ("vision on", [(l, f"{C.A}/context", l + "_{arm}") for l in
                         ("lvl03", "lvl04", "lvl05", "lvl06")]),
          ("cover heals", [(l, f"{C.A}/context_w2", l + "_{arm}") for l in
                           ("lvl04", "lvl05", "lvl06")])]
labels, vals, blocks = [], [], []
for bname, cells in BLOCKS:
    for lab, d, pat in cells:
        c, m = C.cell(d, pat, "control"), C.cell(d, pat, "modulated")
        if not c or not m:
            continue
        a, b = C.causal(c)[1], C.causal(m)[1]
        if math.isnan(a) or math.isnan(b):
            continue
        labels.append(f"{bname} · {lab.replace('lvl0', 'level 0')}")
        vals.append(b - a); blocks.append(bname)

fig, ax = plt.subplots(figsize=(10.0, 6.0))

# GROUPING BY GAP AND LABEL, NOT BY COLOUR. The first version drew the three blocks in the house
# blue and orange -- the exact values every other figure on the page uses for "ordinary agent" and
# "neuromodulated agent" -- so a reader arriving from Figure 4 met blue dots that were not the
# ordinary agent at all, and the third block was drawn in the tick ink. Every mark here is a
# DIFFERENCE between the two agents, so no agent colour can be correct for any of them. One data
# ink, and the blocks are separated by a real gap with their own label.
slot, gap, blocks_seen = [], 1.0, []
pos = 0.0
for bname, _ in BLOCKS:
    n = sum(1 for b in blocks if b == bname)
    if not n:
        continue
    if blocks_seen:
        pos += gap
    blocks_seen.append((bname, pos, n))
    for _ in range(n):
        slot.append(pos); pos += 1.0
y = np.asarray([max(slot) - v for v in slot])

ax.axvspan(-ss["mc"]["f2"], ss["mc"]["f2"], color=house.INK_2, alpha=0.10, lw=0,
           label="seed spread, the wider estimate")
ax.axvspan(-ss["gaenorm"]["f2"], ss["gaenorm"]["f2"], color=house.INK_2, alpha=0.20, lw=0,
           label="seed spread, the narrower estimate")
ax.axvline(0, color=house.INK, lw=1.2)
for yi, v in zip(y, vals):
    ax.plot([0, v], [yi, yi], color=house.INK_2, lw=1.5, alpha=0.55, zorder=2)
    ax.plot([v], [yi], "o", ms=8.5, color=house.INK, zorder=3)
short = [l.split(" \u00b7 ")[1] for l in labels]
ax.set_yticks(y); ax.set_yticklabels(short, fontsize=10)
ax.set_xlim(-2.0, 2.3)
ax.set_ylim(-0.9, max(y) + 0.9)
# Block names go in the left margin as their own text, which is what carries the grouping now.
for bname, p0, n in blocks_seen:
    ymid = max(slot) - (p0 + (n - 1) / 2.0)
    ax.annotate(bname.upper(), xy=(-1.94, ymid), fontsize=10, color=house.INK,
                ha="left", va="center")
ax.set_xlabel("neuromodulated minus ordinary (percentage points per injury quarter)")
ax.set_ylabel("world, and level within it")
ax.grid(axis="y", visible=False)
ax.set_title("Does the modulator change how threat-response grows with injury?\n"
             "Zero means it changed nothing. Every one of the four VISION ON rows is negative; the "
             "blocks either\nside of it reverse. The bands are two estimates of how far apart two "
             "runs land when only the seed differs.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.legend_below(ax, ncol=2, offset=-0.17)
C.record_samples("a05_replication", [
    dict(what="world × level comparisons", used=len(vals), total=9,
         note="every pairing where both agents have a populated causal panel; two curriculum levels "
              "never randomise starting injury and so cannot contribute"),
    dict(what="training runs behind them", used=18, total=18,
         note="one ordinary and one neuromodulated run per comparison, one seed each"),
    dict(what="seeds behind each band", used=5, total=5,
         note="five seeds of one unmodulated agent; the two bands are the two return estimators, "
              "which disagree about the noise floor by a factor of five")])
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
fig.tight_layout()
house.save(fig, os.path.join(C.FIG, "a05_replication"), column_px=C.COLUMN_PX)
for l, v in zip(labels, vals): print(f"  {l:32} {v:+6.2f}")
