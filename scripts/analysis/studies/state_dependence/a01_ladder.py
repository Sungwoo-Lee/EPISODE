"""FIGURE 1 — What actually changes how much behaviour depends on the body: the world, not the brain.

THE QUANTITY. "State span" is how much more of an episode the agent spends hiding in a bush when it
is badly hurt than when it is unhurt, with no threat anywhere — in percentage points. It is measured
only on episodes whose STARTING injury was assigned at random, so the wound cannot be a consequence
of whatever the agent was already doing.

WHAT THE FIGURE COMPARES. Three versions of the world, in the order they were built. First an agent
with no vision at all. Then the same agent with vision switched on. Then the world where sitting in
cover is the only place a wound heals quickly. At each rung, an ordinary agent and one carrying a
neuromodulator — a small network that reads the body's state and rescales the signals flowing
through the rest of the brain, which is precisely the thing predicted to make behaviour depend more
on internal state.

THE SHADED BAND is what two training runs differing ONLY by their random seed do to this number,
measured from five seeds of one unmodulated agent. It is the scale any claimed difference has to beat.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
SS = C.seed_scale()
band = SS["mc"]["f1"]          # the conservative of the two estimators

vals = {}
for i, (lab, d, pat) in enumerate(C.RUNGS):
    for arm in ("control", "modulated"):
        j = C.cell(d, pat, arm)
        if j is not None:
            vals[(i, arm)] = C.causal(j)[0]

fig, ax = plt.subplots(figsize=(10.0, 5.4))
x = np.arange(len(C.RUNGS)); w = 0.34
for k, (arm, lab) in enumerate((("control", "ordinary agent"),
                                ("modulated", "neuromodulated agent"))):
    y = [vals.get((i, arm), np.nan) for i in x]
    ax.bar(x + (k - 0.5) * w, y, width=w, color=C.ARMC[arm], edgecolor="none", label=lab)
    for xi, yi in zip(x, y):
        if not np.isnan(yi):
            ax.errorbar(xi + (k - 0.5) * w, yi, yerr=band, fmt="none",
                        ecolor=house.INK, elinewidth=1.3, capsize=3.6)
ax.set_xticks(x); ax.set_xticklabels([r[0] for r in C.RUNGS], fontsize=10)
ax.set_ylabel("state span (percentage points)")
ax.set_xlabel("the world the agent was trained in")
ax.set_ylim(0, 28)   # headroom: a bar flush with the ceiling reads as clipped
ax.set_title("How much injury changes hiding, with no threat present\n"
             "Error bars are the run-to-run spread from five seeds of one unmodulated agent — "
             "the scale a\nreal difference has to beat. Each change to the WORLD clears it "
             "easily; the neuromodulator does not.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.legend_below(ax, ncol=2, offset=-0.22)
C.record_samples("a01_ladder", [
    dict(what="training runs shown", used=6, total=6,
         note="one ordinary and one neuromodulated run at each of the three worlds; every one is a "
              "single seed, which is the binding limit on this page"),
    dict(what="episodes behind each bar", used=1000000, total=1000000,
         note="the full trajectory store per run, all at seed_base 1,000,000 so the three worlds "
              "are compared on paired episode populations"),
    dict(what="episodes entering the causal estimate", used=20, total=24,
         note="approximate millions of step-rows: only steps in the first 25 of an episode whose "
              "starting injury was randomly assigned, with a predator within two cells"),
    dict(what="seeds behind the error bar", used=5, total=5,
         note="five seeds of one unmodulated agent in a fixed world; the conservative of the two "
              "return estimators is used")])
C.assert_ticks_dont_collide(ax); C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
fig.tight_layout()
house.save(fig, os.path.join(C.FIG, "a01_ladder"), column_px=C.COLUMN_PX)
for (i, arm), v in sorted(vals.items()):
    print(f"  rung {i} {arm:10} {v:6.2f}")
print(f"  seed SD (conservative) {band:.2f}")
