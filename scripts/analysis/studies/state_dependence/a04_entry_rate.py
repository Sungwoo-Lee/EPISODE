"""FIGURE 4 — When a predator is close, a wounded agent takes cover LESS often, not more.

WHAT THIS MEASURE IS, AND WHY IT IS THE HONEST ONE. Everything built on *where the agent is* shares
an artefact: a wounded agent mostly stops moving in order to heal, and whether that registers as
"hiding" depends only on whether it happened to be standing on a bush when it stopped. This measure
escapes that by scoring a DECISION instead of a location: among the moments when the agent is in the
open and chooses to move, how often does the move take it into cover? An agent that freezes leaves
the denominator rather than inflating the numerator.

WHAT IS PLOTTED. The change in that entry rate between the least and the most wounded quarter, with
a predator within two cells, in the first 25 steps of episodes whose starting injury was assigned at
random. Zero would mean a wound makes no difference to the decision. The project's prediction was
that it would be POSITIVE — that being hurt makes an agent take cover more readily when threatened.

It is negative in every condition measured. The analysis that these runs were built for did not
report this measure at all, although the tool that computes it names it as its headline.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
band = C.seed_scale()["mc"]["b0"]
CELLS = [("blind", f"{C.A}/context_prev", "prev_{arm}"),
         ("sighted", f"{C.A}/context", "lvl04_{arm}"),
         ("cover heals", f"{C.A}/context_w2", "lvl04_{arm}")]

fig, ax = plt.subplots(figsize=(10.0, 5.2))
x = np.arange(len(CELLS)); w = 0.34
for k, (arm, lab) in enumerate((("control", "ordinary agent"),
                                ("modulated", "neuromodulated agent"))):
    y, e = [], []
    for _, d, pat in CELLS:
        j = C.cell(d, pat, arm)
        v, ci = C.delta_b0(j) if j else (np.nan, np.nan)
        y.append(v); e.append(band)
    ax.bar(x + (k - 0.5) * w, y, width=w, color=C.ARMC[arm], edgecolor="none", label=lab)
    ax.errorbar(x + (k - 0.5) * w, y, yerr=e, fmt="none", ecolor=house.INK,
                elinewidth=1.3, capsize=3.6)
ax.axhline(0, color=house.INK, lw=1.2)
ax.set_xticks(x); ax.set_xticklabels([c[0] for c in CELLS], fontsize=10)
ax.set_ylabel("change in bush-entry rate (percentage points)")
ax.set_xlabel("the world the agent was trained in")
ax.set_ylim(-3.6, 1.5)
ax.annotate("the predicted direction was UP", xy=(-0.44, 1.15), fontsize=10,
            color=house.TEXT_LIGHT, ha="left", va="top")
ax.set_title("Being wounded makes the agent enter cover LESS when a predator is near\n"
             "Bars below zero in every world and for both agents. Error bars are the run-to-run "
             "spread from\nfive seeds of one unmodulated agent.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.legend_below(ax, ncol=2, offset=-0.22)
C.record_samples("a04_entry_rate", [
    dict(what="training runs", used=6, total=6,
         note="ordinary and neuromodulated at each of three worlds; one seed each"),
    dict(what="decision moments behind each bar", used=1, total=1,
         note="approximate millions: steps in the first 25 of a randomised-injury episode where the "
              "agent was in the open, chose to move, and a predator was within two cells"),
    dict(what="injury quarters compared", used=2, total=4,
         note="the lowest and the highest; the two middle quarters are computed but the span uses "
              "the ends")])
C.assert_ticks_dont_collide(ax); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
fig.tight_layout()
house.save(fig, os.path.join(C.FIG, "a04_entry_rate"), column_px=C.COLUMN_PX)
for nm, d, pat in CELLS:
    for arm in ("control", "modulated"):
        j = C.cell(d, pat, arm)
        if j: print(f"  {nm:12} {arm:10} dB0 = {C.delta_b0(j)[0]:6.2f}")
print(f"  seed SD = {band:.2f}")
