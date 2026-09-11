"""FIGURE 4 - Does the agent hide more when a predator is close, and does that need eyes?

QUESTION. Hiding is only defensive if it is triggered by the threat. This figure plots bush
occupancy against how far the nearest predator was when the agent chose its move, one curve per
arm. A flat curve means the agent hides on a schedule; a rising-toward-zero curve means it hides
in response to something it perceived.

HOW IT IS COMPUTED. For every step, the distance from the agent to the nearest ACTIVE predator is
measured in chebyshev steps (the number of moves a king would need, since the agent moves
diagonally too). The action that produced step t was chosen while the agent was looking at step
t-1, so the distance is read off the PREVIOUS row and the bush occupancy off the current one.
Distances of 8 or more are pooled into one bin. A bin with fewer than 1,000 steps is left as a
gap rather than drawn as a noisy point.

WHAT IT CANNOT SHOW. Predator distance is not randomised - a predator is close partly because of
where the agent went. This curve is therefore descriptive. The causal claims in this report come
from the randomised starting wound (Figures 8-11) and the randomised odour draw (Figure 12).
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _ladder as L, _plot as PL

D = L.load_all(); arms = L.ARM_ORDER
x = np.arange(1, L.DIST_MAX + 1)
GRP = {a: L.resolves_identity(D[a]["sensory"]) for a in arms}
# The four the prose names. Everything else is background, drawn thin so the shape of the two
# families is still visible without fourteen near-identical colours competing for attention.
# Colour carries the family (can this arm's sight resolve WHAT it is looking at?), so the two
# named arms inside a family were drawn identically and could only be told apart by the label at
# the end of the line. Give each named arm its own dash pattern and marker as well. These carry
# no meaning beyond identity -- they exist so a reader can follow one line across the panel.
# HUE still means the family, so the two families stay readable at a glance. Within a family the
# second named arm takes a shifted SHADE of the same hue -- darker orange, lighter green -- kept
# close enough to read as the same family and far enough to separate two lines that cross.
SPOT = {"A_baseline":  ("smell, no direction",   "-",  "o", PL.GROUP_NO),
        "B_olf_only":  ("smell with direction",  "--", "s", PL.GROUP_NO_ALT),
        "V4_blur05":   ("reference agent",       "-",  "o", PL.GROUP_YES),
        "V5_sharp":    ("sharp sight",           "--", "^", PL.GROUP_YES_ALT)}

fig, ax = plt.subplots(1, 2, figsize=(12.8, 5.6), sharey=True)
for j, (key, ttl) in enumerate([("pd", "Nearest PREDATOR - a real threat"),
                                ("rd", "Nearest RABBIT - harmless by construction")]):
    ends = []   # in the rabbit panel three named lines finish within a few points of each other
    for a in arms:
        g = D[a]["grids"]
        y = L.dist_curve(g[f"{key}_bush"], g[f"{key}_tot"])
        c = PL.GROUP_YES if GRP[a] else PL.GROUP_NO
        if a in SPOT:
            _, ls, mk, c = SPOT[a]
            ax[j].plot(x, y, lw=2.4, color=c, ls=ls, marker=mk, ms=5.0, zorder=3)
            ends.append((x[-1], y[-1], f" {a}", c))
        else:
            ax[j].plot(x, y, lw=1.0, color=c, alpha=0.34, zorder=2)
    ax[j].set_title(ttl, fontsize=10, color=PL.INK, loc="left", pad=8)
    # Name the timestep on each axis rather than paraphrasing it. "when it decided" read as
    # though the ANIMAL decided, and the one thing the reader needs is that the two axes come
    # from DIFFERENT rows: the distance the agent was looking at, and what it then did.
    ax[j].set_xlabel("distance to the nearest animal at step t-1")
    ax[j].set_xticks(x); ax[j].set_xticklabels(L.DIST_NAMES)
    ax[j].set_xlim(0.7, L.DIST_MAX + 1.6)
    PL.stagger_end_labels(ax[j], ends)
ax[0].set_ylabel("bush hiding at step t  (% of those steps spent in a bush)")
# The ten background arms were drawn thin with no way to find out what they were; the legend said
# only "the other ten". Name them. They stay individually unidentifiable BY DESIGN -- ten more
# colours would bury the two-family shape this figure is about -- so the legend says that too,
# rather than leaving the reader to work out that no key is coming. Built from ARM_ORDER so it
# cannot go stale if an arm is added or renamed.
rest = [a for a in arms if a not in SPOT]
rest_txt = "thin, unlabelled = the other %d arms, drawn to show the shape of each family.\n" % len(rest)
rest_txt += "They are not told apart individually here: " + ", ".join(rest[:5]) + ",\n" + ", ".join(rest[5:])
h = [plt.Line2D([], [], color=PL.GROUP_YES, lw=2.2, label=L.GROUP_LABEL[True] + "  (9 arms)"),
     plt.Line2D([], [], color=PL.GROUP_NO, lw=2.2, label=L.GROUP_LABEL[False] + "  (5 arms)"),
     plt.Line2D([], [], color=PL.MUTED, lw=2.4, ls="-", marker="o", ms=4.6,
                label="thick, with markers = one of the four arms the text discusses, named at the\n"
                      "end of its line. Hue is the family; shade, dashes and marker mark only identity"),
     plt.Line2D([], [], color=PL.MUTED, lw=1.0, alpha=0.34, label=rest_txt)]
ax[0].legend(handles=h, loc="lower center", bbox_to_anchor=(1.03, 1.055), ncol=1, fontsize=8.3,
             labelspacing=0.85, handletextpad=0.9)
POP = L.population()
pd_used = sum(int(np.asarray(D[a]["grids"]["pd_tot"], float).sum()) for a in arms)
rd_used = sum(int(np.asarray(D[a]["grids"]["rd_tot"], float).sum()) for a in arms)
L.record_samples("lad04_threat_distance_curve", [
    dict(what="step rows, predator panel", used=pd_used, total=POP["steps"],
         note="excludes episodes containing no predator, and each episode's first step, "
              "which has no previous row to read the distance from"),
    dict(what="step rows, rabbit panel", used=rd_used, total=POP["steps"],
         note="same, for episodes containing no rabbit")])

PL.assert_labels_fit(fig, ax)
PL.finish(fig, f"{L.FIG_ROOT}/lad04_threat_distance_curve.png")
print(f"{'arm':22}" + "".join(f"{d:>7}" for d in L.DIST_NAMES) + "   (predator, % in bush)")
for a in arms:
    g = D[a]["grids"]
    print(f"{a:22}" + "".join(f"{v:>7.1f}" for v in L.dist_curve(g["pd_bush"], g["pd_tot"])))
