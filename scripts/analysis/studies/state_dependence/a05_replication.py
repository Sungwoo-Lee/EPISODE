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

fig, ax = plt.subplots(figsize=(10.0, 5.6))
y = np.arange(len(vals))[::-1]
ax.axvspan(-ss["mc"]["f2"], ss["mc"]["f2"], color=house.INK_2, alpha=0.10, lw=0,
           label="seed spread, the wider estimate")
ax.axvspan(-ss["gaenorm"]["f2"], ss["gaenorm"]["f2"], color=house.INK_2, alpha=0.18, lw=0,
           label="seed spread, the narrower estimate")
ax.axvline(0, color=house.INK, lw=1.2)
cols = {"no vision": house.TEXT_LIGHT, "vision on": house.BLUE, "cover heals": house.ORANGE}
for yi, v, b in zip(y, vals, blocks):
    ax.plot([0, v], [yi, yi], color=cols[b], lw=1.6, alpha=0.7, zorder=2)
    ax.plot([v], [yi], "o", ms=8.5, color=cols[b], zorder=3)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=10)
ax.set_xlim(-1.8, 2.1)
ax.set_xlabel("neuromodulated minus ordinary (percentage points per injury quarter)")
ax.set_ylabel("world, and level within it")
ax.grid(axis="y", visible=False)
ax.annotate("four from four here —\nthe shape of a real effect", xy=(-1.72, y[3] + 0.35),
            fontsize=10, color=house.BLUE, ha="left", va="center")
ax.annotate("and it reverses here", xy=(1.62, y[-1] + 0.9), fontsize=10,
            color=house.ORANGE, ha="right", va="center")
ax.set_title("Does the modulator change how threat-response grows with injury?\n"
             "Zero means it changed nothing. The bands are two estimates of how far apart two runs "
             "land when\nonly the random seed differs — which band you trust decides how much of "
             "this is 'significant'.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.legend_below(ax, ncol=2, offset=-0.20)
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
