"""FIGURE 5 - Can the agent tell a predator from a rabbit?

QUESTION. A rabbit cannot hurt the agent. If an arm hides just as hard for a nearby rabbit as for a
nearby predator, that arm is not discriminating - it is reacting to "an animal is near" and paying
for it in lost foraging time. This figure asks which sensory settings buy the ability to tell the
two apart.

WHAT THE ANSWER TURNS OUT TO BE. The arms split into two groups, and the split is not
sight-versus-no-sight. It is whether the agent's sight can resolve WHAT it is looking at. An agent
with a 13-cell visual field carrying eight appearance channels shows no rabbit response at all. An
agent whose visual field carries a single channel - it sees THAT something is there but not WHAT -
falls back into the same false alarm as an agent with no useful sight whatsoever.

HOW IT IS COMPUTED. For each arm and each animal class, the proximity effect is
    P(in bush | nearest animal 1-2 cells away) - P(in bush | nearest animal 6+ cells away)
in percentage points, over all 1,000,000 episodes. Distance is chebyshev (the moves a king would
need) and is read off the row BEFORE the step, since that is the observation the action was chosen
on. Counts are pooled before the ratio is taken, so a distance bin with more steps carries more
weight. The LEFT panel isolates the rabbit response, which is the part that is pure waste, and is the
simpler of the two to read: one number per arm. The RIGHT panel then adds the predator response
beside it with a line joining the pair, so the length of that line is the arm's discrimination.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, matplotlib.pyplot as plt
import _ladder as L, _plot as PL

D = L.load_all(); arms = L.ARM_ORDER
P = np.array([L.proximity_effect(D[a]["grids"]["pd_bush"], D[a]["grids"]["pd_tot"]) for a in arms])
R = np.array([L.proximity_effect(D[a]["grids"]["rd_bush"], D[a]["grids"]["rd_tot"]) for a in arms])

# Does the arm's visual field carry enough channels to tell a predator from a rabbit at range?
resolves_identity = lambda a: L.resolves_identity(D[a]["sensory"])

grp = np.array([resolves_identity(a) for a in arms])
CY, CN = PL.GROUP_YES, PL.GROUP_NO

# Panel order: the SIMPLER panel first. Every value on this figure is one subtraction, and a
# reader meeting it in the two-class panel has to hold two of those subtractions and the line
# between them at once. The rabbit-only panel is the same subtraction shown once, so it is where
# the quantity is easiest to learn -- and it is also the panel the finding is about. The two-class
# panel then reuses a quantity the reader already has.
#
# The subtraction itself is stated as a HEADING over each panel rather than buried in the fourth
# line of an axis label, because a reader who does not know what the numbers ARE cannot start.
# It is carried as the legend's title so it cannot collide with the legend the way a set_title
# with a hand-tuned pad would.
CONTRAST = "(hiding at 1-2 cells)  minus  (hiding at 6+ cells),  in percentage points"

fig, ax = plt.subplots(1, 2, figsize=(13.4, 6.2), sharey=True,
                       gridspec_kw={"width_ratios": [1, 1.25]})
y = np.arange(len(arms))

# ---- left: the rabbit response on its own -------------------------------------------------
ax[0].barh(y, R, color=[CY if g else CN for g in grp], height=0.72, edgecolor="none")
ax[0].axvline(0, color=PL.INK, lw=1)
ax[0].set_yticks(y); ax[0].set_yticklabels(PL.arm_ylabels(arms), fontsize=8)
ax[0].set_ylabel("sensor-ladder arm  (poorest senses at the bottom)")
ax[0].set_xlabel("right of zero = wasted hiding\nleft of zero = hides LESS when a rabbit is near")
ax[0].grid(axis="y", visible=False)
m = max(abs(R)) * 1.55
ax[0].set_xlim(-m, m)
for i in range(len(arms)):
    PL.outward_label(ax[0], R[i], y[i], m * 0.025)
hb = [plt.Rectangle((0, 0), 1, 1, color=CY, label="sight resolves WHAT it sees\n(visual range 2, 8 appearance channels)"),
      plt.Rectangle((0, 0), 1, 1, color=CN, label="sight cannot resolve WHAT it sees\n(range < 2, or a single channel)")]
ax[0].legend(handles=hb, loc="lower center", bbox_to_anchor=(0.5, 1.01), fontsize=8, ncol=1,
             title="FALSE ALARM \u2014 hiding for a nearby RABBIT, which cannot hurt it\n" + CONTRAST,
             title_fontsize=9.5)

# ---- right: the same contrast for both classes, so the gap is visible ----------------------
ax[1].hlines(y, R, P, color=PL.GRID, lw=2.4, zorder=1)
ax[1].scatter(R, y, s=54, color=PL.HARMLESS, zorder=3, label="nearest animal is a RABBIT (harmless)")
ax[1].scatter(P, y, s=54, color=PL.THREAT, zorder=3, label="nearest animal is a PREDATOR (a real threat)")
ax[1].axvline(0, color=PL.INK, lw=1)
ax[1].set_xlabel("left of zero = hides LESS when one is near")
ax[1].grid(axis="y", visible=False)
ax[1].legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=1, fontsize=8.5,
             title="BOTH CLASSES \u2014 the grey line's length is the arm's discrimination\n" + CONTRAST,
             title_fontsize=9.5)
for i in range(len(arms)):
    ax[1].text(P[i] + 1.2, y[i], f"gap {P[i]-R[i]:.0f}", va="center", fontsize=7, color=PL.MUTED)
ax[1].set_xlim(min(R.min(), 0) - 4, P.max() + 9)
POP = L.population()
def _bins(key, bins):
    return sum(int(np.asarray(D[a]["grids"][f"{key}_tot"], float)[list(bins)].sum()) for a in arms)
L.record_samples("lad05_discrimination", [
    dict(what="step rows with a predator 1-2 cells away", used=_bins("pd", L.NEAR_BINS),
         total=POP["steps"], note="the 'near' half of the predator contrast"),
    dict(what="step rows with a predator 6+ cells away", used=_bins("pd", L.FAR_BINS),
         total=POP["steps"], note="the 'far' half"),
    dict(what="step rows with a rabbit 1-2 cells away", used=_bins("rd", L.NEAR_BINS),
         total=POP["steps"], note="the 'near' half of the rabbit contrast"),
    dict(what="step rows with a rabbit 6+ cells away", used=_bins("rd", L.FAR_BINS),
         total=POP["steps"], note="the 'far' half. Distances 3-5 are plotted in Figure 4 but are "
                               "not part of this contrast")])

PL.assert_labels_fit(fig, ax)
PL.finish(fig, f"{L.FIG_ROOT}/lad05_discrimination.png")
print(f"{'arm':22}{'predator':>10}{'rabbit':>9}{'gap':>8}   resolves identity")
for i, a in enumerate(arms):
    print(f"{a:22}{P[i]:>10.1f}{R[i]:>9.1f}{P[i]-R[i]:>+8.1f}   {grp[i]}")
