#!/usr/bin/env python
"""Figure 2 — where in a reinforcement-learning agent the modulation is injected.

Question: an actor-critic agent has several places conditioning could enter — the perceptual
encoder, the shared trunk, the actor, the critic, the world model — and the corpus disagrees
about which is conventional. One survey concluded "many sites, spread through the depth";
another found that does not survive restriction to RL, where papers inject once and late.
Counting the sites settles what the held papers actually do, though not what is best.

Known weakness: 'other' collects papers whose injection-site cell describes a site in terms
this classifier does not recognise (a bespoke module name, or a site named only by a figure
reference). It is a limit of the source cells, not evidence of an unusual site.
"""
from collections import Counter

import _style as S

S.apply_style()
import matplotlib.pyplot as plt  # noqa: E402

rows = S.load_corpus()
rl = [r for r in rows if r["is_rl"] == "RL" and r["site"] not in {"n/a", ""}]
counts = Counter(r["site"] for r in rl)

order = ["encoder", "trunk / all blocks", "actor only", "critic only", "actor + critic",
         "world model", "generated weights", "other"]
present = [k for k in order if counts.get(k)]
vals = [counts[k] for k in present]

# One colour per structural role; 'other' stays grey so it never reads as a finding.
role_color = {
    "encoder": "#1F8A8F", "trunk / all blocks": "#2E9AA0", "actor only": "#C2681B",
    "critic only": "#D98A3D", "actor + critic": "#8A4A12", "world model": "#6E4E9E",
    "generated weights": "#B03A5B", "other": "#B9C0C8",
}

fig, ax = plt.subplots(figsize=(9.4, 4.4))
bars = ax.bar(range(len(present)), vals, color=[role_color[k] for k in present],
              edgecolor="white", linewidth=0.8, width=0.66)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.025, str(v),
            ha="center", va="bottom", fontsize=10, fontweight="bold", color=S.INK)

ax.set_xticks(range(len(present)))
# Wrap EVERY multi-word label, not only the ones that looked long in the source. At eight
# categories each tick slot is about 11 characters wide, and "world model" beside
# "generated weights" overprinted each other while both looked short enough to leave alone.
ax.set_xticklabels([k.replace(" / ", "/\n").replace(" + ", " +\n").replace(" ", "\n")
                    for k in present], fontsize=9, linespacing=1.35)
ax.set_xlabel("Where the modulation enters the agent (injection site)")
ax.set_ylabel("Reinforcement-learning papers (count)")
ax.set_title("Injection site across the reinforcement-learning papers", loc="left")
ax.set_ylim(0, max(vals) * 1.18)
ax.yaxis.grid(True, color=S.GRID, linewidth=0.8)
ax.set_axisbelow(True)

S.record_samples("fig02_injection_site", [
    {"what": "RL papers whose injection-site cell names a site",
     "used": len(rl), "total": len(rows),
     "note": "excludes non-RL papers and theory papers with no site to name"},
    {"what": "of those, papers modulating a critic (alone or with the actor)",
     "used": counts.get("critic only", 0) + counts.get("actor + critic", 0),
     "total": len(rl),
     "note": "the corpus carries one older report that critic modulation is unstable and "
             "several newer ones that it helps; this is the count behind that dispute"},
])
S.finish(fig, "fig02_injection_site")
