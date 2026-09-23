"""FIGURE 3 — The modulator is running, but nine tenths of what it does never changes.

WHY THIS FIGURE IS THE ONE THAT MAKES THE NULL MEAN SOMETHING. A behavioural null has a boring
explanation always available: perhaps the extra network was simply inert, in which case the result
says nothing about the idea behind it. This rules that out, and replaces it with something more
specific.

WHAT IS MEASURED. The neuromodulator's job is to emit a GAIN for every channel it modulates — a
number each feature gets multiplied by. Replaying trained agents on a fixed set of episodes and
recording every gain, its variation splits cleanly in two. Some of it is variation ACROSS CHANNELS:
channel 7 is always scaled up, channel 30 always scaled down, no matter what is happening. That part
is a learned constant, indistinguishable in effect from a fixed weight. The rest is variation ACROSS
TIME within a channel: the same channel scaled differently from moment to moment as the body's state
changes. Only that second part can make behaviour depend on internal state — it is the whole
mechanism the design rests on.

The share of the total that is the across-time part is plotted here, per site.
"""
import sys, os, csv, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _common as C, house

house.apply()
SRC = os.path.join(C.ROOT, "results/analysis/nmn_representation/mod_distribution_olf/distributions.csv")
rows = list(csv.DictReader(open(SRC)))
NICE = {"encoder_unimodal": "encoder\n(one sense at a time)",
        "encoder_multimodal": "encoder\n(senses combined)",
        "rnn": "memory\n(the recurrent core)",
        "actor": "actor\n(chooses the action)",
        "critic": "critic\n(judges the situation)"}
by = collections.defaultdict(list)
for r in rows:
    if r["site"] in NICE:
        by[r["site"]].append(float(r["gamma_rho"]))
order = sorted(by, key=lambda s: np.median(by[s]))

fig, ax = plt.subplots(figsize=(10.0, 5.2))
y = np.arange(len(order))
med = [100 * np.median(by[s]) for s in order]
# ORANGE, not blue. Every other figure teaches blue = ordinary agent / orange = neuromodulated,
# and this figure is measured on modulated arms only, so blue here would name the wrong agent.
ax.barh(y, med, color=house.ORANGE, height=0.62, edgecolor="none")
for i, s in enumerate(order):
    v = 100 * np.asarray(by[s])
    ax.plot(v, np.full_like(v, y[i], dtype=float), "o", ms=4.6,
            color=house.INK_2, alpha=0.55, zorder=3)
    # PAST THE RIGHTMOST DOT, not past the bar end. The bar end is the MEDIAN, so by construction
    # half the arms lie beyond it and a label anchored there lands inside the distribution every
    # time. The text-overlap guard cannot see this: the dots are a PathCollection, not text.
    ax.annotate(f"{med[i]:.0f}%", xy=(v.max() + 1.6, y[i]), va="center", fontsize=10,
                color=house.INK)
ax.axvline(50, color=house.RULE, lw=1)
ax.annotate("half", xy=(50.8, len(order) - 0.55), fontsize=10, color=house.TEXT_LIGHT,
            ha="left", va="top")
ax.set_yticks(y); ax.set_yticklabels([NICE[s] for s in order], fontsize=10)
ax.set_xlim(0, 60)
ax.set_xlabel("share of the modulator's gain variation that changes over time (%)")
ax.set_ylabel("where in the network the modulator acts")
ax.grid(axis="y", visible=False)
ax.set_title("Bars are the median across arms; each dot is one trained arm\n"
             "Everything to the left of the line is a modulator spending most of its output on a "
             "fixed\nper-channel rescaling — a learned constant — rather than on tracking the body.",
             fontsize=10, color=house.INK_2, loc="left", pad=8)
C.record_samples("a03_modulator_mechanism", [
    dict(what="arm × site combinations", used=len(rows), total=len(rows),
         note="every modulated arm of the two 16-cell grids, at every site it modulates"),
    dict(what="episodes replayed per arm", used=128, total=128,
         note="a fixed episode set shared by all arms, so arms are paired rather than each seeing "
              "its own worlds"),
    dict(what="grids represented", used=2, total=2,
         note="the Monte-Carlo and normalised-GAE twins; the figure pools them because the split "
              "is the same in both")])
C.assert_no_text_overlap(fig); C.assert_min_text_px(fig)
fig.tight_layout()
house.save(fig, os.path.join(C.FIG, "a03_modulator_mechanism"), column_px=C.COLUMN_PX)
allr = [float(r["gamma_rho"]) for r in rows]
print(f"  rho median {np.median(allr):.3f}  min {min(allr):.3f}  max {max(allr):.3f}  n={len(allr)}")
for s in order: print(f"    {s:20} median {100*np.median(by[s]):5.1f}%  n={len(by[s])}")
