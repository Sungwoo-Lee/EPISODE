"""FIGURE 2 — The same six agents, measured two ways, giving opposite answers.

WHY THIS FIGURE EXISTS. The first version of this analysis read the left-hand panel and concluded
that nothing changes how much behaviour depends on the body: six agents, built very differently, all
sat at about 21 points. That conclusion was an artefact of the measure.

THE DIFFERENCE BETWEEN THE PANELS. Left: every step of every episode, using whatever injury the
agent happened to be carrying. Right: only episodes whose STARTING injury was handed to the agent at
random, before it had done anything. The left panel is confounded by reverse causation — an agent
carrying a serious wound halfway through an episode was just bitten, and being bitten means a
predator was on top of it, which is itself what drove it into a bush. So the left panel largely
measures "what happens during a predator encounter", which is a property of the environment and is
therefore the same in every run. The right panel cannot contain that loop, because the wound was
assigned before the episode began.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
CELLS = [("blind", f"{C.A}/context_prev", "prev_{arm}"),
         ("sighted", f"{C.A}/context", "lvl04_{arm}"),
         ("cover heals", f"{C.A}/context_w2", "lvl04_{arm}")]

fig, ax = plt.subplots(1, 2, figsize=(10.4, 5.0), sharey=True)
x = np.arange(len(CELLS)); w = 0.34
for p, (panel, title) in enumerate((("observed", "what the agent happened to have\n(confounded)"),
                                    ("randomised_early", "starting injury assigned at random\n(causal)"))):
    for k, (arm, lab) in enumerate((("control", "ordinary agent"),
                                    ("modulated", "neuromodulated agent"))):
        y = []
        for _, d, pat in CELLS:
            j = C.cell(d, pat, arm)
            y.append(j[panel]["metrics"]["state_span"] if j else np.nan)
        ax[p].bar(x + (k - 0.5) * w, y, width=w, color=C.ARMC[arm], edgecolor="none", label=lab)
    ax[p].set_xticks(x); ax[p].set_xticklabels([c[0] for c in CELLS], fontsize=10)
    ax[p].set_title(title, fontsize=10, color=house.INK, loc="left", pad=8)
    ax[p].set_xlabel("world")
ax[0].set_ylabel("state span (percentage points)")
# 50, not 26: at 26 the cover-heals pair in the CONFOUNDED panel (45.3 and 46.5) was drawn
# clipped flat against the ceiling, so the figure showed 26 for a value of 46 and the caption
# describing the panel as 'all about 21' was reading its own clipped drawing.
ax[0].set_ylim(0, 50)
ax[0].annotate("blind and sighted are identical here\n— the vision effect is invisible",
               xy=(-0.42, 47.5), fontsize=10, color=house.RED, ha="left", va="top")
ax[1].annotate("vision doubles it, and it\nrises five-fold overall",
               xy=(-0.42, 47.5), fontsize=10, color=house.GREEN, ha="left", va="top")
C.legend_below(ax[0], ncol=2, offset=-0.24)
C.record_samples("a02_two_panels", [
    dict(what="training runs", used=6, total=6,
         note="ordinary and neuromodulated at each of three worlds; one seed each"),
    dict(what="step-rows in the confounded panel", used=104, total=104,
         note="approximate millions: every step of every episode, no restriction"),
    dict(what="step-rows in the causal panel", used=20, total=104,
         note="approximate millions: only the first 25 steps of episodes whose starting injury was "
              "randomly assigned — about a fifth of the data, which is the price of breaking the loop")])
C.assert_ticks_dont_collide(ax[0]); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
fig.tight_layout(w_pad=2.0)
house.save(fig, os.path.join(C.FIG, "a02_two_panels"), column_px=C.COLUMN_PX)
print("done a02")
