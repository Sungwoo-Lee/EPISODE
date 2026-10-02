#!/usr/bin/env python
"""Figure 4 — how much of the RL evidence you can actually lean on.

Question: the field cites modulation constantly, but how often does a paper isolate what the
modulation contributes, and how often is that paper refereed? This is the figure the review
turns on. Two panels sharing one y-scale (papers, count), because the reader is being asked
to compare them: left, claim strength; right, venue tier.

"Ablated" means the paper ran a controlled comparison of the conditioning mechanism against
an alternative. "Ablated (qualified)" means it ran one but a reviewer recorded a hedge that
stops the number being quotable — a confound left un-ablated, a figure with no printed
value, one run per configuration. That split is the point of the figure.
"""
from collections import Counter

import _style as S

S.apply_style()
import matplotlib.pyplot as plt  # noqa: E402

rows = S.load_corpus()
rl = [r for r in rows if r["is_rl"] == "RL"]

claims = Counter(r["claim"] for r in rl)
venues = Counter(r["venue_tier"] for r in rl)

claim_keys = [k for k in S.CLAIM_ORDER if claims.get(k)]
venue_keys = [k for k in S.VENUE_ORDER if venues.get(k)]
ymax = max(list(claims.values()) + list(venues.values())) * 1.18

fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))

for ax, keys, data, colors, title, xlab in (
    (axes[0], claim_keys, claims, S.CLAIM_COLORS,
     "Is the modulation isolated?", "Claim strength recorded by the reviewer"),
    (axes[1], venue_keys, venues, S.VENUE_COLORS,
     "Where was it published?", "Venue tier, as printed inside the PDF"),
):
    vals = [data[k] for k in keys]
    bars = ax.bar(range(len(keys)), vals, color=[colors[k] for k in keys],
                  edgecolor="white", linewidth=0.8, width=0.68)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + ymax * 0.02, str(v),
                ha="center", va="bottom", fontsize=10, fontweight="bold", color=S.INK)
    ax.set_xticks(range(len(keys)))
    # Wrap on the space so long tier names do not overflow their tick slot (F18).
    ax.set_xticklabels([k.replace(" ", "\n").replace("-", "-\n", 1) if len(k) > 11 else k
                        for k in keys], fontsize=9)
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlab, fontsize=9, color=S.MUTED)
    ax.set_ylim(0, ymax)
    ax.yaxis.grid(True, color=S.GRID, linewidth=0.8)
    ax.set_axisbelow(True)

axes[0].set_ylabel("Reinforcement-learning papers (count)")
axes[1].set_ylabel("Reinforcement-learning papers (count)")
fig.suptitle("Evidence quality across the reinforcement-learning slice of the corpus",
             x=0.005, ha="left", fontsize=13, fontweight="bold", color=S.INK)
fig.text(0.005, -0.04,
         "Both panels share one vertical scale and count the same "
         f"{len(rl)} papers, so bar heights are directly comparable.",
         fontsize=8.5, color=S.MUTED, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.94))

S.record_samples("fig04_evidence_quality", [
    {"what": "papers whose RL-algorithm column names a learning algorithm",
     "used": len(rl), "total": len(rows),
     "note": "imitation-learning and vision papers are excluded; they carry the mechanism "
             "lineage but cannot speak to whether modulation helps an RL agent"},
    {"what": "of those, ablations with no reviewer hedge against them",
     "used": claims.get("ablated", 0), "total": len(rl),
     "note": "the subset a quantitative claim in this review is allowed to rest on"},
])
S.finish(fig, "fig04_evidence_quality")
