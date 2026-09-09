#!/usr/bin/env python
"""Figure 3 — what signal the modulator reads, and how rarely that signal is the observation.

Question: the corpus's sharpest claim is that conditioners in reinforcement learning are
drawn from task identity, language, an inferred belief, or measured physical parameters —
essentially never from the raw current observation feeding the pathway being modulated. This
figure counts the conditioners so the claim can be seen rather than asserted.

Horizontal bars, split by whether the paper runs a reinforcement-learning algorithm, because
the split is itself the finding: the observation-as-conditioner cases cluster in imitation
learning, where there is no policy gradient to entangle.

Known weakness: 'other' is large. The conditioner column is free text written by several
reviewers, and a cell that names a bespoke signal in prose lands in 'other' rather than being
forced into a class it does not fit.
"""
from collections import Counter

import _style as S

S.apply_style()
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

rows = S.load_corpus()
scored = [r for r in rows if r["cond_class"] not in {"n/a", ""}]

order = ["task / goal identity", "language instruction", "inferred belief / latent",
         "physical parameters", "own activity / statistic", "algorithmic knob",
         "exogenous phase / clock", "denoising timestep",
         "index / noise (not a task signal)", "observation (raw)", "other"]
present = [k for k in order if any(r["cond_class"] == k for r in scored)]

rl_counts = [sum(1 for r in scored if r["cond_class"] == k and r["is_rl"] == "RL") for k in present]
nrl_counts = [sum(1 for r in scored if r["cond_class"] == k and r["is_rl"] != "RL") for k in present]

y = np.arange(len(present))
fig, ax = plt.subplots(figsize=(9.4, 5.0))
ax.barh(y, rl_counts, height=0.62, color=S.PRIMARY, edgecolor="white", linewidth=0.7,
        label="Reinforcement learning")
# Hollow, not grey. S.NEUTRAL means "other / residual" on every other figure, and
# "not reinforcement learning" is a substantive class here, not a leftover — so the
# distinction is carried by fill-versus-outline instead of by a colour that is spoken
# for elsewhere (format defect F11).
ax.barh(y, nrl_counts, height=0.62, left=rl_counts, facecolor="white",
        edgecolor=S.PRIMARY, linewidth=1.1, hatch="///",
        label="Not reinforcement learning (vision, imitation, language)")

for i, (a, b) in enumerate(zip(rl_counts, nrl_counts)):
    if a + b:
        ax.text(a + b + 0.35, i, f"{a + b}", va="center", fontsize=9.5,
                fontweight="bold", color=S.INK)

ax.set_yticks(y)
ax.set_yticklabels(present)
ax.invert_yaxis()                       # most common at the top, reading downward
ax.set_xlabel("Papers held in this library (count)")
ax.set_ylabel("What the modulator reads (conditioning signal)")
ax.set_title("The conditioning signal, and where the raw observation sits", loc="left")
ax.xaxis.grid(True, color=S.GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xlim(0, max(a + b for a, b in zip(rl_counts, nrl_counts)) * 1.30)
# The legend goes OUTSIDE the axes. Inside, it collided with the longest bar at the top and
# with the longest bar at the bottom in turn — there is no free corner in a horizontal bar
# chart whose rows are sorted by length, so moving it around inside only relocates the defect.
ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.26), ncol=2, fontsize=9)

# Mark the row the review's central claim is about — and state the claim at the strength the
# data supports, which is narrower than "RL never does this".
if "observation (raw)" in present:
    i = present.index("observation (raw)")
    ax.annotate(f"{rl_counts[i]} RL papers — and in two of them the\n"
                f"stream being modulated is a different one",
                xy=(rl_counts[i] + nrl_counts[i] + 0.5, i), xytext=(30, 0),
                textcoords="offset points", va="center", fontsize=8.2,
                color=S.MUTED, linespacing=1.4)

S.record_samples("fig03_what_the_modulator_reads", [
    {"what": "papers whose conditioning-signal cell describes a signal",
     "used": len(scored), "total": len(rows),
     "note": "excludes surveys and theory papers whose cell is 'n/a' because they propose "
             "no particular conditioner"},
    {"what": "of those, papers running a reinforcement-learning algorithm",
     "used": sum(rl_counts), "total": len(scored),
     "note": "the darker segment of every bar"},
])
S.finish(fig, "fig03_what_the_modulator_reads")
